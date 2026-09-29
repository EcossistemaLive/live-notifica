#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Ponto de Entrada Principal (CLI)
Interface de linha de comando para operação, diagnóstico e execução autônoma.
"""

import sys
import argparse
import json
from pathlib import Path

from .config import (
    load_clients, IMAP_USER, IMAP_HOST, IMAP_PORT, WA_HEADLESS,
    LLM_PROVIDER, logger
)
from .state_db import get_stats
from .email_connector import EmailConnector
from .whatsapp_sender import WhatsAppSender
from .triage import TriageClassifier
from .orchestrator import LiveMonitorOrchestrator
from .scheduler import start_scheduler

def cmd_status():
    """Exibe status do sistema, estatísticas e clientes cadastrados."""
    print("\n" + "="*65)
    print(" LIVE MONITOR - STATUS DO SISTEMA")
    print("="*65)
    print(f" Servidor IMAP:     {IMAP_HOST}:{IMAP_PORT}")
    print(f" Caixa Monitorada:  {IMAP_USER or '(não configurado no .env)'}")
    print(f" Modo WhatsApp:     {'Headless (em segundo plano)' if WA_HEADLESS else 'Headed (visível)'}")
    print(f" Provedor LLM:      {LLM_PROVIDER.upper()}")
    
    stats = get_stats()
    print("\n [Estatísticas de Mensagens]")
    print(f" - Total Processadas:   {stats['total_messages_processed']}")
    print(f" - Disparos WhatsApp:   {stats['whatsapp_sent']}")
    print(f" - Falhas no WhatsApp:  {stats['whatsapp_failed']}")
    print(f" - Ciclos de Varredura: {stats['total_scans']}")
    
    clients = load_clients()
    print(f"\n [Clientes Cadastrados: {len(clients)}]")
    for c in clients:
        advs = len(c.get("destinatarios", {}).get("advogados", []))
        conts = len(c.get("destinatarios", {}).get("contadores", []))
        aliases = ", ".join(c.get("aliases", []))
        print(f" - {c.get('name')} (CNPJ: {c.get('cnpj')})")
        print(f"   Aliases: {aliases}")
        print(f"   Destinatários: {advs} advogados | {conts} contadores")
    print("="*65 + "\n")

def cmd_test_email():
    """Testa a conexão com o servidor de e-mail IMAP."""
    print("\n[+] Testando conexão IMAP...")
    conn = EmailConnector()
    if conn.connect():
        print(f"[OK] Conexão bem-sucedida com {conn.user} em {conn.host}!")
        try:
            status, count = conn.client.select(conn.mailbox, readonly=True)
            print(f"[OK] Caixa '{conn.mailbox}' selecionada. Total de mensagens na caixa: {count[0].decode()}")
        finally:
            conn.disconnect()
    else:
        print("[ERRO] Não foi possível autenticar no servidor de e-mail. Verifique o arquivo .env.")

def cmd_test_triage():
    """Testa o motor de classificação semântica com exemplos reais de intimação."""
    print("\n[+] Executando teste de triagem semântica com exemplos simulados...\n")
    classifier = TriageClassifier()

    exemplos = [
        {
            "subject": "Notificação de Lançamento de Ofício - Termo de Intimação Fiscal e-CAC",
            "body_text": """Prezado Contribuinte,
Informamos que no Domicílio Tributário Eletrônico (DTE) da Receita Federal do Brasil foi disponibilizado o Termo de Intimação nº 08101.002345/2026-11, referente à apuração de divergências na ECF/DCTF do ano-calendário 2024.
Fica o contribuinte intimado a apresentar esclarecimentos no prazo de 15 dias úteis, sob pena de lavratura de auto de infração com multa de ofício de 75%.
CNPJ: 12.345.678/0001-90."""
        },
        {
            "subject": "Comunicação de Citação Eletrônica - Processo Judicial 0004512-33.2026.8.07.0001 - TJDFT",
            "body_text": """Poder Judiciário do Distrito Federal e dos Territórios - TJDFT
