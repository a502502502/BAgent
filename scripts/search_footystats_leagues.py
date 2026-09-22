import requests
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

key = "f2a628dad87df2671c37b2c7eab20de901590c8651b7a332c85bf3c4979dbaba"
url = f"https://api.football-data-api.com/league-list?key={key}"
r = requests.get(url, timeout=10)
leagues = r.json().get("data", [])

target_keywords = ["serie a", "argentina", "brazil", "copa", "italy"]
found = []
for l in leagues:
    name = l.get("name", "").lower()
    country = l.get("country", "").lower()
    if any(k in name or k in country for k in target_keywords):
        latest_season = l.get("season", [])[-1] if l.get("season") else None
        found.append({
            "name": l.get("name"),
            "country": l.get("country"),
            "latest_season": latest_season
        })

print(f"Found {len(found)} target leagues:")
for f in found[:20]:
    print(f"{f['country']} - {f['name']}: {f['latest_season']}")
