import json
from pathlib import Path

nl_dir = Path("reports/snai_nl/catalog")

def search_market_in_match(filename, keywords):
    p = nl_dir / filename
    if not p.exists():
        print(f"File non trovato: {filename}")
        return
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    print(f"\n=======================================================")
    print(f"MATCH: {d.get('match')} (Totale mercati: {len(d.get('markets', []))})")
    print(f"=======================================================")
    found = 0
    for m in d.get("markets", []):
        m_name = m.get("market", "")
        line = m.get("line", "")
        full = f"{m_name} {line}".lower()
        if any(k.lower() in full for k in keywords):
            open_outs = [o for o in m.get("outcomes", []) if o.get("open") and 1.20 <= float(o.get("odds", 0)) <= 1.70]
            if open_outs:
                for o in open_outs[:5]:
                    print(f"  [{m_name}] {line} -> {o.get('selection')} @ {o.get('odds')}")
                    found += 1
                    if found >= 15:
                        return

print("--- RICERCA MERCATI SPECIALI NATIONS LEAGUE ---")
search_market_in_match("croazia---spagna.json", ["yamal", "palo", "tiri", "falli", "corner"])
search_market_in_match("scozia---slovenia.json", ["corner", "angol"])
search_market_in_match("inghilterra---repubblica-ceca.json", ["cartellin", "ammoniz", "punti"])
search_market_in_match("italia---turchia.json", ["tiri", "palo", "corner", "multigoal"])
search_market_in_match("francia---belgio.json", ["mbapp", "tiri", "palo", "corner"])
search_market_in_match("kazakistan---isole-far-oer.json", ["combo", "multigoal", "dnb"])
