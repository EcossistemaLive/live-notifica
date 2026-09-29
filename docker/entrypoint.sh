#!/usr/bin/env bash
set -e

echo "=== INICIANDO LIVE MONITOR CONTAINER ==="
echo "Data/Hora local: $(date)"

# Garante existência dos diretórios de dados
mkdir -p /app/data/logs /app/data/attachments /app/data/whatsapp_session

# Validação rápida de configuração
if [ ! -f /app/config/clients.yaml ]; then
    echo "[AVISO] /app/config/clients.yaml não encontrado. Criando modelo inicial..."
    mkdir -p /app/config
fi

# Se comando passado começar com hífen, prefixa com python -m engine.main
if [ "${1#-}" != "$1" ]; then
    set -- python -m engine.main "$@"
fi

exec "$@"
