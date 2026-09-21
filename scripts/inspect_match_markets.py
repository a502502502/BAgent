import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def inspect_match_markets():
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

        # Click on the match row
        match_row = page.locator(":text('Backa Topola')").first
        print(f"Match row visible: {match_row.is_visible()}")
        match_row.click()
        time.sleep(2.5)

        # Let's take screenshot of markets
        page.screenshot(path=str(root / "reports" / "markets_8376.png"))
        print("Saved markets_8376.png")

        # Let's see all market tabs or headers
        tabs = page.locator("button, .tab, .nav-item, div[role='tab']").all()
        print(f"Found {len(tabs)} tabs/buttons:")
        for t in tabs:
            txt = t.inner_text().strip()
            if txt and len(txt) < 30 and any(k in txt.lower() for k in ['combo', 'multigol', 'doppia', 'gol', 'tempo', 'under', 'over']):
                print(f"  Tab: '{txt}'")

        browser.close()

if __name__ == "__main__":
    inspect_match_markets()
