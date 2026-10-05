import time
import json
from playwright.sync_api import sync_playwright

json_responses = []

def handle_response(response):
    content_type = response.headers.get("content-type", "")
    url = response.url
    if "json" in content_type or "api" in url or "rest" in url or "palinsesto" in url:
        try:
            data = response.json()
            json_responses.append({
                "url": url,
                "status": response.status,
                "keys": list(data.keys()) if isinstance(data, dict) else f"list[{len(data)}]"
            })
            # If it contains odds or markets, save it!
            s_data = json.dumps(data)
            if "1X2" in s_data or "ESPOSITO" in s_data or "CARTELLINO" in s_data:
                print(f"\n🎯 FOUND BETTING DATA in {url[:80]} (size {len(s_data)} bytes)!")
                with open("reports/snai_intercepted_odds.json", "w", encoding="utf-8") as f:
                    f.write(s_data)
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.on("response", handle_response)
    
    print("Navigating to SNAI...")
    page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=25000)
    time.sleep(3)
    
    btn = page.locator("button:has-text('Accetta tutti')")
    if btn.count() > 0:
        btn.first.click()
        print("Clicked Accetta tutti")
        time.sleep(6)
        
    tutte_btn = page.locator("text=TUTTE").first
    if tutte_btn.is_visible():
        tutte_btn.click()
        print("Clicked TUTTE")
        time.sleep(6)
        
    print(f"\nTotal JSON API calls captured: {len(json_responses)}")
    for r in json_responses[:20]:
        print(f"  {r['status']} {r['url'][:80]} -> {r['keys']}")
        
    browser.close()
