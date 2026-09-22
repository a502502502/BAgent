
raise SystemExit(
    "TENNIS BAN (22/09/2026): script disabilitato. BAgent opera solo sul calcio."
)
import sys
import time
import json
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

def scan_netwin_tennis_and_football():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        print("1. Connessione a Netwin Scommesse...")
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

        # ----------------------------------------------------
        # SCAN TENNIS
        # ----------------------------------------------------
        print("\n🎾 --- SCANSIONE TENNIS NETWIN ---")
        tennis_btn = page.locator(":text('TENNIS'), a:has-text('Tennis'), div:has-text('Tennis')").first
        if tennis_btn.is_visible():
            tennis_btn.click()
            time.sleep(2.5)
            
            # Click 'OGGI' if present
            oggi_btn = page.locator("button:has-text('OGGI'), div:has-text('OGGI')").first
            if oggi_btn.is_visible():
                oggi_btn.click()
                time.sleep(2)

            page.screenshot(path=str(root / "reports" / "netwin_tennis_scan.png"))
            print("Screenshot salvato in reports/netwin_tennis_scan.png")

            # Extract matches
            tennis_rows = page.locator("tr, div.riga-evento, .match-row").all()
            print(f"Righe trovate in Tennis: {len(tennis_rows)}")
            for idx, tr in enumerate(tennis_rows[:20]):
                try:
                    txt = tr.inner_text().strip().replace(chr(10), " | ")
                    if len(txt) > 10 and ("1" in txt or "2" in txt or ":" in txt):
                        print(f"Tennis [{idx}]: {txt[:160]}")
                except Exception:
                    pass

        # ----------------------------------------------------
        # SCAN CALCIO OGGI (Tardo Pomeriggio / Sera)
        # ----------------------------------------------------
        print("\n⚽ --- SCANSIONE CALCIO SERA NETWIN ---")
        calcio_btn = page.locator(":text('CALCIO'), a:has-text('Calcio')").first
        if calcio_btn.is_visible():
            calcio_btn.click()
            time.sleep(2)
            
            # Filter 'OGGI'
            oggi_btn = page.locator("button:has-text('OGGI'), div:has-text('OGGI')").first
            if oggi_btn.is_visible():
                oggi_btn.click()
                time.sleep(2)

            page.screenshot(path=str(root / "reports" / "netwin_calcio_scan.png"))
            print("Screenshot salvato in reports/netwin_calcio_scan.png")

            calcio_rows = page.locator("tr, div.riga-evento, .match-row").all()
            print(f"Righe trovate in Calcio: {len(calcio_rows)}")
            for idx, cr in enumerate(calcio_rows[:25]):
                try:
                    txt = cr.inner_text().strip().replace(chr(10), " | ")
                    if len(txt) > 10 and any(h in txt for h in ["17:", "18:", "19:", "20:", "21:"]):
                        print(f"Calcio [{idx}]: {txt[:160]}")
                except Exception:
                    pass

        browser.close()

if __name__ == "__main__":
    scan_netwin_tennis_and_football()
