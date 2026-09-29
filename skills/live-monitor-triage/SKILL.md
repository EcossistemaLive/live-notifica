---
name: live-monitor-triage
description: "Classifica semanticamente intimações governamentais, extrai prazos, severidade, processos e define roteamento para advogados ou contadores."
version: 1.0.0
author: Ecossistema Live
license: MIT
metadata:
  hermes:
    tags: [triage, legal, tax, classification, claude, deadlines, routing]
---

# Live Monitor - Skill: Triagem e Classificação Semântica

## Visão Geral
Esta skill processa o conteúdo de mensagens capturadas e seus anexos, realiza a identificação do órgão emissor, extrai os parâmetros processuais críticos (número do processo, auto de infração, prazo legal em dias corridos ou úteis, data estimada de vencimento e severidade) e decide a qual time parceiro a notificação pertence:
- **Advogados Parceiros**: Ações judiciais, citações, intimações de DJE/PJe, autos com risco de execução fiscal ou penhora (PGFN, SisbaJud), audiências trabalhistas (TRT).
- **Contadores Parceiros**: Malhas fiscais, divergências declaratórias (ECF/DCTF/SPED), comunicações do e-CAC/DTE, débitos de ICMS (SEFAZ), notificações municipais (ISSQN, alvarás).
- **Ambos (Alerta Conjunto)**: Infrações graves, bloqueios judiciais e ordens de fiscalização abrangentes.

## Regras de Urgência
- **Crítica (🔴)**: Prazo fatal de cumprimento $\le 5$ dias, ou citações/penhoras judiciais iminentes.
- **Alta (🟠)**: Prazos entre 6 e 15 dias.
- **Média (🟡)**: Prazos acima de 15 dias ou notificações ordinárias de autorregularização.
- **Baixa (ℹ️)**: Comunicados informativos e circulares sem penalidade direta.

## Como Executar

### 1. Testar o Classificador via CLI
```bash
python -m engine.main --test-triage
```

### 2. Uso Programático
```python
from engine.triage import TriageClassifier

classifier = TriageClassifier()
resultado = classifier.analyze({
    "subject": "Intimação Fiscal e-CAC 2026",
    "body_text": "Fica a empresa intimada a retificar a DCTF no prazo de 15 dias."
})

print(resultado["agency"])       # Receita Federal do Brasil (e-CAC / DTE)
print(resultado["target_role"])  # contadores
print(resultado["prazo_dias"])   # 15
print(resultado["urgency"])      # alta
```

## Mecanismos de IA Híbrida
A skill opera em modo resiliente:
1. **Motor Heurístico Local**: Executa instantaneamente sem requisições externas através de expressões regulares especializadas em normas tributárias e do Código de Processo Civil.
2. **Motor LLM (Claude / Gemini)**: Se as chaves `ANTHROPIC_API_KEY` ou `GEMINI_API_KEY` estiverem configuradas no `.env`, a mensagem é submetida a um modelo que gera um resumo executivo sintetizado em 2 frases para leitura rápida no WhatsApp.
