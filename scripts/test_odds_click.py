import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def inspect_odds_click():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.netwin.it/scommesse", wait_until="networkidle", timeout=45000)
        time.sleep(2)
        
        try:
            cookie_btn = page.locator("button:has-text('Accetta tutti'), #CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                time.sleep(1)
        except Exception:
            pass

        search_input = page.locator("#match-search-input")
        search_input.click()
        search_input.fill("8376")
        page.keyboard.press("Enter")
        time.sleep(2)

        match_row = page.locator(":text('Backa Topola')").first
        match_row.click()
        time.sleep(1.5)

        # Click Combo 1X2
        page.locator(".elemento-macro:has-text('Combo 1X2')").first.click()
        time.sleep(1)
        # Click DC+U/O
        page.locator(":text('DC+U/O')").first.click()
        time.sleep(1)

        # Let's find the dropdown next to 1X + U/O (showing 3.5)
        dropdown = page.locator("select, .dropdown, div[class*='select']").first
        print(f"Dropdown: {dropdown}")

        # Let's click on the odd 1.90 directly to test betslip insertion!
        odd_btn = page.locator(":text('1.90')").first
        print(f"Odd 1.90 visible: {odd_btn.is_visible()}")
        odd_btn.click()
        time.sleep(2)

        # Now let's see what happened in SCHEDINA 1!
        page.screenshot(path=str(root / "reports" / "betslip_with_one_odd.png"))
        print("Saved betslip_with_one_odd.png")

        # Let's see betslip text
        betslip = page.locator(".scheda, .betslip, [class*='coupon'], [class*='schedina']").all()
        for idx, bs in enumerate(betslip):
            txt = bs.inner_text().strip()
            if txt:
                print(f"Betslip [{idx}]: {txt[:150]}")

        browser.close()

if __name__ == "__main__":
    inspect_odds_click()
