"""
services/debate/groq_auditor.py — Online Zero-Cost AI Auditor via Groq Cloud.

Interroga modelli open ad alte prestazioni (es. GPT-OSS 120B, Qwen 27B) su Groq Cloud LPU
in meno di 1 secondo, a costo zero e senza impegnare la CPU/GPU locale dell'utente.
Fornisce un contro-parere indipendente su quote, trappole bookmaker, scenari di perdita e stake.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Carica variabili d'ambiente da .env
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.8-27b"


class GroqAuditor:
    """Auditor critico indipendente online alimentato da Groq Cloud."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key if api_key is not None else os.getenv("GROQ_API_KEY", "")
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("gsk_"))

    def audit_ticket(
        self,
        title: str,
        legs: List[Dict[str, Any]],
        bankroll: float = 37.32,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Invia il ticket a Groq Cloud per un audit critico avversariale."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "GROQ_API_KEY non configurata o non valida.",
                "approved": False,
            }

        target_model = model or self.model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Formatta le selezioni per il prompt
        legs_desc = []
        tot_odd = 1.0
        for i, leg in enumerate(legs, 1):
            odd = float(leg.get("book_odd", 1.0))
            fair = float(leg.get("fair_odd", 1.0))
            p = float(leg.get("probability", 0.0))
            edge = float(leg.get("edge", 0.0))
            tot_odd *= odd
            legs_desc.append(
                f"Leg {i}: {leg.get('match_name')} ({leg.get('tournament', '')})\n"
                f"  - Mercato: {leg.get('market')}\n"
                f"  - Quota Netwin: {odd:.2f} | Quota Fair: {fair:.2f} | P: {p*100:.1f}% | Edge: {edge*100:+.1f}%\n"
                f"  - Note/DNA: {leg.get('sixth_sense', leg.get('notes', 'Standard'))}"
            )

        user_content = (
            f"TICKET DA ESAMINARE: '{title}'\n"
            f"Quota Totale: {tot_odd:.2f} | Bankroll attuale: €{bankroll:.2f}\n\n"
            + "\n\n".join(legs_desc)
            + "\n\n"
            "Istruzioni per l'Audit:\n"
            "1. Analisi Matematica: valuta l'effettivo valore atteso (+EV) e la coerenza delle quote.\n"
            "2. Analisi Trappole Bookmaker: identifica lo scenario esatto (o gli scenari) che portano alla perdita per ciascuna leg.\n"
            "3. Verdetto Finale: 'APPROVATA' o 'BOCCIATA'. Se approvata, indica una percentuale di stake consigliata sul bankroll (es. 2-5%).\n"
            "Sii conciso, spietato contro i rischi occulti e vai dritto al punto."
        )

        system_prompt = (
            "Sei un Senior Risk & Value Betting Auditor. Il tuo compito è smascherare trappole dei bookmaker, "
            "eccessi di confidenza statistica e verificare che le selezioni abbiano valore matematico reale. "
            "Glossario mercati bookmaker italiani (Netwin):\n"
            "- 'MultiGol X-Y Casa' / 'MultiGol X-Y Ospite': indica il totale gol segnati SOLO da quella squadra (es. 'MultiGol 0-1 Ospite' = la squadra in trasferta segna esattamente 0 o 1 gol nel match, ovvero Under 1.5 gol squadra ospite).\n"
            "- 'Chance Mix: A o B': la scommessa è vinta se si verifica la condizione A OPPURE la condizione B (es. 'X2 o Gol' vince con X2 o se entrambe segnano; perde solo in caso di vittoria casalinga a zero 1-0, 2-0, ecc.).\n"
            "- 'MultiGol 0-1 1° Tempo': nel solo primo tempo vengono segnati complessivamente 0 o 1 gol (0-0, 1-0 o 0-1 all'intervallo).\n"
            "Non usare mai gergo vago. Rispondi in italiano con struttura chiara."
        )

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        }

        try:
            resp = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=20)
            if resp.status_code == 404 and target_model != FALLBACK_MODEL:
                # Fallback al secondo modello
                payload["model"] = FALLBACK_MODEL
                resp = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=20)

            if resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Errore HTTP {resp.status_code}: {resp.text}",
                    "approved": False,
                }

            result_json = resp.json()
            critique = result_json["choices"][0]["message"]["content"]
            is_approved = "APPROVATA" in critique.upper() and "BOCCIATA" not in critique.upper().split("APPROVATA")[0]

            return {
                "success": True,
                "model_used": payload["model"],
                "approved": is_approved,
                "critique": critique,
                "total_odd": round(tot_odd, 2),
            }

        except Exception as e:
            logger.error("Errore durante la chiamata a Groq Cloud: %s", e)
            return {
                "success": False,
                "error": str(e),
                "approved": False,
            }
