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

def scrape_tennis_tournaments():
    urls = [
        "https://www.netwin.it/scommesse/tennis/wta/sao-paulo-wta-250",
        "https://www.netwin.it/scommesse/tennis/wta-125k",
        "https://www.netwin.it/scommesse/tennis/challenger",
        "https://www.netwin.it/scommesse/tennis/atp"
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        
        for u in urls:
            t_name = u.split("/")[-1]
            print(f"\n==========================================")
            print(f"🎾 Navigazione: {u}")
            print(f"==========================================")
            page.goto(u, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            
            try:
                page.locator("button:has-text('Accetta tutti')").first.click()
            except Exception:
                pass

            # Screenshot
            page.screenshot(path=str(root / "reports" / f"tennis_{t_name}.png"))

            # Check rows
            rows = page.locator("tr, div.riga-evento, .match-row").all()
            print(f"Righe trovate in {t_name}: {len(rows)}")
            for idx, r in enumerate(rows):
                txt = r.inner_text().strip().replace(chr(10), " | ")
                if len(txt) > 10 and ("1" in txt or "2" in txt or ":" in txt) and "ADM" not in txt:
                    print(f"  [{idx}] {txt[:180]}")

        browser.close()

if __name__ == "__main__":
    scrape_tennis_tournaments()
