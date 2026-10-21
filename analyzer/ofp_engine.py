#!/usr/bin/env python3
"""
BAgent OFP Engine (Oddspedia / Forebet / Pengwin)

Modulo di incrocio a tripla convergenza statistica e tattica:
- O = Oddspedia (Market consensus, quote bookmakers, dropping odds, sentiment)
- F = Forebet (Modelli matematici Poisson, probabilita %, xG, risultati esatti)
- P = MondoPengwin (Analisi qualitativa, flussi mercati speciali, cartellini/angoli)

IMPORTANTE (Reality Gate):
  Non popolare mai questo motore con rose, allenatori o partite a memoria.
  Ogni analisi live deve arrivare da feed certificati (API / DB / scanner),
  mai da dati hard-coded di una giornata specifica.
"""

from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class OFPMatchAnalysis:
    match: str
    kickoff: str
    tournament: str

    # Dati squadre e rose (devono arrivare da fonti certificate)
    home_manager: str
    away_manager: str
    home_key_players: str
    away_key_players: str
    home_absences: str
    away_absences: str

    # 1. O - Oddspedia
    oddspedia_odds: Dict[str, float]
    oddspedia_sentiment: str
    oddspedia_key_market: str

    # 2. F - Forebet
    forebet_pred_score: str
    forebet_prob: Dict[str, int]
    forebet_over_under: str

    # 3. P - Pengwin
    pengwin_pick: str
    pengwin_rationale: str
    pengwin_special: Optional[str]

    # Sintesi OFP
    convergence_grade: str  # "AAA", "AA", "A"
    recommended_primary: str
    recommended_safe: str
    target_odds: float
    risk_profile: str  # "BASSO", "MEDIO", "ALTO"


class OFPEngine:
    """Motore di raccolta e sintesi delle analisi OFP."""

    def __init__(self) -> None:
        self.matches: List[OFPMatchAnalysis] = []

    def add_match(self, analysis: OFPMatchAnalysis) -> None:
        self.matches.append(analysis)

    def get_tier_one_picks(self) -> List[OFPMatchAnalysis]:
        """Restituisce solo i match con massima convergenza (AAA o AA)."""
        return [m for m in self.matches if m.convergence_grade in ("AAA", "AA")]

    def generate_recommended_doubles(self) -> List[Dict]:
        """Genera combinazioni a doppia tra i pick di tier 1."""
        tier1 = self.get_tier_one_picks()
        doubles: List[Dict] = []
        if len(tier1) >= 2:
            m1, m2 = tier1[0], tier1[1]
            doubles.append(
                {
                    "type": "DOPPIA_SICUREZZA_OFP",
                    "label": "Doppia Raddoppio Conservativa (Grade AAA/AA)",
                    "legs": [
                        {
                            "match": m1.match,
                            "pick": m1.recommended_safe,
                            "odds": m1.target_odds,
                        },
                        {
                            "match": m2.match,
                            "pick": m2.recommended_safe,
                            "odds": m2.target_odds,
                        },
                    ],
                    "total_odds": round(m1.target_odds * m2.target_odds, 2),
                }
            )
        return doubles

    def to_dict(self) -> List[Dict]:
        return [
            {
                "match": m.match,
                "kickoff": m.kickoff,
                "tournament": m.tournament,
                "managers": f"{m.home_manager} vs {m.away_manager}",
                "key_players": {
                    "home": m.home_key_players,
                    "away": m.away_key_players,
                },
                "absences": {
                    "home": m.home_absences,
                    "away": m.away_absences,
                },
                "oddspedia": {
                    "odds": m.oddspedia_odds,
                    "sentiment": m.oddspedia_sentiment,
                    "key_market": m.oddspedia_key_market,
                },
                "forebet": {
                    "pred_score": m.forebet_pred_score,
                    "prob": m.forebet_prob,
                    "over_under": m.forebet_over_under,
                },
                "pengwin": {
                    "pick": m.pengwin_pick,
                    "rationale": m.pengwin_rationale,
                    "special": m.pengwin_special,
                },
                "ofp_summary": {
                    "convergence_grade": m.convergence_grade,
                    "recommended_primary": m.recommended_primary,
                    "recommended_safe": m.recommended_safe,
                    "target_odds": m.target_odds,
                    "risk_profile": m.risk_profile,
                },
            }
            for m in self.matches
        ]


def build_empty_ofp_engine() -> OFPEngine:
    """
    Restituisce un motore vuoto pronto a essere popolato da feed live.

    NON usare dati hard-coded di giornate passate. Ogni match deve arrivare
    da scanner / API / Reality Gate certificati.
    """
    return OFPEngine()


if __name__ == "__main__":
    eng = build_empty_ofp_engine()
    print(
        f"OFPEngine pronto ({len(eng.matches)} match). "
        "Popolare solo da fonti certificate — nessun slate hard-coded."
    )