2ª Vara de Execução de Títulos Extrajudiciais de Brasília
Processo nº: 0004512-33.2026.8.07.0001
Classe: Execução Fiscal
Fica a parte executada intimada para efetuar o pagamento do débito ou garantir a execução no prazo de 5 dias corridos, sob pena de penhora online de ativos financeiros (SisbaJud)."""
        },
        {
            "subject": "SEFAZ/SP - Notificação Fiscal de Débito de ICMS Declarado",
            "body_text": """Secretaria de Estado da Fazenda e Planejamento do Estado de São Paulo
Posto Fiscal da Capital
Constatamos a ausência de recolhimento da GIA-ICMS no mês 07/2026.
Prazo para autorregularização: 30 dias a contar da ciência desta notificação."""
        }
    ]

    for i, ex in enumerate(exemplos, 1):
        print(f"--- [Exemplo {i}] Assunto: {ex['subject']} ---")
        res = classifier.analyze(ex)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        print()

def cmd_test_clickup():
    """Testa a integração com a API do ClickUp registrando um evento de auditoria de teste."""
    from .clickup_logger import ClickUpLogger
    print("\n[+] Testando conexão e gravação no ClickUp...")
    logger_cu = ClickUpLogger()
    if not logger_cu.is_configured():
        print("[AVISO] ClickUp não configurado! Execute: python -m engine.main --setup-clickup")
        return

    test_payload = {
        "scan_id": 9999,
        "emails_found": 1,
        "emails_processed": 1,
        "whatsapp_sent": 1,
        "errors": 0,
        "details": [
            {
                "client": "teste-auditoria-conexao",
                "agency": "Receita Federal (Simulação de Auditoria)",
                "message_id": "<test-audit-check@ecossistemalive.com.br>",
                "recipients": ["+55 61 9****-3134"],
                "status": "sent"
            }
        ]
    }
    task_id = logger_cu.log_scan_run(test_payload)
    if task_id:
        print(f"[OK] Tarefa de auditoria registrada com sucesso no ClickUp! ID: {task_id}")
    else:
        print("[ERRO] Falha ao registrar log no ClickUp. Verifique o token e list_id em config/clickup.yaml.")

def cmd_setup_clickup():
    """Assistente para conectar o ClickUp no workspace, space e list definidos."""
    import yaml
    from .clickup_logger import ClickUpLogger, CLICKUP_CONFIG_FILE
    print("\n" + "="*60)
    print(" [LIVE MONITOR] CONFIGURAÇÃO NATIVA DO CLICKUP")
    print("="*60)
    logger_cu = ClickUpLogger()
    token = input(f"Informe o API Token do ClickUp [{logger_cu.api_token[:8]}...]: ").strip() or logger_cu.api_token
    logger_cu.api_token = token
    logger_cu.headers["Authorization"] = token

    print("\nBuscando Workspaces (Teams)...")
    teams = logger_cu.list_workspaces()
    if not teams:
        print("[ERRO] Não foi possível encontrar workspaces com o token fornecido.")
        return

    for idx, t in enumerate(teams, 1):
        print(f" {idx}. {t.get('name')} (ID: {t.get('id')})")
    
    sel_t = input("Selecione o Workspace [1]: ").strip() or "1"
    team_obj = teams[int(sel_t)-1] if sel_t.isdigit() and 1 <= int(sel_t) <= len(teams) else teams[0]
    team_id = team_obj.get("id")

    print(f"\nBuscando Spaces no Workspace '{team_obj.get('name')}'...")
    spaces = logger_cu.list_spaces(team_id)
    for idx, s in enumerate(spaces, 1):
        print(f" {idx}. {s.get('name')} (ID: {s.get('id')})")
    
    sel_s = input("Selecione o Space [1]: ").strip() or "1"
    space_obj = spaces[int(sel_s)-1] if sel_s.isdigit() and 1 <= int(sel_s) <= len(spaces) else spaces[0]
    space_id = space_obj.get("id")

    print(f"\nBuscando Listas no Space '{space_obj.get('name')}'...")
    lists = logger_cu.list_lists(space_id)
    for idx, l in enumerate(lists, 1):
        print(f" {idx}. {l.get('name')} (ID: {l.get('id')})")
    print(" N. Criar nova lista 'Live Monitor - Logs & Execuções'")

    sel_l = input("Selecione a Lista ou 'N': ").strip()
    list_id = None
    if sel_l.upper() == "N":
        list_id = logger_cu.create_list(space_id, "Live Monitor - Logs & Execuções")
    elif sel_l.isdigit() and 1 <= int(sel_l) <= len(lists):
        list_id = lists[int(sel_l)-1].get("id")
    else:
        list_id = lists[0].get("id") if lists else logger_cu.create_list(space_id, "Live Monitor - Logs & Execuções")

    config_data = {
        "api_token": token,
        "team_id": team_id,
        "space_id": space_id,
        "list_id": list_id,
        "audit": {
            "log_every_scan": True,
            "log_only_on_activity": False,
            "tags": ["live-monitor", "ecossistema-live", "auditoria-execucao"],
            "assignee_name": "Cléber"
        }
    }

    with open(CLICKUP_CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f, sort_keys=False)

    print("\n[OK] Configuração do ClickUp salva com sucesso em config/clickup.yaml!")
    print(f" Workspace: {team_obj.get('name')} | Space: {space_obj.get('name')} | List ID: {list_id}\n")

def cmd_audit_security():
    """Executa auditoria de segurança de dados e conformidade LGPD & OAB."""
    from .security_audit import SecurityAuditLGPD_OAB
    auditor = SecurityAuditLGPD_OAB()
    res = auditor.run_full_audit()

    print("\n" + "="*65)
    print(f" AUDITORIA DE SEGURANÇA DE DADOS (LGPD & OAB) - NOTA: {res['score']}%")
    print("="*65)
    for item in res["findings"]:
        icon = "[PASS]" if item["status"] == "PASS" else "[FAIL]"
        print(f"\n {icon} {item['title']} ({item['id']}):")
        for d in item["details"]:
            print(f"    * {d}")
    print("\n" + "-"*65)
    print(f" Relatório Formal em Markdown gerado em:\n {res['report_path']}")
    print("="*65 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Live Monitor - Automação de Intimações e Notificações Oficiais")
    parser.add_argument("--scan", action="store_true", help="Executa uma varredura única imediata na caixa postal")
    parser.add_argument("--scheduler", action="store_true", help="Inicia o agendador autônomo para rodar nos horários programados")
    parser.add_argument("--init-wa-session", action="store_true", help="Abre o navegador visível para autenticar a sessão do WhatsApp Web via QR Code")
    parser.add_argument("--test-email", action="store_true", help="Testa as credenciais e conexão do e-mail IMAP")
    parser.add_argument("--test-triage", action="store_true", help="Testa o classificador semântico com intimações de exemplo")
    parser.add_argument("--test-clickup", action="store_true", help="Testa conexão e registro de auditoria no ClickUp")
    parser.add_argument("--setup-clickup", action="store_true", help="Assistente interativo de configuração de workspace do ClickUp")
    parser.add_argument("--audit-security", action="store_true", help="Executa auditoria de conformidade LGPD e OAB")
    parser.add_argument("--status", action="store_true", help="Exibe o status do sistema e clientes")

    args = parser.parse_args()

    if args.scan:
        orchestrator = LiveMonitorOrchestrator()
        result = orchestrator.run_scan()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.scheduler:
        start_scheduler()
    elif args.init_wa_session:
        wa = WhatsAppSender(headless=False)
        wa.init_interactive_session()
    elif args.test_email:
        cmd_test_email()
    elif args.test_triage:
        cmd_test_triage()
    elif args.test_clickup:
        cmd_test_clickup()
    elif args.setup_clickup:
        cmd_setup_clickup()
    elif args.audit_security:
        cmd_audit_security()
    elif args.status:
        cmd_status()
    else:
        cmd_status()
        print("Dica: Use --scan para varredura única, --audit-security para auditoria LGPD/OAB, ou --help.")

if __name__ == "__main__":
    main()
