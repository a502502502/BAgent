"""
OddsAPICollector — client per The Odds API (the-odds-api.com).

Fornisce quote reali da bookmaker europei per:
  - 1X2 (h2h)
  - BTTS (btts)
  - Corner Over/Under (alternate_totals_corners)
  - Corner per squadra (alternate_team_totals_corners)
  - Qualificazione (to_qualify) — per partite di coppa
  - Doppia chance, risultato esatto

Piano FREE: 500 richieste/mese.
Chiave API: variabile d'ambiente ODDS_API_KEY

Utilizzo:
    collector = OddsAPICollector()
    event_id = collector.find_event("soccer_uefa_europa_conference_league",
                                    "GKS Katowice", "Hapoel Tel Aviv", "2026-08-12")
    odds = collector.get_all_odds(event_id, "soccer_uefa_europa_conference_league")
    print(odds["market_odds"])
    print(odds["corner_odds"])
"""

from __future__ import annotations

import os
import time
from datetime import date, datetime, timezone
from typing import Any, Optional

import requests


BASE_URL = "https://api.the-odds-api.com/v4"

# Sport keys per le competizioni UEFA
SPORT_KEYS = {
    # UEFA — solo CL qualification coperta da The Odds API
    "champions_league_qual": "soccer_uefa_champs_league_qualification",
    # Campionati nazionali
    "premier_league": "soccer_epl",
    "serie_a":        "soccer_italy_serie_a",
    "serie_b":        "soccer_italy_serie_b",
    "la_liga":        "soccer_spain_la_liga",
    "bundesliga":     "soccer_germany_bundesliga",
    "ligue_1":        "soccer_france_ligue_one",
    "eredivisie":     "soccer_netherlands_eredivisie",
    "ekstraklasa":    "soccer_poland_ekstraklasa",
    "allsvenskan":    "soccer_sweden_allsvenskan",
    "superliga_dk":   "soccer_denmark_superliga",
    # Coppe nazionali
    "dfb_pokal":      "soccer_germany_dfb_pokal",
    "efl_cup":        "soccer_england_efl_cup",
    # Note: Conference League e Europa League NON sono coperte
}

# Regioni da interrogare (EU + UK per copertura bookmaker europei)
DEFAULT_REGIONS = "eu,uk"


