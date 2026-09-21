import sys
import time
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from playwright.sync_api import sync_playwright

def test_booking_modal():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.netwin.it/scommesse", wait_until="networkidle", timeout=45000)
        time.sleep(2)
        
        # Accept cookies
        try:
            cookie_btn = page.locator("button:has-text('Accetta tutti'), #CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                time.sleep(1)
        except Exception:
            pass

        # Search 8376
        search_input = page.locator("#match-search-input")
        search_input.click()
        search_input.fill("8376")
        page.keyboard.press("Enter")
        time.sleep(2)

        page.locator(":text('Backa Topola')").first.click()
        time.sleep(1.5)

        # Click Combo 1X2
        page.locator(".elemento-macro:has-text('Combo 1X2')").first.click()
        time.sleep(1)
        # Click DC+U/O
        page.locator(":text('DC+U/O')").first.click()
        time.sleep(1)

        # Click first visible odd to add to cart
        visible_odds = page.locator(".tipoQuotazione_1:visible").all()
        if visible_odds:
            visible_odds[0].scroll_into_view_if_needed()
            visible_odds[0].click(force=True)
            time.sleep(2)

        # Now click PRENOTA
        prenota_btn = page.locator("button:has-text('PRENOTA'), div:has-text('PRENOTA'), a:has-text('PRENOTA')").last
        print(f"Prenota button visible: {prenota_btn.is_visible()}")
        prenota_btn.click()
        time.sleep(3)

        # Take screenshot of the booking modal
        page.screenshot(path=str(root / "reports" / "prenotazione_modal.png"))
        print("Saved prenotazione_modal.png")

        # Let's find modal text or booking code
        modal_elements = page.locator(".modal, .popup, [role='dialog'], .swal2-popup, .cdk-overlay-container, div[class*='dialog']").all()
        print(f"Found {len(modal_elements)} modal elements:")
        for idx, m in enumerate(modal_elements):
            try:
                txt = m.inner_text().strip()
                print(f"  Modal [{idx}]: {txt[:200]}")
            except Exception as e:
                print(f"  Modal [{idx}] error: {e}")

        browser.close()

if __name__ == "__main__":
    test_booking_modal()
