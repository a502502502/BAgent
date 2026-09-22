import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto('https://www.netwin.it/scommesse', timeout=30000)
    page.wait_for_timeout(5000)
    
    text = page.inner_text('body')
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    # Cerca tutte le sezioni di campionati e partite
    events = []
    for i, l in enumerate(lines):
        if any(sep in l for sep in [' - ', ' vs ', ' v ']) and len(l) < 60:
            events.append((l, lines[max(0, i-2):min(len(lines), i+8)]))
            
    print(f"Totale match con '-' o 'vs' trovati: {len(events)}")
    for name, context in events[:30]:
        print(f"MATCH: {name}")
        print(f"   Contesto: {' | '.join(context)}")
        
    browser.close()
