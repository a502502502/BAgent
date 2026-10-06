import json
from pathlib import Path

p = Path("reports/snai_nl/catalog")
today_files = [
    "kazakistan---isole-far-oer.json",
    "albania---san-marino.json",
    "bielorussia---finlandia.json",
    "croazia---spagna.json",
    "estonia---islanda.json",
    "inghilterra---repubblica-ceca.json",
    "lussemburgo---bulgaria.json",
    "moldova---slovacchia.json",
    "scozia---slovenia.json",
    "svizzera---macedonia.json"
]

print("=== MERCATI CANDIDATI NEI 10 MATCH DI OGGI (2026-10-06) ===")
for fn in today_files:
    fl = p / fn
    with open(fl, encoding="utf-8") as fp:
        d = json.load(fp)
    match_name = d.get("match")
    print(f"\n--- {match_name} ({d.get('kickoff_time')}) ---")
    
    # 1X2 and DC
    for m in d.get("markets", []):
        mkt = m.get("market", "").strip()
        line = m.get("line", "").strip()
        
        # Check interesting markets
        if mkt in ["1X2 ESITO FINALE", "DOPPIA CHANCE", "PRIMA A X CORNER", "U/O PUNTI CARTELLINI", "U/O TIRI IN PORTA", "MULTIGOAL"]:
            outs = [f"{o.get('selection')}@{o.get('odds')}" for o in m.get("outcomes", []) if o.get("open") and 1.15 <= float(o.get("odds", 0)) <= 1.65]
            # filter out 12
            outs = [x for x in outs if not x.startswith("12@")]
            if outs:
                print(f"  [{mkt}] {line}: {', '.join(outs[:4])}")
        elif "GIOCATORE" in mkt or "TIRI" in mkt or "COMBO CHANCE" in mkt:
            outs = [f"{o.get('selection')}@{o.get('odds')}" for o in m.get("outcomes", []) if o.get("open") and 1.20 <= float(o.get("odds", 0)) <= 1.55]
            if outs:
                print(f"  [{mkt}] {line}: {', '.join(outs[:3])}")
