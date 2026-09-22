import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        captured_data = []

        def handle_response(response):
            if "netwin.it" in response.url and any(k in response.url.lower() for k in ["event", "sport", "match", "quote", "palinsesto", "prematch"]):
                try:
                    if "json" in response.headers.get("content-type", ""):
                        data = response.json()
                        captured_data.append({"url": response.url, "data": data})
                except Exception:
                    pass

        page.on("response", handle_response)
        
        print("Caricamento https://www.netwin.it/sport...")
        page.goto("https://www.netwin.it/sport", timeout=30000)
        page.wait_for_timeout(5000)
        
        # Cerca i link o testi di calcio
        text_content = page.inner_text("body")
        print("Lunghezza testo pagina:", len(text_content))
        
        # Salvataggio delle API catturate
        print(f"Risposte API catturate: {len(captured_data)}")
        for i, item in enumerate(captured_data[:10]):
            print(f"API {i}: {item['url'][:100]}")
            
        # Cerca input di ricerca
        search_input = page.query_selector("input[type='search'], input[placeholder*='Cerca'], input[placeholder*='cerca']")
        if search_input:
            print("Trovata barra di ricerca! Cerco 'Barnsley'...")
            search_input.fill("Barnsley")
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)
            print("Testo dopo ricerca:", page.inner_text("body")[:500])
        else:
            print("Nessun campo ricerca diretto, cerco elementi partita...")
            # Cerca elementi partita
            matches = page.query_selector_all(".event-row, .match-name, [data-event-id], .event")
            print(f"Elementi partita trovati: {len(matches)}")
            
        browser.close()

if __name__ == "__main__":
    run()
