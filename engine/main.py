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

def main():
    parser = argparse.ArgumentParser(description="Live Monitor - Automação de Intimações e Notificações Oficiais")
    parser.add_argument("--scan", action="store_true", help="Executa uma varredura única imediata na caixa postal")
    parser.add_argument("--scheduler", action="store_true", help="Inicia o agendador autônomo para rodar nos horários programados")
    parser.add_argument("--init-wa-session", action="store_true", help="Abre o navegador visível para autenticar a sessão do WhatsApp Web via QR Code")
    parser.add_argument("--test-email", action="store_true", help="Testa as credenciais e conexão do e-mail IMAP")
    parser.add_argument("--test-triage", action="store_true", help="Testa o classificador semântico com intimações de exemplo")
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
    elif args.status:
        cmd_status()
    else:
        cmd_status()
        print("Dica: Use --scan para varredura única, --scheduler para execução agendada, ou --help.")

if __name__ == "__main__":
    main()
