import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        print("Apertura Netwin Sport...")
        page.goto("https://www.netwin.it/sport", timeout=30000)
        page.wait_for_timeout(4000)
        
        # Accetta cookie
        try:
            cookie_btn = page.locator("button:has-text('Accetta'), button#onetrust-accept-btn-handler").first
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                print("Cookie accettati")
        except Exception:
            pass
            
        page.wait_for_timeout(2000)
        
        # Cerca iframe o widget
        frames = page.frames
        print(f"Frames trovati: {len(frames)}")
        for f in frames:
            print("Frame URL:", f.url[:120])
            
        # Cerca testo EFL o partite
        for query in ["Barnsley", "Peterborough", "Rochdale", "Arsenal", "EFL"]:
            elements = page.locator(f":text-matches('{query}', 'i')").all()
            print(f"Query '{query}': trovati {len(elements)} elementi")
            for el in elements[:5]:
                try:
                    parent_text = el.locator("xpath=..").inner_text()
                    print(f"  Contesto: {parent_text.replace(chr(10), ' | ')[:150]}")
                except Exception:
                    pass
                    
        browser.close()

if __name__ == "__main__":
    run()
