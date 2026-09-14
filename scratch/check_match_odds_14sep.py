import urllib.request
import json
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'x-fsign': 'SW9D1eZo'
}

matches_to_inspect = [
    ('rFwuw4qS', 'Como vs Parma', 'Serie A'),
    ('dxQcraL7', 'Torino vs Roma', 'Serie A'),
    ('nBSIVLy2', 'Inter vs Udinese', 'Serie A'),
    ('Q1TGrNGq', 'Leeds vs Newcastle', 'Premier League'),
    ('hdqa7PVb', 'Villarreal vs Betis', 'LaLiga'),
    ('zorKqtLb', 'Braga vs Estoril', 'Liga Portugal'),
    ('zs2xjNnm', 'Midtjylland vs Brondby', 'Superliga Danimarca'),
    ('r5HQ6xTH', 'Bodo/Glimt vs Sandefjord', 'Eliteserien Norvegia'),
    ('llKk8XsI', 'Gaziantep vs Fenerbahce', 'Super Lig Turchia'),
    ('8GAxJvHk', 'Flamengo vs Corinthians', 'Brasileirao Serie A')
]

print("=== VERIFICA QUOTE & DETTAGLI PRE-MATCH LUNEDÌ 14 SETTEMBRE 2026 ===")
for mid, name, league in matches_to_inspect:
    # Check match detail feed
    url = f'https://local-global.flashscore.ninja/2/x/feed/df_sui_1_{mid}'
    url_odds = f'https://local-global.flashscore.ninja/2/x/feed/df_od_1_{mid}'
    print(f"\n⚽ {name} [{league}] (ID: {mid}):")
    try:
        req = urllib.request.Request(url_odds, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            odds_items = []
            for item in content.split('~'):
                if 'OD÷' in item or '1X2' in item or 'Over' in item:
                    odds_items.append(item[:80])
            if odds_items:
                print("   Quote trovate:", len(odds_items))
            else:
                print("   Feed quote standard.")
    except Exception as e:
        print("   Odds query note:", e)
