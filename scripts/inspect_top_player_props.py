import json
from pathlib import Path

p = Path("reports/snai_nl/catalog")

def inspect_match_props(fn):
    fl = p / fn
    with open(fl, encoding="utf-8") as fp:
        d = json.load(fp)
    print(f"\n=======================================================")
    print(f"MATCH: {d.get('match')}")
    print(f"=======================================================")
    
    for m in d.get("markets", []):
        mkt = m.get("market", "").strip()
        line = m.get("line", "").strip()
        full = f"{mkt} {line}".upper()
        
        # Look for player props:
        # 1. Falli commessi / subiti / quasi cartellino
        # 2. Gol o palo
        # 3. Tiri in porta
        # 4. Marcatore ultra
        
        # Check specific exciting markets
        if any(w in full for w in ["GOL O PALO", "QUASI CARTELLINO", "COMMETTE ALMENO 2 FALLI", "COMMETTE ALMENO", "TIRI IN PORTA ULTRA", "MARCATORE ULTRA"]):
            for o in m.get("outcomes", []):
                odd = float(o.get("odds", 0))
                if o.get("open") and 1.50 <= odd <= 3.20:
                    sel = o.get("selection")
                    print(f"  [{mkt}] {line} -> {sel} @ {odd}")

print("--- RICERCA PROPS ING E CRO-SPA ---")
inspect_match_props("inghilterra---repubblica-ceca.json")
inspect_match_props("croazia---spagna.json")
