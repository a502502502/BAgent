import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def test_combo_selection():
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

        # Search 8376
        search_input = page.locator("#match-search-input")
        search_input.click()
        search_input.fill("8376")
        page.keyboard.press("Enter")
        time.sleep(2)

        # Click the tab 'Combo 1X2' directly!
        combo_tab = page.locator("button:has-text('Combo 1X2'), span:has-text('Combo 1X2'), div:has-text('Combo 1X2')").first
        if combo_tab.is_visible(timeout=3000):
            print("Found Combo 1X2 tab! Clicking...")
            combo_tab.click()
            time.sleep(2)
        else:
            print("Combo 1X2 tab not visible yet, clicking match row...")
            page.locator(":text('Backa Topola')").first.click()
            time.sleep(2)
            page.locator("button:has-text('Combo 1X2'), span:has-text('Combo 1X2')").first.click()
            time.sleep(2)

        page.screenshot(path=str(root / "reports" / "combo_1x2_view.png"))
        print("Saved combo_1x2_view.png")

        # Let's inspect odds elements visible in the page
        odds_elements = page.locator(".odd, .quota, button.btn-quota, div[class*='odd']").all()
        print(f"Found {len(odds_elements)} odds elements.")

        browser.close()

if __name__ == "__main__":
    test_combo_selection()
