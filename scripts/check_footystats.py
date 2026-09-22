import requests
import json
import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")

url = "https://api.football-data-api.com/todays-matches?key=f2a628dad87df2671c37b2c7eab20de901590c8651b7a332c85bf3c4979dbaba"
r = requests.get(url, timeout=15)
data = r.json()
print("Matches found:", len(data.get("data", [])))
for m in data.get("data", []):
    ts = m.get("date_unix", 0)
    dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    comp = m.get("competition_name") or m.get("league_name") or "Unknown"
    home = m.get("home_name")
    away = m.get("away_name")
    status = m.get("status")
    odds_1 = m.get("odds_ft_1")
    odds_x = m.get("odds_ft_x")
    odds_2 = m.get("odds_ft_2")
    odds_o25 = m.get("odds_ft_over25")
    odds_u25 = m.get("odds_ft_under25")
    print(f"[{dt.strftime('%Y-%m-%d %H:%M UTC')}] {comp}: {home} vs {away} ({status}) | 1: {odds_1}, X: {odds_x}, 2: {odds_2} | O2.5: {odds_o25}, U2.5: {odds_u25}")
