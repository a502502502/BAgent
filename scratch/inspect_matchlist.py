import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    )
    page.goto("https://oddspedia.com/it/calcio", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000)

    matches = page.evaluate("""() => {
        if (typeof window.__NUXT__ !== 'undefined' && window.__NUXT__.state) {
            const ml = window.__NUXT__.state.matchlist || {};
            return {
                ml_keys: Object.keys(ml),
                matches_count: ml.matches ? Object.keys(ml.matches).length : 0,
                matches_sample: ml.matches ? Object.values(ml.matches).slice(0, 10).map(m => ({
                    id: m.id,
                    ht: m.ht,
                    at: m.at,
                    league: m.league_name,
                    date: m.date,
                    status: m.status
                })) : []
            };
        }
        return null;
    }""")
    print("Matchlist sample:", matches)
    browser.close()
