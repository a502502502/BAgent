import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def test_visible_click():
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
        search_input.click()
        search_input.fill("8376")
        page.keyboard.press("Enter")
        time.sleep(2)

        match_row = page.locator(":text('Backa Topola')").first
        match_row.click()
        time.sleep(1.5)

        # Click Combo 1X2
        page.locator(".elemento-macro:has-text('Combo 1X2')").first.click()
        time.sleep(1)
        # Click DC+U/O
        page.locator(":text('DC+U/O')").first.click()
        time.sleep(1)

        # Find visible tipoQuotazione_1
        visible_odds = page.locator(".tipoQuotazione_1:visible, p:has-text('1.90'):visible").all()
        print(f"Found {len(visible_odds)} visible odds elements.")
        if visible_odds:
            print("Clicking first visible odd...")
            visible_odds[0].scroll_into_view_if_needed()
            visible_odds[0].click(force=True)
            time.sleep(2)
        else:
            # Try parent container or force click on locator
            print("Trying force click on p:has-text('1.90')...")
            p_el = page.locator("p:has-text('1.90')").last
            p_el.click(force=True)
            time.sleep(2)

        # Take screenshot of the cart on the right
        page.screenshot(path=str(root / "reports" / "cart_after_odd_click.png"))
        print("Saved cart_after_odd_click.png")

        # Check cart contents
        cart_text = page.locator("#schedina-1, .schedina, [class*='cart']").all()
        for idx, ct in enumerate(cart_text[:5]):
            print(f"Cart [{idx}]: {ct.inner_text().replace(chr(10), ' | ')[:150]}")

        browser.close()

if __name__ == "__main__":
    test_visible_click()
