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

    print("Searching elements by JavaScript evaluate...")
    # Find all accordion headers via JS and click them!
    result = page.evaluate("""
        () => {
            const clicked = [];
            // In SNAI, accordion headers can be divs, buttons, or spans
            const allElements = document.querySelectorAll('*');
            for (const el of allElements) {
                // If it looks like a market header or has aria-expanded false or info scommesse sibling
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt.includes('UNO O L') || txt.includes('DUETTO') || txt.includes('TIRI IN PORTA') || txt.includes('RIGORE')) {
                    if (el.children.length <= 2 && el.tagName !== 'BODY' && el.tagName !== 'HTML') {
                        el.click();
                        clicked.push(el.tagName + ': ' + txt.slice(0, 30));
                    }
                }
            }
            return clicked;
        }
    """)
    print("JS Clicked elements count:", len(result))
    for c in result[:10]:
        print("  Clicked:", c)
        
    time.sleep(4)
    
    # Check if BARELLA or other pairs are present now
    body = page.inner_text("body")
    print("Has BARELLA now?", "BARELLA" in body)
    if "BARELLA" in body:
        idx = body.find("BARELLA")
        print("--- SNIPPET FOUND ---")
        print(body[idx-30:idx+250])
        print("---------------------")
        
    browser.close()
