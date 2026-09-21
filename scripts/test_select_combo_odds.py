import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def run_booking():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
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

        # 1. Match 8376: Backa Topola
        print("Searching 8376...")
        search_input = page.locator("#match-search-input")
        search_input.click()
        search_input.fill("8376")
        page.keyboard.press("Enter")
        time.sleep(2)

        match_row = page.locator(":text('Backa Topola')").first
        match_row.click()
        time.sleep(1.5)

        # Click Combo 1X2
        combo_macro = page.locator(".elemento-macro:has-text('Combo 1X2')").first
        if combo_macro.is_visible():
            combo_macro.click()
            time.sleep(1.5)

        # Let's inspect odds buttons
        page.screenshot(path=str(root / "reports" / "combo_1x2_odds_8376.png"))
        print("Saved combo_1x2_odds_8376.png")

        # Let's look for odds elements
        odds_btns = page.locator(".quota, button[class*='quota'], .odd, div[class*='quota']").all()
        print(f"Found {len(odds_btns)} quota elements.")
        for idx, ob in enumerate(odds_btns[:15]):
            try:
                print(f"  Quota [{idx}]: text='{ob.inner_text().strip()}', class='{ob.get_attribute('class')}'")
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    run_booking()
