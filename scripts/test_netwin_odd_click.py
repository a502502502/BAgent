import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def inspect_odd_element():
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

        # Ispeziona gli elementi con testo '1.98', '1.23', '1.51'
        for val in ['1.98', '1.23', '1.51']:
            els = page.locator(f":text-matches('^{val}$', 'i')").all()
            print(f"Valore '{val}': {len(els)} elementi trovati")
            for i, el in enumerate(els):
                tag = el.evaluate("node => node.tagName")
                classes = el.evaluate("node => node.className")
                parent_tag = el.evaluate("node => node.parentElement.tagName")
                parent_classes = el.evaluate("node => node.parentElement.className")
                print(f"  El {i}: <{tag} class='{classes}'> inside <{parent_tag} class='{parent_classes}'>")
                # Prova a cliccare
                try:
                    el.click(timeout=2000)
                    print(f"  -> Cliccato el {i} ({val})!")
                except Exception as e:
                    print(f"  -> Errore click: {e}")

        page.wait_for_timeout(2000)
        page.screenshot(path="reports/netwin_odd_clicked_test.png")
        print("Screenshot salvato in reports/netwin_odd_clicked_test.png")

        # Verifica se SCHEDINA ha elementi
        schedina = page.locator("div:has-text('SCHEDINA 1')").first
        print("Testo Schedina 1:\n", schedina.inner_text()[:400])

        browser.close()

if __name__ == "__main__":
    inspect_odd_element()
