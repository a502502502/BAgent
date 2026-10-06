import json
from pathlib import Path

root = Path("reports/snai/2026-10-06-fino-16")
with open(root / "index.json", encoding="utf-8") as f:
    idx = json.load(f)

print(f"Total matches: {len(idx)}")

matches_to_inspect = [
    "Saudi Arabia U20 - Armenia U20",
    "UD Leiria U23 - Santa Clara U23",
    "Corea del Sud - Uzbekistan",
    "Changchun Yatai - Yanbian Longding",
    "Cina - Tagikistan",
    "Nantong Zhiyun - Shanghai Jiading City Development",
    "Bristol City - Charlton Athletic",
    "Hull City U21 - Wigan U21",
    "Colchester United U21 - Swansea City U21",
    "Albion FC Reserve - Nacional de Montevideo",
    "Azerbaigian U21 - Gibilterra U21",
    "Moldova U21 - Kazakistan U21",
    "Kazakistan - Isole Far Oer"
]

for it in idx:
    if it["match"] not in matches_to_inspect:
        continue
    with open(it["file"], encoding="utf-8") as f:
        d = json.load(f)
    print(f"\n==================================================")
    print(f"MATCH: {it['match']} | KICKOFF: {it['kickoff_time']} | COMP: {it['competition']}")
    print(f"==================================================")
    
    # Print interesting markets:
    for m in d.get("markets", []):
        m_name = m.get("market", "").strip()
        line = m.get("line", "").strip()
        
        # Check specific interesting families
        is_interesting = (
            m_name in ["1X2 ESITO FINALE", "DOPPIA CHANCE", "DRAW NO BET", "UNDER/OVER", "GOAL/NOGOAL", "MULTIGOAL"] or
            "TEMPO" in m_name or "SQUADRA" in m_name or "COMBO CHANCE" in m_name or "MULTIGOAL" in m_name
        )
        if not is_interesting:
            continue
            
        open_outcomes = [o for o in m.get("outcomes", []) if o.get("open") and 1.15 <= float(o.get("odds", 0)) <= 1.85]
        if open_outcomes:
            for o in open_outcomes:
                sel = o.get("selection")
                odd = float(o.get("odds"))
                # Filter out 12
                if m_name == "DOPPIA CHANCE" and sel == "12":
                    continue
                print(f"  [{m_name}] {line} -> {sel} @ {odd}")
