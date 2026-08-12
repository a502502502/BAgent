"""
Cerca partite su SofaScore per data e parola chiave.
Copre oltre 500 campionati incluse le categorie giovanili.

Utilizzo:
    python scripts/search_sofascore.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date, timedelta

from services.football.external.sources.sofascore import SofaScoreSource

def main():
    ss = SofaScoreSource(delay=0.3)
    keyword = input("Cerca squadra (es. 'brann'): ").strip().lower()
    days = int(input("Giorni da cercare da oggi [3]: ").strip() or "3")

    today = date.today()
    print()

    for i in range(-1, days + 1):
        d = today + timedelta(days=i)
        try:
            events = ss.fixtures_by_date(d)
            matches = [
                e for e in events
                if keyword in e.get("homeTeam", {}).get("name", "").lower()
                or keyword in e.get("awayTeam", {}).get("name", "").lower()
            ]
            for e in matches:
                h    = e.get("homeTeam", {}).get("name", "")
                a    = e.get("awayTeam", {}).get("name", "")
                eid  = e.get("id", "")
                comp = e.get("tournament", {}).get("name", "")
                t    = e.get("startTimestamp", 0)
                from datetime import datetime, timezone
                time_str = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%H:%M") if t else "??:??"
                status = e.get("status", {}).get("type", "")
                print(f"[{d} {time_str}] [SS:{eid}] {h} vs {a} | {comp} | {status}")

                # Mostra quote se disponibili
                odds_raw = ss.odds(eid)
                odds = ss.parse_odds(odds_raw)
                if odds:
                    parts = []
                    if "home_win"  in odds: parts.append(f"1={odds['home_win']}")
                    if "draw"      in odds: parts.append(f"X={odds['draw']}")
                    if "away_win"  in odds: parts.append(f"2={odds['away_win']}")
                    if "over_2_5"  in odds: parts.append(f"O2.5={odds['over_2_5']}")
                    if "btts_yes"  in odds: parts.append(f"GG={odds['btts_yes']}")
                    if parts:
                        print(f"  Quote: {' | '.join(parts)}")

        except Exception as e:
            print(f"[{d}] errore: {e}")

if __name__ == "__main__":
    main()
