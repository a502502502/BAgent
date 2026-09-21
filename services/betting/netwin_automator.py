"""
Netwin Sportsbook Automator (Playwright Engine)
Gestisce l'automazione del carrello, selezione quote, prenotazione e piazzamento
di Multiple e Sistemi sul portale Netwin.it, con integrazione Kelly Criterion e gestione variazioni quota.
"""

from __future__ import annotations
import os
import time
import json
import re
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List

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
    Automatore Playwright per Netwin.it con gestione dinamica dello stake (Kelly) 
    e resilienza ai popup di variazione quota.
    """

    def __init__(
        self, 
        headless: bool = True, 
        session_path: Optional[Path] = None,
        sharp_sentinel: Optional[Any] = None,  # Istanza di SharpMarketSentinel
        bankroll: float = 1000.0,
        kelly_fraction: float = 0.5,
        max_stake_pct: float = 5.0
    ):
        self.headless = headless
        self.session_path = session_path or SESSION_DIR
        self.session_path.mkdir(parents=True, exist_ok=True)
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

        self.sharp_sentinel = sharp_sentinel
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.max_stake_pct = max_stake_pct
        self.MIN_AAMS_STAKE = 2.00  # Limite minimo legale Netwin/AAMS

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
                "--disable-features=IsolateOrigins,site-per-process"
            ],
        )

        self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.page.set_default_timeout(15000)
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
            time.sleep(1.5)
            self._accept_cookies_if_present()
            return True
        except Exception as e:
            logger.error(f"Errore caricamento Netwin Sport: {e}")
            return False

    def _accept_cookies_if_present(self):
        """Chiude eventuali banner cookie o popup iniziali."""
        cookie_selectors = [
            "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
            "button#onetrust-accept-btn-handler",
            "button:has-text('Accetta tutti')",
            "button:has-text('Accetta')",
        ]
        for sel in cookie_selectors:
            try:
                locator = self.page.locator(sel).first
                if locator.is_visible(timeout=2000):
                    locator.click()
                    logger.info("✅ Banner cookie accettato.")
                    time.sleep(0.5)
                    break
            except Exception:
                continue

    def _handle_odds_change_modal(self) -> bool:
        """
        Gestisce il popup 'La quota è cambiata, vuoi accettare la nuova quota?'.
        Restituisce True se il popup è stato gestito, False altrimenti.
        """
        try:
            accept_btn = self.page.locator("button:has-text('Accetta'), button:has-text('Conferma'), .btn-accept-odds").first
            if accept_btn.is_visible(timeout=2000):
                logger.warning("⚠️ Rilevata variazione di quota. Accettazione automatica in corso...")
                accept_btn.click()
                time.sleep(1.0)
                return True
        except Exception:
            pass
        return False

    def is_logged_in(self) -> bool:
        """Verifica se la sessione utente è autenticata."""
        self.start()
        try:
            saldo_visible = self.page.locator(":text-matches('Saldo|Disponibile|€', 'i')").count() > 0
            login_btn_visible = self.page.locator("button:has-text('Accedi'), a:has-text('Accedi')").first.is_visible(timeout=2000)
            return saldo_visible and not login_btn_visible
        except Exception:
            return False

    def clear_betslip(self) -> bool:
        """Svuota il carrello scommesse da eventuali selezioni pregresse."""
        try:
            trash_selectors = [
                "button[title*='Svuota']",
                "button:has-text('Svuota')",
                "button:has-text('Cancella tutto')",
                ".clear-cart-btn",
                "i.fa-trash"
            ]
            for sel in trash_selectors:
                locator = self.page.locator(sel).first
                if locator.is_visible(timeout=1500):
                    locator.click()
                    logger.info("🗑️ Carrello scommesse svuotato.")
                    time.sleep(0.5)
                    return True
        except Exception as e:
            logger.debug(f"Nessun carrello da svuotare o già vuoto: {e}")
        return True

    def search_and_add_selection(self, team_name: str, market_type: str, outcome_target: str, alias: Optional[str] = None) -> bool:
        """
        Cerca una partita per nome squadra o Alias FastBet e seleziona la quota corrispondente.
        """
        logger.info(f"Ricerca evento: '{team_name}' (Alias: {alias}) | Mercato: {market_type} | Esito: {outcome_target}")
        try:
            # 1. Utilizzo FastBet Alias se fornito (metodo rapido e affidabile)
            if alias:
                alias_input = self.page.locator("#fastbet-cart-event, input[placeholder*='Codice'], input.fastbet-input").first
                if alias_input.is_visible(timeout=3000):
                    alias_input.click()
                    alias_input.fill(alias)
                    alias_input.press("Enter")
                    time.sleep(1.5)
                    logger.info(f"Ricerca tramite Alias {alias} eseguita.")
                else:
                    logger.warning("Input FastBet non trovato, fallback alla ricerca testuale.")
            
            # 2. Fallback: Barra di ricerca globale testuale
            if not alias or not self.page.locator(".event-row-selected").count() > 0:
                search_input = self.page.locator("#match-search-input, input[placeholder*='Cerca'], input[type='search']").first
                if search_input.is_visible(timeout=3000):
                    search_input.click()
                    search_input.fill("")
                    search_input.type(team_name, delay=50)
                    search_input.press("Enter")
                    time.sleep(1.5)

            # 3. Localizzazione riga evento e apertura mercati
            event_row = self.page.locator(f"div:has-text('{team_name}')").first
            if event_row.is_visible(timeout=4000):
                event_row.click()
                time.sleep(0.8)

            # 4. Selezione quota desiderata
            odds_button = self.page.locator(
                f"button:has-text('{outcome_target}'), div[role='button']:has-text('{outcome_target}'), .odd-btn:has-text('{outcome_target}')"
            ).first

            if odds_button.is_visible(timeout=3000):
                odds_button.click()
                logger.info(f"✅ Quota aggiunta al carrello: {outcome_target}")
                self._handle_odds_change_modal()
                time.sleep(0.5)
                return True
            else:
                logger.warning(f"❌ Bottone quota '{outcome_target}' non individuato.")
                return False

        except Exception as e:
            logger.error(f"Errore selezione {team_name} - {outcome_target}: {e}")
            return False

    def _calculate_optimal_stake(self, selections: List[Dict[str, Any]]) -> float:
        """
        Calcola lo stake ottimale usando il Kelly Criterion se il Sharp Sentinel è disponibile.
        Altrimenti, restituisce uno stake di fallback o quello medio delle selezioni.
        """
        if not self.sharp_sentinel:
            logger.warning("Sharp Sentinel non fornito. Uso stake di fallback o medio.")
            stakes = [s.get("stake", 10.0) for s in selections]
            return max(self.MIN_AAMS_STAKE, sum(stakes) / len(stakes))

        total_edge = 0.0
        count = 0
        
        for item in selections:
            netwin_q = item.get("netwin_odds")
            fair_q = item.get("fair_sharp_odds")
            if netwin_q and fair_q:
                kelly_res = self.sharp_sentinel.calculate_kelly_stake(
                    netwin_odds=netwin_q,
                    fair_sharp_odds=fair_q,
                    bankroll=self.bankroll,
                    kelly_fraction=self.kelly_fraction,
                    max_stake_pct=self.max_stake_pct
                )
                if kelly_res.get("kelly_criterion") == "VALUE_BET":
                    total_edge += kelly_res.get("expected_value", 0.0)
                    count += 1

        if count > 0 and total_edge > 0:
            recommended_stake = sum(
                self.sharp_sentinel.calculate_kelly_stake(
                    netwin_odds=s.get("netwin_odds", 2.0),
                    fair_sharp_odds=s.get("fair_sharp_odds", 1.8),
                    bankroll=self.bankroll,
                    kelly_fraction=self.kelly_fraction,
                    max_stake_pct=self.max_stake_pct
                ).get("stake_amount", 0.0) for s in selections if s.get("fair_sharp_odds")
            )
            final_stake = max(self.MIN_AAMS_STAKE, min(recommended_stake, self.bankroll * (self.max_stake_pct / 100.0)))
            logger.info(f"🧠 Stake dinamico (Kelly) calcolato: {final_stake:.2f} €")
            return round(final_stake, 2)
        
        logger.info("Nessun edge positivo rilevato dal Kelly. Uso stake minimo di sicurezza.")
        return self.MIN_AAMS_STAKE

    def build_ticket(
        self,
        selections: List[Dict[str, Any]],
        bet_mode: str = "MULTIPLE",
        fixed_stake: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Popola l'intero ticket con le selezioni fornite e configura stake e modalità.
        """
        self.open_sportsbook()
        self.clear_betslip()

        added_count = 0
        for item in selections:
            success = self.search_and_add_selection(
                team_name=item["match"],
                market_type=item.get("market", "1X2"),
                outcome_target=item["pick"],
                alias=item.get("alias")
            )
            if success:
                added_count += 1
            time.sleep(0.8)

        logger.info(f"Selezioni aggiunte con successo: {added_count}/{len(selections)}")
        
        if added_count == 0:
            return {"success": False, "error": "Nessuna selezione aggiunta al carrello."}

        stake_to_use = fixed_stake if fixed_stake is not None else self._calculate_optimal_stake(selections)
        self._configure_betslip_mode(bet_mode=bet_mode, stake=stake_to_use)

        summary = self.get_betslip_summary()
        summary["success"] = added_count > 0
        summary["selections_added"] = added_count
        summary["total_requested"] = len(selections)
        summary["applied_stake"] = stake_to_use
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

            stake_input = self.page.locator("input[placeholder*='Importo'], input.stake-input, input[name='stake'], .cart-bets-total-stake input").first
            if stake_input.is_visible(timeout=3000):
                stake_input.click()
                stake_input.fill("")
                stake_input.fill(f"{stake:.2f}")
                stake_input.press("Tab")
                logger.info(f"💰 Stake impostato a: {stake:.2f} €")
            else:
                logger.warning("Input per lo stake non trovato.")
        except Exception as e:
            logger.warning(f"Errore configurazione modalità carrello: {e}")

    def get_betslip_summary(self) -> Dict[str, Any]:
        """Estrae quota totale, bonus moltiplicatore e vincita potenziale dal carrello."""
        summary = {
            "total_odds": "1.00",
            "potential_win": "0.00",
            "is_valid": False,
        }
        try:
            betslip_el = self.page.locator(".betslip, #betslip, div[class*='cart'], div[class*='betslip']").first
            if betslip_el.is_visible(timeout=3000):
                txt = betslip_el.inner_text()
                summary["raw_text"] = txt
                summary["is_valid"] = True
                
                odds_match = re.search(r'Quota totale[:\s]*([0-9]+\.[0-9]{2})', txt, re.IGNORECASE)
                if odds_match:
                    summary["total_odds"] = odds_match.group(1)
                
                win_match = re.search(r'Vincita potenziale[:\s]*([0-9]+\.[0-9]{2})', txt, re.IGNORECASE)
                if win_match:
                    summary["potential_win"] = win_match.group(1)
                    
                logger.info("Riepilogo carrello letto con successo.")
        except Exception as e:
            logger.debug(f"Errore lettura carrello: {e}")
        return summary

    def generate_booking_code(self) -> Dict[str, Any]:
        """Clicca su 'Prenota' e recupera il codice di prenotazione Netwin a 6 cifre con Regex robusta."""
        logger.info("Richiesta generazione Codice Prenotazione...")
        res = {"success": False, "booking_code": "", "error": None}
        try:
            book_btn = self.page.locator("button:has-text('PRENOTA'), button:has-text('Prenota')").first
            if book_btn.is_visible(timeout=3000):
                book_btn.click()
                time.sleep(1.5)
                
                self._handle_odds_change_modal()
                time.sleep(1.0)

                modal_text = self.page.locator(".modal-body, .booking-modal, div:has-text('Codice prenotazione'), .booking-code").first.inner_text(timeout=5000)
                
                code_match = re.search(r'\b\d{6}\b', modal_text)
                if code_match:
                    code = code_match.group(0)
                    res["success"] = True
                    res["booking_code"] = code
                    logger.info(f"🎯 CODICE PRENOTAZIONE GENERATO: {code}")
                    self._save_booking_log(code)
                    return res
                else:
                    res["error"] = "Codice a 6 cifre non trovato nel modal."
                    logger.error("Regex fallita nell'estrazione del codice prenotazione.")
            else:
                res["error"] = "Pulsante Prenota non disponibile o carrello vuoto."
        except Exception as e:
            res["error"] = str(e)
            logger.error(f"Errore prenotazione: {e}")
        return res

    def _save_booking_log(self, booking_code: str):
        """Salva un log JSON della prenotazione per tracciabilità."""
        try:
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "booking_code": booking_code,
                "betslip_summary": self.get_betslip_summary()
            }
            log_file = RECEIPTS_DIR / f"booking_log_{booking_code}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=4)
            logger.info(f"Log prenotazione salvato: {log_file}")
        except Exception as e:
            logger.warning(f"Impossibile salvare il log JSON: {e}")

    def place_bet(self) -> Dict[str, Any]:
        """Conferma e piazza la scommessa reale su Netwin salvando lo screenshot della ricevuta."""
        logger.info("🚀 ESECUZIONE PIAZZAMENTO SCOMMESSA SU NETWIN...")
        res = {"success": False, "receipt_id": None, "screenshot_path": None, "error": None}

        try:
            bet_btn = self.page.locator("button:has-text('Scommetti'), button:has-text('Piazza scommessa'), button.bet-button").first
            if not bet_btn.is_visible(timeout=3000):
                res["error"] = "Pulsante 'Scommetti' non visibile."
                return res

            bet_btn.click()
            time.sleep(1.0)

            quota_changed = self._handle_odds_change_modal()
            if quota_changed:
                logger.info("Variazione quota accettata, procedo con la conferma...")
                time.sleep(1.0)

            confirm_modal = self.page.locator("button:has-text('Conferma'), button:has-text('Continua'), .btn-confirm-bet").first
            if confirm_modal.is_visible(timeout=3000):
                confirm_modal.click()
                time.sleep(2.5)

            ts = int(time.time())
            screenshot_file = RECEIPTS_DIR / f"receipt_{ts}.png"
            self.page.screenshot(path=str(screenshot_file), full_page=False)
            res["screenshot_path"] = str(screenshot_file)

            receipt_el = self.page.locator(":text-matches('Scommessa accettata|Ricevuta|Codice AAMS|Scommessa registrata', 'i')").first
            if receipt_el.is_visible(timeout=5000):
                res["success"] = True
                res["receipt_id"] = f"NW-{ts}"
                logger.info(f"✅ SCOMMESSA ACCETTATA CON SUCCESSO! Screenshot in: {screenshot_file}")
            else:
                res["error"] = "Scommessa inviata, ma conferma visiva non rilevata (possibile errore di quota o saldo)."

        except Exception as e:
            res["error"] = str(e)
            logger.error(f"Errore piazzamento: {e}")

        return res
