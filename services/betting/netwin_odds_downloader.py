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
from playwright.sync_api import sync_playwright

logger = logging.getLogger("NetwinOddsDownloader")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
LIVE_ODDS_FILE = DATA_DIR / "netwin_live_odds.json"
CACHE_ODDS_FILE = DATA_DIR / "netwin_odds_cache.json"

XSPORT_APP_URL = "https://www.netwin.it/xsportapp/xsport_desktop/"

class NetwinOddsDownloader:
    """
    Scarica e decodifica i dati ufficiali di quota dal portale Netwin.it.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parse_under_over_handicap(h_val: int) -> str:
        """Converte il valore numerico di handicap Netwin nel rispettivo spread (es. 250 -> '2.5')."""
        val = h_val / 100.0
        return f"{val:.1f}"

    def parse_torneo_centrale_payload(self, raw_data: Dict[str, Any], tournament_label: str = "") -> List[Dict[str, Any]]:
        """
        Parsa il payload JSON restituito da getTorneoCentrale di XSport.
        """
        events = raw_data.get("avs", [])
        parsed_matches = []

        for ev in events:
            dsl = ev.get("dsl", {})
            raw_match_name = dsl.get("IT") or dsl.get("ORIGINAL_FROM_DB") or "Sconosciuto"
            pal = ev.get("p")
            avv = ev.get("a")
            kickoff_ts = ev.get("ts", "") # es. "20260917 21:00:00"

            # Formatta match name pulito
            teams = [t.strip() for t in raw_match_name.split("-")]
            clean_name = " vs ".join(teams) if len(teams) == 2 else raw_match_name

            match_data = {
                "match_name": clean_name,
                "raw_name": raw_match_name,
                "tournament": tournament_label,
                "kickoff": kickoff_ts,
                "palinsesto": pal,
                "avvenimento": avv,
                "markets": {}
            }

            scs_list = ev.get("scs", [])
            for scs in scs_list:
                desc = (scs.get("d") or "").upper().strip()
                cs = scs.get("cs")
                eqs = scs.get("eqs", [])
                h = scs.get("h", 0)

                # 1. 1X2 FINALE
                if "1X2" in desc:
                    odds_1x2 = {}
                    for eq in eqs:
                        ce = eq.get("ce")
                        q = round(eq.get("q", 0) / 100.0, 2)
                        if ce == 1: odds_1x2["1"] = q
                        elif ce == 2: odds_1x2["X"] = q
                        elif ce == 3: odds_1x2["2"] = q
                    match_data["markets"]["1X2"] = odds_1x2

                # 2. DOPPIA CHANCE
                elif "DOPPIA CHANCE IN" in desc and "OUT" not in desc:
                    for eq in eqs:
                        if eq.get("ce") == 1:
                            match_data["markets"].setdefault("DOPPIA_CHANCE", {})["1X"] = round(eq.get("q", 0) / 100.0, 2)
                        elif eq.get("ce") == 2:
                            match_data["markets"].setdefault("DOPPIA_CHANCE", {})["X2"] = round(eq.get("q", 0) / 100.0, 2)

                elif "DOPPIA CHANCE IN/OUT" in desc:
                    for eq in eqs:
                        if eq.get("ce") == 2:
                            match_data["markets"].setdefault("DOPPIA_CHANCE", {})["12"] = round(eq.get("q", 0) / 100.0, 2)

                elif "DOPPIA CHANCE OUT" in desc:
                    for eq in eqs:
                        if eq.get("ce") == 1 and "X2" not in match_data["markets"].get("DOPPIA_CHANCE", {}):
                            match_data["markets"].setdefault("DOPPIA_CHANCE", {})["X2"] = round(eq.get("q", 0) / 100.0, 2)

                # 3. UNDER / OVER GOL
                elif desc == "U/O" or "UNDER / OVER" in desc:
                    spread_str = self._parse_under_over_handicap(h)
                    uo_dict = {}
                    for eq in eqs:
                        ce = eq.get("ce")
                        q = round(eq.get("q", 0) / 100.0, 2)
                        if ce == 1: uo_dict["Under"] = q
                        elif ce == 2: uo_dict["Over"] = q
                    
                    if uo_dict:
                        match_data["markets"].setdefault("UNDER_OVER", {})[spread_str] = uo_dict

                # 4. GOL / NO GOL
                elif "GOAL" in desc or "GOL" in desc:
                    gng_dict = {}
                    for eq in eqs:
                        ce = eq.get("ce")
                        q = round(eq.get("q", 0) / 100.0, 2)
                        if ce == 1: gng_dict["Gol"] = q
                        elif ce == 2: gng_dict["NoGol"] = q
                    if gng_dict:
                        match_data["markets"]["GOL_NOGOL"] = gng_dict

            parsed_matches.append(match_data)

        return parsed_matches

    def download_tournaments(self, target_tournaments: List[str]) -> List[Dict[str, Any]]:
        """
        Avvia Playwright in background, naviga sui tornei target ed estrae tutti i dati.
        """
        all_results = []
        captured_payloads = {}

        logger.info(f"Avvio scarico quote Netwin per tornei: {target_tournaments}")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            def on_response(resp):
                if "getTorneoCentrale" in resp.url and resp.status == 200:
                    try:
                        text = resp.text()
                        if len(text) > 500:
                            data = json.loads(text)
                            captured_payloads[resp.url] = data
                    except Exception:
                        pass

            page.on("response", on_response)

            try:
                page.goto(XSPORT_APP_URL, timeout=35000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                for tourney in target_tournaments:
                    logger.info(f"Selezione torneo su Netwin: '{tourney}'...")
                    btn = page.locator(f":text-matches('{tourney}', 'i')").first
                    if btn.is_visible(timeout=3000):
                        captured_payloads.clear()
                        btn.click()
                        page.wait_for_timeout(4000)

                        for url, payload in captured_payloads.items():
                            matches = self.parse_torneo_centrale_payload(payload, tournament_label=tourney)
                            logger.info(f"Estratte {len(matches)} partite per {tourney}")
                            all_results.extend(matches)
                    else:
                        logger.warning(f"Torneo '{tourney}' non trovato nel menu Netwin.")

            except Exception as e:
                logger.error(f"Errore durante navigazione Netwin: {e}")
            finally:
                browser.close()

        # Salva nel file live odds
        self._save_live_odds(all_results)
        # Aggiorna la cache per NetwinOddsChecker
        self._sync_with_checker_cache(all_results)

        return all_results

    def _save_live_odds(self, matches: List[Dict[str, Any]]):
        try:
            existing = {}
            if LIVE_ODDS_FILE.exists():
                try:
                    with open(LIVE_ODDS_FILE, "r", encoding="utf-8") as f:
                        old_data = json.load(f)
                        for m in old_data.get("matches", []):
                            existing[m["match_name"].lower()] = m
                except Exception:
                    pass

            for m in matches:
                existing[m["match_name"].lower()] = m

            merged_matches = list(existing.values())
            with open(LIVE_ODDS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_matches": len(merged_matches),
                    "matches": merged_matches
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"Quote Netwin salvate in {LIVE_ODDS_FILE} (Totale partite: {len(merged_matches)})")
        except Exception as e:
            logger.error(f"Errore salvataggio {LIVE_ODDS_FILE}: {e}")

    def _sync_with_checker_cache(self, matches: List[Dict[str, Any]]):
        """Popola data/netwin_odds_cache.json con le quote reali per audit immediato."""
        cache = {}
        if CACHE_ODDS_FILE.exists():
            try:
                with open(CACHE_ODDS_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                cache = {}

        for m in matches:
            match_name = m["match_name"]
            mkts = m.get("markets", {})

            # 1X2
            if "1X2" in mkts:
                for outcome, odd in mkts["1X2"].items():
                    key = f"{match_name.lower()}::{outcome.lower()}"
                    cache[key] = {"match": match_name, "market": outcome, "netwin_odd": odd}

            # Doppia Chance
            if "DOPPIA_CHANCE" in mkts:
                for outcome, odd in mkts["DOPPIA_CHANCE"].items():
                    key = f"{match_name.lower()}::{outcome.lower()}"
                    cache[key] = {"match": match_name, "market": outcome, "netwin_odd": odd}

            # Under / Over
            if "UNDER_OVER" in mkts:
                for spread, uo in mkts["UNDER_OVER"].items():
                    if "Under" in uo:
                        key = f"{match_name.lower()}::under {spread}".lower()
                        cache[key] = {"match": match_name, "market": f"Under {spread}", "netwin_odd": uo["Under"]}
                    if "Over" in uo:
                        key = f"{match_name.lower()}::over {spread}".lower()
                        cache[key] = {"match": match_name, "market": f"Over {spread}", "netwin_odd": uo["Over"]}

            # Gol / NoGol
            if "GOL_NOGOL" in mkts:
                for outcome, odd in mkts["GOL_NOGOL"].items():
                    key = f"{match_name.lower()}::{outcome.lower()}"
                    cache[key] = {"match": match_name, "market": outcome, "netwin_odd": odd}

        try:
            with open(CACHE_ODDS_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            logger.info(f"Sincronizzate {len(cache)} quote reali in {CACHE_ODDS_FILE}")
        except Exception as e:
            logger.error(f"Errore sincronizzazione cache: {e}")
