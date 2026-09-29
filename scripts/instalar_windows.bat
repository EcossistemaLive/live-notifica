@echo off
chcp 65001 > nul
title Instalação do Live Monitor - Configuração Inicial

echo =====================================================================
echo           LIVE MONITOR - ASSISTENTE DE INSTALAÇÃO DO ESCRITÓRIO
echo =====================================================================
echo.
echo Verificando ambiente Python...

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não foi encontrado no computador!
    echo Por favor, instale o Python 3.11 ou superior em https://www.python.org/
    echo Lembre-se de marcar a opção "Add Python to PATH" durante a instalação.
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado!
echo.
echo 1/3 Instalando bibliotecas necessárias...
python -m pip install --upgrade pip
python -m pip install -r engine\requirements.txt

echo.
echo 2/3 Baixando o navegador seguro para WhatsApp Web (Playwright)...
python -m playwright install chromium

echo.
echo 3/3 Configurando arquivos do escritório...
if not exist .env (
    copy .env.example .env > nul
    echo [OK] Arquivo de configurações .env criado a partir do modelo!
) else (
    echo [INFO] Arquivo .env já existe. Mantendo configurações atuais.
)

if not exist config\clients.yaml (
    copy config\clients.template.yaml config\clients.yaml > nul
    echo [OK] Arquivo de clientes config\clients.yaml criado a partir do modelo!
)

echo.
echo =====================================================================
echo             INSTALAÇÃO DE PACOTES CONCLUÍDA COM SUCESSO!
echo =====================================================================
echo.
echo Próximos passos recomendados:
echo 1. Abra o arquivo .env no Bloco de Notas e preencha o e-mail do escritório.
echo 2. Execute o arquivo "conectar_whatsapp.bat" para ler o QR Code da consultoria.
echo 3. Cadastre os clientes da sua carteira no arquivo config\clients.yaml.
echo.
pause
