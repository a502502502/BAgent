"""
Cerca partite per data e parola chiave nel nome squadra.

Utilizzo:
    python scripts/search_fixture.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from datetime import date, timedelta

def load_env(p=Path(".env")):
    if not p.exists(): return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, _, v = line.partition("=")
        if k.strip() and v.strip() and k.strip() not in os.environ:
            os.environ[k.strip()] = v.strip()

load_env(Path(__file__).parent.parent / ".env")

from services.football.external.collector import FootballExternalCollector

def main():
    c = FootballExternalCollector()
    keyword = input("Cerca squadra (es. 'Djurg'): ").strip().lower()
    days = int(input("Quanti giorni da oggi cercare? [3]: ").strip() or "3")

    today = date.today()
    for i in range(-1, days + 1):
        d = today + timedelta(days=i)
        try:
            data = c._get("fixtures", {"date": d.isoformat()})
            for f in data.get("response", []):
                h = f["teams"]["home"]["name"]
                a = f["teams"]["away"]["name"]
                if keyword in h.lower() or keyword in a.lower():
                    fid  = f["fixture"]["id"]
                    lg   = f["league"]["name"]
                    st   = f["fixture"]["status"]["short"]
                    time = f["fixture"]["date"][11:16]
                    print(f"[{d} {time}] [{fid}] {h} vs {a} | {lg} | {st}")
        except Exception as e:
            print(f"{d}: {e}")

if __name__ == "__main__":
    main()
