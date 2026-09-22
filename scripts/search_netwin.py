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
    
    print("Ricerca campionati e match su Netwin...")
    for q in ['Barnsley', 'Peterborough', 'Rochdale', 'Arsenal', 'EFL', 'Trophy', 'Champions', 'Donne', 'Inghilterra']:
        matches = [l for l in lines if q.lower() in l.lower()]
        print(f'Query "{q}": {len(matches)} match -> {matches[:4]}')
        
    # Cerca righe con quote (numeri tipo 1.xx, 2.xx)
    odd_lines = [l for l in lines if any(term in l.lower() for term in ['vs', ' - ']) or (len(l) < 6 and '.' in l and l.replace('.', '').isdigit())]
    print(f"Righe match/quote trovate: {len(odd_lines)}")
    print("Esempio righe match/quote:", odd_lines[:20])
    
    browser.close()
