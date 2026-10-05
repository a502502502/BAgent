import json
from pathlib import Path

snai_dir = Path("reports/snai")

def explore_diverse_families(fname):
    with open(snai_dir / fname, encoding="utf-8") as f:
        data = json.load(f)
    match = data.get("match")
    print(f"\n=======================================================")
    print(f"MATCH: {match}")
    print(f"=======================================================")
    
    families = {
        "Marcatore Più / Tiri Ultra": [],
        "Corner Volume / 1X2": [],
        "Falli / Cartellini": [],
        "Tempi / Entrambi i Tempi": [],
        "Chance Mix / Combo Chance": [],
        "Squadra MultiGol (Casa/Ospite)": []
    }
    
    for m in data.get("markets", []):
        m_name = f"{m.get('market', '')} {m.get('line', '')}".strip()
        outs = m.get("outcomes", [])
        
        # 1. Marcatore Più / Ultra
        if any(k in m_name.upper() for k in ["MARCATORE PIÙ", "MARCATORE PIU", "TIRI IN PORTA ULTRA", "GOL O ASSIST"]):
            for o in outs:
                if 1.40 <= float(o.get("odds", 0)) <= 2.60:
                    families["Marcatore Più / Tiri Ultra"].append((m_name, o["selection"], o["odds"]))
        
        # 2. Corner
        if "CORNER" in m_name.upper():
            for o in outs:
                if 1.35 <= float(o.get("odds", 0)) <= 2.20 and any(w in o["selection"].upper() for w in ["1", "2", "OVER", "UNDER"]):
                    families["Corner Volume / 1X2"].append((m_name, o["selection"], o["odds"]))
                    
        # 3. Falli / Cartellini
        if any(k in m_name.upper() for k in ["FALLI COMMESSI", "CARTELLINO O LORO SOST", "UNO O L'ALTRO"]):
            for o in outs:
                if 1.40 <= float(o.get("odds", 0)) <= 2.50:
                    families["Falli / Cartellini"].append((m_name, o["selection"], o["odds"]))
                    
        # 4. Tempi
        if any(k in m_name.upper() for k in ["ENTRAMBI I TEMPI", "1°T +", "1 TEMPO +", "TEMPO 1 + TEMPO 2"]):
            for o in outs:
                if 1.25 <= float(o.get("odds", 0)) <= 2.20:
                    families["Tempi / Entrambi i Tempi"].append((m_name, o["selection"], o["odds"]))

        # 5. Chance Mix
        if any(k in m_name.upper() for k in ["COMBO CHANCE", "CHANCE MIX"]):
            for o in outs:
                if 1.25 <= float(o.get("odds", 0)) <= 1.80:
                    families["Chance Mix / Combo Chance"].append((m_name, o["selection"], o["odds"]))

        # 6. Squadra Multigol
        if "MULTIGOAL SQUADRA" in m_name.upper():
            for o in outs:
                if 1.25 <= float(o.get("odds", 0)) <= 1.80 and o["selection"] in ["1-3", "2-4", "1-2", "2-5"]:
                    families["Squadra MultiGol (Casa/Ospite)"].append((m_name, o["selection"], o["odds"]))

    for cat, items in families.items():
        if items:
            print(f"  • {cat} ({len(items)} opzioni):")
            for it in items[:3]:
                print(f"      {it[0]} | {it[1]} -> {it[2]}")

explore_diverse_families("italia-turchia.json")
explore_diverse_families("francia-belgio.json")
explore_diverse_families("romania-svezia.json")
explore_diverse_families("bosnia-erzegovina-polonia.json")
explore_diverse_families("irlanda-del-nord-georgia.json")
explore_diverse_families("ucraina-ungheria.json")
explore_diverse_families("croazia-spagna.json")
explore_diverse_families("inghilterra-repubblica-ceca.json")
