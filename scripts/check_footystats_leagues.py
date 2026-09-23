import requests
import json
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

# 1. Check user info
url_pkg = f'https://api.football-data-api.com/user?key={key}'
try:
    r = requests.get(url_pkg, timeout=10)
    print('User info:', r.json())
except Exception as e:
    print('User error:', e)

# 2. Check leagues
url_leagues = f'https://api.football-data-api.com/league-list?key={key}'
try:
    r = requests.get(url_leagues, timeout=10)
    data = r.json()
    leagues = data.get('data', [])
    print(f'\nTotal leagues available in account: {len(leagues)}')
    for l in leagues:
        c_name = l.get('name')
        country = l.get('country')
        season = l.get('season')
        lid = l.get('id')
        print(f"  [{lid}] {c_name} ({country}) - Season: {season}")
except Exception as e:
    print('Leagues error:', e)
