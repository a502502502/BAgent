import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def test_add_to_cart():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.netwin.it/scommesse", wait_until="networkidle", timeout=45000)
        time.sleep(2)
        
        # 1. Accept Cookiebot
        try:
            cookie_btn = page.locator("button:has-text('Accetta tutti'), #CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                print("Cookiebot accepted!")
                time.sleep(1)
        except Exception as e:
            print("Cookie error:", e)

        # 2. Try Fastbet alias input: #fastbet-cart-event
        alias_input = page.locator("#fastbet-cart-event")
        print(f"Alias input visible: {alias_input.is_visible()}")
        if alias_input.is_visible():
            # Let's type 8376 and press Space
            alias_input.click()
            alias_input.fill("8376")
            page.keyboard.press("Space")
            time.sleep(1.5)
            print("Typed 8376 and Space into Alias input.")

        # Let's also search Backa Topola if not opened
        search_input = page.locator("#match-search-input")
        if search_input.is_visible():
            search_input.click()
            search_input.fill("8376")
            page.keyboard.press("Enter")
            time.sleep(2)

        # Let's see what is on screen now
        page.screenshot(path=str(root / "reports" / "alias_8376_test.png"))
        print("Saved alias_8376_test.png")

        # Let's see all clickable elements or odds
        print("--- PAGE TEXT SNIPPETS ---")
        body_text = page.locator("body").inner_text()
        for line in body_text.split("\n"):
            if any(k in line.lower() for k in ["topola", "dubocica", "8376", "prenota", "schedina"]):
                print("  LINE:", line.strip())

        browser.close()

if __name__ == "__main__":
    test_add_to_cart()
