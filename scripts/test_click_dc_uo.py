import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def test_click_dc_uo():
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

        # 1. Search 8376
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

        # Click DC+U/O
        dc_uo_btn = page.locator(":text('DC+U/O')").first
        if dc_uo_btn.is_visible():
            dc_uo_btn.click()
            time.sleep(1.5)
            print("Clicked DC+U/O")

        page.screenshot(path=str(root / "reports" / "dc_uo_view_8376.png"))
        print("Saved dc_uo_view_8376.png")

        # Let's see all texts in table row
        row_texts = page.locator("tr, .riga-evento, .match-row").all()
        for idx, r in enumerate(row_texts[:5]):
            try:
                print(f"Row [{idx}]: {r.inner_text().replace(chr(10), ' | ')}")
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    test_click_dc_uo()
