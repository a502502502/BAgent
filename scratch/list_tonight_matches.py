import os, requests, sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv(".env")
key = os.getenv("FOOTYSTATS_API_KEY", "")

r = requests.get(f"https://api.football-data-api.com/todays-matches?key={key}")
if r.status_code == 200:
    for m in r.json().get("data", []):
        h = m.get("home_name")
        a = m.get("away_name")
        mid = m.get("id")
        t = m.get("date_unix")
        print(f"[{mid}] {h} vs {a} - Time: {t}")
