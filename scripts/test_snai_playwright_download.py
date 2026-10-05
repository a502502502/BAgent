import time
from playwright.sync_api import sync_playwright

def download_snai_match(url: str, output_path: str = "reports/snai_live_download.txt"):
    print(f"Launching automated Edge browser for URL: {url}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
        )
        page = context.new_page()
        
        print("Navigating to SNAI...")
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        time.sleep(3)
        
        # 1. Accept cookies if banner present
        try:
            cookie_btn = page.locator("button:has-text('Accetta'), button:has-text('ACCETTA'), #onetrust-accept-btn-handler").first
            if cookie_btn.is_visible(timeout=2000):
                cookie_btn.click()
                print("Cookie banner accepted.")
                time.sleep(1)
        except Exception:
            pass

        # 2. Click on tab "TUTTE"
        try:
            tutte_tab = page.locator("text='TUTTE'").first
            if tutte_tab.is_visible(timeout=3000):
                tutte_tab.click()
                print("Clicked tab 'TUTTE'!")
                time.sleep(2)
        except Exception as e:
            print("Tab TUTTE click failed or not found:", e)

        # 3. Expand all accordions
        try:
            accordions = page.locator("[aria-expanded='false'], .accordion-header, [data-toggle='collapse']")
            count = accordions.count()
            print(f"Found {count} collapsed accordions, expanding...")
            for i in range(min(count, 50)):
                try:
                    accordions.nth(i).click(timeout=500)
                except Exception:
                    pass
            time.sleep(2)
        except Exception as e:
            print("Accordion expansion note:", e)

        # 4. Extract entire page text
        full_text = page.inner_text("body")
        print(f"Extracted {len(full_text)} characters of market data!")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Saved full catalog to {output_path} successfully!")
        browser.close()
        return full_text

if __name__ == "__main__":
    download_snai_match("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia")
