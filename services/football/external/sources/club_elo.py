"""
ClubElo — API pubblica gratuita per rating ELO dei club europei.
http://api.clubelo.com/

Utile come base per campionati con pochi dati storici.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from functools import lru_cache
from typing import Optional

import requests


BASE_URL = "http://api.clubelo.com"


class ClubEloSource:
    """
    Wrapper per l'API pubblica di ClubElo.

    Metodi principali:
        ratings_on(date)         -> dict[team_name, elo_rating]
        team_history(team_name)  -> list[dict]
        elo_for(team, date)      -> float | None
    """

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "BAgent/1.0"})

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_csv(self, path: str) -> list[dict]:
        url = f"{BASE_URL}/{path}"
        r = self._session.get(url, timeout=15)
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        return list(reader)

    # ------------------------------------------------------------------
    # Ratings
    # ------------------------------------------------------------------

    @lru_cache(maxsize=30)
    def ratings_on(self, match_date: date) -> dict[str, float]:
        """
        Restituisce tutti i rating ELO validi per una data.
        Formato: {nome_squadra: elo_float}
        Cache in-memory per evitare richieste duplicate.
        """
        date_str = match_date.strftime("%Y-%m-%d")
        rows = self._get_csv(date_str)
        return {
            row["Club"]: float(row["Elo"])
            for row in rows
            if row.get("Club") and row.get("Elo")
        }

    def team_history(self, team_name: str) -> list[dict]:
        """Storia completa del rating ELO di una squadra."""
        # ClubElo usa nomi senza spazi (es. ManCity, RealMadrid)
        slug = team_name.replace(" ", "")
        return self._get_csv(slug)

    def elo_for(
        self,
        team: str,
        match_date: date,
    ) -> Optional[float]:
        """
        Rating ELO di una squadra in una data specifica.
        Cerca prima match esatto, poi partial match (case-insensitive).
        """
        ratings = self.ratings_on(match_date)

        # Match esatto
        if team in ratings:
            return ratings[team]

        # Partial match
        team_lower = team.lower()
        for name, elo in ratings.items():
            if team_lower in name.lower() or name.lower() in team_lower:
                return elo

        return None

    def elo_diff(
        self,
        home: str,
        away: str,
        match_date: date,
    ) -> Optional[float]:
        """
        Differenza ELO home - away.
        Positivo = home favorita, negativo = away favorita.
        """
        h = self.elo_for(home, match_date)
        a = self.elo_for(away, match_date)

        if h is None or a is None:
            return None

        return h - a

    def win_probability(
        self,
        home: str,
        away: str,
        match_date: date,
        home_advantage: float = 65.0,
    ) -> Optional[dict[str, float]]:
        """
        Probabilità di vittoria basata su ELO (formula standard).
        home_advantage: punti ELO da aggiungere all'home team (default 65).

        Ritorna: {home_win: float, draw: float, away_win: float}
        o None se ELO non disponibile per una delle due squadre.
        """
        h = self.elo_for(home, match_date)
        a = self.elo_for(away, match_date)

        if h is None or a is None:
            return None

        # Formula ELO standard con home advantage
        diff = (h + home_advantage) - a
        expected_home = 1.0 / (1.0 + 10 ** (-diff / 400.0))

        # Stima draw probability (approssimazione Henriksen)
        draw = 0.30 - 0.20 * abs(expected_home - 0.5)
        home_win = expected_home * (1 - draw)
        away_win = (1 - expected_home) * (1 - draw)

        return {
            "home_win": round(home_win, 4),
            "draw": round(draw, 4),
            "away_win": round(away_win, 4),
            "home_elo": h,
            "away_elo": a,
            "elo_diff": h - a,
        }
