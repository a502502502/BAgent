# DEPRECATED: prefer NetwinAutomator.build_ticket_and_book (services/betting/netwin_automator.py). Booking codes only.
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def test_uo_tab():
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

        # Clicca sul tab Under/Over
        uo_tab = page.locator("button:has-text('Under/Over'), div:has-text('Under/Over'), a:has-text('Under/Over')").first
        if uo_tab.is_visible(timeout=3000):
            print("Trovato tab Under/Over, clicco...")
            uo_tab.click()
            page.wait_for_timeout(1500)
            page.screenshot(path="reports/netwin_uo_tab.png")
            print("Screenshot salvato in reports/netwin_uo_tab.png")

        browser.close()

if __name__ == "__main__":
    test_uo_tab()
