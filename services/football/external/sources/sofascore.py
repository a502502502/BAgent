"""
SofaScore unofficial API — fonte primaria per fixture live, lineups, odds.
Copre oltre 500 campionati senza autenticazione.
"""

from __future__ import annotations

import time
from datetime import date
from typing import Any

import requests


BASE_URL = "https://api.sofascore.com/api/v1"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Connection": "keep-alive",
}


class SofaScoreSource:
    """
    Wrapper per l'API non ufficiale di SofaScore.

    Metodi principali:
        search_event(home, away, match_date) -> dict | None
        event(event_id)                      -> dict
        lineups(event_id)                    -> dict
        odds(event_id)                       -> dict
        injuries(event_id)                   -> dict
        team_form(team_id, n)               -> list[dict]
    """

    def __init__(self, delay: float = 0.5):
        self._delay = delay  # secondi tra richieste per evitare ban
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> Any:
        time.sleep(self._delay)
        url = f"{BASE_URL}/{path}"
        r = self._session.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Fixture search
    # ------------------------------------------------------------------

    def fixtures_by_date(self, match_date: date) -> list[dict]:
        """Restituisce tutte le partite di calcio per una data."""
        date_str = match_date.strftime("%Y-%m-%d")
        data = self._get(
            f"sport/football/scheduled-events/{date_str}"
        )
        return data.get("events", [])

    def search_event(
        self,
        home: str,
        away: str,
        match_date: date,
    ) -> dict | None:
        """
        Cerca una partita per nomi squadra e data.
        Ritorna il primo match che soddisfa la ricerca (case-insensitive,
        partial match), None se non trovato.
        """
        events = self.fixtures_by_date(match_date)

        home_q = home.lower()
        away_q = away.lower()

        for ev in events:
            h = ev.get("homeTeam", {}).get("name", "").lower()
            a = ev.get("awayTeam", {}).get("name", "").lower()

            if home_q in h and away_q in a:
                return ev

        return None

    # ------------------------------------------------------------------
    # Event details
    # ------------------------------------------------------------------

    def event(self, event_id: int) -> dict:
        return self._get(f"event/{event_id}")

    def lineups(self, event_id: int) -> dict:
        try:
            return self._get(f"event/{event_id}/lineups")
        except requests.HTTPError:
            return {}  # non sempre disponibile prima della partita

    def odds(self, event_id: int) -> dict:
        try:
            return self._get(f"event/{event_id}/odds/1/featured")
        except requests.HTTPError:
            return {}

    def parse_odds(self, raw: dict) -> dict:
        """
        Estrae quote 1X2 e Over/Under dalla risposta SofaScore.
        Ritorna dict compatibile con il formato BAgent.
        """
        result = {}
        if not raw:
            return result

        # SofaScore può restituire "featured" o lista di markets
        featured = raw.get("featured", raw)
        choices = featured.get("choices", [])

        for c in choices:
            name = str(c.get("name", "")).strip()
            try:
                odd = float(c.get("odds", 0) or c.get("fractionalValue", 0))
            except (TypeError, ValueError):
                continue
            if odd <= 1.0:
                continue

            if name == "1":
                result["home_win"] = odd
            elif name == "X":
                result["draw"] = odd
            elif name == "2":
                result["away_win"] = odd
            elif name in ("Over 2.5", "Over2.5"):
                result["over_2_5"] = odd
            elif name in ("Under 2.5", "Under2.5"):
                result["under_2_5"] = odd
            elif name in ("Over 1.5", "Over1.5"):
                result["over_1_5"] = odd
            elif name in ("Under 1.5", "Under1.5"):
                result["under_1_5"] = odd
            elif name in ("Over 3.5", "Over3.5"):
                result["over_3_5"] = odd
            elif name in ("Under 3.5", "Under3.5"):
                result["under_3_5"] = odd
            elif name in ("Yes", "GG"):
                result["btts_yes"] = odd
            elif name in ("No", "NG"):
                result["btts_no"] = odd

        return result

    def injuries(self, event_id: int) -> dict:
        """
        SofaScore non ha un endpoint injuries per singolo evento.
        Restituiamo le info dal team se disponibili via team_players.
        """
        return {}

    # ------------------------------------------------------------------
    # Team stats
    # ------------------------------------------------------------------

    def team_form(self, team_id: int, n: int = 10) -> list[dict]:
        """Ultimi N eventi di una squadra."""
        try:
            data = self._get(
                f"team/{team_id}/events/last/0"
            )
            return data.get("events", [])[-n:]
        except requests.HTTPError:
            return []

    def team_players(self, team_id: int) -> list[dict]:
        """Rosa e status infortuni della squadra."""
        try:
            data = self._get(f"team/{team_id}/players")
            return data.get("players", [])
        except requests.HTTPError:
            return []

    # ------------------------------------------------------------------
    # Collect all for a match
    # ------------------------------------------------------------------

    def collect(
        self,
        home: str,
        away: str,
        match_date: date,
    ) -> dict:
        """
        Raccoglie tutti i dati disponibili per una partita.
        Ritorna un dict con: event, lineups, odds, home_form, away_form.
        """
        ev = self.search_event(home, away, match_date)

        if ev is None:
            return {
                "found": False,
                "home": home,
                "away": away,
                "date": match_date.isoformat(),
            }

        event_id = ev["id"]
        home_id = ev.get("homeTeam", {}).get("id")
        away_id = ev.get("awayTeam", {}).get("id")

        result: dict[str, Any] = {
            "found": True,
            "source": "sofascore",
            "event_id": event_id,
            "event": ev,
            "lineups": self.lineups(event_id),
            "odds": self.odds(event_id),
        }

        if home_id:
            result["home_form"] = self.team_form(home_id)
            result["home_players"] = self.team_players(home_id)

        if away_id:
            result["away_form"] = self.team_form(away_id)
            result["away_players"] = self.team_players(away_id)

        return result
