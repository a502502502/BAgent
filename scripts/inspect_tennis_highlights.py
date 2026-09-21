import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def inspect_tennis_and_highlights():
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

        # 1. Click Tennis in "In evidenza"
        print("Clicking Tennis in In Evidenza...")
        tennis_pill = page.locator("div.in-evidenza, .in-evidenza").locator(":text('Tennis')").first
        if not tennis_pill.is_visible():
            tennis_pill = page.locator(":text('Tennis')").first
        
        tennis_pill.click()
        time.sleep(3)
        page.screenshot(path=str(root / "reports" / "tennis_in_evidenza.png"))
        print("Saved reports/tennis_in_evidenza.png")

        # Let's extract text of tennis events
        tennis_elements = page.locator("tr, div.riga-evento, .match-row").all()
        print(f"Found {len(tennis_elements)} tennis rows:")
        for idx, te in enumerate(tennis_elements[:15]):
            try:
                txt = te.inner_text().strip().replace(chr(10), " | ")
                if len(txt) > 5:
                    print(f"  [{idx}] {txt[:160]}")
            except Exception:
                pass

        # 2. Let's inspect Serie C (Trento vs Pro Vercelli)
        print("\n--- Inspecting Serie C (Trento vs Pro Vercelli) ---")
        search_input = page.locator("#match-search-input")
        search_input.click()
        search_input.fill("Trento")
        page.keyboard.press("Enter")
        time.sleep(2)
        page.screenshot(path=str(root / "reports" / "trento_search.png"))

        trento_row = page.locator("tr:has-text('Trento'), div:has-text('Trento')").first
        if trento_row.is_visible():
            print("Trento row:", trento_row.inner_text().replace(chr(10), " | ")[:200])

        browser.close()

if __name__ == "__main__":
    inspect_tennis_and_highlights()
