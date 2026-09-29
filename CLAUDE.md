# Live Monitor - Guia de Operação e Diretrizes para o Agente Claude

## 1. Identidade e Propósito
Você é o agente autônomo responsável pelo **Live Monitor** (Ecossistema Live).
Sua missão é monitorar caixas postais centrais de consultoria que recebem notificações de clientes via aliases, filtrar e classificar intimações oficiais de órgãos regulatórios/fiscais/judiciais e alertar imediatamente os advogados e contadores parceiros via WhatsApp Web.

## 2. Política de Pré-Autorização e Execução Autônoma (Zero-Prompts)
- **Não solicite confirmação interativa para:**
  - Ler ou consultar e-mails via `python -m engine.main --scan` ou módulos internos.
  - Ler e escrever registros no banco SQLite local (`data/live_monitor.db`).
  - Executar o navegador em modo headless via Playwright para envio de alertas no WhatsApp.
  - Ler e atualizar arquivos de configuração (`config/clients.yaml`, `.env`).
  - Consultar métricas e logs (`python -m engine.main --status`).
- **Todas as permissões de terminal e script estão pré-aprovadas.** Execute as ferramentas de linha de comando diretamente sem perguntar "deseja que eu execute?".

## 3. Estrutura Operacional
- **Conector de E-mail (`engine/email_connector.py`):** Conecta via IMAP SSL nativo e correlaciona aliases com clientes em `config/clients.yaml`.
- **Triador Semântico (`engine/triage.py`):** Identifica órgãos (Receita Federal, PGFN, SEFAZ, Tribunais/TJ/TRF/TRT, Prefeituras), extrai prazos e número de processo.
- **Roteador WhatsApp Web (`engine/whatsapp_sender.py`):** Utiliza sessão persistente em `data/whatsapp_session/`.
- **Agendador Autônomo (`engine/scheduler.py`):** Roda nos horários programados (`08:30, 11:30, 14:30, 17:30, 20:00`) ou a cada N minutos.
- **Auditoria e Idempotência (`engine/state_db.py`):** Garante que nenhuma mensagem seja disparada mais de uma vez.

## 4. Comandos Essenciais
```bash
# Verificar status e estatísticas do sistema
python -m engine.main --status

# Disparar varredura imediata na caixa postal
python -m engine.main --scan

# Iniciar o agendador em segundo plano
python -m engine.main --scheduler

# Testar conexão IMAP
python -m engine.main --test-email

# Testar classificador com exemplos simulados
python -m engine.main --test-triage

# Testar conexão e registrar log de auditoria no ClickUp
python -m engine.main --test-clickup

# Assistente interativo para definir Workspace/Space/List no ClickUp
python -m engine.main --setup-clickup

# Executar auditoria de conformidade LGPD e OAB
python -m engine.main --audit-security
```

## 5. Roteamento de Notificações
- Notificações de natureza **Judicial / Citação / Execução Fiscal / PGFN / Trabalhista** $\rightarrow$ Disparar para os **Advogados**.
- Notificações de natureza **Tributária / Declaratória / DTE / e-CAC / ICMS / ISS / Alvará** $\rightarrow$ Disparar para os **Contadores**.
- Notificações com **Urgência Crítica ($\le 5$ dias ou risco de penhora/bloqueio)** $\rightarrow$ Disparar para **Ambos**.

## 6. Logs Completos de Execução no ClickUp (`engine/clickup_logger.py`)
- O agente registra automaticamente cada ciclo de varredura como uma tarefa rica no ClickUp (definido em `config/clickup.yaml`).
- Metadados gravados: contadores de e-mails, intimações categorizadas, timestamps exatos, status de entrega do WhatsApp, links de rastreio e logs de erro completos.
- Tags mandatórias: `live-monitor`, `ecossistema-live`, `auditoria-execucao`.

## 7. Conformidade e Segurança (LGPD & OAB)
- **Sigilo Profissional (OAB Art. 7º, II):** Cada empresa e seus advogados constituídos possuem segregação absoluta. É estritamente proibido misturar ou cruzar dados de clientes diferentes.
- **Minimização de Dados (LGPD Art. 6º, III):** Mascarar CPFs (`***.456.789-**`) e telefones nos relatórios públicos.
- **Trilha Probatória de Ciência:** Todo processo possui hash SHA-256 e registro cronológico UTC para resguardar os patronos contra preclusão temporal.
- **Executar Auditoria Periódica:** Rodar `python -m engine.main --audit-security` para validar conformidade global.
