import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("ODDS_API_KEY", "415a8d781681e9b8b8884575a0a15a09")

url = f"https://api.the-odds-api.com/v4/sports/soccer_argentina_primera_division/odds?apiKey={key}&regions=eu&markets=h2h,totals"
r = requests.get(url, timeout=10)
print("The Odds API status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    print("Matches returned:", len(data))
    for m in data[:5]:
        print(f"  {m.get('home_team')} vs {m.get('away_team')}")
        bookies = [b.get('key') for b in m.get('bookmakers', [])]
        print(f"    Bookmakers ({len(bookies)}): {bookies[:5]}")
else:
    print("Response:", r.text[:300])
