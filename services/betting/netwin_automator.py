"""
Playwright automator for Netwin.it booking codes (6 digits).
Does not place real-money bets: PRENOTA only.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional

from playwright.sync_api import BrowserContext, Page, sync_playwright

from config.settings import NETWIN_RECEIPTS_DIR, NETWIN_SESSION_DIR, NETWIN_URL
from services.betting.netwin_market_parser import (
    UnsupportedNetwinMarket,
    extract_booking_code,
    is_real_netwin_booking_code,
    market_tab_labels,
    outcome_search_texts,
    parse_netwin_selection,
    row_matches_teams,
    split_home_away,
)

logger = logging.getLogger("NetwinAutomator")

RECEIPTS_DIR = NETWIN_RECEIPTS_DIR
_PROFILE_LOCK = threading.Lock()


class NetwinAutomator:
    """Fill a Netwin betslip and emit a 6-digit booking code."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
        NETWIN_SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self) -> Page:
        if self.page and not self.page.is_closed():
            return self.page

        logger.info("Avvio Chromium Netwin (headless=%s)...", self.headless)
        self._playwright = sync_playwright().start()
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        )
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(NETWIN_SESSION_DIR),
            headless=self.headless,
            viewport={"width": 1440, "height": 900},
            user_agent=user_agent,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.page.set_default_timeout(20000)
        return self.page

    def close(self):
        try:
            if self._context:
                self._context.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as exc:
            logger.warning("Errore chiusura browser: %s", exc)
        finally:
            self._context = None
            self._playwright = None
            self.page = None

    def _screenshot(self, name: str) -> Optional[str]:
        if not self.page:
            return None
        path = RECEIPTS_DIR / f"{name}_{int(time.time())}.png"
        try:
            self.page.screenshot(path=str(path), full_page=False)
            return str(path)
        except Exception as exc:
            logger.warning("Screenshot fallito: %s", exc)
            return None

    def open_sportsbook(self) -> bool:
        self.start()
        try:
            self.page.goto(NETWIN_URL, timeout=35000)
            self.page.wait_for_timeout(2500)
            self._accept_cookies_if_present()
            return True
        except Exception as exc:
            logger.error("Errore caricamento Netwin: %s", exc)
            self._screenshot("netwin_open_fail")
            return False

    def _accept_cookies_if_present(self):
        try:
            accept_btn = self.page.locator(
                "button:has-text('Accetta tutti'), "
                "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
            ).first
            if accept_btn.is_visible(timeout=4000):
                accept_btn.click()
                self.page.wait_for_timeout(800)
        except Exception:
            pass

    def clear_betslip(self) -> bool:
        try:
            svuota_btn = self.page.locator(
                "button:has-text('SVUOTA'), .btn:has-text('SVUOTA')"
            ).first
            if svuota_btn.is_visible(timeout=2000):
                svuota_btn.click()
                self.page.wait_for_timeout(800)
        except Exception:
            pass
        return True

    def search_match(self, query: str) -> bool:
        try:
            search_input = self.page.locator("#match-search-input").first
            if not search_input.is_visible(timeout=5000):
                logger.error("Campo #match-search-input non visibile.")
                return False
            search_input.click()
            search_input.fill("")
            search_input.fill(query)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(2200)
            return True
        except Exception as exc:
            logger.error("Errore ricerca '%s': %s", query, exc)
            return False

    def click_match_row(self, home: str, away: str = "") -> bool:
        try:
            rows = self.page.locator(
                "[class*='evento'], [class*='match'], [class*='Evento'], "
                "div:has(> .contenitoreSingolaQuota)"
            )
            count = min(rows.count(), 25)
            for i in range(count):
                row = rows.nth(i)
                try:
                    text = row.inner_text(timeout=800)
                except Exception:
                    continue
                if row_matches_teams(text, home, away):
                    row.click()
                    self.page.wait_for_timeout(1200)
                    return True
            # Fallback: both names visible on page, click the home token
            blob = self.page.inner_text("body")
            if away and row_matches_teams(blob, home, away):
                token = (home.split() or [home])[0]
                loc = self.page.get_by_text(re.compile(re.escape(token), re.I)).first
                if loc.is_visible(timeout=2500):
                    loc.click()
                    self.page.wait_for_timeout(1200)
                    return True
        except Exception as exc:
            logger.warning("Click riga match fallito (%s vs %s): %s", home, away, exc)
        return False

    def _open_market_tab(self, labels: List[str]) -> bool:
        for label in labels:
            loc = self.page.locator(f"text={label}").first
            try:
                if loc.is_visible(timeout=1200):
                    loc.click()
                    self.page.wait_for_timeout(700)
                    return True
            except Exception:
                continue
        return False

    def _click_texts(self, texts: List[str]) -> bool:
        for text in texts:
            loc = self.page.locator(f".contenitoreSingolaQuota:has-text('{text}')").first
            try:
                if loc.is_visible(timeout=1200):
                    loc.click()
                    self.page.wait_for_timeout(700)
                    return True
            except Exception:
                continue
        return False

    def select_outcome(self, market: str, pick: str, target_odd: Optional[float] = None) -> bool:
        try:
            try:
                action = parse_netwin_selection(market, pick)
            except UnsupportedNetwinMarket as exc:
                logger.warning("%s", exc)
                action = None

            if action is not None:
                tabs = market_tab_labels(action)
                if tabs:
                    self._open_market_tab(tabs)

                col_index = action.column_hint()
                if col_index is not None:
                    odds = self.page.locator(".contenitoreSingolaQuota").all()
                    if len(odds) > col_index:
                        odds[col_index].click()
                        logger.info("Quota %s (%s) colonna %s", action.family, action.pick, col_index)
                        self.page.wait_for_timeout(700)
                        return True

                if self._click_texts(outcome_search_texts(action)):
                    logger.info("Quota %s cliccata per etichetta", action.family)
                    return True

            if target_odd and target_odd > 1.0:
                odd_str = f"{target_odd:.2f}"
                odd_el = self.page.locator(f".contenitoreSingolaQuota:has-text('{odd_str}')").first
                if odd_el.is_visible(timeout=2000):
                    odd_el.click()
                    self.page.wait_for_timeout(700)
                    return True
        except Exception as exc:
            logger.error("Errore selezione %s / %s: %s", market, pick, exc)
        return False

    def add_match_selection(self, match_info: Dict[str, Any]) -> bool:
        home, away = split_home_away(match_info)
        market = match_info.get("market", "1X2")
        pick = match_info.get("pick", "1")
        odd = match_info.get("netwin_odds") or match_info.get("real_odd")
        query = home or str(match_info.get("match") or "")
        logger.info("Inserimento: %s vs %s | %s | %s (@%s)", home, away, market, pick, odd)

        if not query or not self.search_match(query):
            return False
        if not self.click_match_row(home, away):
            self._screenshot("netwin_match_miss")
            return False
        ok = self.select_outcome(market=market, pick=pick, target_odd=odd)
        if not ok:
            self._screenshot("netwin_odd_miss")
        return ok

    def generate_booking_code(self, stake: float = 25.0) -> Dict[str, Any]:
        res: Dict[str, Any] = {"success": False, "booking_code": None, "error": None}
        try:
            try:
                stake_input = self.page.locator(
                    "input[placeholder*='Importo'], input.stake-input, "
                    ".cart-bets-total-stake input"
                ).first
                if stake_input.is_visible(timeout=1500):
                    stake_input.click()
                    stake_input.fill(f"{stake:.2f}")
                    self.page.keyboard.press("Tab")
                    self.page.wait_for_timeout(400)
            except Exception:
                pass

            prenota_btn = self.page.locator("button:has-text('PRENOTA')").first
            if not prenota_btn.is_visible(timeout=4000):
                res["error"] = "Pulsante PRENOTA non trovato nel carrello."
                self._screenshot("netwin_prenota_missing")
                return res

            prenota_btn.click()
            self.page.wait_for_timeout(2500)

            boxes = self.page.locator(
                ":text-matches('Prenotazioni effettuate', 'i'), "
                ":text-matches('Codice prenotazione', 'i'), "
                "div:has-text('Prenotazione')"
            )
            snippets: List[str] = []
            n = min(boxes.count(), 8)
            for i in range(n):
                try:
                    snippets.append(boxes.nth(i).inner_text(timeout=1500))
                except Exception:
                    continue
                parent = boxes.nth(i).locator("xpath=..")
                try:
                    snippets.append(parent.inner_text(timeout=1500))
                except Exception:
                    pass

            for snippet in snippets:
                code = extract_booking_code(snippet)
                if is_real_netwin_booking_code(code):
                    res["success"] = True
                    res["booking_code"] = code
                    log_file = RECEIPTS_DIR / f"netwin_booking_{code}.json"
                    log_file.write_text(
                        json.dumps(
                            {
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "booking_code": code,
                                "stake": stake,
                            },
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                    logger.info("Codice prenotazione Netwin: %s", code)
                    return res

            res["error"] = "Codice a 6 cifre non rilevato nel box prenotazioni."
            self._screenshot("netwin_code_missing")
        except Exception as exc:
            res["error"] = str(exc)
            self._screenshot("netwin_book_exception")
        return res

    def build_ticket(
        self,
        selections: List[Dict[str, Any]],
        bet_mode: str = "MULTIPLE",
        stake: float = 25.0,
    ) -> Dict[str, Any]:
        """Fill the cart only. Does not PRENOTA and does not stake money."""
        del bet_mode, stake
        failed: List[str] = []
        added = 0
        for sel in selections:
            if self.add_match_selection(sel):
                added += 1
            else:
                home, away = split_home_away(sel)
                failed.append(f"{home} vs {away}" if away else home)
            self.page.wait_for_timeout(800)
        return {
            "success": added == len(selections) and added > 0,
            "events_added": added,
            "total_events": len(selections),
            "failed": failed,
        }

    def place_bet(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Piazzamento soldi disabilitato. Usa PRENOTA / codice a 6 cifre.",
        }

    def build_ticket_and_book(
        self, selections: List[Dict[str, Any]], stake: float = 25.0
    ) -> Dict[str, Any]:
        logger.info("Compilazione multipla Netwin (%s eventi)", len(selections))
        with _PROFILE_LOCK:
            if not self.open_sportsbook():
                return {"success": False, "error": "Impossibile aprire il portale Netwin."}
            try:
                self.clear_betslip()
                summary = self.build_ticket(selections=selections, stake=stake)
                added = int(summary["events_added"])
                total = int(summary["total_events"])
                if added != total:
                    self._screenshot("netwin_incomplete_slip")
                    return {
                        "success": False,
                        "error": (
                            f"Carrello incompleto: {added}/{total}. "
                            f"Mancano: {', '.join(summary.get('failed') or [])}"
                        ),
                        "events_added": added,
                        "total_events": total,
                        "failed": summary.get("failed"),
                        "stake": stake,
                    }
                book_res = self.generate_booking_code(stake=stake)
                book_res["events_added"] = added
                book_res["total_events"] = total
                book_res["stake"] = stake
                return book_res
            finally:
                self.close()
