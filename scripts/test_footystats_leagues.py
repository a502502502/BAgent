import requests
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

key = "f2a628dad87df2671c37b2c7eab20de901590c8651b7a332c85bf3c4979dbaba"
# Test league list
url = f"https://api.football-data-api.com/league-list?key={key}"
r = requests.get(url, timeout=10)
print("league-list status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    leagues = data.get("data", [])
    print(f"Total leagues available: {len(leagues)}")
    # Find active leagues
    for l in leagues[:15]:
        print(f"ID: {l.get('id')} | Name: {l.get('name')} | Country: {l.get('country')} | Season: {l.get('season')}")
