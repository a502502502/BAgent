import json
from pathlib import Path

p = Path("reports/snai_nl/catalog")
today_matches = []
for f in p.glob("*.json"):
    if f.name == "index.json": 
        continue
    with open(f, encoding="utf-8") as fp:
        d = json.load(fp)
    ko = d.get("kickoff_time", "")
    if "2026-10-06" in ko:
        today_matches.append({
            "match": d.get("match"),
            "kickoff": ko,
            "markets_count": len(d.get("markets", [])),
            "file": f.name
        })

print(f"Total Nations League matches for TODAY (2026-10-06): {len(today_matches)}")
for idx, m in enumerate(sorted(today_matches, key=lambda x: x["kickoff"]), 1):
    print(f"{idx:2d}. [{m['kickoff']}] {m['match']} ({m['markets_count']} mercati) -> {m['file']}")
