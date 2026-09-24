"""
services/betting/netwin_automator.py — Motore Playwright v2.0 per l'automazione affidabile di Netwin.it.
Esegue la ricerca delle partite, selezione delle quote tramite selettori verificati (.contenitoreSingolaQuota),
compilazione della schedina multipla e generazione istantanea del CODICE DI PRENOTAZIONE A 6 CIFRE.
"""

from __future__ import annotations
import os
import time
import json
import re
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List

from playwright.sync_api import sync_playwright, Page, BrowserContext

from services.betting.netwin_market_parser import (
    NetwinMarketAction,
    UnsupportedNetwinMarket,
    market_tab_labels,
    outcome_search_texts,
    parse_netwin_selection,
)

logger = logging.getLogger("NetwinAutomator")

_SECONDARY_FAMILIES = frozenset({"COMBO", "MULTIGOL", "CORNER", "NEXT_GOAL"})


def _parsed_action(market: str, pick: str) -> Optional[NetwinMarketAction]:
    try:
        return parse_netwin_selection(market, pick)
    except UnsupportedNetwinMarket:
        return None


def _needs_secondary_panel(action: NetwinMarketAction) -> bool:
    return action.family in _SECONDARY_FAMILIES

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RECEIPTS_DIR = ROOT_DIR / "reports" / "receipts"
NETWIN_URL = "https://www.netwin.it/scommesse"

