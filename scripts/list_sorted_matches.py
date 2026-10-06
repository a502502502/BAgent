import json
from pathlib import Path

root = Path("reports/snai/2026-10-06-fino-16")
with open(root / "index.json", encoding="utf-8") as f:
    idx = json.load(f)

idx_sorted = sorted(idx, key=lambda x: x["kickoff_time"])
for i, m in enumerate(idx_sorted):
    print(f"{i+1:2d}. {m['kickoff_time']} | {m['competition']} | {m['match']} ({m['market_count']} mkt)")
