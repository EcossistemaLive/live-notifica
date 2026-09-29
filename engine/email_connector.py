#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Conector Nativo de E-mail
Conecta à caixa central da consultoria via IMAP com SSL/TLS,
detecta aliases de clientes, extrai corpo e baixa anexos (PDFs/intimações).
"""

import imaplib
import email
import email.message
from email.header import decode_header
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from .config import (
    IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD, IMAP_USE_SSL,
    IMAP_MAILBOX, ATTACHMENTS_DIR, logger, find_client_by_alias
)
from .state_db import is_message_processed, compute_hash

def clean_header_str(value: Optional[str]) -> str:
    """Decodifica strings de cabeçalho MIME (ex: UTF-8, ISO-8859-1)."""
    if not value:
        return ""
    decoded_fragments = decode_header(value)
    text_parts = []
    for fragment, charset in decoded_fragments:
        if isinstance(fragment, bytes):
            try:
                charset = charset or "utf-8"
                text_parts.append(fragment.decode(charset, errors="replace"))
            except Exception:
                text_parts.append(fragment.decode("latin1", errors="replace"))
        else:
            text_parts.append(str(fragment))
    return " ".join(text_parts).strip()

def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos de nomes de arquivo."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def extract_email_address(raw_header: str) -> str:
    """Extrai apenas o endereço de e-mail (ex: de 'Nome <email@dominio.com>' -> 'email@dominio.com')."""
    if not raw_header:
        return ""
    match = re.search(r'[\w\.-]+@[\w\.-]+', raw_header)
    return match.group(0).lower() if match else raw_header.lower()

class EmailConnector:
    """Cliente IMAP nativo para leitura da caixa central e extração de aliases."""

    def __init__(self):
        self.host = IMAP_HOST
        self.port = IMAP_PORT
        self.user = IMAP_USER
        self.password = IMAP_PASSWORD
        self.use_ssl = IMAP_USE_SSL
        self.mailbox = IMAP_MAILBOX
        self.client: Optional[imaplib.IMAP4] = None

    def connect(self) -> bool:
        """Estabelece conexão com o servidor IMAP."""
        if not self.user or not self.password:
            logger.error("Credenciais de e-mail (IMAP_USER / IMAP_PASSWORD) não foram configuradas.")
            return False
        try:
            if self.use_ssl:
                self.client = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.client = imaplib.IMAP4(self.host, self.port)
            
            self.client.login(self.user, self.password)
            logger.info(f"Conectado com sucesso ao e-mail {self.user} em {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Falha ao conectar no servidor IMAP: {e}")
            self.client = None
            return False

    def disconnect(self):
        """Encerra a sessão IMAP com segurança."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            try:
                self.client.logout()
            except Exception:
                pass
            self.client = None
            logger.debug("Conexão IMAP encerrada.")

    def fetch_unprocessed_emails(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca e-mails não processados.
        Identifica aliases em Delivered-To, X-Original-To, Envelope-To ou To/CC.
        """
        if not self.client:
            if not self.connect():
                return []

        messages_to_process = []
        try:
            status, _ = self.client.select(self.mailbox, readonly=True)
            if status != "OK":
                logger.error(f"Não foi possível selecionar a caixa {self.mailbox}")
                return []

            # Busca e-mails recentes (não lidos ou últimos da caixa)
            status, data = self.client.search(None, "UNSEEN")
            email_ids = data[0].split() if status == "OK" and data[0] else []

            # Se não houver não lidos, opcionalmente busca os últimos X e-mails para checagem por hash
            if not email_ids:
                status, data = self.client.search(None, "ALL")
                all_ids = data[0].split() if status == "OK" and data[0] else []
                email_ids = all_ids[-limit:]  # Pega os mais recentes

            logger.info(f"Localizados {len(email_ids)} e-mails candidatos para verificação.")

            for eid in reversed(email_ids):
                status, msg_data = self.client.fetch(eid, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extrai identificadores
                message_id = clean_header_str(msg.get("Message-ID", f"msg_{eid.decode()}"))
                sender = clean_header_str(msg.get("From", ""))
                subject = clean_header_str(msg.get("Subject", "(Sem Assunto)"))
                date_str = clean_header_str(msg.get("Date", ""))

                # Rastreamento de Alias do Cliente:
                # Provedores de e-mail injetam o destinatário real do alias em headers especiais:
                # 1. Delivered-To (Google Workspace / Postfix)
                # 2. X-Original-To / Envelope-To (Exim / Postfix / cPanel)
                # 3. To / CC (Direto)
                delivered_to = clean_header_str(msg.get("Delivered-To", ""))
                x_original_to = clean_header_str(msg.get("X-Original-To", ""))
                envelope_to = clean_header_str(msg.get("Envelope-To", ""))
                to_hdr = clean_header_str(msg.get("To", ""))
                cc_hdr = clean_header_str(msg.get("CC", ""))

                # Candidatos a alias
                alias_candidates = [
                    extract_email_address(delivered_to),
                    extract_email_address(x_original_to),
                    extract_email_address(envelope_to),
                    extract_email_address(to_hdr),
                    extract_email_address(cc_hdr)
                ]
                # Filtra vazios e remove repetições preservando ordem de prioridade
                seen = set()
                alias_candidates = [x for x in alias_candidates if x and not (x in seen or seen.add(x))]

                # Identifica cliente correspondente
                matched_client = None
                matched_alias = None
                for candidate in alias_candidates:
                    client = find_client_by_alias(candidate)
                    if client:
                        matched_client = client
                        matched_alias = candidate
                        break

                # Extrai corpo do texto e anexos
                body_text, body_html, attachments = self._extract_payload(msg, message_id)

                content_hash = compute_hash(sender, subject, date_str, body_text)

                # Verifica se já foi gravado no banco de estado
                if is_message_processed(message_id, content_hash):
                    logger.debug(f"Mensagem {message_id} ('{subject}') já processada. Ignorando.")
                    continue

                messages_to_process.append({
                    "message_id": message_id,
                    "content_hash": content_hash,
                    "sender": sender,
                    "subject": subject,
                    "date": date_str,
                    "alias_candidates": alias_candidates,
                    "matched_alias": matched_alias,
                    "client": matched_client,
                    "body_text": body_text,
                    "body_html": body_html,
                    "attachments": attachments,
                    "raw_email_id": eid.decode()
                })

                if len(messages_to_process) >= limit:
                    break

        except Exception as e:
            logger.error(f"Erro ao buscar e-mails: {e}", exc_info=True)
        finally:
            self.disconnect()

        return messages_to_process

    def _extract_payload(self, msg: email.message.Message, msg_id: str):
        """Extrai o texto plano, HTML e faz download dos arquivos anexados."""
        body_text = ""
        body_html = ""
        attachments = []

        # Subpasta de anexos específica para esta mensagem
        clean_id = sanitize_filename(msg_id.replace("<", "").replace(">", ""))
        msg_attach_dir = ATTACHMENTS_DIR / clean_id

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Anexos
                filename = part.get_filename()
                if filename:
                    filename = sanitize_filename(clean_header_str(filename))
                    msg_attach_dir.mkdir(parents=True, exist_ok=True)
                    filepath = msg_attach_dir / filename
                    payload = part.get_payload(decode=True)
                    if payload:
                        with open(filepath, "wb") as f:
                            f.write(payload)
                        attachments.append({
                            "filename": filename,
                            "path": str(filepath),
                            "size_bytes": len(payload),
                            "content_type": content_type
                        })
                    continue

                # Texto e HTML
                if "attachment" not in content_disposition:
                    if content_type == "text/plain" and not body_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text = payload.decode(errors="replace")
                    elif content_type == "text/html" and not body_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_html = payload.decode(errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                text_content = payload.decode(errors="replace")
                if msg.get_content_type() == "text/html":
                    body_html = text_content
                else:
                    body_text = text_content

        # Se só temos HTML, converte para texto plano amigável
        if not body_text and body_html:
            if BeautifulSoup:
                try:
                    soup = BeautifulSoup(body_html, "html.parser")
                    body_text = soup.get_text(separator="\n", strip=True)
                except Exception:
                    body_text = re.sub(r'<[^>]+>', ' ', body_html)
            else:
                body_text = re.sub(r'<[^>]+>', ' ', body_html)

        return body_text.strip(), body_html.strip(), attachments
