#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Motor de Triagem e Classificação Semântica
Analisa o conteúdo de e-mails recebidos, classifica intimações e órgãos governamentais,
extrai prazos, número de processo, severidade e define o roteamento para advogados ou contadores.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import requests

from .config import (
    LLM_PROVIDER, ANTHROPIC_API_KEY, GEMINI_API_KEY, logger
)

# Padrões Heurísticos para Detecção de Órgãos
AGENCY_PATTERNS = [
    {
        "agency": "Receita Federal do Brasil (e-CAC / DTE)",
        "category": "receita_federal",
        "keywords": [r"receita federal", r"e-cac", r"caixa postal.*e-cac", r"dte", r"pgfn", r"malha fiscal", r"darf", r"termo de intimacao fiscal"],
        "default_target": "contadores"
    },
    {
        "agency": "Procuradoria-Geral da Fazenda Nacional (PGFN)",
        "category": "pgfn",
        "keywords": [r"pgfn", r"divida ativa da uniao", r"execucao fiscal", r"regularize"],
        "default_target": "advogados"
    },
    {
        "agency": "Secretaria de Estado da Fazenda (SEFAZ)",
        "category": "sefaz",
        "keywords": [r"sefaz", r"secretaria de estado da fazenda", r"dtec", r"auto de infracao estadual", r"icms", r"substituicao tributaria"],
        "default_target": "contadores"
    },
    {
        "agency": "Prefeitura Municipal / Fisco Municipal",
        "category": "prefeitura",
        "keywords": [r"prefeitura", r"issqn", r"alvara de funcionamento", r"notificacao municipal", r"secretaria municipal de fazenda"],
        "default_target": "contadores"
    },
    {
        "agency": "Poder Judiciário / Tribunal de Justiça (TJ)",
        "category": "judicial_estadual",
        "keywords": [
            r"tribunal de justica", r"tjdft", r"tjsp", r"tjrj", r"tjmg", r"tjrs", r"tjpr", r"tjsc", r"tjba", r"tjpe",
            r"\btj[a-z]{2}\b", r"pje", r"esaj", r"projudi", r"intimacao judicial", r"citacao eletronica",
            r"dje", r"diario da justica", r"vara de execucao", r"processo judicial"
        ],
        "default_target": "advogados"
    },
    {
        "agency": "Justiça Federal (TRF)",
        "category": "judicial_federal",
        "keywords": [r"tribunal regional federal", r"\btrf\d?\b", r"justica federal", r"eproc", r"secao judiciaria"],
        "default_target": "advogados"
    },
    {
        "agency": "Justiça do Trabalho (TRT / TST)",
        "category": "trabalhista",
        "keywords": [r"tribunal regional do trabalho", r"\btrt\d?\b", r"tst", r"justica do trabalho", r"vara do trabalho", r"mpt", r"audiencia una", r"reclamacao trabalhista"],
        "default_target": "advogados"
    },
    {
        "agency": "Órgão Regulador / Vigilância Sanitária (ANVISA/MAPA)",
        "category": "regulador",
        "keywords": [r"anvisa", r"vigilancia sanitaria", r"mapa", r"ibama", r"procon", r"inmetro", r"jucesp", r"junta comercial"],
        "default_target": "ambos"
    }
]

