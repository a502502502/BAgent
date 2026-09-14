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
                mid = parts.get('AA', '')
                home = parts.get('CX', '')
                away = parts.get('ER', '')
                time_ts = parts.get('AD', '')
                status = parts.get('AB', '')
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
                    'status': status
                })
        print(f'Total matches found today: {len(matches)}')
        leagues = {}
        for m in matches:
            l = m['league']
            if l not in leagues:
                leagues[l] = []
            leagues[l].append(m)
        print('=== SELEZIONE CAMPIONATI E PARTITE OGGI (14 Settembre 2026) ===')
        for l, mlist in leagues.items():
            l_upper = l.upper()
            if any(k in l_upper for k in ['ITALIA', 'SPAGNA', 'INGHILTERRA', 'FRANCIA', 'GERMANIA', 'PORTOGALLO', 'TURCHIA', 'OLANDA', 'SVEZIA', 'DANIMARCA', 'SERIE', 'LIGA', 'PREMIER', 'SUPER', 'PRIMEIRA', 'CHAMPIONSHIP', 'ARGENTINA', 'BRASILE', 'POLONIA', 'ROMANIA', 'BELGIO', 'SVIZZERA']):
                print(f'\n🏆 {l} ({len(mlist)} partite):')
                for m in mlist:
                    print(f"   • [{m['time']}] {m['home']} vs {m['away']} (ID: {m['mid']})")
except Exception as e:
    print('Error fetching schedule:', e)
