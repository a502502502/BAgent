import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

key = "test85g57"
url = f"https://api.football-data-api.com/league-tables?key={key}&league_id=2012"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    tables = data.get("data", {}).get("all_matches_table_overall", [])
    print(f"Squadre trovate nella classifica: {len(tables)}")
    for row in tables[:5]:
        print(f"Pos {row.get('position')}: {row.get('cleanName')} | Punti: {row.get('points')} | Partite: {row.get('matchesPlayed')} | GF: {row.get('seasonGoals')} | GS: {row.get('seasonConcededNum')}")
