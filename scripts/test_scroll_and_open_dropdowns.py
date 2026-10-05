import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    print("Navigating to SNAI...")
    page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=25000)
    time.sleep(3)
    
    # Accept cookies
    btn = page.locator("button:has-text('Accetta tutti')")
    if btn.count() > 0:
        btn.first.click()
        print("Accepted cookies.")
        time.sleep(5)
        
    # Click TUTTE
    tutte_btn = page.locator("text=TUTTE").first
    if tutte_btn.is_visible():
        tutte_btn.click()
        print("Clicked TUTTE.")
        time.sleep(4)

    # Scroll down step-by-step to load ALL virtualized markets
    print("Scrolling down to trigger virtual rendering...")
    for step in range(12):
        page.mouse.wheel(0, 800)
        time.sleep(0.3)
        
    # Scroll back to top
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

    # Now click all accordion dropdown headers!
    print("Opening all dropdown accordions...")
    opened = page.evaluate("""
        () => {
            let count = 0;
            // Find all headers or chevron buttons
            const allElements = document.querySelectorAll('*');
            for (const el of allElements) {
                const txt = (el.innerText || '').trim();
                if (el.children.length === 0 && txt && (
                    txt.startsWith('UNO O L') ||
                    txt.startsWith('DUETTO') ||
                    txt.startsWith('COMBO:') ||
                    txt.startsWith('1X2 TIRI') ||
                    txt.startsWith('1X2 FALLI') ||
                    txt.startsWith('1X2 PUNTI') ||
                    txt.startsWith('RIGORE') ||
                    txt.startsWith('SOSTITUZIONE') ||
                    txt.startsWith('U/O FALLI')
                )) {
                    // Click its parent or the element itself
                    const target = el.parentElement || el;
                    try {
                        target.click();
                        count++;
                    } catch(e) {}
                }
            }
            return count;
        }
    """)
    print(f"Clicked {opened} dropdown headers via JS!")
    time.sleep(5)

    # Check if BARELLA or CELIK are now in the extracted text!
    full_text = page.inner_text("body")
    print(f"Total extracted body length: {len(full_text)}")
    print("Has 'BARELLA N. O BASTONI A.'?", "BARELLA N. O BASTONI A." in full_text)
    print("Has 'CELIK ZEKI O KABAK OZAN'?", "CELIK ZEKI O KABAK OZAN" in full_text)
    print("Has '2.65' near BARELLA?", "2.65" in full_text)
    
    with open("reports/snai_opened_dropdowns_extracted.txt", "w", encoding="utf-8") as f:
        f.write(full_text)
        
    if "BARELLA N. O BASTONI A." in full_text:
        print("\n>>> SUCCESS! All dropdowns are opened and captured! <<<")
        idx = full_text.find("BARELLA N. O BASTONI A.")
        print(full_text[idx:idx+500])
        
    browser.close()
