import json

with open("data/the_odds_api_live.json", encoding="utf-8") as f:
    fixtures = json.load(f)

tonight_names = ["France", "Italy", "Bosnia", "Ukraine", "Northern Ireland", "Romania", "Montenegro"]

for fx in fixtures:
    home = fx.get("home_team", "")
    away = fx.get("away_team", "")
    if any(tn.lower() in home.lower() for tn in tonight_names):
        print(f"=== {home} vs {away} ===")
        for b in fx.get("bookmakers", [])[:3]:
            print(f"   Bookmaker: {b.get('title')}")
            for m in b.get("markets", []):
                outcomes = " | ".join(f"{o['name']}: {o['price']}" for o in m.get("outcomes", []))
                print(f"      {m.get('key')}: {outcomes}")
