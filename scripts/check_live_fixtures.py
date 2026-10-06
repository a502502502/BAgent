import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("API_FOOTBALL_KEY")
headers = {"x-apisports-key": key}

r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=10)
print("Live fixtures status:", r.status_code)
data = r.json()
print("Total live matches:", data.get("results", 0))
for fix in data.get("response", [])[:20]:
    t = fix.get("teams", {})
    g = fix.get("goals", {})
    s = fix.get("fixture", {}).get("status", {})
    print(f"{t.get('home', {}).get('name')} vs {t.get('away', {}).get('name')}: {g.get('home')} - {g.get('away')} ({s.get('elapsed')}')")
