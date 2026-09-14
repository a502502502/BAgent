import urllib.request, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0', 'x-fsign': 'SW9D1eZo'}

match_ids = {
    'Como vs Parma': 'rFwuw4qS',
    'Torino vs Roma': 'dxQcraL7',
    'Midtjylland vs Brondby': 'zs2xjNnm',
    'Bodo/Glimt vs Sandefjord': 'r5HQ6xTH',
    'Gaziantep vs Fenerbahce': 'llKk8XsI',
    'Inter vs Udinese': 'nBSIVLy2',
    'Leeds vs Newcastle': 'Q1TGrNGq',
    'Villarreal vs Betis': 'hdqa7PVb',
    'FCSB vs Petrolul': 'pCJCHsN9',
    'Braga vs Estoril': 'zorKqtLb',
    'Rio Ave vs Estrela': 'KSG0qXQF',
    'Flamengo vs Corinthians': '8GAxJvHk'
}

for name, mid in match_ids.items():
    url = f"https://local-global.flashscore.ninja/2/x/feed/df_dos_1_{mid}_"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            odds = {}
            for line in content.split('~'):
                if line.startswith('OA÷'):
                    parts = dict(p.split('÷', 1) for p in line.split('¬') if '÷' in p)
                    market = parts.get('OB', '')
                    val = parts.get('OD', '')
                    if market in ['1', 'X', '2', 'Over 2.5', 'Under 2.5', 'Gol', 'No Gol']:
                        odds[market] = val
            print(f"{name}: {odds}")
    except Exception as e:
        print(f"{name}: Err {e}")
