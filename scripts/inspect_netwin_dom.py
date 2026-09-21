import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from services.betting.netwin_automator import NetwinAutomator

def inspect_netwin():
    automator = NetwinAutomator(headless=True)
    try:
        automator.open_sportsbook()
        page = automator.page
        time.sleep(4)
        
        inputs = page.locator("input").all()
        print(f"Found {len(inputs)} input elements:")
        for idx, inp in enumerate(inputs):
            try:
                ph = inp.get_attribute("placeholder") or ""
                t = inp.get_attribute("type") or ""
                cls = inp.get_attribute("class") or ""
                name = inp.get_attribute("name") or ""
                print(f"  [{idx}] placeholder='{ph}', type='{t}', name='{name}', class='{cls}'")
            except Exception as e:
                print(f"  [{idx}] Error: {e}")

        # Let's see if we can find 'Cerca' or search button
        search_candidates = page.locator(":text-matches('Cerca|Search', 'i')").all()
        print(f"Found {len(search_candidates)} text-matches for search:")
        for idx, sc in enumerate(search_candidates[:10]):
            try:
                print(f"  Candidate {idx}: tag={sc.evaluate('el => el.tagName')}, text='{sc.inner_text()[:40]}'")
            except Exception:
                pass

        screenshot_path = root / "reports" / "netwin_live_test.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Screenshot saved to {screenshot_path}")

    finally:
        automator.close()

if __name__ == "__main__":
    inspect_netwin()
