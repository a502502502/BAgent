"""
Netwin Sportsbook Automator (Playwright Engine)
Gestisce l'automazione del carrello, selezione quote, prenotazione e piazzamento
di Multiple e Sistemi sul portale Netwin.it
"""

from __future__ import annotations
import os
import time
import json
import logging
from pathlib import Path
from typing import Optional, Any
from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

# Path di base
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SESSION_DIR = ROOT_DIR / "data" / "netwin_session"
RECEIPTS_DIR = ROOT_DIR / "reports" / "receipts"

# URL Ufficiali Netwin
NETWIN_BASE_URL = "https://www.netwin.it"
NETWIN_SPORT_URL = "https://www.netwin.it/sport"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NetwinAutomator")


class NetwinAutomator:
    """
    Automatore Playwright per Netwin.it
    Supporta:
    - Sessione persistente (salvataggio cookie e login)
    - Ricerca eventi e selezione quote (1X2, Over/Under, Doppia Chance, Combo)
    - Modalità Multipla & Sistemi a correzione d'errore
    - Generazione Codice di Prenotazione (senza spesa)
    - Piazzamento scommessa reale con cattura screenshot ricevuta AAMS
    """

    def __init__(self, headless: bool = True, session_path: Optional[Path] = None):
        self.headless = headless
        self.session_path = session_path or SESSION_DIR
        self.session_path.mkdir(parents=True, exist_ok=True)
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self) -> Page:
        """Inizializza il browser con contesto persistente per mantenere i cookie di sessione."""
        if self.page and not self.page.is_closed():
            return self.page

        logger.info(f"Avvio Browser Netwin (Headless: {self.headless}) con profilo: {self.session_path}")
        self._playwright = sync_playwright().start()
        
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        )

        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
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
        self.page.set_default_timeout(25000)
        return self.page

    def close(self):
        """Chiude il browser e salva lo stato di sessione."""
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
        """Naviga alla sezione sportiva di Netwin."""
        self.start()
        try:
            logger.info(f"Caricamento {NETWIN_SPORT_URL}...")
            self.page.goto(NETWIN_SPORT_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            self._accept_cookies_if_present()
            return True
        except Exception as e:
            logger.error(f"Errore caricamento Netwin Sport: {e}")
            return False

    def _accept_cookies_if_present(self):
        """Chiude eventuali banner cookie o popup iniziali."""
        cookie_selectors = [
            "button#onetrust-accept-btn-handler",
            "button:has-text('Accetta tutti')",
            "button:has-text('Accetta')",
            "button:has-text('OK')",
            ".cookie-accept-btn",
        ]
        for sel in cookie_selectors:
            try:
                if self.page.locator(sel).is_visible(timeout=1500):
                    self.page.locator(sel).click()
                    logger.info("Banner cookie accettato.")
                    time.sleep(0.5)
                    break
            except Exception:
                continue

    def is_logged_in(self) -> bool:
        """Verifica se la sessione utente è autenticata."""
        self.start()
        try:
            # Verifica presenza saldo o nome utente vs pulsante Login
            saldo_visible = self.page.locator(":text-matches('Saldo|Disponibile|€', 'i')").count() > 0
            login_btn_visible = self.page.locator("button:has-text('Accedi'), a:has-text('Accedi'), button:has-text('Login')").is_visible(timeout=2000)
            return saldo_visible and not login_btn_visible
        except Exception:
            return False

    def clear_betslip(self) -> bool:
        """Svuota il carrello scommesse da eventuali selezioni pregresse."""
        try:
            trash_selectors = [
                "button[title*='Svuota']",
                "button:has-text('Svuota')",
                ".clear-cart-btn",
                "i.fa-trash",
                "button:has-text('Cancella tutto')",
            ]
            for sel in trash_selectors:
                if self.page.locator(sel).is_visible(timeout=1000):
                    self.page.locator(sel).click()
                    logger.info("Carrello scommesse svuotato.")
                    time.sleep(0.5)
                    return True
        except Exception as e:
            logger.debug(f"Nessun carrello da svuotare: {e}")
        return True

    def search_and_add_selection(self, team_name: str, market_type: str, outcome_target: str) -> bool:
        """
        Cerca una partita per nome squadra e seleziona la quota corrispondente.
        
        market_type: '1X2', 'UNDER_OVER', 'DOPPIA_CHANCE', 'COMBO', 'CORNER'
        outcome_target: es. '1', '2', 'X', 'Over 1.5', '1X', '1 + Over 1.5'
        """
        logger.info(f"Ricerca evento: '{team_name}' | Mercato: {market_type} | Esito: {outcome_target}")
        try:
            # 1. Utilizzo barra di ricerca globale se presente
            search_input = self.page.locator("input[placeholder*='Cerca'], input[type='search'], .search-box input").first
            if search_input.is_visible(timeout=2000):
                search_input.fill("")
                search_input.type(team_name.split()[0], delay=50)
                search_input.press("Enter")
                time.sleep(1.5)

            # 2. Localizzazione riga evento
            event_row = self.page.locator(f":text-matches('{team_name}', 'i')").first
            if not event_row.is_visible(timeout=3000):
                logger.warning(f"Evento non trovato per keyword '{team_name}'")
                return False

            # Clicca sull'evento per aprire tutti i mercati
            event_row.click()
            time.sleep(1)

            # 3. Selezione quota desiderata
            # Cerca il pulsante quota corrispondente all'esito
            odds_button = self.page.locator(
                f"button:has-text('{outcome_target}'), div[role='button']:has-text('{outcome_target}')"
            ).first

            if odds_button.is_visible(timeout=3000):
                odds_button.click()
                logger.info(f"✅ Quota aggiunta al carrello: {outcome_target}")
                time.sleep(0.5)
                return True
            else:
                logger.warning(f"Bottone quota '{outcome_target}' non individuato direttamente.")
                return False

        except Exception as e:
            logger.error(f"Errore selezione {team_name} - {outcome_target}: {e}")
            return False

    def build_ticket(
        self,
        selections: list[dict],
        bet_mode: str = "MULTIPLE",
        stake: float = 20.0,
    ) -> dict[str, Any]:
        """
        Popola l'intero ticket con le selezioni fornite e configura stake e modalità.
        
        selections format:
        [
            {"match": "Inter", "market": "DOPPIA_CHANCE_OU", "pick": "1X + Over 1.5"},
            {"match": "Real Madrid", "market": "1X2", "pick": "2"}
        ]
        """
        self.open_sportsbook()
        self.clear_betslip()

        added_count = 0
        for item in selections:
            success = self.search_and_add_selection(
                team_name=item["match"],
                market_type=item.get("market", "1X2"),
                outcome_target=item["pick"],
            )
            if success:
                added_count += 1
            time.sleep(0.5)

        logger.info(f"Selezioni aggiunte con successo: {added_count}/{len(selections)}")

        # Configura tipo scommessa (Multipla o Sistema)
        self._configure_betslip_mode(bet_mode=bet_mode, stake=stake)

        # Leggi riepilogo carrello
        summary = self.get_betslip_summary()
        summary["selections_added"] = added_count
        summary["total_requested"] = len(selections)
        return summary

    def _configure_betslip_mode(self, bet_mode: str, stake: float):
        """Seleziona il tab Multipla/Sistema e imposta l'importo di puntata."""
        try:
            if bet_mode.upper() == "SISTEMA":
                sys_tab = self.page.locator("button:has-text('Sistema'), a:has-text('Sistema')").first
                if sys_tab.is_visible(timeout=2000):
                    sys_tab.click()
            else:
                mult_tab = self.page.locator("button:has-text('Multipla'), a:has-text('Multipla')").first
                if mult_tab.is_visible(timeout=2000):
                    mult_tab.click()

            time.sleep(0.5)

            # Inserisci Stake
            stake_input = self.page.locator("input[placeholder*='Importo'], input.stake-input, input[name='stake']").first
            if stake_input.is_visible(timeout=2000):
                stake_input.fill("")
                stake_input.fill(str(stake))
                stake_input.press("Tab")
                logger.info(f"Stake impostato a: {stake:.2f} €")
        except Exception as e:
            logger.warning(f"Errore configurazione modalità carrello: {e}")

    def get_betslip_summary(self) -> dict[str, Any]:
        """Estrae quota totale, bonus moltiplicatore e vincita potenziale dal carrello."""
        summary = {
            "total_odds": "1.00",
            "potential_win": "0.00 €",
            "bonus": "0.00 €",
            "is_valid": False,
        }
        try:
            # Estrazione testi carrello
            betslip_el = self.page.locator(".betslip, #betslip, div[class*='cart']").first
            if betslip_el.is_visible(timeout=2000):
                txt = betslip_el.inner_text()
                summary["raw_text"] = txt
                summary["is_valid"] = True
                logger.info("Riepilogo carrello letto con successo.")
        except Exception as e:
            logger.debug(f"Errore lettura carrello: {e}")
        return summary

    def generate_booking_code(self) -> dict[str, Any]:
        """Clicca su 'Prenota' e recupera il codice di prenotazione Netwin."""
        logger.info("Richiesta generazione Codice Prenotazione...")
        res = {"success": False, "booking_code": "", "error": None}
        try:
            book_btn = self.page.locator("button:has-text('Prenota'), a:has-text('Prenota'), button:has-text('Prenotazione')").first
            if book_btn.is_visible(timeout=3000):
                book_btn.click()
                time.sleep(2)

                # Estrazione codice generato nel modal
                code_el = self.page.locator(".booking-code, span[class*='code'], h3:has-text('Codice')").first
                if code_el.is_visible(timeout=4000):
                    code = code_el.inner_text().strip()
                    res["success"] = True
                    res["booking_code"] = code
                    logger.info(f"🎯 CODICE PRENOTAZIONE GENERATO: {code}")
                    return res
            
            res["error"] = "Pulsante Prenota non disponibile o carrello vuoto."
        except Exception as e:
            res["error"] = str(e)
            logger.error(f"Errore prenotazione: {e}")
        return res

    def place_bet(self) -> dict[str, Any]:
        """
        Conferma e piazza la scommessa reale su Netwin.
        Cattura e salva lo screenshot della ricevuta AAMS.
        """
        logger.info("🚀 ESECUZIONE PIAZZAMENTO SCOMMESSA SU NETWIN...")
        res = {
            "success": False,
            "receipt_id": None,
            "screenshot_path": None,
            "error": None,
        }

        try:
            bet_btn = self.page.locator("button:has-text('Scommetti'), button:has-text('Piazza scommessa'), button.bet-button").first
            if not bet_btn.is_visible(timeout=3000):
                res["error"] = "Pulsante 'Scommetti' non visibile (probabile sessione non attiva o carrello non valido)."
                return res

            bet_btn.click()
            time.sleep(2.5)

            # Conferma eventuale modal secondario di conferma
            confirm_modal = self.page.locator("button:has-text('Conferma'), button:has-text('Continua')").first
            if confirm_modal.is_visible(timeout=2000):
                confirm_modal.click()
                time.sleep(2)

            # Salva screenshot ricevuta
            ts = int(time.time())
            screenshot_file = RECEIPTS_DIR / f"receipt_{ts}.png"
            self.page.screenshot(path=str(screenshot_file))
            res["screenshot_path"] = str(screenshot_file)

            # Verifica se la scommessa è stata accettata
            receipt_el = self.page.locator(":text-matches('Scommessa accettata|Ricevuta|Codice AAMS', 'i')").first
            if receipt_el.is_visible(timeout=5000):
                res["success"] = True
                res["receipt_id"] = f"NW-{ts}"
                logger.info(f"✅ SCOMMESSA ACCETTATA CON SUCCESSO! Ricevuta salvata in: {screenshot_file}")
            else:
                res["error"] = "Scommessa inviata, in attesa di conferma o quota variata."

        except Exception as e:
            res["error"] = str(e)
            logger.error(f"Errore piazzamento scommessa: {e}")

        return res
