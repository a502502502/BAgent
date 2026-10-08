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
        const tips = d.matchListTips || {};
        const smart = d.matchListSmartBets || {};
        return {
            smart: smart,
            tips_sample: Object.entries(tips).slice(0, 15).map(([mid, tlist]) => ({
                match_id: mid,
                count: tlist ? tlist.length : 0,
                tips: tlist
            }))
        };
    }""")
    print("Smart bets:", json.dumps(res["smart"], indent=2))
    print("\nTips sample:")
    for item in res["tips_sample"]:
        print(f"Match ID {item['match_id']} (tips count: {item['count']}):")
        if item['tips']:
            for t in item['tips'][:3]:
                print("  ", t)
    browser.close()
