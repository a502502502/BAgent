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

def dump_evening():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.netwin.it/scommesse", wait_until="networkidle", timeout=45000)
        time.sleep(2)
        
        try:
            page.locator("button:has-text('Accetta tutti')").first.click()
            time.sleep(1)
        except Exception:
            pass

        page.locator(":text('CALENDARIO')").first.click()
        time.sleep(3)

        rows = page.locator("tr, div.riga-evento, .match-row, .box-evento").all()
        print(f"Total calendar rows: {len(rows)}")
        for idx, r in enumerate(rows[30:]):
            txt = r.inner_text().strip().replace("\n", " | ")
            print(f"[{idx+30}] {txt[:160]}")

        # Also let's check if there is a sport filter on top of Calendario!
        sports_filters = page.locator(".filtri-calendario, .filtro-sport, .sport-tabs").all()
        print(f"Sports filters count: {len(sports_filters)}")
        for sf in sports_filters:
            print("  Filter:", sf.inner_text().replace("\n", " | "))

        browser.close()

if __name__ == "__main__":
    dump_evening()
