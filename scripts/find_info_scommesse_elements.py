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
        time.sleep(4)

    # 3. Let's find all clickable elements in the main content area
    dropdown_info = page.evaluate("""
        () => {
            const results = [];
            // Look for all elements that contain chevron icons, svgs, or text like 'Info Scommesse'
            const elements = document.querySelectorAll('*');
            elements.forEach(el => {
                // If this element has sibling or child with 'Info Scommesse'
                if (el.innerText && el.innerText.includes('Info Scommesse') && el.children.length < 5) {
                    results.push({
                        tag: el.tagName,
                        className: el.className,
                        text: el.innerText.split('\\n')[0]
                    });
                }
            });
            return results;
        }
    """)
    print(f"Found {len(dropdown_info)} elements with 'Info Scommesse':")
    for d in dropdown_info[:15]:
        print("  ->", d['tag'], f"class='{d['className']}'", "title:", d['text'])
        
    browser.close()
