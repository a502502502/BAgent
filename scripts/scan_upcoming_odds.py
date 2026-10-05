import json
from datetime import datetime, timezone

with open("data/the_odds_api_live.json", "r", encoding="utf-8") as f:
    fixtures = json.load(f)

print(f"Total fixtures in file: {len(fixtures)}")

today_str = "2026-10-05"
tomorrow_str = "2026-10-06"

today_matches = []
for m in fixtures:
    ctime = m.get("commence_time", "")
    if ctime.startswith(today_str) or ctime.startswith(tomorrow_str):
        today_matches.append(m)

print(f"\nMatches for {today_str} and {tomorrow_str}: {len(today_matches)}")
for m in today_matches:
    print(f"[{m['league']}] {m['commence_time']} | {m['home_team']} vs {m['away_team']} (Bookmakers: {len(m['bookmakers'])})")
    # Show best odds for 1X2 and Over/Under
    best_h2h = {"1": 0.0, "X": 0.0, "2": 0.0}
    totals = {}
    for bm in m.get("bookmakers", []):
        for mkt in bm.get("markets", []):
            if mkt.get("key") == "h2h":
                for out in mkt.get("outcomes", []):
                    name = out.get("name")
                    price = out.get("price", 0.0)
                    if name == m["home_team"]:
                        best_h2h["1"] = max(best_h2h["1"], price)
                    elif name == m["away_team"]:
                        best_h2h["2"] = max(best_h2h["2"], price)
                    elif name == "Draw":
                        best_h2h["X"] = max(best_h2h["X"], price)
            elif mkt.get("key") == "totals":
                for out in mkt.get("outcomes", []):
                    point = out.get("point")
                    name = out.get("name")
                    price = out.get("price", 0.0)
                    k = f"{name} {point}"
                    totals[k] = max(totals.get(k, 0.0), price)
    print(f"   Best 1X2: 1@{best_h2h['1']:.2f}, X@{best_h2h['X']:.2f}, 2@{best_h2h['2']:.2f}")
    if totals:
        print(f"   Best Totals: {', '.join([f'{k}@{v:.2f}' for k, v in list(totals.items())[:4]])}")
