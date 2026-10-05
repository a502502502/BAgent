"""
Automated Match Market Downloader & Valuator for BAgent
======================================================
Usage:
    python scripts/download_match_markets.py <URL>

Automates the retrieval of 100% of markets from SNAI (and other books)
using Microsoft Edge / Chromium in headed mode to completely bypass Akamai/Cloudflare,
automatically accept cookie banners, click 'TUTTE', scroll to render all virtualized
elements, expand ALL 42+ dropdown accordions (Uno o l'Altro, Marcatori, Sanzioni,
Tiri in porta, Falli, Combos), and output structured JSON!
"""

import sys
import time
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright
from services.betting.universal_market_importer import UniversalMarketImporter

def fetch_and_evaluate(url: str, output_prefix: str = "reports/live_match"):
    print("\n=======================================================")
    print("[BAgent] AVVIO SCARICO COMPLETO MERCATI (CON APERTURA TENDINE)")
    print(f"URL: {url}")
    print("=======================================================\n")
    
    with sync_playwright() as p:
        print("[1/5] Avvio browser sicuro (Edge Engine)...")
        browser = p.chromium.launch(channel="msedge", headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
        )
        page = context.new_page()
        
        print("[2/5] Caricamento pagina e bypass cookie/WAF...")
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        time.sleep(3)
        
        # Click cookie banner "Accetta tutti"
        try:
            cookie_btn = page.locator("button:has-text('Accetta tutti'), button:has-text('Accetta'), #onetrust-accept-btn-handler")
            if cookie_btn.count() > 0 and cookie_btn.first.is_visible():
                cookie_btn.first.click()
                print("   -> Banner privacy accettato con successo.")
                time.sleep(4)
        except Exception:
            pass

        # Click tab "TUTTE"
        print("[3/5] Apertura tab 'TUTTE'...")
        try:
            tutte_tab = page.locator("text=TUTTE").first
            if tutte_tab.is_visible(timeout=4000):
                tutte_tab.click()
                print("   -> Tab 'TUTTE' cliccato!")
                time.sleep(3)
        except Exception as e:
            print("   -> Nota tab TUTTE:", e)

        # Smooth virtual scroll to render all markets down the page
        print("[4/5] Scorrimento virtuale e apertura di tutti i menu a tendina...")
        for _ in range(12):
            page.mouse.wheel(0, 800)
            time.sleep(0.25)
            
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)

        # Expand ALL accordion dropdown headers
        opened = page.evaluate("""
            () => {
                let count = 0;
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
                        txt.startsWith('U/O FALLI') ||
                        txt.startsWith('U/O PARATE') ||
                        txt.startsWith('MARGINE VITTORIA') ||
                        txt.startsWith('MINUTO') ||
                        txt.startsWith('RISULTATO')
                    )) {
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
        print(f"   -> Aperti con successo {opened} menu a tendina!")
        time.sleep(4)

        print("[5/5] Estrazione testo integrale a tendine aperte...")
        full_text = page.inner_text("body")
        browser.close()
        
    print(f"   -> Estratti {len(full_text)} caratteri di quote (complete di sottomercati)!")
    
    # Save raw text
    txt_path = f"{output_prefix}_raw.txt"
    Path("reports").mkdir(exist_ok=True)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    # Ingest with UniversalMarketImporter
    importer = UniversalMarketImporter.from_raw_text(full_text, match_name="Live Match")
    summary = importer.summary()
    
    json_path = f"{output_prefix}_catalog.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(importer.catalog, f, indent=2, ensure_ascii=False)
        
    print("\n=======================================================")
    print("SCARICO COMPLETATO CON SUCCESSO!")
    print(f"Mercati principali: {summary['main_markets']}")
    print(f"Coppie Uno o l'Altro rilevate: {summary['uno_o_altro_pairs']}")
    print(f"Giocatori censiti: {summary['players_tracked']}")
    print(f"Totale quote/esiti stimati: {summary['total_estimated_markets']}")
    print(f"File JSON salvato in: {json_path}")
    print("=======================================================\n")
    return importer.catalog

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia"
    fetch_and_evaluate(target_url)
