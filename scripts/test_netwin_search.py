# DEPRECATED: prefer NetwinAutomator.build_ticket_and_book (services/betting/netwin_automator.py). Booking codes only.
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import time

def test_search():
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

        print("Apertura Netwin...")
        page.goto("https://www.netwin.it/scommesse", timeout=30000)
        page.wait_for_timeout(3000)

        # Chiudi cookie
        try:
            page.locator("button:has-text('Accetta tutti')").first.click(timeout=3000)
            page.wait_for_timeout(1500)
        except Exception:
            pass

        # Cerca Criciúma
        search_input = page.locator("#match-search-input").first
        print("Trovato match-search-input:", search_input.is_visible())
        search_input.click()
        search_input.fill("Criciuma")
        page.wait_for_timeout(1000)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)

        # Salva screenshot dopo ricerca
        page.screenshot(path="reports/netwin_search_criciuma.png")
        print("Screenshot salvato in reports/netwin_search_criciuma.png")

        # Cerca risultati
        results = page.locator(":text-matches('Crici|Operário|Operario', 'i')").all()
        print(f"Risultati trovati: {len(results)}")
        for r in results[:10]:
            try:
                print("  Testo trovato:", r.inner_text().replace("\n", " | "))
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    test_search()
