@echo off
chcp 65001 > nul
title Conexão do WhatsApp Web - Live Monitor

echo =====================================================================
echo           CONEXÃO DO WHATSAPP CORPORATIVO (LEITURA DO QR CODE)
echo =====================================================================
echo.
echo Uma janela do navegador será aberta.
echo 1. Abra o WhatsApp no celular do escritório.
echo 2. Vá em Configurações / Aparelhos Conectados -^> Conectar Aparelho.
echo 3. Aponte a câmera para o QR Code na janela que vai abrir.
echo 4. Assim que suas conversas carregarem, o login estará salvo permanentemente!
echo.
pause

python -m engine.main --init-wa-session

echo.
echo Sessão finalizada. Pressione qualquer tecla para sair.
pause > nul
