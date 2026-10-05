import json
from pathlib import Path

snai_dir = Path("reports/snai")

def inspect_game(fname, keywords):
    with open(snai_dir / fname, encoding="utf-8") as f:
        data = json.load(f)
    print(f"\n=== {data.get('match')} ===")
    for m in data.get("markets", []):
        m_name = f"{m.get('market', '')} {m.get('line', '')}".strip()
        for kw in keywords:
            if kw.upper() in m_name.upper():
                outs = [f"{o['selection']} @ {o['odds']}" for o in m.get("outcomes", []) if o.get("open", True) and 1.15 <= float(o.get("odds", 0)) <= 2.20]
                if outs:
                    print(f"  [{m_name}]: {', '.join(outs[:4])}")

inspect_game("italia-turchia.json", ["DOPPIA CHANCE", "1X2 + U/O", "UNDER/OVER", "CORNER", "UNO O L'ALTRO", "CARTELLINO", "TIRI"])
inspect_game("francia-belgio.json", ["DOPPIA CHANCE", "1X2 + U/O", "UNDER/OVER", "CORNER", "MULTIGOAL", "COMBO CHANCE"])
inspect_game("romania-svezia.json", ["DOPPIA CHANCE", "CORNER", "UNDER/OVER", "MULTIGOAL", "1X2 + U/O"])
inspect_game("ucraina-ungheria.json", ["DOPPIA CHANCE", "UNDER/OVER", "MULTIGOAL", "COMBO CHANCE"])
inspect_game("bosnia-erzegovina-polonia.json", ["DOPPIA CHANCE", "UNDER/OVER", "MULTIGOAL", "COMBO CHANCE"])
inspect_game("irlanda-del-nord-georgia.json", ["DOPPIA CHANCE", "UNDER/OVER", "MULTIGOAL", "COMBO CHANCE"])
inspect_game("montenegro-armenia.json", ["DOPPIA CHANCE", "UNDER/OVER", "MULTIGOAL", "1X2 + U/O"])
