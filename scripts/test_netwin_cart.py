import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def test_fastbet_and_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.netwin.it/scommesse", wait_until="networkidle", timeout=45000)
        time.sleep(3)
        
        # Test search with match-search-input
        search_input = page.locator("#match-search-input")
        print(f"Search input visible: {search_input.is_visible()}")
        if search_input.is_visible():
            search_input.click()
            search_input.fill("Backa Topola")
            page.keyboard.press("Enter")
            time.sleep(2)
            print("Typed 'Backa Topola' in search input.")

        # Let's see what appears on screen
        page.screenshot(path=str(root / "reports" / "search_backa_test.png"))
        print("Saved search screenshot.")

        # Let's inspect the coupon / cart area
        cart_elements = page.locator("#coupon-1, .coupon, .cart, .betslip, #reservation-box-coupon-1").all()
        print(f"Cart elements count: {len(cart_elements)}")
        for idx, ce in enumerate(cart_elements):
            print(f"Cart [{idx}]: tag={ce.evaluate('e => e.tagName')}, id={ce.get_attribute('id')}, class={ce.get_attribute('class')}")
            print(f"  Inner text: {ce.inner_text()[:200]}")

        # Let's find any button in coupon-1
        coupon_buttons = page.locator("#coupon-1 button, .coupon button").all()
        print(f"Coupon buttons count: {len(coupon_buttons)}")
        for idx, btn in enumerate(coupon_buttons):
            try:
                print(f"  Button [{idx}]: text='{btn.inner_text()}', id='{btn.get_attribute('id')}', class='{btn.get_attribute('class')}'")
            except Exception as e:
                print(f"  Button [{idx}] error: {e}")

        browser.close()

if __name__ == "__main__":
    test_fastbet_and_search()
