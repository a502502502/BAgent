import requests, re, json

def get_tennis_live():
    url = "https://local-it.flashscore.ninja/2/x/feed/f_2_0_1_it_1"
    headers = {"User-Agent": "Mozilla/5.0", "x-fsign": "SW9D1eZo"}
    r = requests.get(url, headers=headers)
    text = r.text

    targets = [
        {"name": "Walltin vs Lane", "kw": ["walltin", "lane"], "sel": "Lewie Lane (2)", "odds": 1.08},
        {"name": "Rocco vs Dessì", "kw": ["rocco", "dessi", "dessì"], "sel": "Marco Dessì (2)", "odds": 1.20},
        {"name": "Naito vs Avdeeva", "kw": ["naito", "avdeeva"], "sel": "Julia Avdeeva (2)", "odds": 1.52},
        {"name": "Ristic vs Rus", "kw": ["ristic", "rus"], "sel": "Arantxa Rus (2)", "odds": 2.15},
        {"name": "Hercog vs Romero Gormaz", "kw": ["hercog", "romero"], "sel": "Over 18.5 Game", "odds": 1.40}
    ]

    results = []
    for b in text.split("~AA÷"):
        b_lower = b.lower()
        for t in targets:
            if any(k in b_lower for k in t["kw"]):
                m_home = re.search(r"AE÷([^¬]+)", b)
                m_away = re.search(r"AF÷([^¬]+)", b)
                m_status = re.search(r"AB÷([^¬]+)", b)
                m_set_h = re.search(r"AG÷([^¬]+)", b)
                m_set_a = re.search(r"AH÷([^¬]+)", b)
                
                # set games
                ba = re.search(r"BA÷([^¬]+)", b)
                bb = re.search(r"BB÷([^¬]+)", b)
                bc = re.search(r"BC÷([^¬]+)", b)
                bd = re.search(r"BD÷([^¬]+)", b)
                be = re.search(r"BE÷([^¬]+)", b)
                bf = re.search(r"BF÷([^¬]+)", b)
                
                # point
                wa = re.search(r"WA÷([^¬]+)", b)
                wb = re.search(r"WB÷([^¬]+)", b)

                h = m_home.group(1) if m_home else "Home"
                a = m_away.group(1) if m_away else "Away"
                st_code = m_status.group(1) if m_status else "1"
                
                st_label = "Pre-Match"
                if st_code == "2":
                    st_label = "LIVE"
                elif st_code == "3":
                    st_label = "FINALE"

                sh = m_set_h.group(1) if m_set_h else "0"
                sa = m_set_a.group(1) if m_set_a else "0"

                score_detail = f"Sets: {sh}-{sa}"
                games = []
                if ba and bb:
                    games.append(f"1S: {ba.group(1)}-{bb.group(1)}")
                if bc and bd:
                    games.append(f"2S: {bc.group(1)}-{bd.group(1)}")
                if be and bf:
                    games.append(f"3S: {be.group(1)}-{bf.group(1)}")
                if games:
                    score_detail += " (" + ", ".join(games) + ")"
                if wa or wb:
                    score_detail += f" | Game Pts: {wa.group(1) if wa else '0'}-{wb.group(1) if wb else '0'}"

                results.append({
                    "target": t["name"],
                    "match": f"{h} vs {a}",
                    "selection": t["sel"],
                    "odds": t["odds"],
                    "status": st_label,
                    "score": score_detail
                })
                break
    return results

if __name__ == "__main__":
    res = get_tennis_live()
    print(json.dumps(res, indent=2))
