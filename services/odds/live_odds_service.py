"""
services/odds/live_odds_service.py — Servizio di Recupero Quote Reali Live da Bookmaker (FootyStats & The Odds API).
Estrae le quote reali al centesimo per alimentare QuantitativeEngine e applicare la REGOLA DI CALCOLO RIGOROSA:
Edge Reale = (Quota_Reale * Probabilita_Modello) - 1
Se Edge <= 0 -> NO BET / TRAPPOLA DEL BANCO (La quota bookmaker è troppo bassa).
Se Edge > 0 -> VALUE BET (EV+) con calcolo Stake Kelly Frazionale (25%).
"""

from __future__ import annotations
import os
import re
import logging
import requests
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger("LiveOddsService")

ROOT = Path(__file__).resolve().parent.parent.parent
FOOTYSTATS_KEY = os.getenv("FOOTYSTATS_API_KEY", "f2a628dad87df2671c37b2c7eab20de901590c8651b7a332c85bf3c4979dbaba")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

class LiveOddsService:
    """
    Recupera quote reali da API ufficiali di mercato (FootyStats / The Odds API)
    per eliminare qualsiasi stima teorica nei calcoli di BAgent.
    """

    def __init__(self, footystats_key: Optional[str] = None, odds_api_key: Optional[str] = None):
        self.footystats_key = footystats_key or FOOTYSTATS_KEY
        self.odds_api_key = odds_api_key or ODDS_API_KEY
        self.session = requests.Session()
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    def get_matches_by_date(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recupera l'elenco di tutte le partite con quote reali per una determinata data (YYYY-MM-DD).
        Se date_str è None, recupera quelle di oggi.
        """
        if not self.footystats_key:
            logger.warning("Nessuna chiave FootyStats configurata.")
            return []

        cache_key = date_str or "today"
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = f"https://api.football-data-api.com/todays-matches?key={self.footystats_key}"
        if date_str:
            url += f"&date={date_str}"

        try:
            r = self.session.get(url, timeout=12)
            if r.status_code != 200:
                logger.error(f"Errore FootyStats API ({r.status_code}): {r.text}")
                return []
            
            data = r.json().get("data", [])
            results = []
            for m in data:
                home = m.get("home_name", "")
                away = m.get("away_name", "")
                
                odds_dict = {
                    "match": f"{home} vs {away}",
                    "home_team": home,
                    "away_team": away,
                    "league": m.get("competition_name") or m.get("league_name") or "Campionato",
                    "country": m.get("country", ""),
                    "date_unix": m.get("date_unix"),
                    "status": m.get("status"),
                    "odds": {
                        "1": float(m.get("odds_ft_1") or 0.0),
                        "X": float(m.get("odds_ft_x") or 0.0),
                        "2": float(m.get("odds_ft_2") or 0.0),
                        "1X": float(m.get("odds_doublechance_1x") or 0.0),
                        "X2": float(m.get("odds_doublechance_x2") or 0.0),
                        "12": float(m.get("odds_doublechance_12") or 0.0),
                        "Over 1.5": float(m.get("odds_ft_over15") or 0.0),
                        "Under 1.5": float(m.get("odds_ft_under15") or 0.0),
                        "Over 2.5": float(m.get("odds_ft_over25") or 0.0),
                        "Under 2.5": float(m.get("odds_ft_under25") or 0.0),
                        "Over 3.5": float(m.get("odds_ft_over35") or 0.0),
                        "Under 3.5": float(m.get("odds_ft_under35") or 0.0),
                        "Goal (GG)": float(m.get("odds_btts_yes") or 0.0),
                        "NoGoal (NG)": float(m.get("odds_btts_no") or 0.0),
                    },
                    "corners_potential": float(m.get("corners_potential") or 0.0),
                    "cards_potential": float(m.get("cards_potential") or 0.0),
                    "btts_potential": float(m.get("btts_potential") or 0.0)
                }
                results.append(odds_dict)
            
            self._cache[cache_key] = results
            return results
        except Exception as e:
            logger.error(f"Eccezione recupero quote FootyStats: {e}")
            return []

    def get_todays_live_odds(self) -> List[Dict[str, Any]]:
        """Recupera le partite di oggi con quote reali."""
        return self.get_matches_by_date(None)

    def get_weekend_odds(self) -> List[Dict[str, Any]]:
        """Recupera tutte le partite del weekend (Sabato 26/09 e Domenica 27/09)."""
        sat = self.get_matches_by_date("2026-09-26")
        sun = self.get_matches_by_date("2026-09-27")
        return sat + sun

    def find_match_odds(self, home_team: str, away_team: str, date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Cerca le quote reali di una specifica partita.
        Cerca nella data indicata, oppure in oggi e poi nel weekend.
        """
        matches_to_search = []
        if date_str:
            matches_to_search = self.get_matches_by_date(date_str)
        else:
            matches_to_search = self.get_todays_live_odds() + self.get_weekend_odds()

        h_clean = home_team.lower().strip()
        a_clean = away_team.lower().strip()

        for m in matches_to_search:
            mh = m["home_team"].lower()
            ma = m["away_team"].lower()
            if (h_clean in mh or mh in h_clean) and (a_clean in ma or ma in a_clean):
                return m

        return None

    @staticmethod
    def calculate_edge_and_kelly(real_odd: float, model_prob: float, kelly_fraction: float = 0.25) -> Dict[str, Any]:
        """
        REGOLA CARDINE DEL CALCOLO:
        - Quota Equa (Fair): 1 / model_prob
        - Edge Reale: (Quota_Reale * model_prob) - 1.0
        - Se Edge <= 0: Quota bookmaker non conveniente (EV-, Trappola del banco). Stake = 0.
        - Se Edge > 0: Quota conveniente (EV+). Calcolo Kelly frazionario al 25%.
        """
        if model_prob <= 0.0 or model_prob >= 1.0:
            return {
                "fair_odd": 1.0,
                "real_odd": real_odd,
                "edge_pct": 0.0,
                "is_ev_plus": False,
                "kelly_pct": 0.0,
                "verdict": "DATI NON VALIDI"
            }

        fair_odd = round(1.0 / model_prob, 2)

        if real_odd <= 1.0:
            return {
                "fair_odd": fair_odd,
                "real_odd": 0.0,
                "edge_pct": 0.0,
                "is_ev_plus": False,
                "kelly_pct": 0.0,
                "verdict": "QUOTA BOOKMAKER ASSENTE"
            }

        edge = (real_odd * model_prob) - 1.0
        edge_pct = round(edge * 100, 2)
        b = real_odd - 1.0
        q = 1.0 - model_prob

        if edge > 0:
            full_kelly = (b * model_prob - q) / b
            fractional_kelly = max(0.0, full_kelly * kelly_fraction)
            kelly_pct = round(fractional_kelly * 100, 2)
            verdict = f"💎 EV+ ({'+' if edge_pct > 0 else ''}{edge_pct}%) — GIOCABILE"
        else:
            kelly_pct = 0.0
            verdict = f"⚠️ EV- ({edge_pct}%) — TRAPPOLA DEL BANCO (NO BET)"

        return {
            "fair_odd": fair_odd,
            "real_odd": real_odd,
            "edge_pct": edge_pct,
            "is_ev_plus": edge > 0,
            "kelly_pct": kelly_pct,
            "verdict": verdict
        }
