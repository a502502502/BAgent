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

def inspect_all_user_matches():
    aliases = ["984", "8372", "8765", "2575", "8373", "8376", "8374", "8892"]
    
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

        for a in aliases:
            print(f"\n=================== ALIAS {a} ===================")
            search_input.click()
            search_input.fill(a)
            page.keyboard.press("Enter")
            time.sleep(2)

            # Find rows matching alias
            rows = page.locator(f"tr:has-text('{a}'), div:has-text('{a}')").all()
            found_any = False
            for r in rows:
                try:
                    txt = r.inner_text().strip()
                    if a in txt and ("1" in txt or "X" in txt or ":" in txt) and len(txt) < 300:
                        print(f"ROW: {txt.replace(chr(10), ' | ')}")
                        found_any = True
                        break
                except Exception:
                    pass
            if not found_any:
                print(f"No row found for {a} directly, checking body lines...")
                for l in page.locator("body").inner_text().split("\n"):
                    if a in l:
                        print(f"  Line: {l.strip()}")

        browser.close()

if __name__ == "__main__":
    inspect_all_user_matches()
