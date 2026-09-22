# DEPRECATED: prefer NetwinAutomator.build_ticket_and_book (services/betting/netwin_automator.py). Booking codes only.
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import time

def test_add_to_cart():
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

        print("1. Caricamento Netwin...")
        page.goto("https://www.netwin.it/scommesse", timeout=30000)
        page.wait_for_timeout(3000)

        # Cookie
        try:
            page.locator("button:has-text('Accetta tutti')").first.click(timeout=3000)
            page.wait_for_timeout(1000)
        except Exception:
            pass

        # Cerca Criciuma
        search_input = page.locator("#match-search-input").first
        search_input.click()
        search_input.fill("Criciuma")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2500)

        # Clicca sulla quota 1 (1.98) o sul match
        # Cerchiamo i pulsanti quota nella riga
        print("2. Ricerca riga match Criciuma...")
        match_el = page.locator(":text-matches('Criciuma Ec Sc', 'i')").first
        if match_el.is_visible(timeout=3000):
            print("   Trovato testo match! Clicco sul testo per aprire i mercati...")
            match_el.click()
            page.wait_for_timeout(2000)
            page.screenshot(path="reports/netwin_match_expanded.png")
            print("   Screenshot salvato in reports/netwin_match_expanded.png")

        # Verifica carrello prima e dopo aver cliccato una quota
        print("3. Clicco sulla quota 1 (1.98)...")
        odd_1 = page.locator(":text-matches('^1\\.98$', 'i'), button:has-text('1.98'), div:has-text('1.98')").first
        if odd_1.is_visible(timeout=2000):
            odd_1.click()
            print("   ✅ Quota 1.98 cliccata!")
            page.wait_for_timeout(2000)
            page.screenshot(path="reports/netwin_cart_added.png")
            print("   Screenshot carrello salvato in reports/netwin_cart_added.png")

            # Ispeziona carrello
            cart_text = page.locator("div[class*='cart'], div[class*='schedina'], .betslip, #betslip").first.inner_text()
            print("   Testo Carrello:\n", cart_text[:400])

        browser.close()

if __name__ == "__main__":
    test_add_to_cart()
