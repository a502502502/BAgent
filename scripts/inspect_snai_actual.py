import time
from playwright.sync_api import sync_playwright

def inspect_snai_live():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=30000)
        time.sleep(4)
        
        # Accept cookies
        try:
            cookie_btn = page.locator("button:has-text('Accetta tutti'), button:has-text('Accetta')").first
            if cookie_btn.is_visible():
                cookie_btn.click()
                print("Cookie accepted")
                time.sleep(3)
        except Exception:
            pass
            
        # Click TUTTE
        try:
            tutte = page.locator("text=TUTTE").first
            if tutte.is_visible():
                tutte.click()
                print("Clicked TUTTE")
                time.sleep(3)
        except Exception as e:
            print("Error clicking TUTTE:", e)

        # Let's inspect the first 30 bet-items or odd-buttons
        buttons = page.locator("button, .btn-quota, .quota, [data-odd], .odd").all()
        print(f"Total buttons/odds found: {len(buttons)}")
        
        # Take a screenshot of the top section where odds are
        page.screenshot(path="reports/snai_actual_visible_odds.png")
        
        # Extract text of the entire main area
        main_text = page.locator("main, #main, .content, body").first.inner_text()
        with open("reports/snai_actual_visible_text.txt", "w", encoding="utf-8") as f:
            f.write(main_text)
            
        print("Done. Screenshot saved to reports/snai_actual_visible_odds.png")
        browser.close()

if __name__ == "__main__":
    inspect_snai_live()
