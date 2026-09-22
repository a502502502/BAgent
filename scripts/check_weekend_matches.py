import requests
import json
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")

key = "f2a628dad87df2671c37b2c7eab20de901590c8651b7a332c85bf3c4979dbaba"
for d in ["2026-09-26", "2026-09-27"]:
    r = requests.get(f"https://api.football-data-api.com/todays-matches?date={d}&key={key}")
    data = r.json().get("data", [])
    print(f"=== {d} ({len(data)} matches) ===")
    for m in data:
        o1 = m.get("odds_ft_1", 0)
        if o1 > 0:
            ts = m.get("date_unix", 0)
            dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
            home = m.get("home_name")
            away = m.get("away_name")
            print(f"[{dt.strftime('%H:%M UTC')}] {home} vs {away} | 1: {o1}, X: {m.get('odds_ft_x')}, 2: {m.get('odds_ft_2')} | 1X: {m.get('odds_doublechance_1x')} | O1.5: {m.get('odds_ft_over15')} | O2.5: {m.get('odds_ft_over25')}, U2.5: {m.get('odds_ft_under25')}")
