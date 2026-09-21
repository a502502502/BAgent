import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def inspect_details():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.netwin.it/scommesse", wait_until="networkidle", timeout=45000)
        time.sleep(3)
        
        # Check Cerca elements
        print("--- CERCA ELEMENTS ---")
        cerca_elements = page.locator(":text-matches('Cerca', 'i')").all()
        for idx, el in enumerate(cerca_elements):
            try:
                tag = el.evaluate("e => e.tagName")
                classes = el.get_attribute("class")
                outer = el.evaluate("e => e.outerHTML[:200]")
                print(f"[{idx}] <{tag} class='{classes}'>: {outer}")
            except Exception as e:
                print(f"[{idx}] Error: {e}")

        # Check search inputs
        print("--- INPUTS WITH SEARCH OR TEXT ---")
        text_inputs = page.locator("input[type='text'], input[type='search'], input:not([type])").all()
        for idx, inp in enumerate(text_inputs):
            try:
                ph = inp.get_attribute("placeholder") or ""
                cls = inp.get_attribute("class") or ""
                id_attr = inp.get_attribute("id") or ""
                val = inp.input_value()
                print(f"[{idx}] id='{id_attr}', placeholder='{ph}', class='{cls}'")
            except Exception as e:
                print(f"[{idx}] Error: {e}")

        # Check Prenota button
        print("--- PRENOTA BUTTON ---")
        prenota_btn = page.locator(":text-matches('^Prenota', 'i')").all()
        for idx, pb in enumerate(prenota_btn):
            try:
                print(f"[{idx}] tag={pb.evaluate('e => e.tagName')}, class={pb.get_attribute('class')}, html={pb.evaluate('e => e.outerHTML[:200]')}")
            except Exception as e:
                print(f"[{idx}] Error: {e}")

        browser.close()

if __name__ == "__main__":
    inspect_details()