class NetwinAutomator:
    """
    Automatore Playwright per Netwin.it (XSport Engine).
    Genera codici di prenotazione a 6 cifre per caricare istantaneamente multiple e sistemi su Netwin.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self) -> Page:
        """Inizializza il browser Chromium con configurazione stealth."""
        if self.page and not self.page.is_closed():
            return self.page

        logger.info(f"Avvio Browser Chromium Netwin (Headless: {self.headless})...")
        self._playwright = sync_playwright().start()

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        )

        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(ROOT_DIR / "data" / "netwin_profile"),
            headless=self.headless,
            viewport={"width": 1440, "height": 900},
            user_agent=user_agent,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.page.set_default_timeout(20000)
        return self.page

    def close(self):
        """Chiude il browser e pulisce le risorse."""
        try:
            if self._context:
                self._context.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            logger.warning(f"Errore chiusura browser: {e}")
        finally:
            self._context = None
            self._playwright = None
            self.page = None
            logger.info("Browser Netwin chiuso.")

    def open_sportsbook(self) -> bool:
        """Carica la pagina principale di Netwin Scommesse e chiude il banner Cookiebot."""
        self.start()
        try:
            logger.info(f"Caricamento {NETWIN_URL}...")
            self.page.set_viewport_size({"width": 1440, "height": 900})
            self.page.goto(NETWIN_URL, timeout=35000)
            self.page.wait_for_timeout(2500)

            # Chiusura Cookiebot
            self._accept_cookies_if_present()
            return True
        except Exception as e:
            logger.error(f"Errore caricamento Netwin: {e}")
            return False

    def _accept_cookies_if_present(self):
        """Chiude il banner Cookiebot con i selettori verificati."""
        try:
            accept_btn = self.page.locator("button:has-text('Accetta tutti'), #CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
            accept_btn.wait_for(state="visible", timeout=5000)
            accept_btn.click()
            logger.info("✅ Banner Cookiebot chiuso.")
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    def clear_betslip(self) -> bool:
        """Svuota il carrello scommesse da selezioni residue."""
        try:
            svuota_btn = self.page.locator("button:has-text('SVUOTA'), div:has-text('SVUOTA'), .btn:has-text('SVUOTA')").first
            if svuota_btn.is_visible():
                svuota_btn.click()
                logger.info("🗑️ Carrello scommesse svuotato.")
                self.page.wait_for_timeout(800)
                return True
        except Exception:
            pass
        return True

    def search_match(self, team_name: str) -> bool:
        """Cerca un match nella barra di ricerca #match-search-input."""
        try:
            search_input = self.page.locator("#match-search-input").first
            try:
                search_input.wait_for(state="visible", timeout=10000)
            except Exception:
                self._accept_cookies_if_present()
                search_input.wait_for(state="visible", timeout=5000)

            search_input.click()
            search_input.fill("")
            search_input.fill(team_name)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(2500)
            logger.info(f"Ricerca per '{team_name}' inviata.")
            return True
        except Exception as e:
            logger.error(f"Errore ricerca '{team_name}': {e}")
            return False

    def click_match_row(self, team_name: str) -> bool:
        """Clicca sulla riga del match per aprire la vista di lega e mercati."""
        try:
            # Pulisce il nome per il matching
            clean_name = re.sub(r'[^a-zA-Z0-9 ]', '', team_name).strip()
            first_word = clean_name.split()[0] if clean_name.split() else clean_name
            
            match_el = self.page.locator(f":text-matches('{first_word}', 'i')").first
            if match_el.is_visible(timeout=4000):
                match_el.click()
                logger.info(f"Riga match '{first_word}' cliccata per aprire i mercati.")
                self.page.wait_for_timeout(1500)
                return True
        except Exception as e:
            logger.warning(f"Impossibile cliccare riga match '{team_name}': {e}")
        return False

    def select_outcome(self, market: str, pick: str, target_odd: Optional[float] = None) -> bool:
        """
        Seleziona la quota desiderata nella tabella della partita.
        Supporta 1X2, Doppia Chance (1X, X2, 12), Under/Over (2.5, 1.5, 3.5), Gol/NoGol.
        Combo, MultiGol e corner aprono prima il pannello secondario: non stanno nella striscia a 10 colonne.
        """
        try:
            pick_clean = str(pick).strip().upper()
            market_clean = str(market).strip().upper()
            action = _parsed_action(market, pick)

            if action is not None and _needs_secondary_panel(action):
                self._open_market_panel(action)
                if self._click_exact_odd(target_odd, action):
                    logger.info(f"✅ Quota secondaria {action.family} selezionata @{target_odd}.")
                    return True
                logger.warning(f"Pannello {action.family} aperto, quota {target_odd} non trovata per {pick!r}.")
                return False

            # 1. Mercato 1X2
            if pick_clean in ["1", "X", "2"] and ("1X2" in market_clean or "ESITO" in market_clean or market_clean == ""):
                col_index = 0 if pick_clean == "1" else (1 if pick_clean == "X" else 2)
                # I contenitori quota 1X2 sono i primi 3 .contenitoreSingolaQuota della riga
                odds = self.page.locator(".contenitoreSingolaQuota").all()
                if len(odds) >= 3:
                    odds[col_index].click()
                    logger.info(f"✅ Quota 1X2 ({pick_clean}) selezionata con successo.")
                    self.page.wait_for_timeout(800)
                    return True

            # 2. Doppia Chance (1X, 12, X2)
            if pick_clean in ["1X", "12", "X2"] or "DOPPIA CHANCE" in market_clean:
                dc_index = 3 if pick_clean == "1X" else (4 if pick_clean == "12" else 5)
                odds = self.page.locator(".contenitoreSingolaQuota").all()
                if len(odds) >= 6:
                    odds[dc_index].click()
                    logger.info(f"✅ Doppia Chance ({pick_clean}) selezionata con successo.")
                    self.page.wait_for_timeout(800)
                    return True

            # 3. Under / Over
            if "UNDER" in pick_clean or "OVER" in pick_clean:
                is_under = "UNDER" in pick_clean
                uo_target = 6 if is_under else 7  # colonna 6=Under, 7=Over nella vista standard 2.5
                odds = self.page.locator(".contenitoreSingolaQuota").all()
                if len(odds) >= 8:
                    odds[uo_target].click()
                    logger.info(f"✅ Quota Under/Over ({pick_clean}) selezionata con successo.")
                    self.page.wait_for_timeout(800)
                    return True

            # 4. Gol / NoGol
            if "GOL" in pick_clean or "GG" in pick_clean or "NG" in pick_clean:
                is_gol = any(k in pick_clean for k in ["GOL", "GG", "SI", "YES"]) and "NO" not in pick_clean
                gng_target = 8 if is_gol else 9
                odds = self.page.locator(".contenitoreSingolaQuota").all()
                if len(odds) >= 10:
                    odds[gng_target].click()
                    logger.info(f"✅ Quota Gol/NoGol ({pick_clean}) selezionata con successo.")
                    self.page.wait_for_timeout(800)
                    return True

            # 5. Fallback: cerca per valore di quota se fornito
            if self._click_exact_odd(target_odd):
                logger.info(f"✅ Quota trovata per valore esatto @{float(target_odd):.2f}.")
                return True

        except Exception as e:
            logger.error(f"Errore selezione esito {market} - {pick}: {e}")

        return False

    def _open_market_panel(self, action: NetwinMarketAction) -> bool:
        """Apre il tab Combo, MultiGol o Angoli. Senza pagina non alza eccezioni."""
        if self.page is None:
            return False
        for label in market_tab_labels(action):
            if self._click_tab(re.escape(label)):
                return True
        if action.family == "CORNER":
            pattern = "ANGOLI|CORNER|COMBO"
        elif action.family == "NEXT_GOAL":
            pattern = "PROSSIMO GOL|NEXT GOAL"
        elif action.family == "MULTIGOL" or action.combo_type == "MULTIGOL":
            pattern = "MULTIGOL|COMBO"
        else:
            pattern = "COMBO|MULTIGOL|ANGOLI"
        return self._click_tab(pattern)

    def _click_tab(self, pattern: str) -> bool:
        if self.page is None:
            return False
        try:
            tab = self.page.locator(f":text-matches('{pattern}', 'i')").first
            if tab.is_visible(timeout=1200):
                tab.click()
                self.page.wait_for_timeout(600)
                return True
        except Exception as exc:
            logger.warning(f"Tab Netwin '{pattern}' non aperto: {exc}")
        return False

    def _click_exact_odd(self, target_odd: Optional[float], action: Optional[NetwinMarketAction] = None) -> bool:
        """Clicca il .contenitoreSingolaQuota della quota verificata, preferendo la riga del mercato."""
        if self.page is None or not target_odd or float(target_odd) <= 1.0:
            return False
        odd_str = f"{float(target_odd):.2f}"
        hints = [hint.lower() for hint in outcome_search_texts(action)] if action is not None else []
        buttons = self.page.locator(".contenitoreSingolaQuota")
        try:
            count = buttons.count()
        except Exception:
            count = 0
        fallback = None
        for index in range(count):
            button = buttons.nth(index)
            try:
                blob = button.inner_text()
            except Exception:
                continue
            if odd_str not in blob:
                continue
            if fallback is None:
                fallback = button
            if hints and any(hint in blob.lower() for hint in hints):
                button.click()
                self.page.wait_for_timeout(800)
                return True
        if fallback is not None:
            try:
                if fallback.is_visible(timeout=1500):
                    fallback.click()
                    self.page.wait_for_timeout(800)
                    return True
            except Exception:
                pass
        try:
            odd_el = self.page.locator(f".contenitoreSingolaQuota:has-text('{odd_str}')").first
            if odd_el.is_visible(timeout=1500):
                odd_el.click()
                self.page.wait_for_timeout(800)
                return True
        except Exception as exc:
            logger.warning(f"Quota @{odd_str} non cliccabile: {exc}")
        return False

    def add_match_selection(self, match_info: Dict[str, Any]) -> bool:
        """Esegue l'intero ciclo di ricerca e inserimento per una singola selezione."""
        home_team = match_info.get("home", "") or match_info.get("match", "").split(" vs ")[0]
        market = match_info.get("market", "1X2")
        pick = match_info.get("pick", "1")
        odd = match_info.get("netwin_odds") or match_info.get("real_odd")

        logger.info(f"Inserimento: {home_team} | Mercato: {market} | Esito: {pick} (@{odd})")

        if not self.search_match(home_team):
            return False

        self.click_match_row(home_team)

        success = self.select_outcome(market=market, pick=pick, target_odd=odd)
        return success

    def generate_booking_code(self, stake: float = 25.0) -> Dict[str, Any]:
        """
        Clicca su PRENOTA e cattura il Codice Prenotazione a 6 cifre dal box 'Prenotazioni effettuate'.
        """
        res = {"success": False, "booking_code": None, "error": None}
        try:
            # Imposta stake se l'input è visibile
            try:
                stake_input = self.page.locator("input[placeholder*='Importo'], input.stake-input, .cart-bets-total-stake input").first
                if stake_input.is_visible(timeout=1500):
                    stake_input.click()
                    stake_input.fill(f"{stake:.2f}")
                    self.page.keyboard.press("Tab")
                    self.page.wait_for_timeout(500)
            except Exception:
                pass

            prenota_btn = self.page.locator("button:has-text('PRENOTA')").first
            if not prenota_btn.is_visible(timeout=4000):
                res["error"] = "Pulsante PRENOTA non trovato nel carrello."
                return res

            prenota_btn.click()
            logger.info("Pulsante PRENOTA cliccato. Attesa generazione codice...")
            self.page.wait_for_timeout(2500)

            # Estrazione del codice dal box prenotazioni
            prenotazione_box = self.page.locator(":text-matches('Prenotazioni effettuate', 'i')").first
            if prenotazione_box.is_visible(timeout=5000):
                box_text = prenotazione_box.locator("xpath=..").inner_text()
                match = re.search(r'\b(\d{6})\b', box_text)
                if match:
                    code = match.group(1)
                    res["success"] = True
                    res["booking_code"] = code
                    logger.info(f"🎯 CODICE PRENOTAZIONE NETWIN GENERATO: {code}")

                    # Salva ricevuta JSON
                    log_file = RECEIPTS_DIR / f"netwin_booking_{code}.json"
                    with open(log_file, "w", encoding="utf-8") as f:
                        json.dump({
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "booking_code": code,
                            "stake": stake
                        }, f, indent=4)
                    return res

            # Fallback ricerca regex su tutta la pagina
            all_text = self.page.inner_text("body")
            matches = re.findall(r'\b(\d{6})\b', all_text)
            if matches:
                # Prende l'ultimo codice a 6 cifre apparso
                code = matches[-1]
                res["success"] = True
                res["booking_code"] = code
                logger.info(f"🎯 Codice trovato via fallback: {code}")
                return res

            res["error"] = "Codice a 6 cifre non rilevato dopo il click su PRENOTA."
        except Exception as e:
            res["error"] = str(e)
            logger.error(f"Eccezione durante generazione codice prenotazione: {e}")

        return res

    def build_ticket_and_book(self, selections: List[Dict[str, Any]], stake: float = 25.0) -> Dict[str, Any]:
        """
        Flusso completo:
        1. Apre Netwin
        2. Svuota il carrello
        3. Inserisce tutte le selezioni
        4. Clicca PRENOTA
        5. Restituisce il codice a 6 cifre
        """
        logger.info(f"Avvio compilazione multipla Netwin ({len(selections)} eventi)...")
        if not self.open_sportsbook():
            return {"success": False, "error": "Impossibile aprire il portale Netwin."}

        self.clear_betslip()

        added = 0
        for s in selections:
            ok = self.add_match_selection(s)
            if ok:
                added += 1
            self.page.wait_for_timeout(1000)

        logger.info(f"Eventi aggiunti al carrello: {added}/{len(selections)}")
        if added == 0:
            self.close()
            return {"success": False, "error": "Nessun evento aggiunto al carrello."}

        # Genera codice prenotazione
        book_res = self.generate_booking_code(stake=stake)
        book_res["events_added"] = added
        book_res["total_events"] = len(selections)
        book_res["stake"] = stake

        self.close()
        return book_res
