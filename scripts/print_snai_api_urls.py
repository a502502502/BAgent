import time
from playwright.sync_api import sync_playwright

urls = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.on("response", lambda r: urls.append(r.url) if "flutterseatech" in r.url else None)
    
    page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=25000)
    time.sleep(3)
    
    btn = page.locator("button:has-text('Accetta tutti')")
    if btn.count() > 0:
        btn.first.click()
        time.sleep(4)
        
    tutte_btn = page.locator("text=TUTTE").first
    if tutte_btn.is_visible():
        tutte_btn.click()
        time.sleep(4)
        
    print("Found flutterseatech URLs:")
    for u in urls:
        print("  ->", u)
        
    browser.close()
