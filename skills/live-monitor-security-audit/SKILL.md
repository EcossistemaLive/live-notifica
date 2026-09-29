---
name: live-monitor-security-audit
description: "Audita a segurança dos dados, conformidade com a LGPD (Lei 13.709/2018) e exigências éticas e legais da OAB (Lei 8.906/1994 e Provimento 205/2021)."
version: 1.0.0
author: Ecossistema Live
license: MIT
metadata:
  hermes:
    tags: [security, lgpd, oab, compliance, privacy, legal-ethics, audit]
---

# Live Monitor - Skill: Auditoria de Segurança de Dados (LGPD & OAB)

## Visão Geral
Esta skill estabelece o protocolo de auditoria de segurança de dados e privacidade para o **Live Monitor**, aplicando os conceitos e exigências da **Lei Geral de Proteção de Dados (Lei 13.709/2018 - LGPD)** e do **Estatuto da Advocacia e Código de Ética e Disciplina da OAB (Lei 8.906/1994 e Provimento 205/2021)**.

Como o sistema lida com intimações judiciais, execuções fiscais, malhas tributárias e documentos societários sigilosos, a conformidade é obrigatória em todas as etapas da esteira.

---

## 1. Fundamentos da LGPD Aplicados ao Sistema

1. **Base Legal Primária (Art. 7º, II da LGPD):**
   - O tratamento de dados pessoais contidos em autos e notificações governamentais ocorre sob o fundamento do **cumprimento de obrigação legal ou regulatória** pelo controlador (as empresas clientes), sendo o Live Monitor o operador técnico do roteamento célere.
2. **Princípio da Minimização de Dados (Art. 6º, III da LGPD):**
   - Os logs e alertas devem conter apenas o estritamente necessário para que o patrono constituído tome providências.
   - Aplicação de rotinas de mascaramento para dados pessoais:
     - **CPF:** `***.456.789-**` (ocultação dos primeiros e últimos dígitos).
     - **Telefone em Relatórios:** `+55 61 9****-3134`.
3. **Segurança e Sigilo Técnico (Art. 46 da LGPD):**
   - Diretórios sensíveis (`data/whatsapp_session/`, `data/attachments/`, `data/live_monitor.db`) e o arquivo de variáveis de ambiente (`.env`) devem estar estritamente isolados pelo `.gitignore`.
4. **Política de Retenção e Expiração de Documentos (Art. 15 e 16 da LGPD):**
   - Os anexos em PDF são retidos temporariamente como backup de entrega.
   - O auditor avalia documentos com mais de 60 dias para arquivamento ou descarte seguro, evitando passivo desnecessário de dados.

---

## 2. Exigências Éticas e Prerrogativas da OAB

1. **Inviolabilidade do Sigilo Profissional (Art. 7º, II da Lei 8.906/1994):**
   - Todas as comunicações entre a empresa e seus advogados parceiros são resguardadas por sigilo legal.
   - **Regra da Segregação Absoluta:** O auditor valida `config/clients.yaml` e rejeita qualquer configuração em que um mesmo alias de e-mail seja associado a empresas distintas ou que advogados de um cliente recebam comunicações de outro.
2. **Trilha Probatória de Ciência sem Risco de Preclusão:**
   - Para proteger o advogado parceiro contra a alegação de perda de prazo ou revelia, cada intimação capturada é autenticada com hash criptográfico SHA-256 e carimbo de data/hora (ISO 8601).
   - O registro do envio via WhatsApp Web serve como evidência temporal da notificação.
3. **Provimento 205/2021 do Conselho Federal da OAB:**
   - O uso de ferramentas de inteligência artificial e automação é plenamente lícito na rotina jurídica, desde que mantida a discricionariedade, a supervisão humana e a confidencialidade das peças processuais.

---

## 3. Como Executar a Auditoria Automática

### Executar Auditoria via Linha de Comando
```bash
python -m engine.main --audit-security
```

### O que o Auditor Avalia:
- **`OAB_CLIENT_SEGREGATION`**: Verifica se há colisão ou sobreposição de aliases entre empresas e se todos os clientes possuem patronos designados.
- **`LGPD_CREDENTIAL_HYGIENE`**: Confirma o bloqueio de tokens, senhas e credenciais no controle de versão Git.
- **`OAB_AUDIT_TRAIL`**: Valida a presença e integridade dos hashes SHA-256 em todas as mensagens registradas.
- **`LGPD_STORAGE_SECURITY`**: Confirma a integridade física e o isolamento dos diretórios de dados locais.
- **`LGPD_DATA_RETENTION`**: Identifica e aponta documentos antigos para expurgo preventivo.

### Relatório Formal Gerado:
O auditor compila um laudo detalhado em Markdown em:
[`data/reports/AUDITORIA_SEGURANCA_LGPD_OAB.md`](file:///G:/Meu%20Drive/Consultoria/clientes/ecossistema-live/produtos/live-notifica/data/reports/AUDITORIA_SEGURANCA_LGPD_OAB.md).
