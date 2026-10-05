import json
from pathlib import Path

snai_dir = Path("reports/snai")
files = sorted(snai_dir.glob("*.json"))

print(f"Trovati {len(files)} file in {snai_dir}:\n")
print(f"{'FILE':<32} | {'MATCH':<30} | {'KICKOFF':<22} | {'MERCATI'}")
print("-" * 95)

for f in files:
    try:
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
            match = data.get("match", "N/A")
            kickoff = data.get("kickoff_time", "N/A")
            m_count = data.get("market_count", len(data.get("markets", [])))
            print(f"{f.name:<32} | {match:<30} | {kickoff:<22} | {m_count}")
    except Exception as e:
        print(f"{f.name:<32} | ERRORE: {e}")
