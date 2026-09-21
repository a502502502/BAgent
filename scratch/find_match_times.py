import datetime, requests, re

# 1. Otelul Galati timestamp
t_otelul = 1790002800
dt_otelul = datetime.datetime.fromtimestamp(t_otelul, datetime.timezone(datetime.timedelta(hours=2)))
print('Otelul Galati timestamp CEST:', dt_otelul.strftime('%Y-%m-%d %H:%M:%S'))

# 2. Search Flashscore feeds for today (offset 0) and tennis/football
for offset in [0, 1, 2, 3]:
    url = f'https://local-it.flashscore.ninja/2/x/feed/f_1_{offset}_1_it_1'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'x-fsign': 'SW9D1eZo'})
    text = r.text

    matches_to_find = [
        'Otelul', 'Corvinul', 'Struga', 'Arsimi', 'Petrzalka', 'Pohronie', 'Backa', 'Dubocica',
        'Spiteri', 'Primorac', 'Zaytseva', 'Yoruk', 'Dessi', 'Rocco', 'Lane', 'Walltin', 'Beraldo', 'Mondazzi',
        'Omonia', 'Celta'
    ]

    for block in text.split('~AA÷'):
        for m in matches_to_find:
            if m.lower() in block.lower():
                m_time = re.search(r'AD÷(\d+)', block)
                m_home = re.search(r'AE÷([^¬]+)', block)
                m_away = re.search(r'AF÷([^¬]+)', block)
                if m_time and m_home and m_away:
                    ts = int(m_time.group(1))
                    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=2)))
                    time_str = dt.strftime("%Y-%m-%d %H:%M CEST")
                    print(f"Offset {offset} | {m_home.group(1)} vs {m_away.group(1)} -> Kickoff: {time_str}")
                break

# 3. Also check tennis feed (sport 2)
for offset in [0, 1]:
    url = f'https://local-it.flashscore.ninja/2/x/feed/f_2_{offset}_1_it_1'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'x-fsign': 'SW9D1eZo'})
    text = r.text
    for block in text.split('~AA÷'):
        for m in ['Spiteri', 'Primorac', 'Zaytseva', 'Yoruk', 'Dessi', 'Rocco', 'Lane', 'Walltin', 'Beraldo', 'Mondazzi']:
            if m.lower() in block.lower():
                m_time = re.search(r'AD÷(\d+)', block)
                m_home = re.search(r'AE÷([^¬]+)', block)
                m_away = re.search(r'AF÷([^¬]+)', block)
                if m_time and m_home and m_away:
                    ts = int(m_time.group(1))
                    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=2)))
                    time_str = dt.strftime("%Y-%m-%d %H:%M CEST")
                    print(f"TENNIS Offset {offset} | {m_home.group(1)} vs {m_away.group(1)} -> Start: {time_str}")
                break
