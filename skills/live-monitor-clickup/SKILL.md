---
name: live-monitor-clickup
description: "Conecta o Claude nativamente ao ClickUp no workspace definido pelo usuário e registra logs completos e detalhados de todas as execuções do Live Monitor."
version: 1.0.0
author: Ecossistema Live
license: MIT
metadata:
  hermes:
    tags: [clickup, logging, audit, live-monitor, telemetry, execution-logs]
---

# Live Monitor - Skill: Integração Nativa e Logs Detalhados no ClickUp

## Visão Geral
Esta skill orienta o agente Claude a conectar-se nativamente à API do **ClickUp**, vincular-se a um Workspace/Space/Lista definidos pelo usuário na inicialização do sistema, e registrar tarefas de log completas e extremamente detalhadas para **cada ciclo de execução ou varredura do Live Monitor**.

## Como Funciona a Configuração Inicial do Workspace
O ClickUp é configurado de forma declarativa e flexível no arquivo `config/clickup.yaml`:
```yaml
api_token: "pk_82234785_1T2DKGF6NAFLC5PQGZFL8B5VZ049K6Z1"
team_id: "90132599518"        # Workspace ID
space_id: ""                  # Space ID
list_id: "901716425999"       # Lista de Auditoria / Execuções
audit:
  log_every_scan: true        # Grava a cada ciclo
  log_only_on_activity: false # Se true, grava apenas quando houver mensagens/erros
  tags:
    - "live-monitor"
    - "ecossistema-live"
    - "auditoria-execucao"
  assignee_name: "Cléber"     # Grafia obrigatória com C e acento agudo
```

### Assistente Interativo de Configuração
Se o usuário desejar alterar o Workspace, selecionar um novo Space ou criar automaticamente uma lista dedicada (`Live Monitor - Logs & Execuções`), basta executar:
```bash
python -m engine.main --setup-clickup
```
O assistente listará os workspaces, spaces e listas disponíveis na conta, salvando a escolha em `config/clickup.yaml`.

---

## Conteúdo Detalhado Gravado em Cada Execução

A cada varredura disparada pelo agendador ou manualmente, o módulo `engine/clickup_logger.py` gera uma tarefa com os seguintes metadados em Markdown:

1. **Cabeçalho Executivo:**
   - Número Sequencial da Execução (`Scan ID #X`)
   - Data e Hora exatas de início e término (`DD/MM/AAAA HH:MM:SS`)
   - Status Geral (`🟢 SUCESSO` ou `🟠 ATENÇÃO COM ERROS`)
2. **Métricas Operacionais:**
   - Total de e-mails encontrados na caixa postal central da consultoria
   - Quantidade de intimações/notificações válidas identificadas
   - Total de alertas disparados com sucesso via WhatsApp Web
   - Erros ou falhas técnicas registradas com stack trace
3. **Detalhamento de Cada Notificação:**
   - **Empresa / Cliente Mapeado:** ID do cliente e nome fantasia
   - **Órgão Emissor:** Ex: Receita Federal (e-CAC), TJ, SEFAZ, Prefeitura
   - **Processo / Termo:** Número do processo ou auto de infração
   - **Prazos:** Dias úteis/corridos e data limite de cumprimento
   - **Urgência:** Crítica, Alta, Média ou Baixa
   - **Destinatários Notificados:** Lista de advogados e contadores que receberam o alerta no WhatsApp
   - **Message-ID:** Identificador RFC 822 único para rastreabilidade
4. **Campos do ClickUp:**
   - **Nome da Tarefa:** `[Live Monitor] Execução #X (🟢 SUCESSO) - DD/MM/AAAA HH:MM:SS`
   - **Status:** `complete` (se sem falhas) ou `to do` (se houver erros pendentes de revisão)
   - **Prioridade:** Normal (se sem erros) ou Urgente (se falha no disparo)
   - **Tags Obrigatórias:** `live-monitor`, `ecossistema-live`, `auditoria-execucao`

---

## Comandos de Operação

### Testar Conexão e Registro Imediato de Log
```bash
python -m engine.main --test-clickup
```

### Executar Varredura com Gravação Automática no ClickUp
```bash
python -m engine.main --scan
```
Ao final do processamento, a tarefa é imediatamente criada e o link direto do ClickUp é exibido no console e registrado no log do sistema.
