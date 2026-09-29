---
name: live-monitor-whatsapp
description: "Dispara notificações formatadas com resumo executivo e anexos no WhatsApp Web via automação Playwright persistente e headless."
version: 1.0.0
author: Ecossistema Live
license: MIT
metadata:
  hermes:
    tags: [whatsapp, playwright, browser, automation, alerts, headless]
---

# Live Monitor - Skill: Notificação via WhatsApp Web no Navegador

## Visão Geral
Esta skill envia alertas executivos diretamente para os números de WhatsApp de advogados e contadores parceiros cadastrados.
A automação é realizada via **Playwright** utilizando um perfil de navegador persistente (`data/whatsapp_session/`).
Isso garante que:
1. O QR Code só precisa ser escaneado **uma única vez** durante a configuração inicial.
2. Todas as execuções subsequentes rodam **100% em background (headless)** sem intervenção manual.
3. Não depende de APIs não oficiais instáveis ou números terceirizados: o envio parte do WhatsApp corporativo da consultoria.

## Formato Padrão da Mensagem
```text
🟠 *ALERTA DE PRAZO - ALTA*
⚡ *LIVE MONITOR - Sistema de Alertas Automáticos*
━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *Empresa:* Indústria Metalúrgica Alfa Ltda
🏛️ *Órgão Emissor:* Receita Federal do Brasil (e-CAC / DTE)
📄 *Processo / Notificação:* `08101.002345/2026-11`
⏳ *Prazo Legal:* *15 dias* (limite estimado: *14/10/2026*)
━━━━━━━━━━━━━━━━━━━━━━━━
📝 *Resumo da Notificação:*
Termo de Intimação referente à apuração de divergências na ECF/DCTF. Apresentar esclarecimentos para evitar auto de infração.

📅 *Recebido em:* 29/09/2026 10:15
ℹ️ *Ação recomendada:* Favor acusar recebimento e validar a providência necessária.
```

## Como Inicializar a Sessão do WhatsApp (QR Code Único)
Para conectar o WhatsApp corporativo pela primeira vez, execute o comando com interface gráfica aberta:
```bash
python -m engine.main --init-wa-session
```
O navegador Chromium será exibido na tela. Escaneie o QR Code no aplicativo do WhatsApp. Assim que as conversas carregarem, feche o navegador. O token de sessão ficará armazenado em `data/whatsapp_session/`.

## Envio Programático
```python
from engine.whatsapp_sender import WhatsAppSender

sender = WhatsAppSender(headless=True)
sender.send_notification(
    phone="5561996993134",
    message="Mensagem de teste do Live Monitor",
    attachments=[{"path": "data/attachments/intimacao.pdf"}]
)
```

## Proteção e Intervalos de Segurança
- Aplica intervalos anti-bloqueio (`WA_INTERVAL_SECONDS`, padrão 15s) entre mensagens consecutivas.
- Faz digitação simulada e verificação de seletores de entrega antes de liberar o encerramento da página.
