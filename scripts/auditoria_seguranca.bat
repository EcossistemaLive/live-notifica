@echo off
chcp 65001 > nul
title Auditoria de Segurança de Dados (LGPD e OAB)

echo =====================================================================
echo         RELATÓRIO DE AUDITORIA DE SEGURANÇA (LGPD E OAB)
echo =====================================================================
echo Executando testes automáticos de conformidade...
echo.

python -m engine.main --audit-security

echo.
echo Abrindo o laudo de conformidade em Markdown...
if exist "data\reports\AUDITORIA_SEGURANCA_LGPD_OAB.md" (
    start "" "data\reports\AUDITORIA_SEGURANCA_LGPD_OAB.md"
)
pause
