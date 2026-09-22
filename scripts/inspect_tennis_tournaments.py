
raise SystemExit(
    "TENNIS BAN (22/09/2026): script disabilitato. BAgent opera solo sul calcio."
)
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

def inspect_tennis_tournaments():
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

        # Scroll down left sidebar and click TENNIS
        tennis_accordion = page.locator(".sidebar, .left-menu, #left-column").locator(":text('TENNIS')").first
        tennis_accordion.scroll_into_view_if_needed()
        tennis_accordion.click()
        time.sleep(1.5)

        # 1. Click SAO PAULO (WTA 250)
        sao_paulo = page.locator(":text('SAO PAULO (WTA 250)')").first
        if sao_paulo.is_visible():
            print("\n🎾 --- SAO PAULO (WTA 250) ---")
            sao_paulo.click()
            time.sleep(2)
            page.screenshot(path=str(root / "reports" / "tennis_sao_paulo.png"))
            rows = page.locator("tr, div.riga-evento").all()
            for r in rows[:10]:
                txt = r.inner_text().strip().replace(chr(10), " | ")
                if len(txt) > 10 and ("1" in txt or ":" in txt):
                    print("  Match:", txt[:160])

        # 2. Click Challenger or WTA 125K
        wta125 = page.locator(":text('WTA 125K'), :text('Challenger')").first
        if wta125.is_visible():
            print(f"\n🎾 --- {wta125.inner_text().strip()} ---")
            wta125.click()
            time.sleep(2)
            page.screenshot(path=str(root / "reports" / "tennis_wta125_challenger.png"))
            rows = page.locator("tr, div.riga-evento").all()
            for r in rows[:10]:
                txt = r.inner_text().strip().replace(chr(10), " | ")
                if len(txt) > 10 and ("1" in txt or ":" in txt):
                    print("  Match:", txt[:160])

        browser.close()

if __name__ == "__main__":
    inspect_tennis_tournaments()
