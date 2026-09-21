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

def inspect_tennis_sidebar():
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

        # Click TENNIS on the left sidebar (in the accordion)
        tennis_accordion = page.locator(".sidebar, .left-menu, #left-column").locator(":text('TENNIS')").first
        if not tennis_accordion.is_visible():
            tennis_accordion = page.locator("div:has-text('TENNIS')").first
        
        print(f"Tennis accordion visible: {tennis_accordion.is_visible()}")
        tennis_accordion.click()
        time.sleep(2)

        page.screenshot(path=str(root / "reports" / "tennis_sidebar_open.png"))
        print("Saved tennis_sidebar_open.png")

        # Let's see what tournament names appear on the left or in main area
        tournaments = page.locator(".competizione, .categoria, .torneo, a[href*='tennis']").all()
        print(f"Found {len(tournaments)} tournament/tennis links:")
        for idx, t in enumerate(tournaments[:20]):
            try:
                txt = t.inner_text().strip().replace(chr(10), " | ")
                if txt and len(txt) < 50:
                    print(f"  [{idx}] {txt}")
            except Exception:
                pass

        # Also let's check Serie A, Serie B, La Liga for tonight
        print("\n--- Checking Tonight's Serie A / La Liga / Serie C ---")
        matches_search = ["LaLiga", "Serie A", "Serie C", "Spezia"]
        for q in matches_search:
            s_input = page.locator("#match-search-input")
            s_input.click()
            s_input.fill(q)
            page.keyboard.press("Enter")
            time.sleep(1.5)
            rows = page.locator("tr, div.riga-evento").all()
            for r in rows[:3]:
                txt = r.inner_text().strip().replace(chr(10), " | ")
                if any(h in txt for h in ["17:", "18:", "19:", "20:", "21:"]) and len(txt) < 250:
                    print(f"  {q} Match: {txt}")

        browser.close()

if __name__ == "__main__":
    inspect_tennis_sidebar()
