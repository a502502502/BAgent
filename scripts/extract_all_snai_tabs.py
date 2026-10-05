import time
from playwright.sync_api import sync_playwright

TABS_TO_EXTRACT = [
    "PRINCIPALI",
    "GIOCATORI",
    "MULTI GIOCATORI",
    "1X2 GIOCATORI",
    "SANZIONI",
    "SPECIALI MATCH",
    "CORNER",
    "GOAL",
    "COMBO",
    "MULTIGOAL",
    "RISULTATI",
    "TEMPI"
]

all_extracted_text = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    print("Caricamento pagina SNAI...")
    page.goto("https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia", timeout=25000)
    time.sleep(3)
    
    # 1. Accept cookies
    btn = page.locator("button:has-text('Accetta tutti')")
    if btn.count() > 0:
        btn.first.click()
        print("Cookie 'Accetta tutti' cliccato.")
        time.sleep(5)
        
    for tab_name in TABS_TO_EXTRACT:
        print(f"\n--- Clicco sul tab: {tab_name} ---")
        try:
            tab_locator = page.get_by_text(tab_name, exact=True).first
            if tab_locator.is_visible(timeout=3000):
                tab_locator.click()
                print(f"   -> Cliccato tab {tab_name}!")
                time.sleep(3)
                
                # Check for any collapsed sub-accordions inside this tab
                # Click any button or element that expands
                try:
                    # In SNAI each market group can be expanded
                    headers = page.locator(".metamarketHeader, .accordion-header, [data-toggle='collapse']")
                    h_count = headers.count()
                    print(f"      Trovati {h_count} sottomercati in {tab_name}")
                    for i in range(min(h_count, 40)):
                        try:
                            headers.nth(i).click(timeout=300)
                        except Exception:
                            pass
                    time.sleep(1)
                except Exception:
                    pass
                
                tab_text = page.inner_text("body")
                all_extracted_text.append(f"\n\n===== SEZIONE: {tab_name} =====\n\n" + tab_text)
                print(f"      Estratti {len(tab_text)} caratteri per {tab_name}")
                if "BARELLA" in tab_text:
                    print(f"      [OK] BARELLA trovato in {tab_name}!")
            else:
                print(f"   -> Tab {tab_name} non visibile.")
        except Exception as e:
            print(f"Errore tab {tab_name}:", e)
            
    full_dump = "\n".join(all_extracted_text)
    print(f"\nTotale caratteri raccolti: {len(full_dump)}")
    print("Contiene BARELLA N. O BASTONI A.?", "BARELLA N. O BASTONI A." in full_dump)
    print("Contiene CELIK?", "CELIK" in full_dump)
    
    with open("reports/snai_all_tabs_extracted.txt", "w", encoding="utf-8") as f:
        f.write(full_dump)
        
    print("Salvato in reports/snai_all_tabs_extracted.txt!")
    browser.close()
