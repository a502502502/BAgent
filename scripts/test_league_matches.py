import requests
import json
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")

key = "f2a628dad87df2671c37b2c7eab20de901590c8651b7a332c85bf3c4979dbaba"
# Let's check Italy Serie A (17084) and Brazil Serie A (16544)
for s_id, name in [(17084, "Serie A"), (16544, "Brasileirao"), (17199, "La Liga")]:
    url = f"https://api.football-data-api.com/league-matches?key={key}&season_id={s_id}"
    r = requests.get(url, timeout=12)
    if r.status_code == 200:
        matches = r.json().get("data", [])
        print(f"=== {name} (Season {s_id}): {len(matches)} total matches ===")
        # Filter matches in future or today
        now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        upcoming = [m for m in matches if m.get("date_unix", 0) >= now_ts - 86400]
        print(f"Upcoming/recent matches: {len(upcoming)}")
        for u in upcoming[:5]:
            dt = datetime.datetime.fromtimestamp(u.get("date_unix", 0), tz=datetime.timezone.utc)
            print(f"  [{dt.strftime('%Y-%m-%d %H:%M')}] {u.get('home_name')} vs {u.get('away_name')} | Status: {u.get('status')} | 1: {u.get('odds_ft_1')}, X: {u.get('odds_ft_x')}, 2: {u.get('odds_ft_2')}, O2.5: {u.get('odds_ft_over25')}")
