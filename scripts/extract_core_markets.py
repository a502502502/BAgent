import json
from pathlib import Path

root = Path("reports/snai/2026-10-06-fino-16")
with open(root / "index.json", encoding="utf-8") as f:
    idx = json.load(f)

def get_match_summary(query):
    item = next((x for x in idx if query.lower() in x["match"].lower()), None)
    if not item:
        return f"Match not found: {query}"
    with open(item["file"], encoding="utf-8") as f:
        d = json.load(f)
    res = []
    res.append(f"=== {item['kickoff_time']} | {item['competition']} | {item['match']} ===")
    
    # 1X2
    for m in d.get("markets", []):
        mkt = m.get("market", "").strip()
        line = m.get("line", "").strip()
        if mkt == "1X2 ESITO FINALE":
            outs = {o.get("selection"): o.get("odds") for o in m.get("outcomes", []) if o.get("open")}
            res.append(f"  1X2: 1@{outs.get('1')} | X@{outs.get('X')} | 2@{outs.get('2')}")
        elif mkt == "DOPPIA CHANCE":
            outs = {o.get("selection"): o.get("odds") for o in m.get("outcomes", []) if o.get("open")}
            res.append(f"  DC: 1X@{outs.get('1X')} | X2@{outs.get('X2')} | 12@{outs.get('12')}")
        elif "DRAW NO BET" in mkt:
            outs = {o.get("selection"): o.get("odds") for o in m.get("outcomes", []) if o.get("open")}
            res.append(f"  DNB: 1@{outs.get('1')} | 2@{outs.get('2')}")
        elif mkt == "UNDER/OVER":
            outs = {o.get("selection"): o.get("odds") for o in m.get("outcomes", []) if o.get("open")}
            res.append(f"  {line}: O@{outs.get('OVER')} | U@{outs.get('UNDER')}")
        elif mkt == "GOAL/NOGOAL":
            outs = {o.get("selection"): o.get("odds") for o in m.get("outcomes", []) if o.get("open")}
            res.append(f"  GG/NG: GG@{outs.get('GOAL')} | NG@{outs.get('NOGOAL')}")
        elif "MULTIGOAL" in mkt and "MULTIESITI" in line:
            outs = [f"{o.get('selection')}@{o.get('odds')}" for o in m.get("outcomes", []) if o.get("open") and float(o.get("odds", 0)) <= 1.70]
            if outs:
                res.append(f"  {line}: {', '.join(outs[:6])}")
        elif "1 TEMPO" in mkt or "TEMPO 1" in line:
            if "U/O" in line:
                outs = {o.get("selection"): o.get("odds") for o in m.get("outcomes", []) if o.get("open")}
                res.append(f"  1T {line}: O@{outs.get('OVER')} | U@{outs.get('UNDER')}")
            elif "DOPPIA CHANCE" in line:
                outs = {o.get("selection"): o.get("odds") for o in m.get("outcomes", []) if o.get("open")}
                res.append(f"  1T DC: 1X@{outs.get('1X')} | X2@{outs.get('X2')}")
    return "\n".join(res)

print("--- FASCIA 1: 11:00 - 13:00 CEST ---")
print(get_match_summary("Saudi Arabia U20"))
print(get_match_summary("Montenegro U19 F"))
print(get_match_summary("UD Leiria U23"))
print(get_match_summary("Trencin"))
print(get_match_summary("Binh Phuoc"))

print("\n--- FASCIA 2: 13:00 - 13:35 CEST ---")
print(get_match_summary("Corea del Sud"))
print(get_match_summary("Changchun Yatai"))
print(get_match_summary("Cina - Tagikistan"))
print(get_match_summary("Nantong Zhiyun"))
print(get_match_summary("Beslidhja"))

print("\n--- FASCIA 3: 14:00 - 16:00 CEST ---")
print(get_match_summary("Bristol City"))
print(get_match_summary("Hull City U21"))
print(get_match_summary("Colchester"))
print(get_match_summary("Albion FC Reserve"))
print(get_match_summary("Azerbaigian U21"))
print(get_match_summary("Moldova U21"))
print(get_match_summary("Kazakistan - Isole Far Oer"))
