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

def inspect_calendario():
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

        # Click CALENDARIO in top navigation
        cal_btn = page.locator(":text('CALENDARIO')").first
        print(f"CALENDARIO button visible: {cal_btn.is_visible()}")
        cal_btn.click()
        time.sleep(3)

        page.screenshot(path=str(root / "reports" / "netwin_calendario.png"))
        print("Saved netwin_calendario.png")

        # Let's see what is listed in the calendar
        rows = page.locator("tr, div.riga-evento, .match-row, .box-evento").all()
        print(f"Found {len(rows)} calendar rows:")
        for idx, r in enumerate(rows[:30]):
            txt = r.inner_text().strip().replace(chr(10), " | ")
            if len(txt) > 10 and any(k in txt for k in ["Tennis", "Calcio", "17:", "18:", "19:", "20:", "21:"]):
                print(f"  [{idx}] {txt[:160]}")

        browser.close()

if __name__ == "__main__":
    inspect_calendario()
