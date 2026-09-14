import urllib.request, datetime, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0', 'x-fsign': 'SW9D1eZo'}
url = 'https://local-global.flashscore.ninja/2/x/feed/f_1_0_3_it-it_1'
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=12) as resp:
        content = resp.read().decode('utf-8', errors='replace')
        curr_league = ''
        evening_matches = []
        for line in content.split('~'):
            if line.startswith('ZA÷'):
                parts = dict(p.split('÷', 1) for p in line.split('¬') if '÷' in p)
                curr_league = parts.get('ZA', '')
            elif line.startswith('AA÷'):
                parts = dict(p.split('÷', 1) for p in line.split('¬') if '÷' in p)
                home = parts.get('CX', parts.get('AE', ''))
                away = parts.get('AF', parts.get('ER', ''))
                time_ts = parts.get('AD', '')
                status = parts.get('AB', '')
                try:
                    dt = datetime.datetime.fromtimestamp(int(time_ts))
                    time_str = dt.strftime('%H:%M')
                except:
                    time_str = ''
                if time_str and time_str >= '18:00':
                    evening_matches.append({
                        'league': curr_league,
                        'time': time_str,
                        'home': home,
                        'away': away,
                        'mid': parts.get('AA', ''),
                        'status': status
                    })
        
        # Priority leagues
        priority_keywords = [
            'SERIE A', 'LALIGA', 'PREMIER LEAGUE', 'SUPERLIGA', 'ELITESERIEN', 
            'LIGA PORTUGAL', 'SUPER LIG', 'SUPERETTAN', 'LIGAT HA\'AL', 
            'SERIE B', 'PRIMERA NACIONAL', 'LIGA PROFESIONAL', 'LIGA PRO', 'LIGA MX'
        ]
        
        filtered = []
        for m in evening_matches:
            l_up = m['league'].upper()
            if any(k in l_up for k in priority_keywords) or any(c in l_up for c in ['ITALIA', 'SPAGNA', 'PORTOGALLO', 'INGHILTERRA', 'DANIMARCA', 'NORVEGIA', 'TURCHIA', 'ROMANIA']):
                filtered.append(m)
                
        print(f"Trovate {len(filtered)} partite serali di rilievo:")
        for m in sorted(filtered, key=lambda x: x['time']):
            print(f"[{m['time']}] {m['league']} -> {m['home']} vs {m['away']} (ID: {m['mid']})")
except Exception as e:
    print('Error:', e)
