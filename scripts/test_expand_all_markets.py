import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def test_expand_match():
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

        # Clicca sul pulsante +1161 o freccia
        expand_btn = page.locator(":text-matches('\\+[0-9]+', 'i')").first
        if expand_btn.is_visible(timeout=3000):
            print("Trovato pulsante mercati estesi:", expand_btn.inner_text())
            expand_btn.click()
            page.wait_for_timeout(2500)
            page.screenshot(path="reports/netwin_all_markets_expanded.png")
            print("Screenshot salvato in reports/netwin_all_markets_expanded.png")

        browser.close()

if __name__ == "__main__":
    test_expand_match()
