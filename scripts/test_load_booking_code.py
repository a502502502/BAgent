import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def inspect_code():
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

        # Inserisci il codice 303404 nel campo 'Codice' e clicca 'Carica' per vedere se ricarica la schedina!
        codice_input = page.locator("#input-reservation-box-coupon-1, input[placeholder*='Codice']").first
        print("Trovato campo Codice:", codice_input.is_visible())
        codice_input.fill("303404")
        
        carica_btn = page.locator("button:has-text('Carica'), input[value='Carica'], .btn:has-text('Carica'), div:has-text('Carica')").first
        print("Trovato pulsante Carica:", carica_btn.is_visible())
        carica_btn.click()
        page.wait_for_timeout(3000)

        page.screenshot(path="reports/netwin_code_loaded.png")
        print("Screenshot salvato in reports/netwin_code_loaded.png")

        # Verifica se la schedina ha ricaricato Criciuma
        cart_text = page.locator("div[class*='cart'], div[class*='schedina'], .betslip, #betslip").first.inner_text()
        print("Testo Carrello dopo Carica:\n", cart_text[:400])

        browser.close()

if __name__ == "__main__":
    inspect_code()
