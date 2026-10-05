import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=False)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    print("Navigating...")
    page.goto('https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia', timeout=25000)
    time.sleep(3)
    
    # Click Accetta tutti
    btn = page.locator("button:has-text('Accetta tutti')")
    if btn.count() > 0:
        btn.first.click()
        print("Clicked 'Accetta tutti'!")
        time.sleep(6)
    
    page.screenshot(path='reports/snai_after_cookies.png')
    text = page.inner_text('body')
    print("Length after cookies:", len(text))
    print("Has 1.40?", "1.40" in text)
    print("Has ESPOSITO?", "ESPOSITO" in text)
    print("Has TUTTE?", "TUTTE" in text)
    
    # If TUTTE is present, click it!
    tutte_btn = page.locator("text='TUTTE'")
    if tutte_btn.count() > 0:
        tutte_btn.first.click()
        print("Clicked 'TUTTE'!")
        time.sleep(4)
        text_tutte = page.inner_text('body')
        print("Length after TUTTE:", len(text_tutte))
        with open("reports/snai_playwright_full_extracted.txt", "w", encoding="utf-8") as f:
            f.write(text_tutte)
        print("Saved to reports/snai_playwright_full_extracted.txt")
        
    browser.close()