# Regex para Prazos e Processos
RE_DEADLINE_DAYS = re.compile(
    r'(?:prazo\s+(?:de|para\s+[\w\s]+)?:?\s*|em\s+at[ée]\s+)(\d{1,3})\s*(?:dias|dias\s+corridos|dias\s+úteis)',
    re.IGNORECASE
)
RE_PROCESS_NUM = re.compile(r'\b(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}|\d{5}\.\d{6}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}/\d{4}-\d{2})\b')
RE_CNPJ = re.compile(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b')

class TriageClassifier:
    """Motor de triagem semântica para classificação de notificações fiscais/jurídicas."""

    def __init__(self):
        self.provider = LLM_PROVIDER

    def analyze(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a análise do e-mail.
        Combina heurística robusta e chamada a LLM quando disponível.
        """
        subject = email_data.get("subject", "")
        body = email_data.get("body_text", "")
        full_text = f"Assunto: {subject}\n\n{body}"

        # 1. Executa análise heurística básica
        heuristic_res = self._heuristic_analysis(full_text)

        # 2. Se houver chave de API e LLM estiver configurado, enriquece com resumo estruturado
        if self.provider == "anthropic" and ANTHROPIC_API_KEY:
            llm_res = self._llm_analysis_anthropic(full_text)
            if llm_res:
                return self._merge_results(heuristic_res, llm_res)
        elif self.provider == "gemini" and GEMINI_API_KEY:
            llm_res = self._llm_analysis_gemini(full_text)
            if llm_res:
                return self._merge_results(heuristic_res, llm_res)

        return heuristic_res

    def _heuristic_analysis(self, text: str) -> Dict[str, Any]:
        """Analisa o texto através de padrões regulares e palavras-chave."""
        text_lower = text.lower()
        
        detected_agency = "Outro Órgão / Notificação Geral"
        detected_category = "geral"
        target_role = "contadores"
        urgency = "media"

        # Detecta Órgão
        for pattern in AGENCY_PATTERNS:
            for kw in pattern["keywords"]:
                if re.search(kw, text_lower):
                    detected_agency = pattern["agency"]
                    detected_category = pattern["category"]
                    target_role = pattern["default_target"]
                    break
            if detected_category != "geral":
                break

        # Detecta Prazo
        prazo_dias = None
        data_limite = None
        deadline_match = RE_DEADLINE_DAYS.search(text)
        if deadline_match:
            try:
                prazo_dias = int(deadline_match.group(1))
                limite_dt = datetime.now() + timedelta(days=prazo_dias)
                data_limite = limite_dt.strftime("%d/%m/%Y")
            except Exception:
                pass

        # Detecta Número do Processo
        process_match = RE_PROCESS_NUM.search(text)
        process_number = process_match.group(1) if process_match else "Não especificado"

        # Detecta CNPJ
        cnpj_match = RE_CNPJ.search(text)
        cnpj_detected = cnpj_match.group(0) if cnpj_match else None

        # Urgência
        if prazo_dias is not None:
            if prazo_dias <= 5:
                urgency = "critica"
            elif prazo_dias <= 15:
                urgency = "alta"
            else:
                urgency = "media"
        elif any(k in text_lower for k in ["penhora", "bloqueio judicial", "mandado", "citacao", "urgente"]):
            urgency = "critica"
            target_role = "advogados"

        summary = f"Notificação identificada de {detected_agency}. Processo/Identificador: {process_number}."
        if prazo_dias:
            summary += f" Prazo estimado de {prazo_dias} dias (até {data_limite})."

        return {
            "agency": detected_agency,
            "category": detected_category,
            "target_role": target_role,
            "process_number": process_number,
            "cnpj_detected": cnpj_detected,
            "prazo_dias": prazo_dias,
            "data_limite": data_limite,
            "urgency": urgency,
            "summary": summary,
            "is_relevant": detected_category != "geral" or prazo_dias is not None
        }

    def _llm_analysis_anthropic(self, text: str) -> Optional[Dict[str, Any]]:
        """Usa a API Anthropic Claude para triagem semântica precisa."""
        try:
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            prompt = f"""Você é o motor de triagem do Live Monitor, um sistema para indústrias e empresas que monitora intimações oficiais.
Analise a mensagem abaixo e responda estritamente em formato JSON válido:

Texto da mensagem:
\"\"\"
{text[:4000]}
\"\"\"

Campos esperados no JSON:
{{
  "is_relevant": true/false (true se for intimação, notificação fiscal, judicial, SEFAZ, Receita, prefeitura ou órgão regulador),
  "agency": "Nome do órgão emissor",
  "category": "judicial" | "receita_federal" | "sefaz" | "prefeitura" | "trabalhista" | "regulador" | "outro",
  "target_role": "advogados" | "contadores" | "ambos",
  "process_number": "Número do processo ou auto de infração se houver",
  "prazo_dias": número inteiro de dias para cumprimento ou null,
  "data_limite": "DD/MM/AAAA ou null",
  "urgency": "critica" | "alta" | "media" | "baixa",
  "summary": "Resumo executivo claro em no máximo 2 frases do que se trata e qual a ação requerida"
}}
"""
            payload = {
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 600,
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                content = res.json()["content"][0]["text"]
                # Extrai bloco JSON
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
        except Exception as e:
            logger.warning(f"Falha ao chamar LLM Anthropic: {e}. Usando triagem heurística.")
        return None

    def _llm_analysis_gemini(self, text: str) -> Optional[Dict[str, Any]]:
        """Usa a API Gemini para triagem semântica."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
            prompt = f"""Você é o motor de triagem do Live Monitor. Analise a mensagem e responda APENAS em JSON:
{text[:4000]}

Formato esperado:
{{
  "is_relevant": true,
  "agency": "Nome do órgão",
  "category": "judicial | receita_federal | sefaz | prefeitura | trabalhista | regulador | outro",
  "target_role": "advogados | contadores | ambos",
  "process_number": "número ou Não especificado",
  "prazo_dias": 15,
  "data_limite": "DD/MM/AAAA",
  "urgency": "critica | alta | media | baixa",
  "summary": "Resumo objetivo em 2 frases"
}}
"""
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                raw_json = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_json)
        except Exception as e:
            logger.warning(f"Falha ao chamar LLM Gemini: {e}. Usando triagem heurística.")
        return None

    def _merge_results(self, heuristic: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
        """Combina os dados heurísticos com os dados de inteligência semântica."""
        merged = dict(heuristic)
        for k, v in llm.items():
            if v is not None and v != "":
                merged[k] = v
        return merged
