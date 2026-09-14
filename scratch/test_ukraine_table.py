import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

key = "test85g57"
url = f"https://api.football-data-api.com/league-tables?key={key}&league_id=17191"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        tables = res.get("data", {}).get("all_matches_table_overall", [])
        print("Trovate squadre:", len(tables))
        for t in tables[:10]:
            print(f"{t.get('position')}° {t.get('cleanName')} - Pt: {t.get('points')} (Giocate: {t.get('matchesPlayed')})")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print("Error:", e)
