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

    @staticmethod
    def _fetch_aggregate_payload(cat_id: str, tourn_id: str, agg_id: int, request_context=None) -> Dict[str, Any] | None:
        url = (
            f"https://www.netwin.it/XSportDatastore/getTorneoCentrale"
            f"?systemCode=EPLAY24&lingua=IT&hash=&sportId=1"
            f"&categoryId={cat_id}&tournamentId={tourn_id}&idAggregata={agg_id}"
        )
        if request_context is not None:
            try:
                resp = request_context.get(url, timeout=10000)
                if resp.status == 200:
                    return resp.json()
            except Exception as e:
                logger.warning(f"Errore download aggregato {agg_id} via Playwright request: {e}")

        try:
            import urllib.request
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": XSPORT_APP_URL,
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"Errore download aggregato {agg_id} via urllib: {e}")
            return None

    def _merge_aggregate_markets(self, matches: List[Dict[str, Any]], aggregate_payload: Dict[str, Any], agg_id: int):
        if not aggregate_payload or not matches:
            return

        events = aggregate_payload.get("avs", [])
        if not events:
            return

        match_by_key: Dict[Any, Dict[str, Any]] = {}
        for m in matches:
            pal = m.get("palinsesto")
            avv = m.get("avvenimento")
            if pal is not None and avv is not None:
                match_by_key[(pal, avv)] = m
            clean_name = m.get("match_name", "").lower()
            if clean_name:
                match_by_key[clean_name] = m

        for ev in events:
            pal = ev.get("p")
            avv = ev.get("a")
            m = match_by_key.get((pal, avv))
            if not m:
                dsl = ev.get("dsl", {})
                raw_name = dsl.get("IT") or dsl.get("ORIGINAL_FROM_DB") or ""
                teams = [t.strip().lower() for t in raw_name.split("-")]
                clean_name = " vs ".join(teams) if len(teams) == 2 else raw_name.lower()
                m = match_by_key.get(clean_name)

            if not m:
                continue

            for scs in ev.get("scs", []):
                desc = (scs.get("d") or "").upper().strip()
                h = scs.get("h", 0)
                spread_str = self._parse_under_over_handicap(h) if h < 10000 else ""
                mg_range = decode_multigol_range(h) if h >= 10000 else ""

                for eq in scs.get("eqs", []):
                    ce = eq.get("ce")
                    q = round(eq.get("q", 0) / 100.0, 2)
                    if q <= 1.01:
                        continue

                    # 1. DC + Under/Over (agg 452)
                    if agg_id == 452:
                        label = None
                        if "DOPPIA CHANCE IN" in desc and "OUT" not in desc:
                            label = f"1X + Under {spread_str}" if ce == 1 else (f"1X + Over {spread_str}" if ce == 2 else None)
                        elif "DOPPIA CHANCE OUT" in desc and "IN" not in desc:
                            label = f"X2 + Under {spread_str}" if ce == 1 else (f"X2 + Over {spread_str}" if ce == 2 else None)
                        elif "DOPPIA CHANCE IN/OUT" in desc:
                            label = f"12 + Under {spread_str}" if ce == 1 else (f"12 + Over {spread_str}" if ce == 2 else None)
                        if label:
                            m["markets"].setdefault("COMBO", {})[label] = q

                    # 2. DC + MultiGol (agg 1477)
                    elif agg_id == 1477:
                        label = None
                        if "DC IN" in desc and "OUT" not in desc and ce == 1:
                            label = f"1X + MultiGol {mg_range}"
                        elif "DC OUT" in desc and "IN" not in desc and ce == 3:
                            label = f"X2 + MultiGol {mg_range}"
                        elif "DC IN/OUT" in desc and ce == 1:
                            label = f"12 + MultiGol {mg_range}"
                        if label:
                            m["markets"].setdefault("COMBO", {})[label] = q

                    # 3. MultiGol Standard (agg 335)
                    elif agg_id == 335:
                        if ce == 1 and mg_range:
                            m["markets"].setdefault("MULTIGOL", {})[f"MultiGol {mg_range}"] = q

                    # 4. 1X2 + Under/Over (agg 444)
                    elif agg_id == 444:
                        m_map = {1: "1 + Under", 2: "1 + Over", 3: "X + Under", 4: "X + Over", 5: "2 + Under", 6: "2 + Over"}
                        prefix = m_map.get(ce)
                        if prefix and spread_str:
                            m["markets"].setdefault("COMBO", {})[f"{prefix} {spread_str}"] = q

                    # 5. DC + Gol/NoGol (agg 456)
                    elif agg_id == 456:
                        label = None
                        if "DOPPIA CHANCE IN" in desc and "OUT" not in desc:
                            label = "1X + Gol" if ce == 1 else ("1X + NoGol" if ce == 2 else None)
                        elif "DOPPIA CHANCE OUT" in desc and "IN" not in desc:
                            label = "X2 + Gol" if ce == 1 else ("X2 + NoGol" if ce == 2 else None)
                        elif "DOPPIA CHANCE IN/OUT" in desc:
                            label = "12 + Gol" if ce == 1 else ("12 + NoGol" if ce == 2 else None)
                        if label:
                            m["markets"].setdefault("COMBO", {})[label] = q

                    # 6. Chance Mix 1X2 o Under/Over (agg 459)
                    elif agg_id == 459 and ce == 1 and spread_str:
                        label = None
                        if "1 O OVER" in desc: label = f"Chance Mix: 1 o Over {spread_str}"
                        elif "X O OVER" in desc: label = f"Chance Mix: X o Over {spread_str}"
                        elif "2 O OVER" in desc: label = f"Chance Mix: 2 o Over {spread_str}"
                        elif "1 O UNDER" in desc: label = f"Chance Mix: 1 o Under {spread_str}"
                        elif "X O UNDER" in desc: label = f"Chance Mix: X o Under {spread_str}"
                        elif "2 O UNDER" in desc: label = f"Chance Mix: 2 o Under {spread_str}"
                        if label:
                            m["markets"].setdefault("CHANCE_MIX", {})[label] = q

                    # 7. Chance Mix 1X2 o Gol/NoGol (agg 460)
                    elif agg_id == 460 and ce == 1:
                        label = None
                        if "1 OR GOL" in desc: label = "Chance Mix: 1 o Gol"
                        elif "X OR GOL" in desc: label = "Chance Mix: X o Gol"
                        elif "2 OR GOL" in desc: label = "Chance Mix: 2 o Gol"
                        elif "1 OR NOGOL" in desc: label = "Chance Mix: 1 o NoGol"
                        elif "X OR NOGOL" in desc: label = "Chance Mix: X o NoGol"
                        elif "2 OR NOGOL" in desc: label = "Chance Mix: 2 o NoGol"
                        if label:
                            m["markets"].setdefault("CHANCE_MIX", {})[label] = q

                    # 8. Chance Mix Gol/NoGol o Under/Over (agg 461)
                    elif agg_id == 461 and ce == 1 and spread_str:
                        label = None
                        if "GOAL O OVER" in desc or "GOL O OVER" in desc: label = f"Gol o Over {spread_str}"
                        elif "NO GOAL O OVER" in desc or "NOGOL O OVER" in desc: label = f"NoGol o Over {spread_str}"
                        elif "NO GOAL O UNDER" in desc or "NOGOL O UNDER" in desc: label = f"NoGol o Under {spread_str}"
                        if label:
                            m["markets"].setdefault("CHANCE_MIX", {})[label] = q

                    # 9. Chance Mix DC o Gol/NoGol (agg 2846)
                    elif agg_id == 2846 and ce == 1:
                        label = None
                        if "1X OR GOL" in desc: label = "Chance Mix: 1X o Gol"
                        elif "X2 OR GOL" in desc: label = "Chance Mix: X2 o Gol"
                        elif "12 OR GOL" in desc: label = "Chance Mix: 12 o Gol"
                        elif "1X OR NOGOL" in desc: label = "Chance Mix: 1X o NoGol"
                        elif "X2 OR NOGOL" in desc: label = "Chance Mix: X2 o NoGol"
                        elif "12 OR NOGOL" in desc: label = "Chance Mix: 12 o NoGol"
                        if label:
                            m["markets"].setdefault("CHANCE_MIX", {})[label] = q

                    # 10. MultiGol Squadra Casa e Ospite (agg 389)
                    elif agg_id == 389 and ce == 1 and mg_range:
                        if "CASA" in desc:
                            m["markets"].setdefault("MULTIGOL_SQUADRA", {})[f"MultiGol {mg_range} Casa"] = q
                        elif "OSP" in desc:
                            m["markets"].setdefault("MULTIGOL_SQUADRA", {})[f"MultiGol {mg_range} Ospite"] = q

                    # 11. 1X2 + Gol/NoGol (agg 448)
                    elif agg_id == 448:
                        m_map = {1: "1 + Gol", 2: "1 + NoGol", 3: "X + Gol", 4: "X + NoGol", 5: "2 + Gol", 6: "2 + NoGol"}
                        label = m_map.get(ce)
                        if label:
                            m["markets"].setdefault("COMBO", {})[label] = q

                    # 12. Under/Over + Gol/NoGol (agg 450)
                    elif agg_id == 450 and spread_str:
                        uo_gng_map = {1: f"Under {spread_str} + Gol", 2: f"Over {spread_str} + Gol", 3: f"Under {spread_str} + NoGol", 4: f"Over {spread_str} + NoGol"}
                        label = uo_gng_map.get(ce)
                        if label:
                            m["markets"].setdefault("COMBO", {})[label] = q

                    # 13. Draw No Bet (agg 2613)
                    elif agg_id == 2613:
                        label = "DNB 1" if ce == 1 else ("DNB 2" if ce == 2 else None)
                        if label:
                            m["markets"].setdefault("DRAW_NO_BET", {})[label] = q

                    # 14. 1X2 e Doppia Chance 1° Tempo (agg 341)
                    elif agg_id == 341:
                        label = None
                        if "1X2" in desc and h == 1:
                            m1x2_map = {1: "1 1° Tempo", 2: "X 1° Tempo", 3: "2 1° Tempo"}
                            label = m1x2_map.get(ce)
                        elif "DOPPIA CHANCE IN" in desc and "OUT" not in desc and h == 1 and ce == 1:
                            label = "1X 1° Tempo"
                        elif "DOPPIA CHANCE OUT" in desc and "IN" not in desc and h == 1 and ce == 2:
                            label = "X2 1° Tempo"
                        elif "DOPPIA CHANCE IN/OUT" in desc and h == 1 and ce == 2:
                            label = "12 1° Tempo"
                        if label:
                            m["markets"].setdefault("PRIMO_TEMPO", {})[label] = q

                    # 15. Under/Over 1° Tempo (agg 344)
                    elif agg_id == 344:
                        tempo = h >> 16
                        spread_val = (h & 0xFFFF) / 10.0
                        spread_1t = f"{spread_val:.1f}"
                        if tempo == 1:
                            label = f"Under {spread_1t} 1° Tempo" if ce == 1 else (f"Over {spread_1t} 1° Tempo" if ce == 2 else None)
                            if label:
                                m["markets"].setdefault("PRIMO_TEMPO", {})[label] = q

                    # 16. Gol/NoGol 1° Tempo (agg 345)
                    elif agg_id == 345 and h == 1:
                        label = "Gol 1° Tempo" if ce == 1 else ("NoGol 1° Tempo" if ce == 2 else None)
                        if label:
                            m["markets"].setdefault("PRIMO_TEMPO", {})[label] = q

                    # 17. MultiGol 1° Tempo (agg 352)
                    elif agg_id == 352 and ce == 1:
                        if "1" in desc or (h >> 16) == 1 or "1°" in desc or "1?" in desc:
                            mg_1t = decode_multigol_range(h)
                            if mg_1t:
                                m["markets"].setdefault("PRIMO_TEMPO", {})[f"MultiGol {mg_1t} 1° Tempo"] = q

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
                    search_name = TOURNAMENT_ALIASES.get(tourney.lower().strip(), tourney)
                    logger.info(f"Selezione torneo su Netwin: '{tourney}' (cercato come '{search_name}')...")
                    btn = page.locator(f":text-matches('^{search_name}$', 'i')")
                    if btn.count() == 0:
                        btn = page.locator(f":text-matches('{search_name}', 'i')")
                    btn = btn.first
                    if btn.is_visible(timeout=3000):
                        captured_payloads.clear()
                        btn.click()
                        page.wait_for_timeout(4000)

                        for url, payload in captured_payloads.items():
                            matches = self.parse_torneo_centrale_payload(payload, tournament_label=tourney)
                            logger.info(f"Estratte {len(matches)} partite per {tourney}")

                            try:
                                parsed_url = urllib.parse.urlparse(url)
                                qparams = urllib.parse.parse_qs(parsed_url.query)
                                cat_id = qparams.get("categoryId", [None])[0]
                                tourn_id = qparams.get("tournamentId", [None])[0]
                                if cat_id and tourn_id:
                                    logger.info(f"Scaricamento aggregati secondari per {tourney} (cat={cat_id}, tourn={tourn_id})...")
                                    for agg_id in SECONDARY_AGGREGATES:
                                        agg_payload = self._fetch_aggregate_payload(cat_id, tourn_id, agg_id, request_context=page.request)
                                        if agg_payload:
                                            self._merge_aggregate_markets(matches, agg_payload, agg_id)
                            except Exception as e:
                                logger.warning(f"Errore download aggregati secondari per {tourney}: {e}")

                            all_results.extend(matches)
                    else:
                        logger.warning(f"Torneo '{tourney}' ('{search_name}') non trovato nel menu Netwin.")

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

            # Combo
            if "COMBO" in mkts:
                for outcome, odd in mkts["COMBO"].items():
                    key = f"{match_name.lower()}::{outcome.lower()}"
                    cache[key] = {"match": match_name, "market": outcome, "netwin_odd": odd}

            # MultiGol
            if "MULTIGOL" in mkts:
                for outcome, odd in mkts["MULTIGOL"].items():
                    key = f"{match_name.lower()}::{outcome.lower()}"
                    cache[key] = {"match": match_name, "market": outcome, "netwin_odd": odd}

            # Primo Tempo, Chance Mix, MultiGol Squadra, Draw No Bet
            for cat in ["PRIMO_TEMPO", "CHANCE_MIX", "MULTIGOL_SQUADRA", "DRAW_NO_BET"]:
                if cat in mkts:
                    for outcome, odd in mkts[cat].items():
                        key = f"{match_name.lower()}::{outcome.lower()}"
                        cache[key] = {"match": match_name, "market": outcome, "netwin_odd": odd}

        try:
            with open(CACHE_ODDS_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            logger.info(f"Sincronizzate {len(cache)} quote reali in {CACHE_ODDS_FILE}")
        except Exception as e:
            logger.error(f"Errore sincronizzazione cache: {e}")
