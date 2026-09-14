import urllib.request
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
                away = parts.get('AF', '')
                time_ts = parts.get('AD', '')
                try:
                    dt = datetime.datetime.fromtimestamp(int(time_ts))
                    time_str = dt.strftime('%H:%M')
                    hour = dt.hour
                    minute = dt.minute
                except Exception:
                    continue
                
                # Check between 11:00 and 14:30
                # 11:00 <= time <= 14:30
                if (11 <= hour < 14) or (hour == 14 and minute <= 30):
                    matches.append({
                        'league': current_league,
                        'mid': mid,
                        'home': home,
                        'away': away,
                        'time': time_str,
                        'hour': hour,
                        'minute': minute
                    })
        
        matches.sort(key=lambda x: (x['hour'], x['minute']))
        print(f"Trovate {len(matches)} partite tra le 11:00 e le 14:30:\n")
        for m in matches:
            print(f"• [{m['time']}] 🏆 {m['league']} ➔ {m['home']} vs {m['away']} (ID: {m['mid']})")
except Exception as e:
    print('Error:', e)
