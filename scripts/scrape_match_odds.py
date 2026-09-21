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

def scrape_match_odds(alias):
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
        search_input.fill(str(alias))
        page.keyboard.press("Enter")
        time.sleep(2.5)

        # Get all text from main content
        content = page.locator(".risultati-ricerca, .main-content, #main, .elenco-eventi, .box-eventi").first
        if content.is_visible():
            print(f"--- MATCH {alias} OVERVIEW ---")
            print(content.inner_text()[:600])
        else:
            print(f"Content not visible for {alias}, dumping body lines:")
            lines = page.locator("body").inner_text().split("\n")
            for l in lines:
                if str(alias) in l or "1X2" in l or "DOPPIA" in l:
                    print("  ", l.strip())

        # Click on match
        match_link = page.locator(f":text('{alias}')").first
        if match_link.is_visible():
            match_link.click()
            time.sleep(2)
            
            # Print all available market categories
            macros = page.locator(".elemento-macro").all()
            macro_names = [m.inner_text().strip() for m in macros if m.inner_text().strip()]
            print(f"Available Macros for {alias}: {macro_names}")

            # If Combo 1X2 exists, inspect it
            combo_m = page.locator(".elemento-macro:has-text('Combo 1X2')").first
            if combo_m.is_visible():
                combo_m.click()
                time.sleep(1.5)
                # Print all subtabs
                subtabs = page.locator(".elemento-macro, button, .tab, .btn").all()
                print("Subtabs in Combo 1X2:")
                # Screenshot
                page.screenshot(path=str(root / "reports" / f"scrape_combo_{alias}.png"))
                print(f"Saved reports/scrape_combo_{alias}.png")

        browser.close()

if __name__ == "__main__":
    alias = sys.argv[1] if len(sys.argv) > 1 else "8376"
    scrape_match_odds(alias)
