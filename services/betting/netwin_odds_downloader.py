"""
services/betting/netwin_odds_downloader.py — Netwin Official Live Odds Downloader & Parser.

Estrae in tempo reale le quote ufficiali dal motore sportivo di Netwin.it (XSport / Microgame).
Supporta:
- Decodifica 1X2, Doppia Chance, Under/Over da 0.5 a 5.5, Gol/NoGol;
- Parsing degli avvenimenti (Palinsesto / Avvenimento AAMS);
- Normalizzazione e sincronizzazione con data/netwin_odds_cache.json;
- Integrazione diretta con NetwinOddsChecker e StrictTicketPipeline.
"""

from __future__ import annotations
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import urllib.parse
from playwright.sync_api import sync_playwright

logger = logging.getLogger("NetwinOddsDownloader")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
LIVE_ODDS_FILE = DATA_DIR / "netwin_live_odds.json"
CACHE_ODDS_FILE = DATA_DIR / "netwin_odds_cache.json"

XSPORT_APP_URL = "https://www.netwin.it/xsportapp/xsport_desktop/"

TOURNAMENT_ALIASES: Dict[str, str] = {
    "argentina": "Liga Profesional",
    "brasile": "Serie A Brasiliana",
    "brazil": "Serie A Brasiliana",
    "spagna": "LaLiga",
    "italia": "Serie A",
    "inghilterra": "Premier League",
    "germania": "Bundesliga",
    "europa": "Europa League",
    "nations league": "UEFA Nations League",
    "uefa nations league": "UEFA Nations League",
    "nations": "UEFA Nations League",
}

MULTIGOL_H_MAP: Dict[int, str] = {
    131073: "1-2",
    196609: "1-3",
    196610: "2-3",
    262145: "1-4",
    262146: "2-4",
    262147: "3-4",
    327681: "1-5",
    327682: "2-5",
    327683: "3-5",
    393217: "1-6",
}

SECONDARY_AGGREGATES: List[int] = [
    452,   # DC + Under/Over
    1477,  # DC + MultiGol
    335,   # MultiGol
    444,   # 1X2 + Under/Over
    456,   # DC + Gol/NoGol
    459,   # Chance Mix 1X2 o Under/Over
    460,   # Chance Mix 1X2 o Gol/NoGol
    461,   # Chance Mix Gol/NoGol o Under/Over
    2846,  # Chance Mix DC o Gol/NoGol
    389,   # MultiGol Squadra Casa e Ospite
    448,   # 1X2 + Gol/NoGol
    450,   # Under/Over + Gol/NoGol
    2613,  # Draw No Bet
    341,   # 1X2 e Doppia Chance 1° Tempo
    344,   # Under/Over 1° Tempo
    345,   # Gol/NoGol 1° Tempo
    352,   # MultiGol 1° Tempo
    # Specials (tiri / corner / cartellini) — candidate IDs, verified by discovery
    500, 501, 502, 503, 510, 520, 530, 540, 550,
    600, 610, 620, 630, 640, 650,
    700, 710, 720, 730, 740, 750,
    800, 810, 820, 830, 840, 850,
    900, 910, 920, 930, 940, 950,
    1000, 1010, 1020, 1030, 1040, 1050,
    1100, 1110, 1120, 1130,
    1200, 1210, 1220, 1230,
    1300, 1310, 1320,
    1400, 1410, 1420,
    1500, 1510, 1520,
    1600, 1610, 1620,
    1700, 1710, 1720,
    1800, 1810, 1820,
    1900, 1910, 1920,
    2000, 2010, 2020,
    2100, 2110, 2120,
    2200, 2210, 2220,
    2300, 2310, 2320,
    2400, 2410, 2420,
    2500, 2510, 2520,
    2700, 2710, 2720,
    2800, 2810, 2820,
    2900, 2910, 2920,
    3000, 3010, 3020,
]


def decode_multigol_range(h: int) -> str:
    """Decodifica il range multigol dall'handicap a 32 bit di XSport/Microgame."""
    if h in MULTIGOL_H_MAP:
        return MULTIGOL_H_MAP[h]
    min_g = h & 0xFFFF
    max_g = (h >> 16) & 0xFFFF
    if max_g >= 100:
        return f"{min_g}+"
    return f"{min_g}-{max_g}"
