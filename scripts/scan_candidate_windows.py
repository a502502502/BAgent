import json
from pathlib import Path

root = Path("reports/snai/2026-10-06-fino-16")
with open(root / "index.json", encoding="utf-8") as f:
    idx = json.load(f)

def inspect_match(m_name):
    item = next((x for x in idx if m_name.lower() in x["match"].lower()), None)
    if not item:
        print(f"Match not found: {m_name}")
        return
    with open(item["file"], encoding="utf-8") as f:
        d = json.load(f)
    print(f"\n=======================================================")
    print(f"MATCH: {item['match']} | KICKOFF: {item['kickoff_time']} | COMP: {item['competition']}")
    print(f"=======================================================")
    for m in d.get("markets", []):
        mkt = m.get("market", "").strip()
        line = m.get("line", "").strip()
        for o in m.get("outcomes", []):
            if o.get("open"):
                odd = float(o.get("odds", 0))
                sel = o.get("selection", "")
                if 1.18 <= odd <= 1.70:
                    # Filter out purely monotonous or trap selections
                    if mkt == "DOPPIA CHANCE" and sel == "12":
                        continue
                    if "UNDER 3.5" in line and ("1X" in mkt or "1X" in line):
                        continue
                    if any(kw in mkt for kw in ["1X2", "DOPPIA CHANCE", "DRAW NO BET", "UNDER/OVER", "GOAL/NOGOAL", "MULTIGOAL", "TEMPO", "SEGNA GOAL"]):
                        print(f"  [{mkt}] {line} -> {sel} @ {odd}")

# Window 1: 11:00 - 13:00
print("--- WINDOW 1 (11:00 - 13:00) ---")
inspect_match("Saudi Arabia U20")
inspect_match("UD Leiria U23")
inspect_match("Trencin")
inspect_match("Binh Phuoc")

# Window 2: 13:00 - 13:35
print("\n--- WINDOW 2 (13:00 - 13:35) ---")
inspect_match("Corea del Sud")
inspect_match("Changchun Yatai")
inspect_match("Cina")
inspect_match("Nantong Zhiyun")

# Window 3: 14:00 - 16:00
print("\n--- WINDOW 3 (14:00 - 16:00) ---")
inspect_match("Bristol City")
inspect_match("Colchester United U21")
inspect_match("Albion FC Reserve")
inspect_match("Moldova U21")
inspect_match("Kazakistan - Isole Far Oer")
