#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Configuração do Sistema
Carrega variáveis de ambiente, cadastro de clientes em YAML e configurações de execução.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from dotenv import load_dotenv

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
WA_SESSION_DIR = DATA_DIR / "whatsapp_session"
LOGS_DIR = DATA_DIR / "logs"

# Cria diretórios necessários
for d in [DATA_DIR, CONFIG_DIR, ATTACHMENTS_DIR, WA_SESSION_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Carrega arquivo .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # Tenta carregar da pasta config ou engine
    alt_env = CONFIG_DIR / ".env"
    if alt_env.exists():
        load_dotenv(alt_env)
    else:
        load_dotenv()

# Configuração de Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = LOGS_DIR / "live_monitor.log"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("LiveMonitor")

# Configurações de E-mail
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
IMAP_USE_SSL = os.getenv("IMAP_USE_SSL", "true").lower() in ("true", "1", "yes")
IMAP_MAILBOX = os.getenv("IMAP_MAILBOX", "INBOX")

# Configurações de WhatsApp Web
WA_HEADLESS = os.getenv("WA_HEADLESS", "true").lower() in ("true", "1", "yes")
WA_TIMEOUT_MS = int(os.getenv("WA_TIMEOUT_MS", "45000"))
WA_DEFAULT_DDI = os.getenv("WA_DEFAULT_DDI", "55")
WA_INTERVAL_SECONDS = int(os.getenv("WA_INTERVAL_SECONDS", "15"))

# Configurações de IA / Triagem
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()  # anthropic | gemini | heuristic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

# Configurações de Agendamento
SCHEDULE_TIMES = os.getenv("SCHEDULE_TIMES", "08:30,11:30,14:30,17:30,20:00").split(",")
SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "0"))  # 0 significa usar SCHEDULE_TIMES

# Caminho do cadastro de clientes
CLIENTS_FILE = CONFIG_DIR / "clients.yaml"

def load_clients() -> List[Dict[str, Any]]:
    """Carrega lista de clientes cadastrados do arquivo clients.yaml."""
    if not CLIENTS_FILE.exists():
        logger.warning(f"Arquivo de clientes não encontrado em {CLIENTS_FILE}. Usando lista vazia.")
        return []
    try:
        with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("clients", []) if data else []
    except Exception as e:
        logger.error(f"Erro ao carregar {CLIENTS_FILE}: {e}")
        return []

def find_client_by_alias(alias: str) -> Optional[Dict[str, Any]]:
    """Busca cliente pelo alias de e-mail (case-insensitive)."""
    alias_clean = alias.strip().lower()
    clients = load_clients()
    for client in clients:
        for client_alias in client.get("aliases", []):
            if client_alias.strip().lower() == alias_clean:
                return client
            # Se for formato completo com nome ex: "Empresa <empresa@dominio.com>"
            if f"<{client_alias.strip().lower()}>" in alias_clean:
                return client
    return None
