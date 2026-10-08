import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    )
    page.goto("https://oddspedia.com/it/calcio", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000)

    res = page.evaluate("""() => {
        const d = window.__NUXT__.data[0];
        const ml = d.matchList || [];
        const smart = d.matchListSmartBets || {};
        const tips = d.matchListTips || {};
        return {
            matches_count: ml.length,
            matches: ml.slice(0, 30).map(m => ({
                id: m.id,
                ht: m.ht,
                at: m.at,
                date: m.date,
                league: m.league_name || m.slug,
                url: m.url
            })),
            smart_bets: Object.keys(smart).length,
            smart_sample: smart,
            tips_count: Object.keys(tips).length
        };
    }""")
    print("Matches in matchList:", res["matches_count"])
    for m in res["matches"]:
        print(f"  {m['date']} | {m['league']} | {m['ht']} vs {m['at']} | URL: {m['url']}")
    print("\nSmart Bets keys count:", res["smart_bets"])
    print("Tips count:", res["tips_count"])
    browser.close()