class OddsAPICollector:
    """
    Client per The Odds API v4.

    Recupera quote reali da bookmaker europei per qualsiasi partita.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        delay: float = 0.5,
        regions: str = DEFAULT_REGIONS,
    ):
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Chiave API mancante. Imposta ODDS_API_KEY nel file .env"
            )
        self.delay   = delay
        self.regions = regions

    # ------------------------------------------------------------------
    # HTTP base
    # ------------------------------------------------------------------

    def _get(self, endpoint: str, params: dict[str, Any] = {}) -> Any:
        time.sleep(self.delay)
        params = {"apiKey": self.api_key, **params}
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)

        # Log richieste rimanenti
        remaining = r.headers.get("x-requests-remaining")
        if remaining:
            print(f"[OddsAPI] Richieste rimanenti: {remaining}")

        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Sport disponibili
    # ------------------------------------------------------------------

    def list_sports(self) -> list[dict]:
        """Lista tutti gli sport/campionati disponibili."""
        return self._get("sports")

    def find_sport_key(self, name: str) -> Optional[str]:
        """Cerca il sport key per nome (es. 'Conference League')."""
        sports = self.list_sports()
        name_lower = name.lower()
        for s in sports:
            if name_lower in s.get("title", "").lower() or name_lower in s.get("key", "").lower():
                return s["key"]
        return None

    # ------------------------------------------------------------------
    # Ricerca evento
    # ------------------------------------------------------------------

    def list_events(self, sport_key: str, match_date: Optional[str] = None) -> list[dict]:
        """
        Lista eventi disponibili per uno sport.

        match_date: 'YYYY-MM-DD' opzionale per filtrare
        """
        params: dict[str, Any] = {"dateFormat": "iso"}
        if match_date:
            # Filtra per data: commenceTime tra inizio e fine giornata
            params["commenceTimeFrom"] = f"{match_date}T00:00:00Z"
            params["commenceTimeTo"]   = f"{match_date}T23:59:59Z"

        return self._get(f"sports/{sport_key}/events", params)

    def find_event(
        self,
        sport_key: str,
        home: str,
        away: str,
        match_date: Optional[str] = None,
    ) -> Optional[str]:
        """
        Trova l'event_id per nome squadre.

        Ritorna event_id (str) o None se non trovato.
        """
        events = self.list_events(sport_key, match_date)

        home_lower = home.lower()
        away_lower = away.lower()

        for ev in events:
            h = ev.get("home_team", "").lower()
            a = ev.get("away_team", "").lower()

            # Match esatto
            if h == home_lower and a == away_lower:
                return ev["id"]

            # Match parziale (nomi abbreviati)
            if home_lower[:5] in h and away_lower[:5] in a:
                return ev["id"]

        return None

    # ------------------------------------------------------------------
    # Quote principali (/odds endpoint)
    # ------------------------------------------------------------------

    def get_odds(
        self,
        sport_key: str,
        markets: str = "h2h,btts,double_chance",
        event_ids: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Recupera quote per i mercati principali.

        markets: stringa comma-separated (h2h, btts, double_chance, etc.)
        event_ids: lista di event_id da filtrare (opzionale)
        """
        params: dict[str, Any] = {
            "regions":   self.regions,
            "markets":   markets,
            "oddsFormat": "decimal",
        }
        if event_ids:
            params["eventIds"] = ",".join(event_ids)

        return self._get(f"sports/{sport_key}/odds", params)

    # ------------------------------------------------------------------
    # Quote per evento singolo (corner, to_qualify, ecc.)
    # ------------------------------------------------------------------

    def get_event_odds(
        self,
        sport_key: str,
        event_id: str,
        markets: str = "alternate_totals_corners,alternate_team_totals_corners,to_qualify,correct_score",
    ) -> dict:
        """
        Recupera quote per mercati speciali di un singolo evento.

        Questo endpoint supporta corner, qualificazione, risultato esatto.
        Costo: 1 richiesta per mercato × regioni.
        """
        params = {
            "regions":    self.regions,
            "markets":    markets,
            "oddsFormat": "decimal",
        }
        return self._get(f"sports/{sport_key}/events/{event_id}/odds", params)

    # ------------------------------------------------------------------
    # Raccolta completa per una partita
    # ------------------------------------------------------------------

    def collect(
        self,
        sport_key: str,
        home: str,
        away: str,
        match_date: Optional[str] = None,
        include_corners: bool = True,
        include_qualify: bool = True,
    ) -> dict:
        """
        Raccoglie tutte le quote disponibili per una partita.

        Ritorna dict con:
          event_id, market_odds (1X2, BTTS, ecc.),
          corner_odds (over/under), qualify_odds
        """
        # Trova evento
        event_id = self.find_event(sport_key, home, away, match_date)
        if not event_id:
            return {
                "status": "EVENT_NOT_FOUND",
                "home": home, "away": away,
                "market_odds": {}, "corner_odds": {}, "qualify_odds": {},
            }

        result: dict[str, Any] = {
            "status":       "OK",
            "event_id":     event_id,
            "sport_key":    sport_key,
            "home":         home,
            "away":         away,
            "match_date":   match_date,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "market_odds":  {},
            "corner_odds":  {},
            "qualify_odds": {},
        }

        # Quote principali (h2h + btts)
        try:
            raw_main = self.get_odds(
                sport_key,
                markets="h2h,btts",
                event_ids=[event_id],
            )
            if raw_main:
                result["market_odds"] = self._parse_main_odds(raw_main[0])
        except Exception as e:
            print(f"[OddsAPI] Errore quote principali: {e}")

        # Quote corner e qualificazione
        extra_markets = []
        if include_corners:
            extra_markets += ["alternate_totals_corners", "alternate_team_totals_corners"]
        if include_qualify:
            extra_markets.append("to_qualify")

        if extra_markets:
            try:
                raw_event = self.get_event_odds(
                    sport_key, event_id,
                    markets=",".join(extra_markets),
                )
                if include_corners:
                    result["corner_odds"] = self._parse_corner_odds(raw_event)
                if include_qualify:
                    result["qualify_odds"] = self._parse_qualify_odds(raw_event, home, away)
            except Exception as e:
                print(f"[OddsAPI] Errore quote speciali: {e}")

        return result

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _best_odd(self, bookmakers: list[dict], market_key: str, outcome: str) -> Optional[float]:
        """Trova la quota migliore tra i bookmaker per un outcome specifico."""
        best = None
        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") != market_key:
                    continue
                for o in market.get("outcomes", []):
                    if o.get("name", "").lower() == outcome.lower():
                        price = float(o.get("price", 0))
                        if best is None or price > best:
                            best = price
        return best

    def _parse_main_odds(self, event_data: dict) -> dict:
        """Estrae quote 1X2 e BTTS dal primo bookmaker disponibile."""
        bookmakers = event_data.get("bookmakers", [])
        if not bookmakers:
            return {}

        result = {}

        # Prova prima Pinnacle, poi bet365, poi il primo disponibile
        preferred = ["pinnacle", "bet365", "unibet"]
        bm_list = sorted(
            bookmakers,
            key=lambda b: preferred.index(b["key"]) if b["key"] in preferred else 99
        )

        for bm in bm_list:
            for market in bm.get("markets", []):
                key = market.get("key")
                outcomes = {o["name"].lower(): float(o["price"]) for o in market.get("outcomes", [])}

                if key == "h2h" and "home_win" not in result:
                    home = event_data.get("home_team", "")
                    away = event_data.get("away_team", "")
                    result["home_win"] = outcomes.get(home.lower())
                    result["draw"]     = outcomes.get("draw")
                    result["away_win"] = outcomes.get(away.lower())

                elif key == "btts" and "btts_yes" not in result:
                    result["btts_yes"] = outcomes.get("yes")
                    result["btts_no"]  = outcomes.get("no")

        return {k: v for k, v in result.items() if v is not None}

    def _parse_corner_odds(self, event_data: dict) -> dict:
        """
        Estrae quote corner over/under dalla risposta dell'event odds endpoint.

        Cerca i threshold più comuni: 8.5, 9.5, 10.5, 11.5
        """
        bookmakers = event_data.get("bookmakers", [])
        result = {}

        thresholds = {8.5, 9.5, 10.5, 11.5}
        team_thresholds = {4.5, 5.5, 6.5}

        for bm in bookmakers:
            for market in bm.get("markets", []):
                key = market.get("key", "")

                if key == "alternate_totals_corners":
                    for o in market.get("outcomes", []):
                        name  = o.get("name", "").lower()   # "over" o "under"
                        point = o.get("point")              # es. 9.5
                        price = float(o.get("price", 0))

                        if point in thresholds:
                            mkt_key = f"{'over' if 'over' in name else 'under'}_{str(point).replace('.', '_')}"
                            if mkt_key not in result or price > result[mkt_key]:
                                result[mkt_key] = price

                elif key == "alternate_team_totals_corners":
                    home_team = event_data.get("home_team", "")
                    for o in market.get("outcomes", []):
                        name        = o.get("name", "").lower()
                        description = o.get("description", "").lower()
                        point       = o.get("point")
                        price       = float(o.get("price", 0))

                        if home_team.lower() in description and point in team_thresholds:
                            mkt_key = f"home_{'over' if 'over' in name else 'under'}_{str(point).replace('.', '_')}"
                            if mkt_key not in result or price > result[mkt_key]:
                                result[mkt_key] = price

        return result

    def _parse_qualify_odds(self, event_data: dict, home: str, away: str) -> dict:
        """
        Estrae quote di qualificazione dal mercato to_qualify.

        Ritorna {home_qualify, away_qualify}
        """
        bookmakers = event_data.get("bookmakers", [])
        result = {}

        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") != "to_qualify":
                    continue

                for o in market.get("outcomes", []):
                    name  = o.get("name", "").lower()
                    price = float(o.get("price", 0))

                    if home.lower()[:5] in name and "home_qualify" not in result:
                        result["home_qualify"] = price
                    elif away.lower()[:5] in name and "away_qualify" not in result:
                        result["away_qualify"] = price

        return result
