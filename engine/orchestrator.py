#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Orquestrador Central
Executa a esteira completa:
1. Varredura e parsing da caixa postal central
2. Extração de alias e correlação com cliente
3. Triagem semântica (órgão, prazo, severidade, processo)
4. Roteamento e envio via WhatsApp Web aos advogados e contadores
5. Persistência de auditoria e controle de duplicidade no SQLite
"""

import json
from datetime import datetime
from typing import Dict, Any, List

from .config import logger, find_client_by_alias, load_clients
from .email_connector import EmailConnector
from .triage import TriageClassifier
from .whatsapp_sender import WhatsAppSender, format_alert_message
from .clickup_logger import ClickUpLogger
from .state_db import (
    log_scan_start, log_scan_finish, record_processed_message,
    update_whatsapp_status, is_message_processed
)

class LiveMonitorOrchestrator:
    """Orquestrador do fluxo autônomo do Live Monitor."""

    def __init__(self):
        self.email_connector = EmailConnector()
        self.classifier = TriageClassifier()
        self.whatsapp_sender = WhatsAppSender()
        self.clickup_logger = ClickUpLogger()

    def run_scan(self) -> Dict[str, Any]:
        """
        Executa uma rodada completa de varredura e notificação.
        Retorna relatório de execução.
        """
        scan_id = log_scan_start()
        logger.info(f"=== [LIVE MONITOR] INICIANDO VARREDURA (Scan ID: {scan_id}) ===")

        emails_found = 0
        emails_processed = 0
        whatsapp_sent = 0
        errors = 0
        details = []

        try:
            candidates = self.email_connector.fetch_unprocessed_emails(limit=50)
            emails_found = len(candidates)

            for item in candidates:
                msg_id = item["message_id"]
                content_hash = item["content_hash"]
                subject = item["subject"]
                sender = item["sender"]
                date_str = item["date"]
                matched_client = item.get("client")
                matched_alias = item.get("matched_alias")

                logger.info(f"Processando e-mail: '{subject}' | De: {sender} | Alias: {matched_alias}")

                # 1. Se não encontrou cliente associado ao alias
                if not matched_client:
                    logger.warning(f"E-mail {msg_id} recebido sem cliente mapeado para os aliases: {item.get('alias_candidates')}")
                    # Registra no banco como não mapeado para não processar em loop
                    record_processed_message({
                        "message_id": msg_id,
                        "content_hash": content_hash,
                        "client_id": "unmapped",
                        "alias_detected": str(item.get("alias_candidates")),
                        "sender": sender,
                        "subject": subject,
                        "received_date": date_str,
                        "category": "unmapped_alias",
                        "agency": "Desconhecido",
                        "process_number": "N/D",
                        "prazo_dias": None,
                        "data_limite": None,
                        "urgency": "baixa",
                        "attachments_json": json.dumps([a["filename"] for a in item.get("attachments", [])]),
                        "whatsapp_status": "skipped_unmapped",
                        "error_message": "Nenhum cliente cadastrado no clients.yaml para este alias."
                    })
                    continue

                # 2. Executa a Triagem Semântica
                triage = self.classifier.analyze(item)
                logger.info(f"Resultado da triagem para '{subject}': Órgão: {triage.get('agency')}, Urgência: {triage.get('urgency')}, Destino: {triage.get('target_role')}")

                # 3. Registra no banco
                attachments_list = item.get("attachments", [])
                record_id = record_processed_message({
                    "message_id": msg_id,
                    "content_hash": content_hash,
                    "client_id": matched_client.get("id"),
                    "alias_detected": matched_alias,
                    "sender": sender,
                    "subject": subject,
                    "received_date": date_str,
                    "category": triage.get("category"),
                    "agency": triage.get("agency"),
                    "process_number": triage.get("process_number"),
                    "prazo_dias": triage.get("prazo_dias"),
                    "data_limite": triage.get("data_limite"),
                    "urgency": triage.get("urgency"),
                    "attachments_json": json.dumps([a["filename"] for a in attachments_list]),
                    "whatsapp_status": "pending"
                })

                emails_processed += 1

                # 4. Verifica se é relevante para disparo
                if not triage.get("is_relevant", True):
                    logger.info(f"Mensagem {msg_id} classificada como não relevante. Disparo ignorado.")
                    update_whatsapp_status(msg_id, "skipped_irrelevant", "")
                    continue

                # 5. Resolve os contatos que devem receber a notificação
                recipients = self._resolve_recipients(matched_client, triage)
                if not recipients:
                    logger.warning(f"Cliente {matched_client.get('id')} não possui contatos de advogados/contadores configurados para esta categoria.")
                    update_whatsapp_status(msg_id, "skipped_no_recipients", "")
                    continue

                # 6. Formata mensagem e envia via WhatsApp Web
                alert_text = format_alert_message(matched_client.get("name", "Cliente"), triage, date_str)
                send_success_all = True
                sent_phones = []

                for rec in recipients:
                    phone = rec.get("whatsapp")
                    name = rec.get("nome", "Parceiro")
                    logger.info(f"Enviando alerta para {name} ({phone})...")
                    
                    # Checa envio de PDF
                    send_pdf = matched_client.get("configuracoes", {}).get("enviar_pdf_anexo", True)
                    att_to_send = attachments_list if send_pdf else None

                    success = self.whatsapp_sender.send_notification(phone, alert_text, att_to_send)
                    if success:
                        whatsapp_sent += 1
                        sent_phones.append(phone)
                    else:
                        send_success_all = False
                        errors += 1

                # Atualiza status no banco
                final_status = "sent" if send_success_all else ("partial" if sent_phones else "failed")
                update_whatsapp_status(
                    msg_id,
                    final_status,
                    ",".join(sent_phones),
                    None if send_success_all else "Falha no envio para um ou mais destinatários"
                )

                details.append({
                    "message_id": msg_id,
                    "client": matched_client.get("id"),
                    "agency": triage.get("agency"),
                    "recipients": sent_phones,
                    "status": final_status
                })

        except Exception as e:
            logger.error(f"Erro crítico durante a varredura: {e}", exc_info=True)
            errors += 1
        finally:
            summary = f"Encontrados: {emails_found} | Processados: {emails_processed} | WhatsApp Enviados: {whatsapp_sent} | Erros: {errors}"
            log_scan_finish(scan_id, emails_found, emails_processed, whatsapp_sent, errors, summary)
            logger.info(f"=== [LIVE MONITOR] VARREDURA FINALIZADA: {summary} ===")

        result = {
            "scan_id": scan_id,
            "emails_found": emails_found,
            "emails_processed": emails_processed,
            "whatsapp_sent": whatsapp_sent,
            "errors": errors,
            "details": details
        }

        # Registra log detalhado no ClickUp (se configurado)
        try:
            clickup_task_id = self.clickup_logger.log_scan_run(result)
            if clickup_task_id:
                result["clickup_task_id"] = clickup_task_id
        except Exception as cu_err:
            logger.warning(f"Erro ao registrar log no ClickUp: {cu_err}")

        return result

    def _resolve_recipients(self, client: Dict[str, Any], triage: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Determina os contatos de advogados e contadores a serem notificados
        com base no perfil do cliente e na classificação da intimação.
        """
        destinatarios = client.get("destinatarios", {})
        advogados = destinatarios.get("advogados", [])
        contadores = destinatarios.get("contadores", [])

        target_role = triage.get("target_role", "ambos")
        category = triage.get("category", "")
        urgency = triage.get("urgency", "media")

        selected = []

        # Roteamento para advogados
        if target_role in ("advogados", "ambos") or urgency == "critica":
            for adv in advogados:
                rules = adv.get("notificar_em", ["todos"])
                if "todos" in rules or any(r in category or r in rules for r in [category, "judicial", "urgente"]):
                    selected.append(adv)

        # Roteamento para contadores
        if target_role in ("contadores", "ambos"):
            for cont in contadores:
                rules = cont.get("notificar_em", ["todos"])
                if "todos" in rules or any(r in category or r in rules for r in [category, "receita_geral", "dte", "sefaz", "prefeitura"]):
                    selected.append(cont)

        # Remove duplicatas de telefone
        unique_recipients = []
        seen_phones = set()
        for rec in selected:
            phone = rec.get("whatsapp", "").strip()
            if phone and phone not in seen_phones:
                seen_phones.add(phone)
                unique_recipients.append(rec)

        return unique_recipients
