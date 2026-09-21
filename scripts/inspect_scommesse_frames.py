import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def inspect_scommesse():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        
        url = "https://www.netwin.it/scommesse"
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle", timeout=45000)
        time.sleep(5)
        
        print(f"Current URL: {page.url}")
        print(f"Page Title: {page.title()}")
        print(f"Number of frames: {len(page.frames)}")
        for idx, frame in enumerate(page.frames):
            print(f"  Frame {idx}: name='{frame.name}', url='{frame.url}'")
            try:
                # search in frame
                inputs = frame.locator("input").all()
                print(f"    Frame {idx} inputs count: {len(inputs)}")
                for i, inp in enumerate(inputs[:5]):
                    ph = inp.get_attribute("placeholder") or ""
                    print(f"      [{i}] placeholder='{ph}', type='{inp.get_attribute('type')}'")
            except Exception as e:
                print(f"    Frame {idx} error: {e}")

        # Check if there are buttons or links with 'Calcio', 'Live', 'Prenota', 'Scommetti'
        for text in ['Prenota', 'Carrello', 'Schedina', 'Calcio', 'Cerca']:
            cnt = page.locator(f":text-matches('{text}', 'i')").count()
            print(f"Count for '{text}': {cnt}")

        screenshot_path = root / "reports" / "scommesse_test.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Saved fullpage screenshot to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    inspect_scommesse()
