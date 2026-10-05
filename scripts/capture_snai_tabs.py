import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=30000)
        time.sleep(3)
        try:
            cookie = page.locator("button:has-text('Accetta tutti')").first
            if cookie.is_visible():
                cookie.click()
                time.sleep(2)
        except Exception:
            pass

        # 1. PRINCIPALI
        print("Clicking PRINCIPALI...")
        p_tab = page.locator("text=PRINCIPALI").first
        if p_tab.is_visible():
            p_tab.click()
            time.sleep(2)
            page.screenshot(path="reports/snai_principali.png")

        # 2. COMBO
        print("Clicking COMBO...")
        c_tab = page.locator("text=COMBO").first
        if c_tab.is_visible():
            c_tab.click()
            time.sleep(2)
            page.screenshot(path="reports/snai_combo.png")

        # 3. GOAL
        print("Clicking GOAL...")
        g_tab = page.locator("text=GOAL").first
        if g_tab.is_visible():
            g_tab.click()
            time.sleep(2)
            page.screenshot(path="reports/snai_goal.png")

        browser.close()
        print("Done capturing tabs!")

if __name__ == "__main__":
    run()
