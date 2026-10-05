import json

with open("data/the_odds_api_live.json", encoding="utf-8") as f:
    data = json.load(f)

nl = [m for m in data if m.get("league") == "soccer_uefa_nations_league"]
print(f"Total Nations League fixtures: {len(nl)}\n")
for i, m in enumerate(nl, 1):
    print(f"[{i}] {m['commence_time']} | {m['home_team']} vs {m['away_team']}")
    # print 1x2 odds from first bookmaker if available
    bks = m.get("bookmakers", [])
    if bks:
        bk = bks[0]
        markets = {mk["key"]: mk["outcomes"] for mk in bk.get("markets", [])}
        h2h = markets.get("h2h", [])
        h2h_str = " | ".join(f"{o['name']}: {o['price']}" for o in h2h)
        print(f"    Bookmaker ({bk.get('title')}): {h2h_str}")
