import urllib.request
import json
import sys
import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'x-fsign': 'SW9D1eZo'
}

url = 'https://local-global.flashscore.ninja/2/x/feed/f_1_0_3_it-it_1'
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=12) as resp:
        content = resp.read().decode('utf-8', errors='replace')
        current_league = ''
        matches = []
        for line in content.split('~'):
            if line.startswith('ZA÷'):
                parts = line.split('¬')
                for p in parts:
                    if p.startswith('ZA÷'):
                        current_league = p[3:]
            elif line.startswith('AA÷'):
                parts = {}
                for item in line.split('¬'):
                    if '÷' in item:
                        k, v = item.split('÷', 1)
                        parts[k] = v
                # Flashscore match line keys:
                # AA = match ID
                # CX = Home Team Name
                # AF = Away Team Name
                # AD = Timestamp (seconds)
                # BC / BD / BE = odds or similar if present
                mid = parts.get('AA', '')
                home = parts.get('CX', '')
                away = parts.get('AF', '')
                time_ts = parts.get('AD', '')
                try:
                    time_str = datetime.datetime.fromtimestamp(int(time_ts)).strftime('%H:%M') if time_ts else ''
                except Exception:
                    time_str = ''
                matches.append({
                    'league': current_league,
                    'mid': mid,
                    'home': home,
                    'away': away,
                    'time': time_str,
                    'raw': parts
                })

        print(f"=== PARTITE DI OGGI (LUNEDÌ 14 SETTEMBRE 2026) ===")
        valid_leagues = [
            'ITALY: Serie A',
            'ENGLAND: Premier League',
            'SPAIN: LaLiga',
            'PORTUGAL: Liga Portugal',
            'DENMARK: Superliga',
            'NORWAY: Eliteserien',
            'SWEDEN: Superettan',
            'TURKEY: Super Lig',
            'ROMANIA: Superliga',
            'IRELAND: Premier Division',
            'BRAZIL: Serie A Betano',
            'ARGENTINA: Torneo Betano'
        ]
        
        filtered = []
        for m in matches:
            for vl in valid_leagues:
                if vl.lower() in m['league'].lower():
                    filtered.append(m)
                    break
        
        print(f"Trovate {len(filtered)} partite nei campionati target:")
        for m in filtered:
            print(f"⚽ [{m['time']}] {m['league']} ➔ {m['home']} vs {m['away']} (ID: {m['mid']})")
            
except Exception as e:
    print('Error:', e)
