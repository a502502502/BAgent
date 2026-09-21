import requests, re, datetime

def get_matches(sport_id, target_tournaments):
    url = f"https://local-it.flashscore.ninja/2/x/feed/f_{sport_id}_0_1_it_1"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "x-fsign": "SW9D1eZo"})
    text = r.text
    
    current_tournament = ""
    for block in text.split("~"):
        if block.startswith("ZA÷"):
            current_tournament = block.split("¬")[0].replace("ZA÷", "")
        elif block.startswith("AA÷"):
            # check if tournament matches
            matches_tourn = any(t.lower() in current_tournament.lower() for t in target_tournaments)
            if matches_tourn or len(target_tournaments) == 0:
                m_time = re.search(r"AD÷(\d+)", block)
                m_home = re.search(r"AE÷([^¬]+)", block)
                m_away = re.search(r"AF÷([^¬]+)", block)
                m_status = re.search(r"AB÷([^¬]+)", block)
                if m_time and m_home and m_away:
                    ts = int(m_time.group(1))
                    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=2)))
                    print(f"[{current_tournament}] {m_home.group(1)} vs {m_away.group(1)} -> {dt.strftime('%H:%M CEST')} (Status: {m_status.group(1) if m_status else 'Pre'})")

print("--- TENNIS MATCHES ---")
get_matches(2, ["Tolentino", "Ankara", "Pula", "Falun"])

print("\n--- FOOTBALL MATCHES ---")
get_matches(1, ["Romania", "Macedonia", "Slovakia", "Serbia", "Europa League"])
