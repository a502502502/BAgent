import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

key = "test85g57"
url = f"https://api.football-data-api.com/league-list?key={key}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=10) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    for item in res.get("data", []):
        if "Ukrainian Premier League" in item.get("name", ""):
            print("Found:", item.get("name"), "Season data:", item.get("season"))
            break
