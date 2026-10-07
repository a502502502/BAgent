"""
scripts/extract_oddspedia_tipsters.py — Modulo di ingestione e analisi per i Top Tipster e Pronostici di Oddspedia.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


@dataclass
class OddspediaTipsterProfile:
    rank: int
    name: str
    country: str
    profit_eur: float
    yield_pct: float
    total_tips: int
    winning_tips: int
    avg_odds: float
    recent_form: str
    open_tips_count: int
    followers: int = 0

    @property
    def win_rate_pct(self) -> float:
        if self.total_tips == 0:
            return 0.0
        return round((self.winning_tips / self.total_tips) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["win_rate_pct"] = self.win_rate_pct
        return d


@dataclass
class OddspediaTipPrediction:
    tip_id: int
    tipster_name: str
    tipster_profit: float
    match: str
    sport: str
    market: str
    selection: str
    odds: float
    created_at: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fetch_oddspedia_tipsters_and_tips(headless: bool = True) -> Dict[str, Any]:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="it-IT",
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        url = "https://oddspedia.com/it/pronostici/classifica-tipsters"
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)

        # 1. Estrazione classifica top tipster dal DOM
        dom_cards = page.evaluate("""() => {
            const list = [];
            const cards = document.querySelectorAll('.tipster');
            cards.forEach((c, idx) => {
                const avatarEl = c.querySelector('.user-avatar');
                const exactName = avatarEl ? (avatarEl.getAttribute('title') || '').trim() : '';
                const text = c.innerText.replace(/\\s+/g, ' ').trim();
                list.push({exactName, text});
            });
            return list;
        }""")

        tipsters: List[OddspediaTipsterProfile] = []
        for idx, item in enumerate(dom_cards):
            text = item.get("text") or ""
            exact_name = item.get("exactName") or f"Tipster_{idx+1}"
            try:
                parts = text.split()
                # Trova parola PROFITTO
                if "PROFITTO" in parts and "YIELD" in parts:
                    prof_idx = parts.index("PROFITTO")
                    profit_str = parts[prof_idx - 1].replace(".", "").replace(",", ".")
                    profit_val = float(profit_str)

                    yield_idx = parts.index("YIELD")
                    yield_str = parts[yield_idx - 1].replace("%", "").replace(",", ".")
                    yield_val = float(yield_str)

                    # Paese
                    country = "N/D"
                    if "Livello" in parts:
                        lvl_idx = parts.index("Livello")
                        # il paese e' tra il nome e la cifra profitto
                        country_candidates = parts[lvl_idx + 2 : prof_idx - 1]
                        # togli le parole del nome
                        name_words = exact_name.split()
                        filtered_country = [w for w in country_candidates if w not in name_words]
                        if filtered_country:
                            country = " ".join(filtered_country)

                    # Totale pronostici e vittorie
                    total_tips = 0
                    win_tips = 0
                    if "PRONOSTICI" in parts:
                        p_idx = parts.index("PRONOSTICI")
                        total_tips = int(parts[p_idx - 2])
                        win_tips = int(parts[p_idx - 1].replace("(", "").replace(")", ""))

                    # Quota media
                    avg_odds = 0.0
                    if "MEDIA" in parts and "QUOTE" in parts:
                        mq_idx = parts.index("MEDIA")
                        avg_odds = float(parts[mq_idx - 1].replace(",", "."))

                    # Forma
                    form = "N/D"
                    if "FORMA" in parts:
                        f_idx = parts.index("FORMA")
                        form = parts[f_idx - 1]

                    # Pronostici aperti
                    open_tips = 0
                    if "APERTI" in parts:
                        ap_idx = parts.index("APERTI")
                        open_tips = int(parts[ap_idx - 2])

                    tipsters.append(
                        OddspediaTipsterProfile(
                            rank=idx + 1,
                            name=exact_name,
                            country=country,
                            profit_eur=profit_val,
                            yield_pct=yield_val,
                            total_tips=total_tips,
                            winning_tips=win_tips,
                            avg_odds=avg_odds,
                            recent_form=form,
                            open_tips_count=open_tips,
                        )
                    )
            except Exception as e:
                logger.debug("Errore parsing card %d: %s", idx, e)

        # 2. Estrazione ultimi pronostici dallo State Nuxt
        raw_tips = page.evaluate("""() => {
            if (typeof window.__NUXT__ !== 'undefined' && window.__NUXT__.data && window.__NUXT__.data[0]) {
                return window.__NUXT__.data[0].latestTips || [];
            }
            return [];
        }""")

        predictions: List[OddspediaTipPrediction] = []
        for t in raw_tips:
            sel_raw = t.get("selection") or {}
            if isinstance(sel_raw, list):
                sel = sel_raw[0] if sel_raw else {}
            elif isinstance(sel_raw, dict):
                sel = sel_raw
            else:
                sel = {}
            ht = sel.get("ht_name") or "Home"
            at = sel.get("at_name") or "Away"
            match_name = f"{ht} - {at}"
            predictions.append(
                OddspediaTipPrediction(
                    tip_id=t.get("id") or 0,
                    tipster_name=t.get("user_nickname") or "Anonimo",
                    tipster_profit=float(str(t.get("user_profit") or "0").replace(",", ".")),
                    match=match_name,
                    sport=str(sel.get("sport_slug") or "calcio"),
                    market=str(sel.get("market_name") or "1X2"),
                    selection=str(sel.get("outcome_name") or "Pick"),
                    odds=float(sel.get("odd") or 0.0),
                    created_at=str(t.get("created_at") or ""),
                    status=str(t.get("status") or "active"),
                )
            )

        browser.close()

    return {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "total_tipsters": len(tipsters),
        "tipsters": [t.to_dict() for t in tipsters],
        "latest_predictions_count": len(predictions),
        "latest_predictions": [p.to_dict() for p in predictions],
    }


def fetch_tipster_open_tips(username: str, headless: bool = True) -> Dict[str, Any]:
    """Estrae i pronostici attivi di un singolo tipster dal suo profilo pubblico."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="it-IT",
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        api_tips = []

        def handle_response(response):
            try:
                if "getTips" in response.url or "getUserTips" in response.url or ("tips" in response.url and "api" in response.url):
                    data = response.json()
                    if isinstance(data, list):
                        api_tips.extend(data)
                    elif isinstance(data, dict):
                        api_tips.extend(data.get("data") or data.get("tips") or [])
            except Exception:
                pass

        page.on("response", handle_response)

        url = f"https://oddspedia.com/it/u/{username}"
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3500)

        # Selettori dal DOM
        dom_tips = page.evaluate("""() => {
            const list = [];
            const cards = document.querySelectorAll('.user-tips__item, .tip-card, .tip-item, .card');
            cards.forEach(c => {
                const text = c.innerText.replace(/\\s+/g, ' ').trim();
                if (text.length > 20) {
                    list.push(text);
                }
            });
            return list;
        }""")

        browser.close()

    return {"api_tips": api_tips, "dom_tips": dom_tips}


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    data = fetch_oddspedia_tipsters_and_tips(headless=True)
    out_dir = Path(__file__).resolve().parent.parent / "reports" / "oddspedia"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "tipsters_intel.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Salvati {data['total_tipsters']} tipster e {data['latest_predictions_count']} pronostici in {out_file}")
    print("\n--- TEST RECUPERO PRONOSTICI APERTI TOP TIPSTER 's00n' ---")
    s00n_tips = fetch_tipster_open_tips("s00n", headless=True)
    print(f"API tips intercettati: {len(s00n_tips['api_tips'])}, DOM cards: {len(s00n_tips['dom_tips'])}")
    for dt in s00n_tips["dom_tips"][:5]:
        print(" - Pronostico aperto s00n:", dt)


if __name__ == "__main__":
    main()
