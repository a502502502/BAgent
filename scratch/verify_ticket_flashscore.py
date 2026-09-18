import sys, json
sys.path.insert(0, ".")
from services.football.external.sources.flashscore_live import FlashscoreLiveEngine

engine = FlashscoreLiveEngine()
matches = engine.fetch_feed()
print(f"Feed Flashscore caricato: {len(matches)} partite totali")

ticket_targets = [
    {"id": 1, "name": "Chernomorets Odessa vs Obolon Kyiv", "kw": ["odesa", "chernomorets", "obolon"]},
    {"id": 2, "name": "Arabia Saudita U23 vs Qatar U23", "kw": ["saudi", "qatar"]},
    {"id": 3, "name": "Maccabi Yavne vs Hapoel Herzelia", "kw": ["yavne", "herzliya", "herzelia"]},
    {"id": 4, "name": "Zhejiang FC vs Wuhan Three Towns", "kw": ["zhejiang", "wuhan"]},
    {"id": 5, "name": "Polissya Zhytomyr vs Kryvbas", "kw": ["polissya", "kryvbas"]},
    {"id": 6, "name": "Hapoel Tel Aviv vs Hapoel Petah Tikva", "kw": ["tel aviv", "petah tikva"]},
    {"id": 7, "name": "Highbury FC vs Gomora United", "kw": ["highbury", "gomora"]}
]

for t in ticket_targets:
    found = None
    for m in matches:
        txt = (m["home"] + " " + m["away"]).lower()
        if any(k in txt for k in t["kw"]):
            found = m
            break
    if found:
        print(f"[Leg {t['id']}] {t['name']}")
        print(f"       -> Flashscore: {found['home']} vs {found['away']}")
        print(f"       -> Risultato:  {found['score']} ({found['status']} - {found['period']})")
    else:
        print(f"[Leg {t['id']}] {t['name']} -> NON TROVATA NEL FEED (o non iniziata)")
