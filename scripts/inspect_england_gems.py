import json
from pathlib import Path

fl = Path("reports/snai_nl/catalog/inghilterra---repubblica-ceca.json")
with open(fl, encoding="utf-8") as f:
    d = json.load(f)

print("Top props in Inghilterra - Repubblica Ceca:")
for m in d.get("markets", []):
    mkt = m.get("market", "")
    line = m.get("line", "")
    full = f"{mkt} {line}".upper()
    if any(k in full for k in ["KANE", "BELLINGHAM", "SAKA", "SADILEK", "SOUCEK", "GOL O PALO", "QUASI CARTELLINO"]):
        for o in m.get("outcomes", []):
            odd = float(o.get("odds", 0))
            if o.get("open") and 1.50 <= odd <= 3.20:
                print(f"  [{mkt}] {line} -> {o.get('selection')} @ {odd}")
