import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def inspect_prenotazione_element():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto("https://www.netwin.it/scommesse", timeout=30000)
        page.wait_for_timeout(3000)

        try:
            page.locator("button:has-text('Accetta tutti')").first.click(timeout=3000)
            page.wait_for_timeout(1000)
        except Exception:
            pass

        search_input = page.locator("#match-search-input").first
        search_input.click()
        search_input.fill("Criciuma")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2500)

        # Clicca sul match
        page.locator(":text-matches('Criciuma Ec Sc', 'i')").first.click()
        page.wait_for_timeout(2000)

        # Clicca sulla quota 1.98
        odd_el = page.locator(".contenitoreSingolaQuota:has-text('1.98')").first
        if odd_el.is_visible(timeout=3000):
            odd_el.click()
            page.wait_for_timeout(1500)

        # Clicca su PRENOTA
        prenota_btn = page.locator("button:has-text('PRENOTA')").first
        if prenota_btn.is_visible():
            prenota_btn.click()
            page.wait_for_timeout(2500)

            # Cerca elementi contenenti 6 cifre nel carrello o nel box prenotazioni
            prenotazione_box = page.locator(":text-matches('Prenotazioni effettuate', 'i')").first
            if prenotazione_box.is_visible(timeout=3000):
                parent = prenotazione_box.locator("xpath=..")
                print("Testo box prenotazione:\n", parent.inner_text())
                
                # Trova tutti gli elementi testo nel box
                import re
                txt = parent.inner_text()
                match = re.search(r'\b(\d{6})\b', txt)
                if match:
                    print(f"🎯 CODICE ESTRATTO CON SUCCESSO: {match.group(1)}")
                else:
                    print("Nessun match regex a 6 cifre nel box.")

        browser.close()

if __name__ == "__main__":
    inspect_prenotazione_element()
