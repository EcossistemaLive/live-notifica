@echo off
chcp 65001 > nul
title Live Monitor - Executando Monitoramento em Segundo Plano

echo =====================================================================
echo                LIVE MONITOR - SERVIÇO EM OPERAÇÃO
echo =====================================================================
echo O robô está monitorando os e-mails e pronto para avisar os advogados.
echo Para pausar o robô, feche esta janela ou pressione Ctrl+C.
echo.

python -m engine.main --scheduler

pause
