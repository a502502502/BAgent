import json
from pathlib import Path

p = Path("reports/snai_nl/catalog")

matches = [
    "croazia---spagna.json",
    "inghilterra---repubblica-ceca.json",
    "scozia---slovenia.json",
    "svizzera---macedonia.json"
]

print("=== RICERCA GEMME NASCOSTE: PLAYER PROPS (SNAI NATIONS LEAGUE) ===")

for m_file in matches:
    fl = p / m_file
    with open(fl, encoding="utf-8") as fp:
        d = json.load(fp)
    match_name = d.get("match")
    print(f"\n=======================================================")
    print(f"MATCH: {match_name}")
    print(f"=======================================================")
    
    # Collect gems in specific categories:
    # 1. Falli commessi / subiti
    # 2. Tiri in porta
    # 3. Gol / Assist / Cartellino
    # 4. Quasi cartellino
    
    for m in d.get("markets", []):
        mkt = m.get("market", "").strip()
        line = m.get("line", "").strip()
        full = f"{mkt} {line}".upper()
        
        # Falli giocatori
        if any(k in full for k in ["FALLI COMMESSI", "FALLI SUBITI", "SOMMA FALLI", "COMMETTE ALMENO"]):
            for o in m.get("outcomes", []):
                if o.get("open") and 1.45 <= float(o.get("odds", 0)) <= 2.60:
                    print(f"  [FALLI] {line} -> {o.get('selection')} @ {o.get('odds')}")

        # Tiri in porta / Somma tiri
        elif any(k in full for k in ["TIRI IN PORTA", "SOMMA TIRI"]):
            if "GIOCATORE" in full or "ULTRA" in full:
                for o in m.get("outcomes", []):
                    if o.get("open") and 1.60 <= float(o.get("odds", 0)) <= 2.80:
                        print(f"  [TIRI PROPS] {line} -> {o.get('selection')} @ {o.get('odds')}")

        # Segna o Assist o Cartellino / Gol o Palo
        elif any(k in full for k in ["SEGNA O ASSIST", "GOL O PALO", "QUASI CARTELLINO"]):
            for o in m.get("outcomes", []):
                if o.get("open") and 1.60 <= float(o.get("odds", 0)) <= 2.60:
                    print(f"  [SPECIALI PROPS] {line} -> {o.get('selection')} @ {o.get('odds')}")
