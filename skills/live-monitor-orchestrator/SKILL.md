---
name: live-monitor-orchestrator
description: "Orquestra a esteira completa do Live Monitor (e-mail via alias, triagem IA, envio WhatsApp) com execução agendada e autorização autônoma."
version: 1.0.0
author: Ecossistema Live
license: MIT
metadata:
  hermes:
    tags: [orchestration, autonomous, cron, scheduler, live-monitor, docker]
---

# Live Monitor - Skill: Orquestração e Execução Agendada

## Visão Geral
Esta skill é o cérebro operacional do Live Monitor. Ela combina os três módulos anteriores (E-mail IMAP, Triagem Semântica e Notificação WhatsApp Web) e provê a camada de agendamento autônomo (executando múltiplas vezes ao dia sem requerer permissões interativas a cada passo).

## Fluxo da Esteira Ponta a Ponta
```text
   [ E-mail do Órgão ]
          │ (enviado ao alias do cliente)
          ▼
┌─────────────────────────┐
│ Caixa da Consultoria    │ (Leitura via IMAP SSL)
└─────────┬───────────────┘
          │ Extração de alias (Delivered-To / Envelope-To)
          ▼
┌─────────────────────────┐
│ Identificação do Cliente│ (Busca no config/clients.yaml)
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Triagem Semântica (IA)  │ (Classifica órgão, extrai processo, prazo e urgência)
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Roteamento Inteligente  │ ──► Advogados (ações judiciais, citações, penhoras)
│                         │ ──► Contadores (fiscal, e-CAC, SEFAZ, prefeituras)
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Disparo WhatsApp Web    │ (Playwright Headless com perfil persistente)
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Banco de Estado SQLite  │ (Grava auditoria e garante que o e-mail nunca seja duplicado)
└─────────────────────────┘
```

## Como Operar

### 1. Varredura Imediata (One-Shot)
Para rodar um ciclo de verificação agora e sair:
```bash
python -m engine.main --scan
```

### 2. Iniciar Modo Daemon Agendado (Várias vezes ao dia)
Para manter o agente rodando continuamente em segundo plano conforme os horários definidos em `SCHEDULE_TIMES`:
```bash
python -m engine.main --scheduler
```
Por padrão, os horários programados são:
`08:30`, `11:30`, `14:30`, `17:30`, `20:00`.
Também é possível configurar um intervalo cíclico em minutos definindo `SCHEDULE_INTERVAL_MINUTES=30` no `.env`.

### 3. Verificar Saúde e Métricas
```bash
python -m engine.main --status
```

## Autonomia e Permissões Pré-Autorizadas
Para evitar que o agente pare e fique pedindo aprovações de terminal ou interação humana:
1. Todas as credenciais são lidas de variáveis de ambiente (`.env`).
2. A sessão do WhatsApp é mantida em disco (`data/whatsapp_session/`).
3. O banco SQLite controla idempotência silenciosamente.
4. Falhas em e-mails específicos não abortam o lote: são registradas no banco para posterior re-tentativa e o fluxo prossegue para as próximas mensagens.
