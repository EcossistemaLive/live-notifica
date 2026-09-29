#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Envio Automatizado via WhatsApp Web (Playwright)
Utiliza contexto de navegador persistente para manter a sessão salva,
permitindo envios autônomos e headless sem intervenção humana repetida.
"""

import time
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright, BrowserContext, Page

from .config import (
    WA_SESSION_DIR, WA_HEADLESS, WA_TIMEOUT_MS, WA_DEFAULT_DDI,
    WA_INTERVAL_SECONDS, OFFICE_NAME, logger
)

def format_e164(phone: str, ddi: str = WA_DEFAULT_DDI) -> str:
    """Higieniza e formata número de telefone para o padrão internacional E.164 sem '+'."""
    digits = "".join(filter(str.isdigit, str(phone)))
    if not digits:
        return ""
    if digits.startswith(ddi) and len(digits) >= 12:
        return digits
    return f"{ddi}{digits}"

def format_alert_message(client_name: str, triage: Dict[str, Any], date_str: str) -> str:
    """
    Gera o texto executivo padronizado para envio aos advogados ou contadores.
    """
    urgency_emoji = {
        "critica": "🔴 *URGÊNCIA CRÍTICA*",
        "alta": "🟠 *ALERTA DE PRAZO - ALTA*",
        "media": "🟡 *NOTIFICAÇÃO FISCAL/JURÍDICA*",
        "baixa": "ℹ️ *INFORMATIVO OFICIAL*"
    }.get(triage.get("urgency", "media"), "⚠️ *NOTIFICAÇÃO OFICIAL*")

    msg_lines = [
        f"{urgency_emoji}",
        f"⚡ *{OFFICE_NAME.upper()} - Alertas de Intimações & Prazos*",
        f"━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🏢 *Empresa:* {client_name}",
        f"🏛️ *Órgão Emissor:* {triage.get('agency', 'Órgão Governamental')}",
        f"📄 *Processo / Notificação:* `{triage.get('process_number', 'N/D')}`",
    ]

    if triage.get("prazo_dias"):
        msg_lines.append(f"⏳ *Prazo Legal:* *{triage.get('prazo_dias')} dias* (limite estimado: *{triage.get('data_limite')}*)")

    msg_lines.extend([
        f"━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📝 *Resumo da Notificação:*",
        f"{triage.get('summary', 'Notificação oficial capturada da caixa central.')}",
        f"",
        f"📅 *Recebido em:* {date_str}",
        f"ℹ️ *Ação recomendada:* Favor acusar recebimento e validar a providência necessária."
    ])

    return "\n".join(msg_lines)

class WhatsAppSender:
    """Gerencia a sessão do navegador e disparos pelo WhatsApp Web."""

    def __init__(self, headless: Optional[bool] = None):
        self.headless = WA_HEADLESS if headless is None else headless
        self.session_dir = str(WA_SESSION_DIR)
        self.timeout = WA_TIMEOUT_MS

    def init_interactive_session(self):
        """
        Abre o navegador visível (headed) para o usuário escanear o QR Code
        pela primeira vez. Uma vez logado, a sessão fica salva permanentemente.
        """
        logger.info("Iniciando WhatsApp Web para autenticação inicial (QR Code)...")
        print("\n" + "="*60)
        print(" [LIVE MONITOR] INICIALIZAÇÃO DE SESSÃO WHATSAPP WEB")
        print(" O navegador será aberto. Por favor, escaneie o QR Code no seu celular.")
        print(" Quando suas conversas carregarem completamente, você pode fechar o navegador")
        print(" ou pressionar ENTER aqui no terminal.")
        print("="*60 + "\n")

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                headless=False,
                channel="chrome" if Path("C:/Program Files/Google/Chrome/Application/chrome.exe").exists() else None,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()
            page.goto("https://web.whatsapp.com", timeout=60000)

            try:
                # Aguarda até que a barra lateral ou caixa de pesquisa do WhatsApp apareça (logado)
                page.wait_for_selector("div[contenteditable='true']", timeout=120000)
                logger.info("Sessão do WhatsApp Web autenticada com sucesso!")
                print("\n[OK] Sessão salva com sucesso em data/whatsapp_session!")
                time.sleep(5)
            except Exception as e:
                print(f"\n[Aviso] Tempo de espera encerrado ou login pendente: {e}")
            finally:
                browser.close()

    def send_notification(self, phone: str, message: str, attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Envia uma notificação formatada para um destinatário via WhatsApp Web.
        Executa de forma autônoma e headless.
        """
        clean_phone = format_e164(phone)
        if not clean_phone:
            logger.error(f"Número de telefone inválido: '{phone}'")
            return False

        logger.info(f"Disparando notificação via WhatsApp Web para {clean_phone}...")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=self.session_dir,
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu"
                    ]
                )
                page = browser.new_page()
                page.set_default_timeout(self.timeout)

                # Monta URL direta com texto pré-codificado
                encoded_msg = urllib.parse.quote(message)
                target_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

                page.goto(target_url, wait_until="domcontentloaded")

                # Aguarda carregar o painel da conversa
                # O seletor abaixo identifica o botão de envio ou a caixa de mensagem com o texto preenchido
                send_button_selector = (
                    "button[aria-label='Enviar'], span[data-icon='send'], button span[data-icon='send']"
                )

                # Aguarda o botão enviar ficar visível ou caixa de texto pronta
                try:
                    page.wait_for_selector(send_button_selector, timeout=self.timeout)
                except Exception:
                    # Verifica se o número não existe no WhatsApp
                    body_text = page.locator("body").inner_text()
                    if "número de telefone compartilhado por url é inválido" in body_text.lower() or "invalid phone" in body_text.lower():
                        logger.error(f"WhatsApp informou que o número {clean_phone} é inválido ou não possui conta.")
                        browser.close()
                        return False
                    raise

                time.sleep(2)  # Pausa de segurança

                # Clica no botão de enviar
                send_button = page.locator(send_button_selector).first
                send_button.click()
                logger.info(f"Mensagem enviada com sucesso para {clean_phone}!")

                # Se houver anexos (ex: PDF da notificação) e arquivo existir
                if attachments:
                    for att in attachments:
                        file_path = att.get("path")
                        if file_path and Path(file_path).exists():
                            self._attach_file(page, file_path)

                time.sleep(WA_INTERVAL_SECONDS)  # Intervalo de segurança anti-bloqueio
                browser.close()
                return True

            except Exception as e:
                logger.error(f"Erro ao enviar WhatsApp para {clean_phone}: {e}", exc_info=True)
                return False

    def _attach_file(self, page: Page, filepath: str):
        """Faz upload de arquivo anexo na conversa atual do WhatsApp Web."""
        try:
            logger.info(f"Anexando arquivo {filepath}...")
            # Clica no botão de anexar (+)
            attach_btn_selector = "span[data-icon='plus'], span[data-icon='attach-menu-plus'], div[title='Anexar']"
            page.wait_for_selector(attach_btn_selector, timeout=10000)
            page.locator(attach_btn_selector).first.click()

            time.sleep(1)
            # Localiza o input file de documento
            file_input = page.locator("input[type='file'][accept*='*']").first
            file_input.set_input_files(filepath)

            # Aguarda a tela de prévia do anexo e clica no botão de enviar
            send_attach_btn = "span[data-icon='send']"
            page.wait_for_selector(send_attach_btn, timeout=15000)
            page.locator(send_attach_btn).first.click()
            logger.info(f"Anexo {Path(filepath).name} enviado com sucesso!")
            time.sleep(3)
        except Exception as e:
            logger.warning(f"Não foi possível anexar o arquivo {filepath}: {e}")
