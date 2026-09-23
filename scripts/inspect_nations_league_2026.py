import requests
import datetime
import sys

import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

env_path = Path(__file__).resolve().parent.parent / '.env'
key = os.environ.get('FOOTYSTATS_API_KEY', '')
if not key and env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        if line.startswith('FOOTYSTATS_API_KEY='):
            key = line.split('=', 1)[1].strip()

url = f'https://api.football-data-api.com/league-matches?key={key}&league_id=16808'

r = requests.get(url, timeout=15)
data = r.json()
matches = data.get('data', [])
print(f'Total matches in Nations League 2026/2027 (ID: 16808): {len(matches)}')

# Filter matches around 24 September 2026
target_date = datetime.date(2026, 9, 24)
sep24_matches = []
for m in matches:
    ts = m.get('date_unix', 0)
    dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    if dt.date() == target_date:
        sep24_matches.append((dt, m))

print(f'\nMatches on {target_date} ({len(sep24_matches)} found):')
for dt, m in sep24_matches:
    home = m.get('home_name')
    away = m.get('away_name')
    status = m.get('status')
    o1 = m.get('odds_ft_1')
    ox = m.get('odds_ft_x')
    o2 = m.get('odds_ft_2')
    o25 = m.get('odds_ft_over25')
    u25 = m.get('odds_ft_under25')
    btts = m.get('odds_btts_yes')
    xg_h = m.get('team_a_xg') or m.get('home_xg')
    xg_a = m.get('team_b_xg') or m.get('away_xg')
    print(f"[{dt.strftime('%H:%M UTC')}] {home} vs {away} ({status})")
    print(f"    1X2: {o1} | {ox} | {o2} | O2.5: {o25} | U2.5: {u25} | BTTS: {btts}")
    print(f"    xG: Home={xg_h}, Away={xg_a}")

if not sep24_matches:
    print("\nListing first 10 matches of the tournament to check dates:")
    for m in matches[:10]:
        ts = m.get('date_unix', 0)
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        print(f"  [{dt.strftime('%Y-%m-%d %H:%M')}] {m.get('home_name')} vs {m.get('away_name')} ({m.get('status')})")
