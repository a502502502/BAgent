import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("https://www.netwin.it/scommesse", timeout=30000)
    
    # Chiudi cookie
    try:
        btn = page.locator("button:has-text('Accetta tutti')").first
        btn.click(timeout=4000)
        print("Cookiebot cliccato")
    except Exception as e:
        print("Cookiebot error:", e)
        
    inp = page.locator("#match-search-input").first
    inp.wait_for(state="visible", timeout=10000)
    print("inp.wait_for riuscito! is_visible:", inp.is_visible())
    
    inp.click()
    inp.fill("Criciuma")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    print("Ricerca completata!")
    b.close()
