import json
from pathlib import Path

root = Path("reports/snai/2026-10-06-fino-16")
with open(root / "index.json", encoding="utf-8") as f:
    idx = json.load(f)

print(f"Total catalog files: {len(idx)}")
categorized = {}

for it in idx:
    fl = Path(it["file"])
    if not fl.exists():
        continue
    with open(fl, encoding="utf-8") as f:
        d = json.load(f)
    match_str = f"{it['kickoff_time']} | {it['match']} ({it['competition']})"
    for m in d.get("markets", []):
        m_name = m.get("market", "").strip()
        line = m.get("line", "").strip()
        for o in m.get("outcomes", []):
            odd = float(o.get("odds", 0))
            if o.get("open") and 1.15 <= odd <= 1.85:
                # Group into families
                fam = "OTHER"
                if m_name == "DOPPIA CHANCE":
                    fam = "DOPPIA_CHANCE"
                elif "1X2" in m_name and "1 TEMPO" not in m_name and "COMBO" not in m_name:
                    fam = "ESITO_FINALE_1X2"
                elif "DRAW NO BET" in m_name or "RIMBORSO IN CASO DI PARITA" in m_name:
                    fam = "DRAW_NO_BET"
                elif "UNDER/OVER" in m_name and "TEMPO" not in m_name and "SQUADRA" not in m_name:
                    fam = "UNDER_OVER_MATCH"
                elif "GOAL/NOGOAL" in m_name:
                    fam = "GOAL_NOGOAL"
                elif "1 TEMPO" in m_name or "TEMPO X" in m_name:
                    fam = "TEMPI"
                elif "SQUADRA" in m_name or "SEGNA GOAL" in m_name:
                    fam = "GOL_SQUADRA"
                elif "MULTIGOAL" in m_name:
                    fam = "MULTIGOAL"
                elif "COMBO" in m_name:
                    fam = "COMBO"

                if fam not in categorized:
                    categorized[fam] = []
                categorized[fam].append({
                    "match": it["match"],
                    "kickoff": it["kickoff_time"],
                    "comp": it["competition"],
                    "market": m_name,
                    "line": line,
                    "sel": o.get("selection"),
                    "odd": odd
                })

for fam, items in sorted(categorized.items()):
    print(f"\n=== FAMIGLIA: {fam} (Totale selezioni: {len(items)}) ===")
    # show top 5 samples
    for itm in items[:8]:
        print(f"  [{itm['kickoff'][:16]}] {itm['match']} | {itm['market']} - {itm['line']} -> {itm['sel']} @ {itm['odd']}")
