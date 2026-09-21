import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def inspect_tab_tag():
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
        time.sleep(2)

        # Find any element containing Combo 1X2
        elements = page.locator("*:has-text('Combo 1X2')").all()
        print(f"Found {len(elements)} elements with 'Combo 1X2':")
        for i, el in enumerate(elements[-5:]): # usually the most specific is at the end
            try:
                tag = el.evaluate("e => e.tagName")
                cls = el.get_attribute("class") or ""
                print(f"  [{i}] tag={tag}, class='{cls}', text='{el.inner_text().strip()[:30]}'")
            except Exception as e:
                print(f"  [{i}] error: {e}")

        # Let's click the last one
        if elements:
            target = elements[-1]
            print("Clicking target:", target.evaluate("e => e.outerHTML[:100]"))
            target.click()
            time.sleep(2)
            page.screenshot(path=str(root / "reports" / "after_click_combo.png"))
            print("Saved after_click_combo.png")

        browser.close()

if __name__ == "__main__":
    inspect_tab_tag()
