import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ODDS_API_KEY", "415a8d781681e9b8b8884575a0a15a09")

# Check available soccer sports
sports_url = f"https://api.the-odds-api.com/v4/sports?apiKey={api_key}"
r = requests.get(sports_url, timeout=10)
if r.status_code != 200:
    print("Error fetching sports:", r.status_code, r.text)
    exit(1)

sports = r.json()
soccer_sports = [s for s in sports if s.get("group") == "Soccer" and s.get("active")]
print(f"Active Soccer Sports: {len(soccer_sports)}")
for s in soccer_sports:
    print(f"  {s['key']}: {s['title']}")

# Fetch upcoming matches for today across key active leagues
key_leagues = [
    "soccer_uefa_nations_league",
    "soccer_argentina_primera_division",
    "soccer_italy_serie_a",
    "soccer_spain_la_liga",
    "soccer_epl",
    "soccer_brazil_campeonato"
]

all_fixtures = []

for league in key_leagues:
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds?apiKey={api_key}&regions=eu&markets=h2h,totals"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        matches = resp.json()
        print(f"League '{league}': {len(matches)} matches found")
        for m in matches:
            all_fixtures.append({
                "league": league,
                "id": m["id"],
                "commence_time": m["commence_time"],
                "home_team": m["home_team"],
                "away_team": m["away_team"],
                "bookmakers": m["bookmakers"]
            })
    else:
        print(f"League '{league}' returned {resp.status_code}: {resp.text[:100]}")

print(f"\nTotal fixtures retrieved: {len(all_fixtures)}")
with open("data/the_odds_api_live.json", "w", encoding="utf-8") as f:
    json.dump(all_fixtures, f, indent=2)
print("Saved fixtures to data/the_odds_api_live.json")
