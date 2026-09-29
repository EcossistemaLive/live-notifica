---
name: live-monitor-email
description: "Acessa a caixa postal central da consultoria via conector nativo IMAP TLS, rastreia aliases de clientes em headers e extrai corpo e anexos."
version: 1.0.0
author: Ecossistema Live
license: MIT
metadata:
  hermes:
    tags: [email, imap, alias, live-monitor, inbox, attachments]
---

# Live Monitor - Skill: Conexão e Leitura de E-mails via Alias

## Visão Geral
Esta skill permite ao agente conectar-se de forma nativa e segura à caixa de e-mail central da consultoria (onde todos os e-mails de clientes chegam via aliases/redirecionamento), inspecionar mensagens recentes/não lidas, identificar qual cliente PJ é o destinatário original através de cabeçalhos de envelope (`Delivered-To`, `X-Original-To`, `Envelope-To`, `To`), extrair o conteúdo textual e salvar anexos oficiais (PDFs de intimações e autos de infração).

## Como Funciona o Rastreamento de Alias
Quando um órgão governamental (Receita Federal, SEFAZ, Tribunal) envia um e-mail para um cliente monitorado (ex: `notificacoes@empresa.com.br`), o e-mail é recebido ou redirecionado para a caixa central da consultoria com um alias específico.
Os servidores de e-mail gravam o alias nos cabeçalhos RFC 822:
1. `Delivered-To`: cabeçalho padrão do Google Workspace e Postfix.
2. `X-Original-To`: cabeçalho de destino original em servidores Exim / Postfix / cPanel.
3. `Envelope-To`: envelope SMTP do destinatário.
4. `To` / `CC`: destinatário aparente.

A skill lê esses campos na ordem de precedência e faz a consulta no arquivo `config/clients.yaml` para correlacionar imediatamente com a empresa cliente cadastrada.

## Como Executar

### 1. Testar Conexão IMAP
```bash
python -m engine.main --test-email
```

### 2. Buscar E-mails Pendentes via Script Python
```python
from engine.email_connector import EmailConnector

connector = EmailConnector()
emails = connector.fetch_unprocessed_emails(limit=20)
for e in emails:
    print(f"ID: {e['message_id']}")
    print(f"Assunto: {e['subject']}")
    print(f"Cliente Detectado: {e.get('client', {}).get('name')}")
    print(f"Anexos Baixados: {[a['filename'] for a in e['attachments']]}")
```

## Variáveis de Ambiente Necessárias
Definidas no arquivo `.env`:
- `IMAP_HOST`: Host do servidor (ex: `imap.gmail.com`)
- `IMAP_PORT`: Porta segura (ex: `993`)
- `IMAP_USER`: Endereço da caixa central
- `IMAP_PASSWORD`: Senha de app dedicada
- `IMAP_USE_SSL`: `true`
- `IMAP_MAILBOX`: `INBOX`

## Critérios de Idempotência
Antes de retornar um e-mail como elegível para processamento, a skill consulta `engine.state_db.is_message_processed` tanto pelo `Message-ID` original quanto pelo hash criptográfico SHA-256 do remetente, assunto, data e trecho do corpo. Mensagens já registradas no banco são ignoradas automaticamente.
