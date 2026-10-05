import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("reports/snai_italia_turchia_full_catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

for cat, items in catalog.items():
    print(f"\n==================== {cat.upper()} ====================")
    for it in items:
        # show if edge is positive or high visibility
        flag = "🔥" if it["edge_pct"] > 5.0 else ("✅" if it["edge_pct"] > 0 else "❌")
        print(f"  {flag} {it['selezione']:<36} | P: {it['prob_pct']:>5}% | Q: @{it['snai_odds']:<5} | Fair: @{it['fair_odds']:<5} | EV: {it['edge_pct']:>6}% | {it['verdict']}")
