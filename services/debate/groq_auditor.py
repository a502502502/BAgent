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

# Bocciatura ammessa solo con uno di questi segnali. L'EV negativo non è tra questi.
_STRUCTURAL_MARKERS = (
    "RISCHIO_STRUTTURALE",
    "1X2 SECCO",
    "SEGNO 1 SECCO",
    "SEGNO 2 SECCO",
    "ANTI-FAVORITA",
    "CORAZZATA",
    "REGOLA #80",
    "REGOLA #82",
)


def resolve_audit_verdict(critique: str) -> tuple[bool, Optional[str]]:
    """L'EV e l'edge non bocciano la scommessa. Restano un avviso.

    approved è False solo se il testo segnala un rischio strutturale.
    """
    upper = critique.upper()
    structural = any(marker in upper for marker in _STRUCTURAL_MARKERS)
    if structural and "BOCCIATA" in upper:
        return False, None
    model_approved = "APPROVATA" in upper and "BOCCIATA" not in upper.split("APPROVATA")[0]
    if model_approved:
        return True, None
    return True, "EV/edge: avviso informativo, non bloccante."


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
            "1. Analisi Matematica: calcola il valore atteso (EV) e riportalo. "
            "L'EV negativo o sotto +4% è SOLO un avviso. Non è mai un motivo di bocciatura.\n"
            "2. Analisi Trappole Bookmaker: identifica lo scenario esatto che fa perdere ciascuna selezione.\n"
            "3. Verdetto Finale: 'APPROVATA', anche con EV negativo. "
            "Scrivi 'BOCCIATA' solo insieme alla parola RISCHIO_STRUTTURALE, "
            "e solo per un vincolo di mercato (1X2 secco, anti-favorita su corazzata, under stretto su corazzata, tetto di gol su attacco dominante). "
            "Se approvata, indica una percentuale di stake consigliata sul bankroll (es. 2-5%).\n"
            "Sii conciso e vai dritto al punto."
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
            is_approved, ev_warning = resolve_audit_verdict(critique)

            return {
                "success": True,
                "model_used": payload["model"],
                "approved": is_approved,
                "ev_warning": ev_warning,
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

    def dialectic_debate_loop(
        self,
        title: str,
        initial_legs: List[Dict[str, Any]],
        rectification_callback: Optional[Any] = None,
        bankroll: float = 37.32,
        max_turns: int = 3,
    ) -> Dict[str, Any]:
        """
        Regola #77: Ciclo Dialettico Obbligatorio Pre-Costruzione Schedina.
        1. L'Auditor (Groq 120B) fa l'avvocato del diavolo e scova la trappola.
        2. Il Modellista Quantitativo accoglie l'obiezione e ristruttura le giocate.
        3. Re-Audit finché non si raggiunge il consenso unanime (APPROVATA).
        """
        debate_history = []
        current_legs = list(initial_legs)
        current_title = title

        for turn in range(1, max_turns + 1):
            audit_res = self.audit_ticket(current_title, current_legs, bankroll=bankroll)
            debate_history.append({
                "turn": turn,
                "title": current_title,
                "legs": [dict(l) for l in current_legs],
                "approved": audit_res.get("approved", False),
                "critique": audit_res.get("critique", ""),
                "total_odd": audit_res.get("total_odd", 1.0),
            })

            if audit_res.get("approved"):
                return {
                    "consensus_reached": True,
                    "final_status": "APPROVATA",
                    "turns_needed": turn,
                    "final_legs": current_legs,
                    "total_odd": audit_res.get("total_odd", 1.0),
                    "audit_verdict": audit_res.get("critique", ""),
                    "debate_history": debate_history,
                }

            # Se bocciata e ci sono altri turni, attiva la rettifica quantitativa
            if turn < max_turns and rectification_callback is not None:
                new_legs = rectification_callback(audit_res, current_legs)
                if new_legs and new_legs != current_legs:
                    current_legs = new_legs
                    current_title = f"{title} (Rettifica Turno {turn+1})"
                    continue

        return {
            "consensus_reached": False,
            "final_status": "BOCCIATA_SENZA_CONSENSO",
            "turns_needed": max_turns,
            "final_legs": current_legs,
            "total_odd": debate_history[-1].get("total_odd", 1.0) if debate_history else 1.0,
            "audit_verdict": debate_history[-1].get("critique", "") if debate_history else "",
            "debate_history": debate_history,
        }
