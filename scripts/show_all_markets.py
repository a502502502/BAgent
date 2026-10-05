import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("reports/italia_turchia_all_markets.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

current_cat = ""
for r in rows:
    if r["category"] != current_cat:
        current_cat = r["category"]
        print(f"\n=== {current_cat.upper()} ===")
    print(f"  {r['pick']:<32} | P: {r['prob_pct']:>5}% | Q.Mercato: @{r['market_odds']:<4} | Q.Fair: @{r['fair_odds']:<4} | Edge: {r['edge_pct']:>6}% | {r['status']}")
