#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Módulo de Integração e Logs Detalhados no ClickUp
Registra logs operacionais, auditoria de execução, prazos, metadados de intimação
e trilha completa de auditoria diretamente no ClickUp do usuário.
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from .config import CONFIG_DIR, BASE_DIR, logger

CLICKUP_CONFIG_FILE = CONFIG_DIR / "clickup.yaml"

class ClickUpLogger:
    """Cliente para registro de auditoria e logs detalhados de execução no ClickUp."""

    def __init__(self):
        self.config = self._load_config()
        self.api_token = self.config.get("api_token") or os.getenv("CLICKUP_API_TOKEN", "")
        self.team_id = str(self.config.get("team_id") or os.getenv("CLICKUP_TEAM_ID", "90132599518"))
        self.space_id = str(self.config.get("space_id") or os.getenv("CLICKUP_SPACE_ID", ""))
        self.list_id = str(self.config.get("list_id") or os.getenv("CLICKUP_LIST_ID", "901716425999"))
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json; charset=utf-8"
        }

    def _load_config(self) -> Dict[str, Any]:
        """Carrega configurações do ClickUp a partir de config/clickup.yaml."""
        if CLICKUP_CONFIG_FILE.exists():
            try:
                with open(CLICKUP_CONFIG_FILE, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Não foi possível ler {CLICKUP_CONFIG_FILE}: {e}")
        return {}

    def is_configured(self) -> bool:
        """Verifica se o token e lista do ClickUp estão configurados."""
        return bool(self.api_token and self.list_id)

    def log_scan_run(self, scan_data: Dict[str, Any]) -> Optional[str]:
        """
        Cria uma tarefa executiva detalhada no ClickUp registrando a execução do Live Monitor.
        Retorna o ID da tarefa criada ou None em caso de falha.
        """
        if not self.is_configured():
            logger.warning("ClickUp não está configurado. Log no ClickUp ignorado. Configure config/clickup.yaml.")
            return None

        scan_id = scan_data.get("scan_id", 0)
        found = scan_data.get("emails_found", 0)
        processed = scan_data.get("emails_processed", 0)
        sent = scan_data.get("whatsapp_sent", 0)
        errors = scan_data.get("errors", 0)
        details = scan_data.get("details", [])
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        status_flag = "🟢 SUCESSO" if errors == 0 else "🟠 ATENÇÃO COM ERROS"
        task_name = f"[Live Monitor] Execução #{scan_id} ({status_flag}) - {now_str}"

        # Monta a descrição detalhada em Markdown
        desc_lines = [
            f"# ⚡ Relatório Executivo de Execução - Live Monitor",
            f"**Data/Hora da Execução:** {now_str}",
            f"**Identificador da Varredura (Scan ID):** `#{scan_id}`",
            f"**Status Geral:** {status_flag}",
            f"",
            f"---",
            f"## 📊 Métricas Operacionais",
            f"- **E-mails Encontrados na Caixa Central:** `{found}`",
            f"- **Intimações/Notificações Processadas:** `{processed}`",
            f"- **Alertas Enviados via WhatsApp Web:** `{sent}`",
            f"- **Erros / Falhas Registradas:** `{errors}`",
            f"",
            f"---",
            f"## 📋 Detalhamento dos E-mails e Notificações Processadas"
        ]

        if not details:
            desc_lines.append("_Nenhuma nova intimação ou notificação pendente processada neste ciclo._")
        else:
            for i, item in enumerate(details, 1):
                desc_lines.extend([
                    f"### {i}. Cliente: `{item.get('client')}`",
                    f"- **Órgão Emissor:** {item.get('agency', 'N/D')}",
                    f"- **Message-ID:** `{item.get('message_id', 'N/D')}`",
                    f"- **Status de Envio WhatsApp:** `{item.get('status', 'N/D')}`",
                    f"- **Destinatários Notificados:** `{', '.join(item.get('recipients', [])) or 'Nenhum'}`",
                    f""
                ])

        desc_lines.extend([
            f"---",
            f"## 🔒 Conformidade e Trilha de Auditoria",
            f"- **Responsável Técnico:** Cléber",
            f"- **Privacidade:** Telefones e metadados segregados por cliente.",
            f"- **Idempotência:** Hashes gravados no banco SQLite local.",
            f"- **Auditoria OAB/LGPD:** Comunicações destinadas estritamente aos advogados e contadores cadastrados para a empresa."
        ])

        description = "\n".join(desc_lines)

        url = f"https://api.clickup.com/api/v2/list/{self.list_id}/task"
        payload = {
            "name": task_name,
            "description": description,
            "status": "complete" if errors == 0 else "to do",
            "priority": 2 if errors == 0 else 1,
            "tags": ["live-monitor", "ecossistema-live", "auditoria-execucao"],
            "notify_all": False
        }

        try:
            res = requests.post(url, headers=self.headers, json=payload, timeout=20)
            if res.status_code in (200, 201):
                task_id = res.json().get("id")
                task_url = res.json().get("url")
                logger.info(f"[ClickUp] Log de execução gravado com sucesso! Tarefa: {task_url}")
                return task_id
            else:
                logger.error(f"[ClickUp] Falha ao registrar log ({res.status_code}): {res.text}")
                return None
        except Exception as e:
            logger.error(f"[ClickUp] Exceção ao conectar na API: {e}")
            return None

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """Lista os workspaces / teams disponíveis na conta do ClickUp."""
        url = "https://api.clickup.com/api/v2/team"
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            if res.status_code == 200:
                return res.json().get("teams", [])
        except Exception as e:
            logger.error(f"Erro ao listar workspaces do ClickUp: {e}")
        return []

    def list_spaces(self, team_id: str) -> List[Dict[str, Any]]:
        """Lista os espaços dentro de um workspace."""
        url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            if res.status_code == 200:
                return res.json().get("spaces", [])
        except Exception as e:
            logger.error(f"Erro ao listar spaces do ClickUp: {e}")
        return []

    def list_lists(self, space_id: str) -> List[Dict[str, Any]]:
        """Lista as listas dentro de um space (incluindo listas avulsas e em pastas)."""
        lists = []
        # Listas avulsas (folderless)
        url_folderless = f"https://api.clickup.com/api/v2/space/{space_id}/list"
        try:
            res = requests.get(url_folderless, headers=self.headers, timeout=15)
            if res.status_code == 200:
                lists.extend(res.json().get("lists", []))
        except Exception as e:
            logger.error(f"Erro ao buscar listas folderless: {e}")

        # Listas dentro de pastas
        url_folders = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
        try:
            res = requests.get(url_folders, headers=self.headers, timeout=15)
            if res.status_code == 200:
                for folder in res.json().get("folders", []):
                    lists.extend(folder.get("lists", []))
        except Exception as e:
            logger.error(f"Erro ao buscar pastas no ClickUp: {e}")

        return lists

    def create_list(self, space_id: str, list_name: str = "Live Monitor - Logs & Execuções") -> Optional[str]:
        """Cria uma nova lista para o Live Monitor no space selecionado."""
        url = f"https://api.clickup.com/api/v2/space/{space_id}/list"
        payload = {"name": list_name}
        try:
            res = requests.post(url, headers=self.headers, json=payload, timeout=15)
            if res.status_code in (200, 201):
                new_list_id = res.json().get("id")
                logger.info(f"[ClickUp] Nova lista criada: {list_name} (ID: {new_list_id})")
                return new_list_id
        except Exception as e:
            logger.error(f"Erro ao criar lista no ClickUp: {e}")
        return None
