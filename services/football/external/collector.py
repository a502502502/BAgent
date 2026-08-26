"""
FootballExternalCollector — client API-Football v3.

Raccoglie per qualsiasi partita/campionato:
  - Fixture (dati partita, stato, venue)
  - Infortuni giocatori
  - Formazioni ufficiali
  - Quote pre-partita
  - Statistiche squadra (forma, gol, possesso...)
  - Statistiche giocatori (minuti, gol, assist, rating)
  - Head-to-head storico

Piano FREE (100 req/giorno):
  - Tutti gli endpoint sono inclusi
  - Stagioni correnti disponibili

Utilizzo:
    collector = FootballExternalCollector()

    # Cerca la partita per nome squadre + data
    fixture_id = collector.find_fixture("Juventus", "Inter", "2025-09-20")

    # Raccoglie tutto
    data = collector.collect_sixth_sense(fixture_id)
    print(data["injuries_summary"])
    print(data["lineups_summary"])

Variabile d'ambiente: API_FOOTBALL_KEY
"""

from __future__ import annotations

import os
import time
from datetime import date, datetime, timezone
from typing import Any, Optional

import requests


BASE_URL = "https://v3.football.api-sports.io"


class FootballExternalCollector:
    """
    Client completo per API-Football v3.

    Supporta qualsiasi campionato tramite league_id.
    Vedi la lista completa su: https://www.api-football.com/coverage
    """

    def __init__(self, api_key: Optional[str] = None, delay: float = 0.5):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Chiave API mancante. Imposta API_FOOTBALL_KEY nel file .env "
                "o come variabile d'ambiente."
            )
        self.delay = delay  # secondi tra richieste
        self._session = requests.Session()
        self._session.headers.update({
            "x-apisports-key": self.api_key,
        })

    # ------------------------------------------------------------------
    # HTTP base
    # ------------------------------------------------------------------

    def _get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        time.sleep(self.delay)
        r = self._session.get(
            f"{BASE_URL}/{endpoint}",
            params=params,
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("errors") and data["errors"] != []:
            raise RuntimeError(f"API-Football error: {data['errors']}")
        return data

    def quota_status(self) -> dict:
        """Mostra richieste rimanenti del piano."""
        r = self._session.get(f"{BASE_URL}/status", timeout=10)
        r.raise_for_status()
        return r.json().get("response", {})

    # ------------------------------------------------------------------
    # Ricerca fixture
    # ------------------------------------------------------------------

    def find_fixture(
        self,
        home: str,
        away: str,
        match_date: str | date,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
    ) -> Optional[int]:
        """
        Cerca l'ID fixture per nome squadre e data.

        match_date: stringa 'YYYY-MM-DD' o oggetto date
        league_id:  opzionale, velocizza la ricerca
        season:     anno stagione (es. 2024), opzionale

        Ritorna fixture_id (int) o None se non trovata.
        """
        if isinstance(match_date, date):
            match_date = match_date.isoformat()

        params: dict[str, Any] = {"date": match_date}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season

        data = self._get("fixtures", params)
        results = data.get("response", [])

        for item in results:
            teams = item.get("teams", {})
            h = teams.get("home", {}).get("name", "").lower()
            a = teams.get("away", {}).get("name", "").lower()
            if h == home.lower() and a == away.lower():
                return item["fixture"]["id"]

        # Secondo tentativo: ricerca parziale (utile per nomi abbreviati)
        for item in results:
            teams = item.get("teams", {})
            h = teams.get("home", {}).get("name", "").lower()
            a = teams.get("away", {}).get("name", "").lower()
            if home.lower() in h and away.lower() in a:
                return item["fixture"]["id"]

        return None

    def search_league(self, name: str, country: Optional[str] = None) -> list[dict]:
        """
        Cerca un campionato per nome. Utile per trovare il league_id.

        Esempio: collector.search_league("Serie A")
        Nota: l'API non supporta country + search insieme, filtra lato client.
        """
        params: dict[str, Any] = {"search": name}
        data = self._get("leagues", params)
        results = [
            {
                "id":      l["league"]["id"],
                "name":    l["league"]["name"],
                "country": l["country"]["name"],
                "season":  l["seasons"][-1]["year"] if l.get("seasons") else None,
            }
            for l in data.get("response", [])
        ]
        # Filtra per paese lato client se richiesto
        if country:
            results = [r for r in results if country.lower() in r["country"].lower()]
        return results

    # ------------------------------------------------------------------
    # Endpoint singoli
    # ------------------------------------------------------------------

    def fixture(self, fixture_id: int) -> dict:
        return self._get("fixtures", {"id": fixture_id})

    def injuries(self, fixture_id: int) -> dict:
        return self._get("injuries", {"fixture": fixture_id})

    def lineups(self, fixture_id: int) -> dict:
        return self._get("fixtures/lineups", {"fixture": fixture_id})

    def events_raw(self, fixture_id: int) -> dict:
        """Eventi grezzi della partita (gol, cartellini, sostituzioni)."""
        return self._get("fixtures/events", {"fixture": fixture_id})

    def events(self, fixture_id: int) -> list[dict]:
        """
        Eventi della partita in formato pulito, ordinati per minuto.
        Ogni evento: {minute, type, detail, team, player, assist}.
        type: 'Goal' | 'Card' | 'subst' | 'Var'
        Fonte affidabile per notifiche live (gol/cartellini/sostituzioni con
        minuto preciso) — preferire questa a Flashscore incidents_raw(), che
        non e' documentata e richiede parsing di un formato proprietario.
        """
        raw = self.events_raw(fixture_id)
        out = []
        for ev in raw.get("response", []):
            out.append({
                "minute": ev["time"]["elapsed"],
                "extra": ev["time"].get("extra"),
                "type": ev["type"],
                "detail": ev.get("detail"),
                "team": ev["team"]["name"],
                "player": (ev.get("player") or {}).get("name"),
                "assist": (ev.get("assist") or {}).get("name"),
            })
        return out

    def odds(self, fixture_id: int) -> dict:
        """Quote PRE-partita (fisse al momento del kickoff, non si aggiornano a match in corso)."""
        return self._get("odds", {"fixture": fixture_id})

    def live_odds(self, fixture_id: Optional[int] = None) -> dict:
        """
        Quote LIVE (in-play), aggiornate in tempo reale per le partite in
        corso. Utile per proporre una giocata riparatoria mentre un ticket
        sta andando male: include mercati come 'To Win 2nd Half', 'Double
        Chance', '3-Way Handicap', 'Over/Under Line' (soglia adattata al
        punteggio attuale), 'Final Score' (con i risultati ormai impossibili
        segnati 'suspended': True).
        Senza fixture_id, restituisce TUTTE le partite live con quote
        disponibili in quel momento (utile per scovare opportunita').
        """
        params = {"fixture": fixture_id} if fixture_id else {}
        return self._get("odds/live", params)

    def list_available_markets(self, fixture_id: int) -> list[str]:
        """
        Elenca tutti i nomi di mercato disponibili per una fixture, su tutti
        i bookmaker restituiti da API-Football (es. Bet365, 10Bet...).

        Utile per scoprire in anticipo se un mercato "di nicchia" (falli
        giocatore, cartellini giocatore, corner squadra...) esiste prima di
        andare a cercarlo a mano su Netwin/Domusbet.
        """
        raw = self.odds(fixture_id)
        resp = raw.get("response", [])
        if not resp:
            return []
        markets: set[str] = set()
        for bm in resp[0].get("bookmakers", []):
            for bet in bm.get("bets", []):
                markets.add(bet["name"])
        return sorted(markets)

    def player_prop_odds(
        self,
        fixture_id: int,
        market: str,
        bookmaker: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Estrae le quote per un mercato "per giocatore" (es. 'Player Fouls
        Committed', 'Player to be booked', 'Player Shots On Target').

        `market` fa match parziale case-insensitive sul nome del mercato
        (es. "fouls committed" trova "Player Fouls Committed").
        `bookmaker` opzionale filtra su un singolo bookmaker (es. "Bet365");
        se omesso, restituisce i risultati di TUTTI i bookmaker disponibili.

        Ritorna una lista di dict: {bookmaker, market, player, line, odd}.
        Nota: sono le quote del bookmaker restituito da API-Football (di
        solito Bet365/10Bet), NON quelle di Netwin/Domusbet — usare questo
        metodo per decidere a colpo d'occhio quali giocatori/soglie valgono
        la pena, poi confermare il numero esatto su Netwin prima di giocare.
        """
        raw = self.odds(fixture_id)
        resp = raw.get("response", [])
        if not resp:
            return []

        market_lower = market.lower()
        out: list[dict[str, Any]] = []
        for bm in resp[0].get("bookmakers", []):
            bm_name = bm.get("name", "")
            if bookmaker and bookmaker.lower() != bm_name.lower():
                continue
            for bet in bm.get("bets", []):
                if market_lower not in bet["name"].lower():
                    continue
                for v in bet.get("values", []):
                    value = v.get("value", "")
                    player, _, line = value.partition(" - ")
                    out.append({
                        "bookmaker": bm_name,
                        "market": bet["name"],
                        "player": player.strip() or value,
                        "line": line.strip(),
                        "odd": v.get("odd"),
                    })
        return out

    def fixture_stats(self, fixture_id: int) -> dict:
        """Statistiche della partita: possesso, tiri, corner, ecc."""
        return self._get("fixtures/statistics", {"fixture": fixture_id})

    def player_stats(self, fixture_id: int) -> dict:
        """Statistiche giocatori: minuti, gol, assist, rating, dribbling."""
        return self._get("fixtures/players", {"fixture": fixture_id})

    def head_to_head(
        self,
        home_team_id: int,
        away_team_id: int,
        last: int = 10,
    ) -> dict:
        """Ultimi N scontri diretti tra le due squadre."""
        return self._get(
            "fixtures/headtohead",
            {"h2h": f"{home_team_id}-{away_team_id}", "last": last},
        )

    def team_stats(
        self,
        team_id: int,
        league_id: int,
        season: int,
    ) -> dict:
        """Statistiche stagionali squadra: forma, gol, clean sheets."""
        return self._get(
            "teams/statistics",
            {"team": team_id, "league": league_id, "season": season},
        )

    def sidelined(self, player_id: int) -> dict:
        """Storico infortuni/squalifiche di un giocatore."""
        return self._get("sidelined", {"player": player_id})

    def parse_corner_stats(self, raw_team_stats: dict) -> dict:
        """
        Estrae statistiche corner dalle statistiche stagionali squadra.

        Input: risposta grezza di /teams/statistics
        Output: {
            corners_for_home, corners_for_away, corners_for_total,
            corners_against_home, corners_against_away, corners_against_total,
            matches_home, matches_away, matches_total,
            avg_corners_for, avg_corners_against
        }
        """
        resp = raw_team_stats.get("response", {})
        if not resp:
            return {}

        corners = resp.get("corners", {})
        fixtures = resp.get("fixtures", {})

        # Gol corner fatti
        cf = corners.get("total", {}) or {}
        corners_for_home  = cf.get("home")  or 0
        corners_for_away  = cf.get("away")  or 0
        corners_for_total = cf.get("total") or 0

        # Partite giocate
        played = fixtures.get("played", {}) or {}
        matches_home  = played.get("home")  or 0
        matches_away  = played.get("away")  or 0
        matches_total = played.get("total") or 0

        avg_for = corners_for_total / matches_total if matches_total else 0

        return {
            "corners_for_home":     corners_for_home,
            "corners_for_away":     corners_for_away,
            "corners_for_total":    corners_for_total,
            "matches_home":         matches_home,
            "matches_away":         matches_away,
            "matches_total":        matches_total,
            "avg_corners_for":      round(avg_for, 2),
        }

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def parse_injuries(self, raw: dict) -> list[dict]:
        """
        Estrae lista infortuni leggibile.

        Ritorna lista di {player, team, type, reason}
        """
        out = []
        for item in raw.get("response", []):
            p = item.get("player", {})
            t = item.get("team", {})
            out.append({
                "player": p.get("name", ""),
                "team":   t.get("name", ""),
                "type":   p.get("type", ""),
                "reason": p.get("reason", ""),
            })
        return out

    def parse_lineups(self, raw: dict) -> dict:
        """
        Estrae formazioni leggibili.

        Ritorna {home: {formation, coach, startXI, substitutes},
                 away: {formation, coach, startXI, substitutes}}
        """
        out = {}
        for team_data in raw.get("response", []):
            t = team_data.get("team", {})
            name = t.get("name", "unknown")
            out[name] = {
                "formation":   team_data.get("formation", ""),
                "coach":       team_data.get("coach", {}).get("name", ""),
                "startXI":     [
                    {
                        "name":   p["player"]["name"],
                        "number": p["player"]["number"],
                        "pos":    p["player"]["pos"],
                    }
                    for p in team_data.get("startXI", [])
                ],
                "substitutes": [
                    p["player"]["name"]
                    for p in team_data.get("substitutes", [])
                ],
            }
        return out

    def parse_odds(self, raw: dict) -> dict:
        """
        Estrae quote principali dal primo bookmaker disponibile.

        Ritorna {home_win, draw, away_win, over_2_5, under_2_5, btts_yes, btts_no}
        """
        result = {}
        bookmakers = raw.get("response", [])
        if not bookmakers:
            return result

        bets = bookmakers[0].get("bookmakers", [])
        if not bets:
            return result

        for bet_group in bets[0].get("bets", []):
            name = bet_group.get("name", "")
            values = {v["value"]: float(v["odd"]) for v in bet_group.get("values", [])}

            if name == "Match Winner":
                result["home_win"]  = values.get("Home")
                result["draw"]      = values.get("Draw")
                result["away_win"]  = values.get("Away")

            elif "Goals Over/Under" in name and "2.5" in name:
                result["over_2_5"]  = values.get("Over 2.5")
                result["under_2_5"] = values.get("Under 2.5")

            elif "Goals Over/Under" in name and "1.5" in name:
                result["over_1_5"]  = values.get("Over 1.5")
                result["under_1_5"] = values.get("Under 1.5")

            elif "Goals Over/Under" in name and "3.5" in name:
                result["over_3_5"]  = values.get("Over 3.5")
                result["under_3_5"] = values.get("Under 3.5")

            elif name == "Both Teams Score":
                result["btts_yes"] = values.get("Yes")
                result["btts_no"]  = values.get("No")

        return {k: v for k, v in result.items() if v is not None}

    def format_injuries_for_llm(self, injuries: list[dict], home: str, away: str) -> str:
        """Formatta gli infortuni come testo per il prompt del Sesto Senso."""
        if not injuries:
            return "Nessun infortunio registrato."

        home_inj = [i for i in injuries if home.lower() in i["team"].lower()]
        away_inj = [i for i in injuries if away.lower() in i["team"].lower()]

        lines = []
        if home_inj:
            lines.append(f"INFORTUNI {home.upper()}:")
            for i in home_inj:
                lines.append(f"  - {i['player']}: {i['type']} ({i['reason']})")
        if away_inj:
            lines.append(f"INFORTUNI {away.upper()}:")
            for i in away_inj:
                lines.append(f"  - {i['player']}: {i['type']} ({i['reason']})")

        return "\n".join(lines)

    def format_lineups_for_llm(self, lineups: dict) -> str:
        """Formatta le formazioni come testo per il prompt del Sesto Senso."""
        if not lineups:
            return "Formazioni non ancora disponibili."

        lines = []
        for team_name, data in lineups.items():
            lines.append(f"{team_name.upper()} ({data['formation']}) — Coach: {data['coach']}")
            starters = ", ".join(p["name"] for p in data["startXI"])
            lines.append(f"  Titolari: {starters}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Raccolta completa
    # ------------------------------------------------------------------

    def collect(self, fixture_id: int) -> dict:
        """Raccoglie dati base per una partita."""
        collected_at = datetime.now(timezone.utc).isoformat()
        return {
            "fixture_id":   fixture_id,
            "collected_at": collected_at,
            "fixture":      self.fixture(fixture_id),
            "injuries":     self.injuries(fixture_id),
            "lineups":      self.lineups(fixture_id),
            "odds":         self.odds(fixture_id),
        }

    def collect_sixth_sense(
        self,
        home: str,
        away: str,
        match_date: str | date,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
    ) -> dict:
        """
        Raccoglie tutti i dati rilevanti per il Sesto Senso.

        Ricerca automaticamente il fixture_id dai nomi squadre e data.
        Ritorna dati già parsati + testo formattato per il prompt LLM.

        Esempio:
            data = collector.collect_sixth_sense("Juventus", "Inter", "2025-09-20")
            print(data["injuries_text"])    # pronto per il Sesto Senso
            print(data["lineups_text"])
            print(data["market_odds"])      # quote reali dal bookmaker
        """
        collected_at = datetime.now(timezone.utc).isoformat()

        # Cerca fixture
        fixture_id = self.find_fixture(home, away, match_date, league_id, season)
        if not fixture_id:
            return {
                "status": "FIXTURE_NOT_FOUND",
                "home": home,
                "away": away,
                "match_date": str(match_date),
                "collected_at": collected_at,
                "injuries_text": "",
                "lineups_text": "",
                "market_odds": {},
            }

        # Raccoglie dati
        raw_injuries = self.injuries(fixture_id)
        raw_lineups  = self.lineups(fixture_id)
        raw_odds     = self.odds(fixture_id)

        # Parsing
        injuries_list = self.parse_injuries(raw_injuries)
        lineups_dict  = self.parse_lineups(raw_lineups)
        market_odds   = self.parse_odds(raw_odds)

        # Testo per LLM
        injuries_text = self.format_injuries_for_llm(injuries_list, home, away)
        lineups_text  = self.format_lineups_for_llm(lineups_dict)

        # Statistiche corner da /fixtures/statistics (se partita già giocata)
        # e da /teams/statistics (medie stagionali, per partite future)
        home_corner_stats = {}
        away_corner_stats = {}
        try:
            raw_fixture_stats = self.fixture_stats(fixture_id)
            home_corner_stats, away_corner_stats = self._parse_fixture_corner_stats(
                raw_fixture_stats
            )
        except Exception:
            pass

        return {
            "status":            "OK",
            "fixture_id":        fixture_id,
            "home":              home,
            "away":              away,
            "match_date":        str(match_date),
            "collected_at":      collected_at,
            "injuries":          injuries_list,
            "injuries_text":     injuries_text,
            "lineups":           lineups_dict,
            "lineups_text":      lineups_text,
            "market_odds":       market_odds,
            "home_corner_stats": home_corner_stats,
            "away_corner_stats": away_corner_stats,
            "raw": {
                "injuries": raw_injuries,
                "lineups":  raw_lineups,
                "odds":     raw_odds,
            },
        }

    def _parse_fixture_corner_stats(self, raw: dict) -> tuple[dict, dict]:
        """
        Estrae statistiche corner da /fixtures/statistics.

        Ritorna (home_stats, away_stats) con avg_corners_for calcolato
        dalla partita singola (usato come stima puntuale).
        """
        teams = raw.get("response", [])
        home_stats = {}
        away_stats = {}

        for team_data in teams:
            stats = {s["type"]: s["value"] for s in team_data.get("statistics", [])}
            corners = stats.get("Corner Kicks", 0) or 0
            is_home = team_data.get("team", {}).get("id") == team_data.get("home_team_id")

            entry = {
                "avg_corners_for": float(corners),
                "matches_home":    1,
                "matches_away":    1,
                "matches_total":   1,
            }

            if not home_stats:
                home_stats = entry
            else:
                away_stats = entry

        return home_stats, away_stats
