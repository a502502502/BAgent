"""
services/analysis/post_mortem_engine.py — Post-Mortem Engine & Tactical Feedback Loop (Pilastro 4).

Analizza automaticamente i match e i ticket conclusi:
- Verifica tabellini effettivi (gol, corner, xG, cartellini rossi prematuri, rigori);
- Identifica la causa radice della perdita (Early Red Card, Low Shot Volume, Catena difensiva, ecc.);
- Memorizza la 'lezione tattica' nel database per auto-calibrare il Sesto Senso ed evitare recidive.
"""

from __future__ import annotations
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from services.database.performance_tracker import PerformanceTracker

logger = logging.getLogger("PostMortemEngine")

class PostMortemEngine:
    """
    Motore di auto-apprendimento post-gara per BAgent.
    """

    FAILURE_CATEGORIES = {
        "EARLY_RED_CARD": "Espulsione prematura (< 45') che altera irrimediabilmente il baricentro.",
        "LOW_SHOT_VOLUME": "Produzione offensiva della favorita inferiore alle 14 conclusioni.",
        "PARK_THE_BUS": "Avversario arroccato in area con blocco ultrabasso e match congelato.",
        "PENALTY_VARIANCE": "Rigore fallito o concesso al tramonto del match contro l'inerzia tattica.",
        "DIESEL_FIRST_HALF": "Fase di studio eccessiva con 0-0 al 45' e risveglio tardivo.",
        "SURPRISE_TURNOVER": "Rotazione massiccia dell'undici iniziale decisa nel riscaldamento."
    }

    def __init__(self, tracker: Optional[PerformanceTracker] = None):
        self.tracker = tracker or PerformanceTracker()

    def diagnose_failure(
        self,
        match_name: str,
        market_name: str,
        actual_goals_ft: int,
        actual_goals_ht: int,
        actual_corners: Optional[int] = None,
        red_card_minute: Optional[int] = None,
        total_shots: Optional[int] = None,
        missed_penalty: bool = False
    ) -> Dict[str, Any]:
        """
        Diagnostica la causa del fallimento di una scommessa incrociando i dati reali del match.
        """
        category = "UNCLASSIFIED_VARIANCE"
        lesson = ""
        rule = "Regola #41"

        if red_card_minute is not None and red_card_minute <= 45:
            category = "EARLY_RED_CARD"
            lesson = f"Espulsione al minuto {red_card_minute}' ha distorto la struttura tattica di {match_name}."
            rule = "Regola #50 (Assedio & Adattamento Live)"
        elif missed_penalty:
            category = "PENALTY_VARIANCE"
            lesson = f"Rigore fallito decisivo ha impedito la conversione del volume offensivo in {match_name}."
            rule = "Regola #47 (Mercati Elastici sui Tiri anziché Gol Fissi)"
        elif actual_goals_ht == 0 and actual_goals_ft <= 1:
            category = "PARK_THE_BUS"
            lesson = f"Partita bloccata chiusa con soli {actual_goals_ft} gol. In match tattici evitare mercati rigidi e preferire MultiGol 1-3 o Under protetti."
            rule = "Regola #39 & Regola #51 (MultiGol Protetti & Corto Muso)"
        elif total_shots is not None and total_shots < 16 and "CORNER" in market_name.upper():
            category = "LOW_SHOT_VOLUME"
            lesson = f"Solo {total_shots} tiri totali registrati. Mancanza di volume di fuoco balistico necessario per generare corner."
            rule = "Regola #45 (Soglia Minima 18-20 Tiri per i Corner)"
        elif actual_goals_ht == 0 and actual_goals_ft >= 2:
            category = "DIESEL_FIRST_HALF"
            lesson = f"Partita con avvio diesel (0-0 HT, {actual_goals_ft} gol nel 2°T). Confermata la fragilità dei mercati primo tempo."
            rule = "Regola #40 (Fase 6 Anti-Scadenza 45') & Regola #47 (MG 0-2 1°T + 1-3 2°T)"
        else:
            category = "TACTICAL_VARIANCE"
            lesson = f"Esito non conforme alle aspettative statistiche. Revisionare la profondità della rassegna stampa per {match_name}."
            rule = "Regola #43 (Integrazione Sesto Senso)"

        return {
            "category": category,
            "category_description": self.FAILURE_CATEGORIES.get(category, "Varianza statistica ordinaria"),
            "lesson": lesson,
            "applied_rule": rule
        }

    def record_post_mortem(
        self,
        match_name: str,
        market_name: str,
        odds: float,
        outcome: str,
        actual_goals_ft: int,
        actual_goals_ht: int,
        actual_corners: Optional[int] = None,
        red_card_minute: Optional[int] = None,
        total_shots: Optional[int] = None,
        missed_penalty: bool = False
    ) -> int:
        """Esegue la diagnosi e registra la lezione tattica nel database."""
        stats_str = f"FT: {actual_goals_ft}, HT: {actual_goals_ht}"
        if actual_corners is not None:
            stats_str += f", Corner: {actual_corners}"
        if total_shots is not None:
            stats_str += f", Tiri: {total_shots}"
        if red_card_minute is not None:
            stats_str += f", Rosso: {red_card_minute}'"

        if outcome == "WON":
            lesson_text = f"Mercato '{market_name}' confermato pienamente dalla dinamica di gioco ({stats_str})."
            cat = "SUCCESS_CONFIRMATION"
            rule = "Validazione Positiva"
        else:
            diag = self.diagnose_failure(
                match_name, market_name, actual_goals_ft, actual_goals_ht,
                actual_corners, red_card_minute, total_shots, missed_penalty
            )
            lesson_text = diag["lesson"]
            cat = diag["category"]
            rule = diag["applied_rule"]

        lesson_id = self.tracker.record_tactical_lesson(
            match_name=match_name,
            market_name=market_name,
            odds=odds,
            outcome=outcome,
            tactical_lesson=lesson_text,
            failure_category=cat,
            actual_stats=stats_str,
            applied_rule=rule
        )
        logger.info(f"Lezione tattica #{lesson_id} registrata per {match_name}: {cat}")
        return lesson_id

    def get_recent_tactical_lessons(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Restituisce le lezioni tattiche recenti dal database."""
        with self.tracker._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM tactical_lessons
            ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
