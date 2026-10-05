import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=25000)
    time.sleep(3)
    
    # Accept cookies
    btn = page.locator("button:has-text('Accetta tutti')")
    if btn.count() > 0:
        btn.first.click()
        time.sleep(4)
        
    # Click TUTTE
    tutte_btn = page.locator("text='TUTTE'")
    if tutte_btn.count() > 0:
        tutte_btn.first.click()
        time.sleep(3)

    # Locate all metamarketHeader
    headers = page.locator(".metamarketHeader")
    n = headers.count()
    print(f"Total .metamarketHeader found: {n}")
    
    for i in range(min(n, 20)):
        txt = headers.nth(i).inner_text().replace("\n", " ")
        print(f"{i}: {txt}")
        
    # Now let's click on ALL .metamarketHeader that are not expanded!
    print("Clicking all .metamarketHeader...")
    for i in range(n):
        try:
            h = headers.nth(i)
            # Check if it has a chevron or if clicking it expands
            h.scroll_into_view_if_needed(timeout=1000)
            h.click(timeout=1000)
        except Exception:
            pass
            
    time.sleep(4)
    
    # Check body text
    body = page.inner_text("body")
    print(f"Body length after expanding all metamarketHeaders: {len(body)}")
    print("Has BARELLA now?", "BARELLA" in body)
    print("Has CELIK now?", "CELIK" in body)
    print("Has PRIMO MARCATORE ESPOSITO now?", "ESPOSITO P. O" in body)
    
    with open("reports/snai_fully_expanded_palinsesto.txt", "w", encoding="utf-8") as f:
        f.write(body)
        
    browser.close()
