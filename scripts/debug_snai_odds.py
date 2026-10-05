import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=30000)
    time.sleep(3)
    
    try:
        btn = page.locator("button:has-text('Accetta tutti')").first
        if btn.is_visible():
            btn.click()
            print("Cookie accepted")
            time.sleep(2)
    except Exception as e:
        print("Cookie error:", e)
        
    # Take screenshot of the odds
    page.screenshot(path="reports/live_snai_top.png")
    
    # Let's inspect the first 20 odds boxes on the page
    cards = page.locator(".single-market, .market-row, .disponibili, .odd-container, .event-bets").all()
    print(f"Found {len(cards)} market containers")
    
    # Print the page text for the top markets
    body_text = page.inner_text("body")
    with open("reports/snai_live_debug.txt", "w", encoding="utf-8") as f:
        f.write(body_text)
        
    print("Written to reports/snai_live_debug.txt")
    browser.close()
