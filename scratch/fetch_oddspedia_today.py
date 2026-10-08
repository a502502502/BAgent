import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    )
    # Go to oddspedia football matches today
    page.goto("https://oddspedia.com/it/calcio", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000)

    # Extract match list from Nuxt state or DOM
    matches_info = page.evaluate("""() => {
        const res = [];
        if (typeof window.__NUXT__ !== 'undefined' && window.__NUXT__.state) {
            const matches = window.__NUXT__.state.matches || {};
            return Object.keys(matches).slice(0, 30);
        }
        // DOM fallback
        document.querySelectorAll('.match-list-item').forEach(el => {
            res.push(el.innerText.replace(/\\s+/g, ' ').trim());
        });
        return res;
    }""")
    print("Matches extracted count:", len(matches_info))
    print("Sample:", matches_info[:10])
    browser.close()
