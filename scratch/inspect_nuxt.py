import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    )
    page.goto("https://oddspedia.com/it/calcio", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000)

    nuxt_keys = page.evaluate("""() => {
        if (typeof window.__NUXT__ !== 'undefined') {
            return {
                keys: Object.keys(window.__NUXT__),
                state_keys: window.__NUXT__.state ? Object.keys(window.__NUXT__.state) : [],
                data_len: window.__NUXT__.data ? window.__NUXT__.data.length : 0
            };
        }
        return null;
    }""")
    print("NUXT structure:", nuxt_keys)
    browser.close()
