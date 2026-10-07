"""
services/football/external/sources/oddspedia.py — Client di Ingestion e Radar per Oddspedia.

Estrae segnali di mercato ad alta frequenza da Oddspedia:
1. Dropping Odds (quote in rapido calo, indicatori di notizie esclusive o flussi anomali).
2. Value Bets (selezioni con quota superiore alla probabilita fair stimata dal mercato).
3. Comparazione bookmaker soft vs sharp per rilevare ritardi di allineamento (es. SNAI vs Pinnacle).

Utilizza Playwright con estrazione diretta dallo state SSR di Nuxt.js (window.__NUXT__).
Zero chiamate ad API a pagamento.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
REPORTS_DIR = ROOT_DIR / "reports" / "oddspedia"

OUTCOME_MAP = {
    "o1": "1 (Casa)",
    "o2": "X (Pareggio)",
    "o3": "2 (Trasferta)",
    "o_over": "Over",
    "o_under": "Under",
    "o_yes": "Gol (Si)",
    "o_no": "No Gol",
}


@dataclass
class OddspediaSignal:
    signal_type: str  # DROPPING_ODDS, VALUE_BET
    match_id: int
    home_team: str
    away_team: str
    sport: str
    category: str
    league: str
    kickoff_utc: str
    market: str
    selection: str
    drop_percentage: float = 0.0
    initial_odd: Optional[float] = None
    current_odd: Optional[float] = None
    fair_probability_pct: Optional[float] = None
    overvalue_pct: Optional[float] = None
    best_bookmaker: Optional[str] = None
    bookmakers_count: int = 0
    italian_bookmakers: List[Dict[str, Any]] = field(default_factory=list)
    raw_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)



@dataclass
class OddspediaMatchInsights:
    """Note qualitative, trend H2H e statistiche estratte dalla scheda partita Oddspedia."""
    match_id: int
    home_team: str
    away_team: str
    home_form: str = ""
    away_form: str = ""
    statements: List[str] = field(default_factory=list)  # Dati di scommesse / note match_keys
    betting_stats: Dict[str, Any] = field(default_factory=dict)  # goals, btts, corners, cards
    inplay_status: Optional[str] = None
    current_time: Optional[int] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None
    referee: Optional[str] = None
    weather: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OddspediaHotBet:
    """Scommessa ad alta frequenza statistica (streak certificata da Oddspedia)."""
    match: str
    league: str
    market: str
    streak_count: str
    win_percentage: float
    odd: float
    kickoff: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)



class OddspediaSource:
    """Wrapper di scraping e parsing per le quote e i movimenti di Oddspedia."""

    BASE_URL = "https://oddspedia.com"
    DROPPING_URL = "https://oddspedia.com/dropping-odds"
    VALUEBETS_URL = "https://oddspedia.com/valuebets"
    HOTBETS_URL = "https://oddspedia.com/it/hot-bets"


    # Principali bookmaker con licenza ADM/AAMS monitorati su Oddspedia
    ADM_BOOKMAKERS = {
        "snai",
        "sisal",
        "eurobet",
        "goldbet",
        "planetwin365",
        "bet365",
        "bwin",
        "lottomatica",
        "better",
        "betfair",
    }

    def __init__(self, headless: bool = True, timeout_ms: int = 25000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    def fetch_dropping_odds(
        self,
        sport: str = "football",
        min_drop_pct: float = 10.0,
        limit: int = 30,
    ) -> List[OddspediaSignal]:
        """Estrae le quote in calo con percentuale di ribasso superiore alla soglia."""
        state = self._fetch_nuxt_betting_tools(self.DROPPING_URL)
        if not state:
            logger.warning("Impossibile recuperare lo state Nuxt per Dropping Odds.")
            return []

        return self.parse_dropping_odds_state(
            state=state,
            sport=sport,
            min_drop_pct=min_drop_pct,
            limit=limit,
        )

    def fetch_value_bets(
        self,
        sport: str = "football",
        min_overvalue_pct: float = 3.0,
        max_overvalue_pct: float = 20.0,
        limit: int = 30,
    ) -> List[OddspediaSignal]:
        """Estrae le value bets filtrate per evitare errori materiali di battitura del bookmaker."""
        state = self._fetch_nuxt_betting_tools(self.VALUEBETS_URL)
        if not state:
            logger.warning("Impossibile recuperare lo state Nuxt per Value Bets.")
            return []

        return self.parse_value_bets_state(
            state=state,
            sport=sport,
            min_overvalue_pct=min_overvalue_pct,
            max_overvalue_pct=max_overvalue_pct,
            limit=limit,
        )

    def _fetch_nuxt_betting_tools(self, url: str) -> Optional[Dict[str, Any]]:
        """Apre la pagina con Playwright ed estrae l'oggetto window.__NUXT__.state.bettingTools."""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                page.wait_for_timeout(3000)

                raw_state = page.evaluate("""() => {
                    try {
                        if (typeof window.__NUXT__ !== 'undefined' && window.__NUXT__.state) {
                            return window.__NUXT__.state.bettingTools || null;
                        }
                    } catch(e) {}
                    return null;
                }""")
                browser.close()
                return raw_state
        except Exception as e:
            logger.error("Errore durante l'estrazione Playwright da %s: %s", url, e)
            return None

    def parse_dropping_odds_state(
        self,
        state: Dict[str, Any],
        sport: str = "football",
        min_drop_pct: float = 10.0,
        limit: int = 30,
    ) -> List[OddspediaSignal]:
        """Effettua il parsing puro dei dati di dropping odds dallo state di Nuxt."""
        signals: List[OddspediaSignal] = []
        tool_data = state.get("toolData") or {}
        matches = tool_data.get("matches") or tool_data.get("data") or []
        if isinstance(matches, dict):
            matches = list(matches.values())

        for m in matches:
            if not isinstance(m, dict):
                continue
            m_sport = str(m.get("sport_slug") or m.get("sport_name") or "").lower()
            if sport and sport.lower() not in m_sport:
                continue

            max_drop = float(m.get("maxDrop") or 0.0)
            if max_drop < min_drop_pct:
                continue

            odd_target = str(m.get("oddNumberDrop") or "o1").lower()
            selection_label = OUTCOME_MAP.get(odd_target, odd_target)

            # Estrai le quote e i bookmaker
            all_odds_list = []
            italian_bookies = []
            best_bookie = None
            best_odd = 0.0
            initial_odd = None
            current_odd = None

            for odds_group in m.get("odds", []):
                for drop_info in odds_group.get("allDrops", []):
                    b_slug = str(drop_info.get("slug") or "").lower()
                    c_val = float(drop_info.get("current") or 0.0)
                    m_val = float(drop_info.get("max") or 0.0)
                    if c_val > 0:
                        current_odd = c_val
                    if m_val > 0:
                        initial_odd = m_val

                for b in odds_group.get("allOdds", []):
                    b_name = b.get("name") or b.get("slug")
                    b_slug = str(b.get("slug") or "").lower()
                    b_odd = float(b.get("current") or 0.0)
                    if b_odd > best_odd:
                        best_odd = b_odd
                        best_bookie = b_name

                    if any(adm in b_slug for adm in self.ADM_BOOKMAKERS):
                        italian_bookies.append({
                            "name": b_name,
                            "slug": b_slug,
                            "odd": b_odd,
                        })

            signal = OddspediaSignal(
                signal_type="DROPPING_ODDS",
                match_id=int(m.get("id") or m.get("match_key") or 0),
                home_team=str(m.get("ht") or "Home").strip(),
                away_team=str(m.get("at") or "Away").strip(),
                sport=m_sport,
                category=str(m.get("category_name") or "").strip(),
                league=str(m.get("league_name") or "").strip(),
                kickoff_utc=str(m.get("md") or "").strip(),
                market=str(m.get("ot_name") or m.get("group_name") or "1X2").strip(),
                selection=selection_label,
                drop_percentage=round(max_drop, 1),
                initial_odd=initial_odd,
                current_odd=current_odd or best_odd,
                best_bookmaker=best_bookie,
                bookmakers_count=int(m.get("allBookies") or 0),
                italian_bookmakers=italian_bookies,
                raw_info={
                    "dropBid": m.get("dropBid"),
                    "last_change": m.get("last_change"),
                },
            )
            signals.append(signal)
            if len(signals) >= limit:
                break

        # Ordina per calo percentuale decrescente
        signals.sort(key=lambda s: s.drop_percentage, reverse=True)
        return signals

    def parse_value_bets_state(
        self,
        state: Dict[str, Any],
        sport: str = "football",
        min_overvalue_pct: float = 3.0,
        max_overvalue_pct: float = 20.0,
        limit: int = 30,
    ) -> List[OddspediaSignal]:
        """Effettua il parsing puro dei dati di value bets dallo state di Nuxt."""
        signals: List[OddspediaSignal] = []
        tool_data = state.get("toolData") or {}
        matches = tool_data.get("matches") or tool_data.get("data") or []
        if isinstance(matches, dict):
            matches = list(matches.values())

        for m in matches:
            if not isinstance(m, dict):
                continue
            m_sport = str(m.get("sport_slug") or m.get("sport_name") or "").lower()
            if sport and sport.lower() not in m_sport:
                continue

            overvalue = float(m.get("overvalue") or m.get("value") or 0.0)
            if overvalue < min_overvalue_pct or overvalue > max_overvalue_pct:
                continue

            prob = float(m.get("prob") or m.get("probability") or 0.0)

            # Raccogli quote disponibili
            odds_list = m.get("odds") or []
            best_bookie = None
            best_odd = 0.0
            italian_bookies = []

            for b in odds_list:
                b_name = b.get("bookie_name") or b.get("bookie_slug")
                b_slug = str(b.get("bookie_slug") or "").lower()
                b_odd = float(b.get("odd") or 0.0)
                if b_odd > best_odd:
                    best_odd = b_odd
                    best_bookie = b_name

                if any(adm in b_slug for adm in self.ADM_BOOKMAKERS):
                    italian_bookies.append({
                        "name": b_name,
                        "slug": b_slug,
                        "odd": b_odd,
                    })

            signal = OddspediaSignal(
                signal_type="VALUE_BET",
                match_id=int(m.get("id") or m.get("match_key") or 0),
                home_team=str(m.get("ht") or "Home").strip(),
                away_team=str(m.get("at") or "Away").strip(),
                sport=m_sport,
                category=str(m.get("category_name") or "").strip(),
                league=str(m.get("league_name") or "").strip(),
                kickoff_utc=str(m.get("md") or "").strip(),
                market=str(m.get("ot_name") or "Esito Finale").strip(),
                selection=str(m.get("selection") or m.get("title") or "Selezione").strip(),
                fair_probability_pct=round(prob, 1),
                overvalue_pct=round(overvalue, 1),
                current_odd=best_odd,
                best_bookmaker=best_bookie,
                italian_bookmakers=italian_bookies,
                raw_info={"sr_id": m.get("sr_id")},
            )
            signals.append(signal)
            if len(signals) >= limit:
                break

        signals.sort(key=lambda s: (s.overvalue_pct or 0.0), reverse=True)
        return signals

    def export_signals_to_json(
        self,
        signals: List[OddspediaSignal],
        output_file: Optional[Path] = None,
    ) -> Path:
        """Salva i segnali estratti in formato JSON per l'ingestion di BAgent."""
        out = output_file or (REPORTS_DIR / "latest_signals.json")
        out.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "total_signals": len(signals),
            "signals": [s.to_dict() for s in signals],
        }
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Segnali Oddspedia esportati con successo in %s", out)
        return out

    def fetch_match_insights(self, match_url: str) -> Optional[OddspediaMatchInsights]:
        """Apre la pagina del match su Oddspedia ed estrae tutte le note, statistiche e H2H."""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                )
                page = context.new_page()
                page.goto(match_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                page.wait_for_timeout(3000)

                event_state = page.evaluate("""() => {
                    try {
                        if (typeof window.__NUXT__ !== 'undefined' && window.__NUXT__.state) {
                            return window.__NUXT__.state.event || null;
                        }
                    } catch(e) {}
                    return null;
                }""")
                browser.close()

                if not event_state:
                    logger.warning("Impossibile recuperare state.event da %s", match_url)
                    return None

                return self.parse_match_insights_state(event_state)
        except Exception as e:
            logger.error("Errore durante estrazione note match da %s: %s", match_url, e)
            return None

    def parse_match_insights_state(self, event_state: Dict[str, Any]) -> OddspediaMatchInsights:
        """Effettua il parsing puro di note qualitative e statistiche dallo state dell'evento."""
        e = event_state.get("event") or {}
        raw_keys = e.get("match_keys") or []
        statements: List[str] = []
        for k in raw_keys:
            if isinstance(k, dict) and k.get("statement"):
                stmt = str(k["statement"]).strip()
                if stmt:
                    statements.append(stmt)
            elif isinstance(k, str) and k.strip():
                statements.append(k.strip())

        # Estrazione statistiche strutturate sulle scommesse (goals, btts, corners, cards)
        betting_stats_raw = (event_state.get("bettingStats") or {}).get("data") or []
        structured_stats: Dict[str, Any] = {}
        for cat in betting_stats_raw:
            if not isinstance(cat, dict):
                continue
            cat_label = cat.get("label") or "unknown"
            structured_stats[cat_label] = cat.get("data", [])

        # Punteggio ed eventuale live
        hscore = e.get("hscore")
        ascore = e.get("ascore")

        return OddspediaMatchInsights(
            match_id=int(e.get("id") or 0),
            home_team=str(e.get("ht") or "Home").strip(),
            away_team=str(e.get("at") or "Away").strip(),
            home_form=str(e.get("ht_form") or "").replace("?", "").strip(),
            away_form=str(e.get("at_form") or "").replace("?", "").strip(),
            statements=statements,
            betting_stats=structured_stats,
            inplay_status=e.get("inplay_status"),
            current_time=e.get("current_time"),
            home_score=int(hscore) if hscore is not None else None,
            away_score=int(ascore) if ascore is not None else None,
            venue=e.get("venue_name"),
            referee=e.get("referee_name"),
            weather=e.get("weather_conditions"),
        )

    def analyze_match_warnings(self, insights: OddspediaMatchInsights) -> List[str]:
        """Analizza le note e restituisce avvisi precoci su potenziali trappole o segnali."""
        warnings: List[str] = []
        for s in insights.statements:
            s_low = s.lower()
            if "subito gol in ciascuna" in s_low or "ha subito gol" in s_low:
                warnings.append(f"CONCESSION_STREAK: {s}")
            if "vince la partita nel 8" in s_low or "vince la partita nel 9" in s_low:
                warnings.append(f"DOMINANT_CONVERSION: {s}")
            if "non ha mai perso" in s_low or "ha perso solo" in s_low:
                warnings.append(f"H2H_TREND: {s}")
            if "migliore di quella" in s_low:
                warnings.append(f"SUPERIOR_MOMENTUM: {s}")

        # Analisi forma se presente
        if insights.home_form and insights.away_form:
            h_wins = insights.home_form.count("W")
            a_wins = insights.away_form.count("W")
            if a_wins > h_wins + 1:
                warnings.append(
                    f"FORM_ALERT: Squadra ospite in forma migliore ({insights.away_form} vs {insights.home_form})"
                )

        return warnings

    def fetch_hot_bets(self, limit: int = 20) -> List[OddspediaHotBet]:
        """Estrae le 'Hot Bets' (scommesse con serie statistica eccezionale e 74% win rate dichiarato)."""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                )
                page = context.new_page()
                page.goto(self.HOTBETS_URL, wait_until="networkidle", timeout=self.timeout_ms)
                page.wait_for_timeout(2500)

                raw_rows = page.evaluate("""() => {
                    const items = [];
                    const rowEls = document.querySelectorAll('.hot-bets-stats-table-row');
                    rowEls.forEach(r => {
                        const league = r.querySelector('.hot-bets-stats-table-row__header')?.innerText.replace(/\\s+/g, ' ').trim() || '';
                        const market = r.querySelector('.hot-bets-stats-table-row__market-label')?.innerText.replace(/\\s+/g, ' ').trim() || '';
                        const matchInfo = r.querySelector('.hot-bets-stats-table-row__content-match')?.innerText.replace(/\\s+/g, ' ').trim() || '';
                        const playedGames = r.querySelector('.hot-bets-stats-table-row__played-games')?.innerText.replace(/\\s+/g, ' ').trim() || '';
                        const percent = r.querySelector('.hot-bets-stats-table-row__percent')?.innerText.replace(/\\s+/g, ' ').trim() || '';
                        const odd = r.querySelector('.hot-bets-stats-table-row__odd')?.innerText.replace(/\\s+/g, ' ').trim() || '';

                        items.push({
                            league,
                            market,
                            matchInfo,
                            playedGames,
                            percent,
                            odd
                        });
                    });
                    return items;
                }""")
                browser.close()

                return self.parse_hot_bets_rows(raw_rows)[:limit]
        except Exception as e:
            logger.error("Errore durante estrazione Hot Bets: %s", e)
            return []

    def parse_hot_bets_rows(self, raw_rows: List[Dict[str, str]]) -> List[OddspediaHotBet]:
        """Effettua il parsing e la normalizzazione dei record estratti dalla tabella Hot Bets."""
        hot_bets: List[OddspediaHotBet] = []
        for r in raw_rows:
            raw_market = r.get("market") or ""
            # Normalizzazione etichetta mercato
            if "btts" in raw_market.lower():
                clean_market = "Entrambe le Squadre Segnano: Si (GG)"
            elif "total_goals_over" in raw_market.lower():
                clean_market = "Over Gol"
            elif "total_goals_under" in raw_market.lower():
                clean_market = "Under Gol"
            else:
                clean_market = raw_market

            # Estrazione percentuale
            pct_str = (r.get("percent") or "0").replace("%", "").strip()
            try:
                pct = float(pct_str)
            except ValueError:
                pct = 0.0

            # Estrazione quota
            odd_str = (r.get("odd") or "0").strip()
            try:
                odd = float(odd_str)
            except ValueError:
                odd = 0.0

            match_text = r.get("matchInfo") or ""
            league_text = (r.get("league") or "").replace(raw_market, "").strip()

            hot_bets.append(
                OddspediaHotBet(
                    match=match_text,
                    league=league_text,
                    market=clean_market,
                    streak_count=r.get("playedGames") or "",
                    win_percentage=pct,
                    odd=odd,
                )
            )

        # Ordina per percentuale di vittoria decrescente
        hot_bets.sort(key=lambda x: x.win_percentage, reverse=True)
        return hot_bets


