import time
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        print("Navigating to Netwin...")
        page.goto("https://www.netwin.it/scommesse", timeout=30000)
        time.sleep(3)
        
        try:
            accept_btn = page.locator("button:has-text('Accetta tutti')")
            if accept_btn.is_visible(timeout=4000):
                accept_btn.click()
                print("Cookie accepted")
                time.sleep(1)
        except Exception as e:
            print("Cookie error:", e)

        # Look for football section / matches
        # Click 'Oggi' or look for matches
        try:
            oggi_tab = page.locator("button:has-text('Oggi'), div:has-text('Oggi'), a:has-text('Oggi')").first
            if oggi_tab.is_visible(timeout=3000):
                print("Found Oggi button, clicking...")
                oggi_tab.click()
                time.sleep(2)
        except Exception as e:
            pass

        rows = page.locator(".contenitoreAvvenimento")
        count = rows.count()
        print(f"Total .contenitoreAvvenimento rows: {count}")
        for i in range(min(count, 30)):
            t = rows.nth(i).inner_text().replace("\n", " | ")
            print(f"[{i+1}] {t}")

        browser.close()

if __name__ == "__main__":
    main()
