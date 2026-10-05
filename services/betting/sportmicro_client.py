"""Client per Sportmicro API (https://football.sportmicro.com).

Interroga il feed ufficiale Sportmicro per i mercati speciali e combinati
(incluso 'To Score In Both Halves', 'To Win Both Halves', 'Both Teams To Score').
Integra le quote nel formato standard BAgent per il calcolo dell'Edge.
"""

from __future__ import annotations

import json
import logging
import os
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

logger = logging.getLogger("SportmicroClient")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

DEFAULT_CACHE_DIR = ROOT_DIR / "data" / "cache" / "sportmicro"


TEAM_TRANSLATIONS = {
    "francia": "france",
    "belgio": "belgium",
    "germania": "germany",
    "spagna": "spain",
    "italia": "italy",
    "turchia": "turkiye",
    "turkey": "turkiye",
    "cipro": "cyprus",
    "lettonia": "latvia",
    "ucraina": "ukraine",
    "ungheria": "hungary",
    "armenia": "armenia",
    "montenegro": "montenegro",
    "bosnia": "bosnia",
    "bosnia erzegovina": "bosnia & herzegovina",
    "polonia": "poland",
    "irlanda del nord": "northern ireland",
    "georgia": "georgia",
    "olanda": "netherlands",
    "paesi bassi": "netherlands",
    "scozia": "scotland",
    "galles": "wales",
    "danimarca": "denmark",
    "portogallo": "portugal",
    "norvegia": "norway",
    "repubblica ceca": "czech republic",
    "slovacchia": "slovakia",
    "romania": "romania",
    "svezia": "sweden",
    "grecia": "greece",
    "austria": "austria",
    "kosovo": "kosovo",
    "israele": "israel",
    "svizzera": "switzerland",
    "croazia": "croatia",
    "serbia": "serbia",
}


def _normalize_name(name: str) -> str:
    """Normalizza i nomi squadra per il matching fuzzy."""
    n = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    n = n.lower().replace("-", " ").replace(".", " ").replace("'", "").replace("&", "e")
    n = " ".join(n.split())
    # Rimuove prefissi o suffissi comuni
    for word in ("fc", "cf", "ac", "as", "sc", "afc", "u21", "national", "team"):
        n = " ".join(part for part in n.split() if part != word)
    n = n.strip()
    return TEAM_TRANSLATIONS.get(n, n)


