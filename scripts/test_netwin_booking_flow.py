import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import time

def test_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("1. Apertura https://www.netwin.it/scommesse...")
        page.goto("https://www.netwin.it/scommesse", timeout=30000)
        page.wait_for_timeout(3000)

        # 2. Chiudi Cookiebot
        print("2. Chiusura Cookiebot...")
        try:
            accept_btn = page.locator("button:has-text('Accetta tutti'), #CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
            if accept_btn.is_visible(timeout=5000):
                accept_btn.click()
                print("   ✅ Cookiebot chiuso.")
                page.wait_for_timeout(2000)
        except Exception as e:
            print("   ⚠️ Cookiebot non trovato o errore:", e)

        # 3. Screenshot dopo chiusura cookie
        page.screenshot(path="reports/netwin_no_cookie.png")
        print("   Screenshot salvato in reports/netwin_no_cookie.png")

        # 4. Trova barra di ricerca
        print("3. Ricerca campo input...")
        search_inputs = page.locator("input").all()
        print(f"   Totale campi input trovati: {len(search_inputs)}")
        for i, inp in enumerate(search_inputs):
            try:
                placeholder = inp.get_attribute("placeholder") or ""
                inp_id = inp.get_attribute("id") or ""
                inp_cls = inp.get_attribute("class") or ""
                print(f"   Input {i}: id='{inp_id}', placeholder='{placeholder}', class='{inp_cls[:40]}'")
            except Exception:
                pass

        # 5. Cerca pulsanti quote visibili nella pagina principale
        print("4. Ricerca quote sulla home...")
        odd_buttons = page.locator(".odd, [data-odd], button.odd-btn, .cell-odd, div[class*='odd']").all()
        print(f"   Quote trovate: {len(odd_buttons)}")
        for b in odd_buttons[:5]:
            try:
                print("   Quota text:", b.inner_text().replace("\n", " | "))
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    test_flow()
