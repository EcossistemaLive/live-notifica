---
name: live-monitor
description: "Gerencia, monitora e dispara o agente Live Monitor (leitura de intimações fiscais/judiciais via alias de e-mail e envio via WhatsApp Web aos advogados e contadores)."
version: 1.0.0
author: Ecossistema Live
license: MIT
metadata:
  hermes:
    tags: [live-monitor, legal, tax, email, whatsapp, automation, docker]
    related_skills: [google-workspace, hermes-s6-container-supervision]
---

# Live Monitor - Skill de Supervisão e Gestão (Hermes)

## Visão Geral
Esta skill permite ao agente Hermes supervisionar, gerenciar e executar o serviço **Live Monitor** tanto no host quanto dentro do container Docker.
O Live Monitor atende empresas e indústrias, monitorando uma caixa central da consultoria que recebe intimações via aliases de e-mail dos clientes, classifica o órgão (Receita, SEFAZ, Tribunais, Prefeituras) e notifica advogados e contadores via WhatsApp Web.

## Quando Usar
- Para verificar se o serviço Live Monitor está rodando ou saudável.
- Para forçar uma varredura imediata na caixa postal sem aguardar o agendador (`scan-now`).
- Para consultar o total de intimações processadas e disparos efetuados.
- Para gerenciar o ciclo de vida do container Docker do Live Monitor (`docker compose up/restart/logs`).
- Para cadastrar ou inspecionar clientes e aliases de e-mail monitorados.

## Localização dos Arquivos
- **Host Windows:** `G:\Meu Drive\Consultoria\clientes\ecossistema-live\produtos\live-notifica\`
- **Caminho no Container Docker:** `/app` ou `/workspace/clientes/ecossistema-live/produtos/live-notifica/`
- **Banco de Estado SQLite:** `data/live_monitor.db`
- **Sessão Persistente do WhatsApp:** `data/whatsapp_session/`
- **Configuração de Clientes:** `config/clients.yaml`

## Comandos Rápidos de Operação

### 1. Inspecionar Saúde e Estatísticas
```bash
python -m engine.main --status
```
Ou no Docker:
```bash
docker exec live-monitor-service python -m engine.main --status
```

### 2. Disparar Varredura Imediata
```bash
python -m engine.main --scan
```
Ou no Docker:
```bash
docker exec live-monitor-service python -m engine.main --scan
```

### 3. Testar Conexão com o Servidor de E-mail
```bash
python -m engine.main --test-email
```

### 4. Gestão via Docker Compose
Na pasta `docker/`:
```bash
# Iniciar o serviço em segundo plano
docker compose up -d

# Ver logs em tempo real
docker compose logs -f --tail=100

# Reiniciar o serviço
docker compose restart
```

## Protocolo de Notificação
Ao receber um pedido do usuário como:
- *"Hermes, como estão as intimações do Live Monitor hoje?"*
- *"Hermes, verifique os e-mails dos clientes agora"*
- *"Hermes, rode uma varredura no Live Monitor"*

O agente Hermes executa:
1. `python -m engine.main --status` para checar as métricas gerais.
2. `python -m engine.main --scan` se o usuário solicitou uma verificação imediata.
3. Responde com um sumário executivo contendo:
   - Quantidade de mensagens novas encontradas
   - Intimações identificadas por órgão (Receita, SEFAZ, TJ, etc.)
   - Notificações enviadas aos advogados e contadores via WhatsApp
   - Ocorrências pendentes ou erros de entrega, se houver.
