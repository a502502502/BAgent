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

def inspect_tennis_matches():
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

        # 1. Search our upcoming tennis players
        players_to_search = ["Rus", "Romero", "Hercog", "Ristic", "Swiatek", "Sabalenka", "Sinner", "Alcaraz", "Paolini"]
        print("--- Searching Tennis Players on Netwin ---")
        for p_name in players_to_search:
            search_input = page.locator("#match-search-input")
            search_input.click()
            search_input.fill(p_name)
            page.keyboard.press("Enter")
            time.sleep(1.5)
            
            # Check results
            rows = page.locator("tr, div.riga-evento").all()
            for r in rows:
                txt = r.inner_text().strip().replace(chr(10), " | ")
                if p_name.lower() in txt.lower() and ("1" in txt or ":" in txt or "oggi" in txt.lower()):
                    print(f"Found Tennis Match for '{p_name}': {txt[:160]}")
                    break

        # 2. Click on Eventi Live -> Tennis pill
        print("\n--- Checking Live Tennis (Eventi Live) ---")
        live_tennis_pill = page.locator(".eventi-live, div").locator(":text('Tennis')").first
        if live_tennis_pill.is_visible():
            live_tennis_pill.click()
            time.sleep(2)
            page.screenshot(path=str(root / "reports" / "live_tennis_view.png"))
            rows = page.locator("tr, div.riga-evento").all()
            print(f"Live Tennis rows: {len(rows)}")
            for idx, r in enumerate(rows[:10]):
                txt = r.inner_text().strip().replace(chr(10), " | ")
                if len(txt) > 10 and ("1" in txt or ":" in txt):
                    print(f"  Live [{idx}]: {txt[:140]}")

        browser.close()

if __name__ == "__main__":
    inspect_tennis_matches()
