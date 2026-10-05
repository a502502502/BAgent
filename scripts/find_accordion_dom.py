import time
from bs4 import BeautifulSoup
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

    html = page.content()
    print("Total HTML length:", len(html))
    
    soup = BeautifulSoup(html, "html.parser")
    # Search for any text with UNO O L'ALTRO
    found = []
    for tag in soup.find_all(True):
        if tag.string and "UNO O L'ALTRO" in tag.string:
            found.append(f"{tag.name} (class={tag.get('class')}): {tag.string.strip()}")
            # Print parent
            parent = tag.parent
            print(f"Parent {parent.name} (class={parent.get('class')} id={parent.get('id')})")
            print("Parent HTML snippet:", str(parent)[:400])
            break
            
    print("Found count:", len(found))
    browser.close()
