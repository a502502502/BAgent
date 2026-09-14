import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

key = "test85g57"

endpoints = [
    ("league-list", f"https://api.football-data-api.com/league-list?key={key}"),
    ("todays-matches", f"https://api.football-data-api.com/todays-matches?key={key}"),
    ("league-tables (EPL)", f"https://api.football-data-api.com/league-tables?key={key}&league_id=2012"),
    ("match (sample)", f"https://api.football-data-api.com/match?key={key}&match_id=12345"),
    ("teams (sample)", f"https://api.football-data-api.com/teams?key={key}&team_id=150")
]

print("=== TESTING FOOTYSTATS API ENDPOINTS WITH KEY: test85g57 ===")
for name, url in endpoints:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            status = data.get("status")
            message = data.get("message")
            data_content = data.get("data")
            is_list = isinstance(data_content, list)
            length = len(data_content) if is_list else (1 if data_content else 0)
            print(f"✅ {name}: Status={status}, Items={length}, Message={message}")
            if data_content and not is_list and isinstance(data_content, dict):
                print(f"   Keys in data: {list(data_content.keys())[:8]}")
            elif is_list and length > 0:
                print(f"   Sample item: {data_content[0] if isinstance(data_content[0], (str, int)) else list(data_content[0].keys())[:6]}")
    except urllib.error.HTTPError as e:
        print(f"❌ {name}: HTTP {e.code} - {e.reason}")
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
