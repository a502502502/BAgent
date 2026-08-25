"""
Flashscore/LiveScore.in unofficial feed — fonte non ufficiale via
local-global.flashscore.ninja (lo stesso backend usato da livescore.in).

A differenza di Sofascore (bloccata con 403 da questo ambiente) e di
API-Football (che pubblica solo formazioni ufficiali confermate, spesso
tardi), questa fonte e' raggiungibile e pubblica le formazioni prima.

Il formato di risposta e' testo "pipe-delimited" proprietario di Flashscore:
record separati da '~', campi separati da '¬', chiave/valore separati da '÷'.
Non c'e' documentazione ufficiale — il parsing qui e' stato ricostruito
empiricamente (vedi sessione 25 Agosto 2026, CLAUDE.md).

Per trovare il match_id (mid) di una partita non c'e' un modo affidabile
via richiesta diretta (nessun endpoint di ricerca noto funzionante); va
recuperato una volta tramite browser da livescore.in (vedi il link della
partita, contiene '?mid=XXXXXXXX') e poi riutilizzato qui.
"""

from __future__ import annotations

import re
from typing import Any, Optional

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "x-fsign": "SW9D1eZo",
}

BASE_URL = "https://local-global.flashscore.ninja/2/x/feed"


class FlashscoreSource:
    """Client per il feed non ufficiale di Flashscore/LiveScore.in."""

    def __init__(self, delay: float = 0.3, timeout: int = 8):
        self.delay = delay
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def _fetch(self, feed_code: str, match_id: str) -> str:
        url = f"{BASE_URL}/{feed_code}_1_{match_id}"
        r = self._session.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.text

    # ------------------------------------------------------------------
    # Lineups
    # ------------------------------------------------------------------

    def lineups_raw(self, match_id: str) -> str:
        """df_li = 'data feed lineups'."""
        return self._fetch("df_li", match_id)

    def lineups(self, match_id: str) -> dict[int, dict[str, Any]]:
        """
        Ritorna {1: {...}, 2: {...}} — team 1 = come appare per primo nel
        feed (di solito la squadra di casa, ma verificare sempre contro
        un'altra fonte quale sia realmente 'home' per la partita specifica).

        Ogni valore: {"starters": [str, ...], "subs": [str, ...], "coach": str|None}
        "starters" include il ruolo tra parentesi quando presente, es. "Song Bum-Keun (G)(C)".
        Ritorna dict vuoto {1: {...vuoto...}, 2: {...vuoto...}} se le
        formazioni non sono ancora state pubblicate (risposta senza 'LI÷').
        """
        try:
            text = self.lineups_raw(match_id)
        except requests.HTTPError:
            text = ""
        return self._parse_lineup(text)

    @staticmethod
    def _parse_lineup(text: str) -> dict[int, dict[str, Any]]:
        teams: dict[int, dict[str, Any]] = {
            1: {"starters": [], "subs": [], "coach": None},
            2: {"starters": [], "subs": [], "coach": None},
        }
        section = "Starting Lineups"
        current_team = 1
        for rec in text.split("~"):
            if "LB÷" in rec:
                section = rec.split("LB÷")[1].split("¬")[0]
            m = re.match(r"LC÷(\d)", rec)
            if m:
                current_team = int(m.group(1))
            if "LI÷" not in rec:
                continue
            name = rec.split("LI÷")[1].split("¬")[0]
            role = ""
            if "LR÷" in rec:
                role = rec.split("LR÷")[1].split("¬")[0]
            label = f"{name} {role}".strip()
            if section == "Starting Lineups":
                teams[current_team]["starters"].append(label)
            elif section == "Substitutes":
                teams[current_team]["subs"].append(name)
            elif section == "Coaches":
                teams[current_team]["coach"] = name
        return teams

    def lineups_available(self, match_id: str) -> bool:
        lu = self.lineups(match_id)
        return bool(lu[1]["starters"]) or bool(lu[2]["starters"])

    # ------------------------------------------------------------------
    # Match stats (corner, falli, cartellini, possesso...)
    # ------------------------------------------------------------------

    def stats_raw(self, match_id: str) -> str:
        """df_st = 'data feed stats'."""
        return self._fetch("df_st", match_id)

    def stats(self, match_id: str) -> dict[str, dict[str, str]]:
        """Ritorna {nome_statistica: {"home": val, "away": val}}."""
        try:
            text = self.stats_raw(match_id)
        except requests.HTTPError:
            return {}
        result: dict[str, dict[str, str]] = {}
        for block in text.split("¬~SD÷"):
            if "SG÷" in block and "SH÷" in block and "SI÷" in block:
                name = block.split("SG÷")[1].split("¬")[0]
                val_h = block.split("SH÷")[1].split("¬")[0]
                val_a = block.split("SI÷")[1].split("¬")[0]
                result[name] = {"home": val_h, "away": val_a}
        return result

    # ------------------------------------------------------------------
    # Match incidents (gol, cartellini, sostituzioni)
    # ------------------------------------------------------------------

    def incidents_raw(self, match_id: str) -> str:
        """df_sui = 'data feed summary/incidents'."""
        return self._fetch("df_sui", match_id)