class SportmicroClient:
    """Client REST per Sportmicro Football API."""

    BASE_URL = "https://football.sportmicro.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        timeout: int = 10,
        max_retries: int = 2,
    ):
        self.api_key = api_key or os.getenv("SPORTMICRO_API_KEY", "").strip()
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "BAgent/2.0 SportmicroClient",
        }

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.is_configured:
            logger.warning("SPORTMICRO_API_KEY non configurata.")
            return None

        url = f"{self.BASE_URL}{endpoint}"
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.get(
                    url,
                    headers=self._headers(),
                    params=params,
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    return None
                elif resp.status_code == 429:
                    logger.warning(f"Sportmicro 429 Rate Limit su {endpoint}. Attesa di 5s prima del riprova...")
                    time.sleep(5.0)
                    continue
                elif resp.status_code in (500, 502, 503, 504):
                    logger.warning(
                        f"Sportmicro HTTP {resp.status_code} su {endpoint} (tentativo {attempt+1}/{self.max_retries+1}): {resp.text[:150]}"
                    )
                    if attempt < self.max_retries:
                        time.sleep(1.0 * (attempt + 1))
                        continue
                    return None
                else:
                    logger.warning(f"Sportmicro errore {resp.status_code} su {endpoint}: {resp.text[:150]}")
                    return None
            except requests.RequestException as e:
                logger.warning(f"Eccezione connessione Sportmicro su {endpoint}: {e}")
                if attempt < self.max_retries:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                return None
        return None

    def is_healthy(self) -> bool:
        """Verifica se l'API risponde correttamente."""
        res = self._get("/odds/bookmakers", params={"limit": 1})
        return res is not None

    def get_matches_for_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Recupera le partite per una data specifica (YYYY-MM-DD)."""
        cache_file = self.cache_dir / f"matches_{date_str}.json"
        params = [
            ("start_time", f"gte.{date_str}T00:00:00"),
            ("start_time", f"lte.{date_str}T23:59:59"),
            ("limit", "100"),
        ]
        data = self._get("/matches", params=params)
        if data and isinstance(data, list):
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.debug(f"Errore scrittura cache matches: {e}")
            return data

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def find_match_id(self, home_team: str, away_team: str, matches: Optional[List[Dict[str, Any]]] = None) -> Optional[int]:
        """Trova l'ID partita Sportmicro confrontando i nomi squadra."""
        if not matches:
            return None
        norm_home = _normalize_name(home_team)
        norm_away = _normalize_name(away_team)

        for m in matches:
            m_home = _normalize_name(m.get("home_team_name", ""))
            m_away = _normalize_name(m.get("away_team_name", ""))
            # Match esatto o contenimento
            if (norm_home in m_home or m_home in norm_home) and (norm_away in m_away or m_away in norm_away):
                return m.get("id")
        return None

    def get_score_in_both_halves_odds(
        self,
        match_id: int,
        preferred_bookmakers: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Recupera le quote 'Segna in entrambi i tempi' per Casa e Ospite.
        Ritorna un dizionario con i mercati formattati per BAgent:
        {
            "Casa Segna in Entrambi i Tempi: SI": odd,
            "Ospite Segna in Entrambi i Tempi: SI": odd,
        }
        """
        data = self._get("/odds/to-score-in-both-halves", params={"match_id": f"eq.{match_id}"})
        if not data or not isinstance(data, list):
            return {}

        match_odds_list = data[0].get("periods", [])
        if not match_odds_list:
            return {}

        odds_entries = match_odds_list[0].get("odds", [])
        if not odds_entries:
            return {}

        pref = [b.lower() for b in (preferred_bookmakers or ["bet365", "admiralbet it", "unibet", "betvictor"])]

        selected_home: Optional[float] = None
        selected_away: Optional[float] = None

        # Priorità ai bookmaker preferiti
        for entry in odds_entries:
            bname = str(entry.get("bookmaker_name", "")).lower()
            if any(p in bname for p in pref):
                h = entry.get("home")
                a = entry.get("away")
                if h and not selected_home:
                    selected_home = float(h)
                if a and not selected_away:
                    selected_away = float(a)
                if selected_home and selected_away:
                    break

        # Fallback: prendi la prima quota disponibile o la mediana
        if not selected_home or not selected_away:
            for entry in odds_entries:
                h = entry.get("home")
                a = entry.get("away")
                if h and not selected_home:
                    selected_home = float(h)
                if a and not selected_away:
                    selected_away = float(a)

        result: Dict[str, float] = {}
        if selected_home and selected_home > 1.0:
            result["Casa Segna in Entrambi i Tempi: SI"] = round(selected_home, 2)
            result["Casa Segna in Entrambi i Tempi"] = round(selected_home, 2)
        if selected_away and selected_away > 1.0:
            result["Ospite Segna in Entrambi i Tempi: SI"] = round(selected_away, 2)
            result["Ospite Segna in Entrambi i Tempi"] = round(selected_away, 2)

        return result

    def get_injuries(self, match_id: int) -> List[Dict[str, Any]]:
        """Recupera la lista infortuni e assenze ufficiali per il match (player_name, reason, type)."""
        data = self._get("/injuries", params={"match_id": f"eq.{match_id}"})
        if data and isinstance(data, list):
            return data
        return []

    def get_clean_sheet_odds(self, match_id: int) -> Dict[str, float]:
        """Recupera le quote Clean Sheet (Porta Inviolata Casa e Ospite)."""
        data = self._get("/odds/clean-sheet", params={"match_id": f"eq.{match_id}"})
        if not data or not isinstance(data, list):
            return {}
        try:
            odds_list = data[0].get("periods", [])[0].get("odds", [])
            if not odds_list:
                return {}
            b = odds_list[0]
            res = {}
            if b.get("home"):
                res["Clean Sheet Casa"] = float(b["home"])
            if b.get("away"):
                res["Clean Sheet Ospite"] = float(b["away"])
            return res
        except (IndexError, KeyError, TypeError, ValueError):
            return {}

    def get_to_win_both_halves_odds(self, match_id: int) -> Dict[str, float]:
        """Recupera le quote 'Vince entrambi i tempi' per Casa e Ospite."""
        data = self._get("/odds/to-win-both-halves", params={"match_id": f"eq.{match_id}"})
        if not data or not isinstance(data, list):
            return {}
        try:
            odds_list = data[0].get("periods", [])[0].get("odds", [])
            if not odds_list:
                return {}
            b = odds_list[0]
            res = {}
            if b.get("home"):
                res["Casa Vince Entrambi i Tempi"] = float(b["home"])
            if b.get("away"):
                res["Ospite Vince Entrambi i Tempi"] = float(b["away"])
            return res
        except (IndexError, KeyError, TypeError, ValueError):
            return {}

    def get_to_win_to_nil_odds(self, match_id: int) -> Dict[str, float]:
        """Recupera le quote 'Vittoria a zero' per Casa e Ospite."""
        data = self._get("/odds/to-win-to-nil", params={"match_id": f"eq.{match_id}"})
        if not data or not isinstance(data, list):
            return {}
        try:
            odds_list = data[0].get("periods", [])[0].get("odds", [])
            if not odds_list:
                return {}
            b = odds_list[0]
            res = {}
            if b.get("home"):
                res["Casa Vince a Zero"] = float(b["home"])
            if b.get("away"):
                res["Ospite Vince a Zero"] = float(b["away"])
            return res
        except (IndexError, KeyError, TypeError, ValueError):
            return {}

    def enrich_odds_dict(
        self,
        match_name: str,
        odds_dict: Dict[str, float],
        date_str: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Arricchisce un odds_dict esistente con i mercati recuperati da Sportmicro.
        Non sovrascrive mercati già presenti.
        """
        parts = match_name.split(" vs ") if " vs " in match_name else match_name.split(" - ")
        if len(parts) != 2:
            return odds_dict

        home_team, away_team = parts[0].strip(), parts[1].strip()
        date_key = date_str or time.strftime("%Y-%m-%d")
        matches = self.get_matches_for_date(date_key)
        mid = self.find_match_id(home_team, away_team, matches)
        if not mid:
            return odds_dict

        both_halves = self.get_score_in_both_halves_odds(mid)
        for mkt, odd in both_halves.items():
            if mkt not in odds_dict:
                odds_dict[mkt] = odd

        win_halves = self.get_to_win_both_halves_odds(mid)
        for mkt, odd in win_halves.items():
            if mkt not in odds_dict:
                odds_dict[mkt] = odd

        win_nil = self.get_to_win_to_nil_odds(mid)
        for mkt, odd in win_nil.items():
            if mkt not in odds_dict:
                odds_dict[mkt] = odd

        clean_sheet = self.get_clean_sheet_odds(mid)
        for mkt, odd in clean_sheet.items():
            if mkt not in odds_dict:
                odds_dict[mkt] = odd

        return odds_dict
