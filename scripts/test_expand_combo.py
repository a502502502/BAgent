import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def test_select_odd_and_book():
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

        # Click on '+379' or down arrow to expand all markets
        expand_btn = page.locator(":text-matches('\\+\\d+', 'i')").first
        if expand_btn.is_visible():
            print("Found expand button:", expand_btn.inner_text())
            expand_btn.click()
            time.sleep(2)

        # Let's see what tabs or markets appear now
        page.screenshot(path=str(root / "reports" / "expanded_8376.png"))
        print("Saved expanded_8376.png")

        # Let's find Combo 1X2 tab and click it
        combo_tab = page.locator(":text('Combo 1X2')").first
        if combo_tab.is_visible():
            print("Clicking Combo 1X2 tab...")
            combo_tab.click()
            time.sleep(1.5)
            page.screenshot(path=str(root / "reports" / "combo_1x2_8376.png"))

        browser.close()

if __name__ == "__main__":
    test_select_odd_and_book()
