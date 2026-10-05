import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=25000)
    time.sleep(3)
    
    # 1. Accept cookies
    btn = page.locator("button:has-text('Accetta tutti')")
    if btn.count() > 0:
        btn.first.click()
        time.sleep(4)
        
    # 2. Click TUTTE
    tutte_btn = page.locator("text=TUTTE").first
    if tutte_btn.is_visible():
        tutte_btn.click()
        print("TUTTE clicked!")
        time.sleep(3)

    # 3. Target "UNO O L'ALTRO: CARTELLINO ULTRA INC TS"
    print("Locating UNO O L'ALTRO: CARTELLINO ULTRA INC TS...")
    target = page.get_by_text("UNO O L'ALTRO: CARTELLINO ULTRA INC TS").first
    print("Visible before scroll?", target.is_visible())
    
    # Scroll to it
    target.scroll_into_view_if_needed()
    time.sleep(1)
    print("Visible after scroll?", target.is_visible())
    
    # Click it!
    target.click()
    print("Clicked target!")
    time.sleep(3)
    
    # Check if BARELLA or CELIK is now in body
    body = page.inner_text("body")
    print("Has BARELLA now?", "BARELLA" in body)
    if "BARELLA" in body:
        idx = body.find("BARELLA")
        print("Found snippet:")
        print(body[idx-20:idx+300])
        
    browser.close()
