import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", wait_until="networkidle", timeout=30000)
    time.sleep(3)
    
    # 1. Accept cookies
    btn = page.locator("button:has-text('Accetta tutti')")
    if btn.count() > 0:
        btn.first.click()
        print("Clicked Accetta tutti")
        time.sleep(5)
        
    # 2. Click TUTTE
    tutte_btn = page.locator("text='TUTTE'")
    if tutte_btn.count() > 0:
        tutte_btn.first.click()
        print("Clicked TUTTE")
        time.sleep(5)

    # 3. Check metamarketHeaders count
    print("Evaluating page via JS...")
    res = page.evaluate("""
        () => {
            const headers = document.querySelectorAll('.metamarketHeader, [class*="metamarketHeader"]');
            const data = [];
            headers.forEach((h, idx) => {
                const btn = h.querySelector('button') || h;
                const title = h.innerText.replace(/\\n/g, ' ').trim();
                data.push({idx, title});
                // Click to expand!
                try {
                    btn.click();
                } catch(e) {}
            });
            return {
                count: headers.length,
                samples: data.slice(0, 15)
            };
        }
    """)
    print("Headers found & clicked:", res['count'])
    for s in res['samples']:
        print(f"  [{s['idx']}] {s['title']}")
        
    time.sleep(6)
    
    # Check if BARELLA or CELIK or other pairs are present now!
    body = page.inner_text("body")
    print("Length of body after expansion:", len(body))
    print("Has BARELLA now?", "BARELLA" in body)
    print("Has CELIK now?", "CELIK" in body)
    print("Has UNO O L'ALTRO?", "UNO O L'ALTRO" in body)
    
    # Let's search for "BARELLA N. O BASTONI A."
    if "BARELLA N. O BASTONI A." in body:
        print(">>> SUCCESS! BARELLA N. O BASTONI A. IS IN THE BODY! <<<")
        idx = body.find("BARELLA N. O BASTONI A.")
        print(body[idx:idx+400])
    elif "BARELLA" in body:
        idx = body.find("BARELLA")
        print("Found BARELLA:", body[idx:idx+300])
        
    with open("reports/snai_fully_opened_test.txt", "w", encoding="utf-8") as f:
        f.write(body)
        
    browser.close()
