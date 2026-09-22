
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

def inspect_tennis_properly():
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

        # Let's find any button or link with 'tennis' in href or text
        print("--- Finding Tennis Links on Netwin ---")
        tennis_links = page.locator("a[href*='tennis'], button:has-text('Tennis'), div:has-text('Tennis')").all()
        for idx, tl in enumerate(tennis_links):
            try:
                href = tl.get_attribute("href") or ""
                txt = tl.inner_text().strip().replace("\n", " ")
                if href or (txt and len(txt) < 30):
                    print(f"  [{idx}] text='{txt}', href='{href}'")
            except Exception:
                pass

        # Try to navigate directly to tennis URL if pattern exists (e.g. /scommesse/tennis or /sport/tennis)
        tennis_urls = ["https://www.netwin.it/scommesse/tennis", "https://www.netwin.it/sport/tennis"]
        for u in tennis_urls:
            print(f"Trying direct URL: {u}")
            res = page.goto(u, timeout=15000)
            print(f"  Status: {res.status if res else 'None'}, Title: {page.title()}, URL: {page.url}")
            time.sleep(2)
            # Check if tennis matches are listed
            page.screenshot(path=str(root / "reports" / f"direct_{u.split('/')[-1]}_{u.split('/')[-2]}.png"))
            lines = [l.strip() for l in page.locator("body").inner_text().split("\n") if len(l.strip()) > 5]
            for l in lines[:15]:
                print("    ", l)

        browser.close()

if __name__ == "__main__":
    inspect_tennis_properly()
