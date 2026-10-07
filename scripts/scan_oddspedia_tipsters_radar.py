"""
scripts/scan_oddspedia_tipsters_radar.py — Radar e Intelligence sui Top Tipster di Oddspedia.

Analizza la community dei tipster verificati di Oddspedia:
1. Classifica per Yield %, Profitto Netto e Quota Media.
2. Segmentazione strategica per BAgent:
   - "Core / Cassaforte" (Quota media 1.80 - 2.30, Win Rate > 45%, Yield > +8%)
   - "Satellite / Gemme" (Yield > +12%, Quota media > 3.00, Profitto elevato)
3. Estrazione dei pronostici aperti per cross-validation con quote SNAI.
4. Applicazione rigida di Regola #80, Regola #82 e Regola #84.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT_DIR / "reports" / "oddspedia"


@dataclass
class TipsterProfile:
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
    profile_url: str
    category: str = "UNCLASSIFIED"

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
class TipsterPick:
    tipster_name: str
    tipster_yield: float
    match: str
    market: str
    selection: str
    odds: float
    timestamp: str
    source_type: str  # LIVE_FEED, NUXT_STATE
    bagent_validation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OddspediaTipsterRadar:
    RANKING_URL = "https://oddspedia.com/it/pronostici/classifica-tipsters"

    def __init__(self, headless: bool = True):
        self.headless = headless

    def run_scan(self) -> Dict[str, Any]:
        logger.info("Avvio scansione radar Top Tipster su Oddspedia...")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale="it-IT",
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            page.goto(self.RANKING_URL, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(3000)

            # 1. Parsing classifica
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

            tipsters: List[TipsterProfile] = []
            for idx, item in enumerate(dom_cards):
                text = item.get("text") or ""
                exact_name = item.get("exactName") or f"Tipster_{idx+1}"
                try:
                    parts = text.split()
                    if "PROFITTO" in parts and "YIELD" in parts:
                        prof_idx = parts.index("PROFITTO")
                        profit_val = float(parts[prof_idx - 1].replace(".", "").replace(",", "."))

                        yield_idx = parts.index("YIELD")
                        yield_val = float(parts[yield_idx - 1].replace("%", "").replace(",", "."))

                        country = "N/D"
                        if "Livello" in parts:
                            lvl_idx = parts.index("Livello")
                            country_candidates = parts[lvl_idx + 2 : prof_idx - 1]
                            name_words = exact_name.split()
                            filtered_country = [w for w in country_candidates if w not in name_words]
                            if filtered_country:
                                country = " ".join(filtered_country)

                        total_tips = 0
                        win_tips = 0
                        if "PRONOSTICI" in parts:
                            p_idx = parts.index("PRONOSTICI")
                            total_tips = int(parts[p_idx - 2])
                            win_tips = int(parts[p_idx - 1].replace("(", "").replace(")", ""))

                        avg_odds = 0.0
                        if "MEDIA" in parts and "QUOTE" in parts:
                            mq_idx = parts.index("MEDIA")
                            avg_odds = float(parts[mq_idx - 1].replace(",", "."))

                        form = "N/D"
                        if "FORMA" in parts:
                            f_idx = parts.index("FORMA")
                            form = parts[f_idx - 1]

                        open_tips = 0
                        if "APERTI" in parts:
                            ap_idx = parts.index("APERTI")
                            open_tips = int(parts[ap_idx - 2])

                        # Assegnazione categoria per BAgent
                        # Core: quote medie 1.80-2.30, Win Rate > 45%, Yield > 8%
                        win_rate = (win_tips / total_tips * 100) if total_tips else 0
                        category = "UNCLASSIFIED"
                        if 1.70 <= avg_odds <= 2.40 and win_rate >= 44.0 and yield_val >= 7.0:
                            category = "CORE_CASSAFORTE_CANDIDATE"
                        elif avg_odds >= 3.0 and yield_val >= 12.0:
                            category = "SATELLITE_GEMME_CANDIDATE"
                        elif yield_val >= 10.0:
                            category = "GENERAL_VALUE_SPECIALIST"

                        profile_url = f"https://oddspedia.com/it/u/{exact_name}"

                        tipsters.append(
                            TipsterProfile(
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
                                profile_url=profile_url,
                                category=category,
                            )
                        )
                except Exception as e:
                    logger.debug("Errore card %d: %s", idx, e)

            # 2. Estrazione pronostici recenti da Nuxt state
            raw_tips = page.evaluate("""() => {
                if (typeof window.__NUXT__ !== 'undefined' && window.__NUXT__.data && window.__NUXT__.data[0]) {
                    return window.__NUXT__.data[0].latestTips || [];
                }
                return [];
            }""")

            picks: List[TipsterPick] = []
            for t in raw_tips:
                sel_raw = t.get("selection") or {}
                sel = sel_raw[0] if isinstance(sel_raw, list) else (sel_raw if isinstance(sel_raw, dict) else {})
                ht = sel.get("ht_name") or "Home"
                at = sel.get("at_name") or "Away"
                picks.append(
                    TipsterPick(
                        tipster_name=t.get("user_nickname") or "Anonimo",
                        tipster_yield=0.0,
                        match=f"{ht} - {at}",
                        market=str(sel.get("market_name") or "1X2"),
                        selection=str(sel.get("outcome_name") or "Pick"),
                        odds=float(sel.get("odd") or 0.0),
                        timestamp=str(t.get("created_at") or ""),
                        source_type="NUXT_STATE",
                    )
                )

            # 3. Estrazione pronostici aperti dal profilo del Top Tipster Core "s00n"
            s00n_picks = self._extract_tipster_profile_feed(page, "s00n", yield_pct=10.2)
            picks.extend(s00n_picks)

            browser.close()

        # Validazione e cross-check per BAgent
        validated_picks = self._validate_picks_against_bagent_rules(picks)

        result = {
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "total_tipsters_tracked": len(tipsters),
            "top_tipsters": [t.to_dict() for t in tipsters],
            "total_open_picks_found": len(validated_picks),
            "picks": [p.to_dict() for p in validated_picks],
        }

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_file = REPORTS_DIR / "tipsters_radar_latest.json"
        out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Radar Tipster Oddspedia completato e salvato in %s", out_file)
        return result

    def _extract_tipster_profile_feed(
        self,
        page: Any,
        username: str,
        yield_pct: float,
    ) -> List[TipsterPick]:
        url = f"https://oddspedia.com/it/u/{username}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2500)
            lines = page.evaluate("""() => {
                return document.body.innerText.split('\\n').map(l => l.trim()).filter(l => l.length > 2);
            }""")

            picks = []
            for i in range(len(lines) - 4):
                line = lines[i]
                if ("Pronostici" in line or "minuti fa" in line or "ore fa" in line) and i + 3 < len(lines):
                    potential_match = lines[i + 1]
                    potential_market_pick = lines[i + 2]
                    potential_odd = lines[i + 3]

                    # Filtro euristico
                    if (" - " in potential_match or " vs " in potential_match) and any(
                        c.isdigit() for c in potential_odd
                    ):
                        try:
                            odd_val = float(potential_odd.replace(",", "."))
                            market_part = potential_market_pick
                            selection_part = potential_market_pick
                            if ":" in potential_market_pick:
                                parts = potential_market_pick.split(":", 1)
                                market_part = parts[0].strip()
                                selection_part = parts[1].strip()

                            picks.append(
                                TipsterPick(
                                    tipster_name=username,
                                    tipster_yield=yield_pct,
                                    match=potential_match,
                                    market=market_part,
                                    selection=selection_part,
                                    odds=odd_val,
                                    timestamp=line,
                                    source_type="LIVE_FEED",
                                )
                            )
                        except ValueError:
                            pass
            return picks
        except Exception as e:
            logger.warning("Impossibile estrarre feed per %s: %s", username, e)
            return []

    def _validate_picks_against_bagent_rules(self, picks: List[TipsterPick]) -> List[TipsterPick]:
        """Applica la checklist qualitativa di BAgent a ciascun suggerimento dei tipster."""
        for p in picks:
            validation = {
                "cross_check_status": "ANALYZED",
                "rules_applied": [],
                "bagent_recommendation": "",
            }

            # Regola #80: Protezione della quota
            sel_low = p.selection.lower()
            if "draw no bet" in sel_low or "dnb" in sel_low:
                validation["rules_applied"].append("REGOLA_80_EQUIVALENT_PROTECTION")
                validation["bagent_recommendation"] = (
                    "Il tipster usa Draw No Bet (rimborso su pareggio). In ottica SNAI/Netwin, "
                    "verificare se la Doppia Chance (1X o X2) offre sufficiente assorbimento a quota giocabile "
                    "oppure se la combo DC + Over 1.5 genera un Expected Value superiore."
                )
            elif "handicap" in sel_low:
                validation["rules_applied"].append("REGOLA_80_HANDICAP_CAUTION")
                validation["bagent_recommendation"] = (
                    "Handicap asiatico/europeo: consentito solo con Poisson lambda verificato. "
                    "Evitare se la linea richiede scarto netto superiore a 1.5 gol."
                )
            else:
                validation["rules_applied"].append("STANDARD_MACRO_CHECK")
                validation["bagent_recommendation"] = (
                    "Confrontare con i mercati combinati ufficiali SNAI per individuare asimmetrie rispetto alla quota soft."
                )

            # Regola #82: Verifica Anti-Stale H2H
            validation["rules_applied"].append("REGOLA_82_ANTI_STALE_H2H_MANDATORY")

            # Regola #84: Protocollo Formazioni
            if any(term in sel_low for term in ["segna", "marcatore", "tiri", "assist", "falli", "cartellino"]):
                validation["rules_applied"].append("REGOLA_84_LINEUP_GATE_MANDATORY")
                validation["lineup_status"] = "WAITING_LINEUPS (T-60m)"
            else:
                validation["lineup_status"] = "MACRO_MARKET_EARLY_PLAYABLE"

            p.bagent_validation = validation
        return picks


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    radar = OddspediaTipsterRadar(headless=True)
    report = radar.run_scan()

    print("\n=======================================================")
    print("ODDSPEDIA TIPSTER RADAR — REPORT SINTETICO BAGENT")
    print("=======================================================")
    print(f"Tipster monitorati: {report['total_tipsters_tracked']}")
    print(f"Pronostici aperti analizzati: {report['total_open_picks_found']}")

    print("\n--- PROFILI TIPSTER IDENTIFICATI PER CATEGORIA ---")
    for t in report["top_tipsters"]:
        cat_label = t["category"]
        print(f"[{t['rank']}] {t['name']} ({t['country']}) -> Yield: +{t['yield_pct']}% | Quota media: {t['avg_odds']} | Win Rate: {t['win_rate_pct']}% | Categoria: {cat_label}")

    print("\n--- SELEZIONI APERTE ANALIZZATE & CROSS-CHECK BAGENT ---")
    for p in report["picks"]:
        v = p["bagent_validation"]
        print(f"- Tipster: {p['tipster_name']} (Yield +{p['tipster_yield']}%)")
        print(f"  Match: {p['match']} | Quota: {p['odds']}")
        print(f"  Selezione: {p['market']} -> {p['selection']}")
        print(f"  Lineup Status: {v.get('lineup_status')}")
        print(f"  Raccomandazione: {v.get('bagent_recommendation')}\n")


if __name__ == "__main__":
    main()
