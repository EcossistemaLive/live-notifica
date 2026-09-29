#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Banco de Dados de Estado (SQLite)
Garante idempotência, rastreamento de mensagens processadas e histórico de auditoria.
"""

import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from .config import DATA_DIR, logger

DB_FILE = DATA_DIR / "live_monitor.db"

def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão ativa com o banco SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa as tabelas do banco de dados se não existirem."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Tabela de Mensagens Processadas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                content_hash TEXT NOT NULL,
                client_id TEXT,
                alias_detected TEXT,
                sender TEXT,
                subject TEXT,
                received_date TEXT,
                category TEXT,
                agency TEXT,
                process_number TEXT,
                prazo_dias INTEGER,
                data_limite TEXT,
                urgency TEXT,
                attachments_json TEXT,
                whatsapp_status TEXT DEFAULT 'pending',
                whatsapp_sent_at TEXT,
                whatsapp_recipients TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_id ON processed_messages(message_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON processed_messages(content_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_id ON processed_messages(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wa_status ON processed_messages(whatsapp_status)")
        
        # Tabela de Logs de Execução do Scheduler
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                emails_found INTEGER DEFAULT 0,
                emails_processed INTEGER DEFAULT 0,
                whatsapp_sent INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                log_summary TEXT
            )
        """)
        
        conn.commit()
    logger.debug(f"Banco de dados inicializado em {DB_FILE}")

def is_message_processed(message_id: str, content_hash: Optional[str] = None) -> bool:
    """Verifica se uma mensagem já foi processada anteriormente."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if content_hash:
            cursor.execute(
                "SELECT id FROM processed_messages WHERE message_id = ? OR content_hash = ?",
                (message_id, content_hash)
            )
        else:
            cursor.execute(
                "SELECT id FROM processed_messages WHERE message_id = ?",
                (message_id,)
            )
        row = cursor.fetchone()
        return row is not None

def compute_hash(sender: str, subject: str, date: str, body: str) -> str:
    """Calcula hash SHA256 do conteúdo para detectar duplicatas."""
    payload = f"{sender}|{subject}|{date}|{body[:500]}"
    return hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()

def record_processed_message(data: Dict[str, Any]) -> int:
    """Grava o registro de uma mensagem processada."""
    now_iso = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO processed_messages (
                message_id, content_hash, client_id, alias_detected, sender, subject,
                received_date, category, agency, process_number, prazo_dias, data_limite,
                urgency, attachments_json, whatsapp_status, whatsapp_sent_at, whatsapp_recipients,
                error_message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("message_id"),
            data.get("content_hash"),
            data.get("client_id"),
            data.get("alias_detected"),
            data.get("sender"),
            data.get("subject"),
            data.get("received_date"),
            data.get("category"),
            data.get("agency"),
            data.get("process_number"),
            data.get("prazo_dias"),
            data.get("data_limite"),
            data.get("urgency"),
            data.get("attachments_json", "[]"),
            data.get("whatsapp_status", "pending"),
            data.get("whatsapp_sent_at"),
            data.get("whatsapp_recipients", ""),
            data.get("error_message"),
            now_iso
        ))
        conn.commit()
        return cursor.lastrowid

def update_whatsapp_status(message_id: str, status: str, recipients: str, error: Optional[str] = None):
    """Atualiza o status de entrega do WhatsApp."""
    now_iso = datetime.now().isoformat() if status == "sent" else None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE processed_messages
            SET whatsapp_status = ?, whatsapp_sent_at = ?, whatsapp_recipients = ?, error_message = ?
            WHERE message_id = ?
        """, (status, now_iso, recipients, error, message_id))
        conn.commit()

def log_scan_start() -> int:
    """Registra início de uma varredura."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scan_logs (started_at, status)
            VALUES (?, 'running')
        """, (datetime.now().isoformat(),))
        conn.commit()
        return cursor.lastrowid

def log_scan_finish(scan_id: int, found: int, processed: int, sent: int, errors: int, summary: str = ""):
    """Atualiza término de uma varredura."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scan_logs
            SET finished_at = ?, emails_found = ?, emails_processed = ?,
                whatsapp_sent = ?, errors = ?, status = 'completed', log_summary = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), found, processed, sent, errors, summary, scan_id))
        conn.commit()

def get_stats() -> Dict[str, Any]:
    """Retorna estatísticas gerais do sistema para auditoria."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_messages")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE whatsapp_status = 'sent'")
        sent = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE whatsapp_status = 'failed'")
        failed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scan_logs")
        total_scans = cursor.fetchone()[0]
        
        return {
            "total_messages_processed": total,
            "whatsapp_sent": sent,
            "whatsapp_failed": failed,
            "total_scans": total_scans
        }

# Inicializa ao importar
init_db()
