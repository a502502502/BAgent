import json
from pathlib import Path

files = [
    "italia-turchia.json",
    "francia-belgio.json",
    "bosnia-erzegovina-polonia.json",
    "ucraina-ungheria.json",
    "irlanda-del-nord-georgia.json",
    "romania-svezia.json",
    "montenegro-armenia.json"
]

print("=== VERIFICA MERCATI RESILIENTI NEI CATALOGHI SNAI ===")

for fname in files:
    path = Path("reports/snai") / fname
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    match = data.get("match", fname)
    markets = data.get("markets", [])
    
    print(f"\n=======================================================")
    print(f"MATCH: {match} ({len(markets)} mercati disponibili)")
    print(f"=======================================================")
    
    # Cerchiamo mercati chiave
    found = []
    for m in markets:
        m_name = m.get("market", "")
        line = m.get("line", "")
        outcomes = m.get("outcomes", [])
        
        # Filtro mercati di interesse
        m_full = f"{m_name} {line}".strip()
        if any(k in m_full.upper() for k in [
            "DOPPIA CHANCE + MULTIGOAL",
            "COMBO: 1X2 + U/O",
            "CHANCE MIX",
            "COMBO CHANCE",
            "1X2 CORNER",
            "UNDER/OVER",
            "MULTIGOAL"
        ]):
            for o in outcomes:
                sel = o.get("selection", "")
                odds = o.get("odds")
                # prendi selezioni interessanti
                if odds and 1.15 <= float(odds) <= 1.85:
                    found.append((m_full, sel, float(odds)))
                    
    print(f"Trovate {len(found)} opzioni tra 1.15 e 1.85. Eccone alcune tra le migliori:")
    # Stampiamo un campione significativo
    for item in found[:15]:
        print(f"   {item[0]:<40} | {item[1]:<20} | Quota: {item[2]}")
