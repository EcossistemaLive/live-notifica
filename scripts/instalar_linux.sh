#!/usr/bin/env bash
set -e

echo "====================================================================="
echo "       LIVE MONITOR - INSTALAÇÃO DO SISTEMA (LINUX / DOCKER)         "
echo "====================================================================="

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python 3 não encontrado! Instale via: sudo apt update && sudo apt install -y python3 python3-pip"
    exit 1
fi

echo "1/3 Instalando dependências..."
python3 -m pip install --upgrade pip
python3 -m pip install -r engine/requirements.txt

echo "2/3 Instalando navegador Chromium e dependências de sistema..."
python3 -m playwright install --with-deps chromium

echo "3/3 Preparando arquivos de configuração..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[OK] Arquivo .env criado a partir do modelo!"
fi

if [ ! -f config/clients.yaml ]; then
    cp config/clients.template.yaml config/clients.yaml
    echo "[OK] Arquivo config/clients.yaml criado a partir do modelo!"
fi

chmod +x docker/entrypoint.sh 2>/dev/null || true

echo "====================================================================="
echo "                  INSTALAÇÃO CONCLUÍDA COM SUCESSO!                  "
echo "====================================================================="
echo "Para iniciar via Docker:   cd docker && docker compose up -d"
echo "Para iniciar no terminal:  python3 -m engine.main --scheduler"
