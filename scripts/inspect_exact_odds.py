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

def inspect_exact_odds():
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

        matches_to_check = [
            ("8376", "Backa Topola vs Gfk Dubocica"),
            ("8374", "Paok B vs Nestos Chrysoupoli"),
            ("8892", "Ofk Vrsac vs Fk Bor 1919"),
            ("8372", "Pas Pyrgos vs Ae Larissa"),
            ("8373", "Panthrakikos vs Niki Volou"),
        ]

        results = {}

        for alias, name in matches_to_check:
            print(f"\n==========================================")
            print(f"Checking Alias {alias}: {name}")
            print(f"==========================================")
            search_input = page.locator("#match-search-input")
            search_input.click()
            search_input.fill(alias)
            page.keyboard.press("Enter")
            time.sleep(2)

            # Get 1X2 and main odds from search table
            row = page.locator(f"tr:has-text('{alias}'), div.riga-evento:has-text('{alias}')").first
            if row.is_visible():
                txt = row.inner_text().replace("\n", " | ")
                print(f"Main row text: {txt}")
                results[alias] = {"main_row": txt, "markets": {}}
            else:
                # Just find by text
                match_el = page.locator(f":text('{alias}')").first
                if match_el.is_visible():
                    print("Found element with text:", match_el.inner_text())
                else:
                    print(f"Alias {alias} not found in search results.")
                    continue

            # Click match to open details
            try:
                page.locator(f":text('{alias}')").first.click()
                time.sleep(1.5)
            except Exception as e:
                print("Error clicking match:", e)
                continue

            # Check Combo 1X2 tab
            macro = page.locator(".elemento-macro:has-text('Combo 1X2')").first
            if macro.is_visible():
                macro.click()
                time.sleep(1)
                
                # Check DC+U/O
                dcuo = page.locator(":text('DC+U/O')").first
                if dcuo.is_visible():
                    dcuo.click()
                    time.sleep(1)
                    # Read table
                    dc_uo_text = page.locator(".tabella-quote, .table, table, .container-quote").first.inner_text()
                    print(f"DC+U/O table: {dc_uo_text[:300].replace(chr(10), ' | ')}")

                # Check DC+MG
                dcmg = page.locator(":text('DC+MG')").first
                if dcmg.is_visible():
                    dcmg.click()
                    time.sleep(1)
                    dc_mg_text = page.locator(".tabella-quote, .table, table, .container-quote").first.inner_text()
                    print(f"DC+MG table: {dc_mg_text[:300].replace(chr(10), ' | ')}")

            # Also check MultiGol macro tab
            mg_macro = page.locator(".elemento-macro:has-text('MultiGol')").first
            if mg_macro.is_visible():
                mg_macro.click()
                time.sleep(1)
                mg_text = page.locator(".tabella-quote, .table, table, .container-quote").first.inner_text()
                print(f"MultiGol table: {mg_text[:300].replace(chr(10), ' | ')}")

        browser.close()

if __name__ == "__main__":
    inspect_exact_odds()
