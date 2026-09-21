import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def book_gemme_ticket():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        print("1. Connessione a Netwin...")
        page.goto("https://www.netwin.it/scommesse", wait_until="networkidle", timeout=45000)
        time.sleep(2)
        
        # Cookiebot
        try:
            cookie_btn = page.locator("button:has-text('Accetta tutti'), #CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                time.sleep(1)
        except Exception:
            pass

        # Helper to search and add an event
        def select_event_odds(alias: str, team_name: str, macro_tab: str, sub_tab: str, odd_filter: str):
            print(f"\n--- Inserimento {team_name} (Alias {alias}) ---")
            search_input = page.locator("#match-search-input")
            search_input.click()
            search_input.fill(alias)
            page.keyboard.press("Enter")
            time.sleep(2)

            match_row = page.locator(f":text('{team_name}')").first
            if match_row.is_visible(timeout=3000):
                match_row.click()
                time.sleep(1.5)
            
            # Click macro tab (es. Combo 1X2)
            macro = page.locator(f".elemento-macro:has-text('{macro_tab}')").first
            if macro.is_visible(timeout=2000):
                macro.click()
                time.sleep(1)

            # Click sub tab (es. DC+U/O o DC+MG)
            if sub_tab:
                sub = page.locator(f":text('{sub_tab}')").first
                if sub.is_visible(timeout=2000):
                    sub.click()
                    time.sleep(1)

            # Look for visible odd
            # Click the first visible odd in the selection
            visible_odds = page.locator(".tipoQuotazione_1:visible").all()
            print(f"Quote visibili per {team_name}: {len(visible_odds)}")
            if visible_odds:
                visible_odds[0].scroll_into_view_if_needed()
                visible_odds[0].click(force=True)
                time.sleep(1.5)
                print(f"✅ Quota aggiunta per {team_name}")
            else:
                print(f"⚠️ Nessuna quota trovata direttamente per {team_name}")

        # Event 1: Backa Topola (8376)
        select_event_odds("8376", "Backa Topola", "Combo 1X2", "DC+U/O", "1X + OV")

        # Event 2: Paok B (8374)
        select_event_odds("8374", "Paok", "Combo 1X2", "DC+MG", "1X + MG")

        # Event 3: Ofk Vrsac (8892)
        select_event_odds("8892", "Vrsac", "Combo 1X2", "DC+MG", "1X + MG")

        # Configura Stake (seleziona tab Multipla se presente)
        print("\nConfigurazione Carrello e Prenotazione...")
        mult_btn = page.locator("button:has-text('MULTIPLA'), div:has-text('MULTIPLA')").first
        if mult_btn.is_visible():
            mult_btn.click()
            time.sleep(0.5)

        # Clicca PRENOTA
        prenota_btn = page.locator("button:has-text('PRENOTA'), div:has-text('PRENOTA'), a:has-text('PRENOTA')").last
        if prenota_btn.is_visible(timeout=3000):
            prenota_btn.click()
            time.sleep(3)
            print("Pulsante PRENOTA cliccato!")

        # Screenshot carrello e codice
        screenshot_path = root / "reports" / "prenotazione_netwin_ufficiale.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Screenshot salvato in: {screenshot_path}")

        # Estrai il codice a 6 cifre
        prenotazione_block = page.locator(":text-matches('\\b\\d{5,7}\\b')").all()
        extracted_codes = []
        for pb in prenotazione_block:
            try:
                txt = pb.inner_text().strip()
                if txt.isdigit() and len(txt) in [5, 6, 7]:
                    extracted_codes.append(txt)
            except Exception:
                pass

        print("Codici di prenotazione individuati:", set(extracted_codes))
        browser.close()

if __name__ == "__main__":
    book_gemme_ticket()
