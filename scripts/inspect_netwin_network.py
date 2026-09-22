import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        # Launch with stealth arguments
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

        urls = []
        page.on("request", lambda req: urls.append((req.method, req.url)))

        print("Navigazione su https://www.netwin.it/scommesse...")
        try:
            page.goto("https://www.netwin.it/scommesse", wait_until="networkidle", timeout=25000)
        except Exception as e:
            print("Timeout networkidle, procedo comunque:", e)

        page.wait_for_timeout(3000)
        print("Titolo pagina:", page.title())
        print("URL corrente:", page.url)

        # Filtra le richieste API
        api_requests = [u for u in urls if any(k in u[1].lower() for k in ["api", "json", "sport", "event", "cart", "betslip", "odds", "book"])]
        print(f"\nRichieste API rilevate ({len(api_requests)}):")
        for m, u in api_requests[:25]:
            print(f"[{m}] {u[:120]}")

        # Salva screenshot per capire cosa vede il browser
        page.screenshot(path="reports/netwin_inspect.png")
        print("\nScreenshot salvato in reports/netwin_inspect.png")
        browser.close()

if __name__ == "__main__":
    inspect()
