"""
Cerca partite di oggi e domani nei campionati principali.
Mostra solo partite con quote disponibili.

Utilizzo:
    python scripts/find_today_matches.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date, timedelta
from pathlib import Path

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

# Campionati principali con buona copertura dati
MAJOR_LEAGUES = {
    39:  "Premier League",
    40:  "Championship",
    61:  "Ligue 1",
    62:  "Ligue 2",
    78:  "Bundesliga",
    79:  "Bundesliga 2",
    88:  "Eredivisie",
    94:  "Primeira Liga",
    103: "Eliteserien (Norvegia)",
    113: "Allsvenskan (Svezia)",
    119: "Superliga (Danimarca)",
    135: "Serie A",
    136: "Serie B",
    140: "La Liga",
    141: "La Liga 2",
    144: "Pro League (Belgio)",
    169: "Veikkausliiga (Finlandia)",
    179: "Scottish Premiership",
    197: "Super League (Grecia)",
    203: "Süper Lig (Turchia)",
    848: "UEFA Conference League",
    2:   "UEFA Champions League",
    3:   "UEFA Europa League",
}

def main():
    c = FootballExternalCollector()

    today = date.today()
    dates = [today, today + timedelta(days=1)]

    all_matches = []

    for d in dates:
        print(f"\n[Cerco partite per {d}...]")
        try:
            data = c._get("fixtures", {"date": d.isoformat()})
            for f in data.get("response", []):
                league_id = f["league"]["id"]
                if league_id not in MAJOR_LEAGUES:
                    continue

                status = f["fixture"]["status"]["short"]
                if status not in ("NS", "TBD"):
                    continue  # solo partite non ancora iniziate

                fid  = f["fixture"]["id"]
                h    = f["teams"]["home"]["name"]
                a    = f["teams"]["away"]["name"]
                time = f["fixture"]["date"][11:16]
                league = MAJOR_LEAGUES[league_id]

                all_matches.append({
                    "date": d,
                    "time": time,
                    "fixture_id": fid,
                    "home": h,
                    "away": a,
                    "league": league,
                    "league_id": league_id,
                })
        except Exception as e:
            print(f"  Errore {d}: {e}")

    if not all_matches:
        print("\nNessuna partita trovata nei campionati principali.")
        return

    print(f"\n{'='*70}")
    print(f"  PARTITE DISPONIBILI — {len(all_matches)} totali")
    print(f"{'='*70}")

    current_league = None
    for m in sorted(all_matches, key=lambda x: (x["league"], x["date"], x["time"])):
        if m["league"] != current_league:
            current_league = m["league"]
            print(f"\n── {current_league} ──")
        print(f"  [{m['date']} {m['time']}] {m['home']} vs {m['away']}  [ID:{m['fixture_id']}]")

    # Ora recupera le quote per le partite di oggi
    print(f"\n{'='*70}")
    print(f"  QUOTE DISPONIBILI (solo oggi)")
    print(f"{'='*70}")

    today_matches = [m for m in all_matches if m["date"] == today]
    for m in today_matches[:15]:  # limita per non esaurire la quota API
        try:
            raw_odds = c.odds(m["fixture_id"])
            odds = c.parse_odds(raw_odds)
            if odds.get("home_win"):
                h_odd = odds.get("home_win", "-")
                d_odd = odds.get("draw", "-")
                a_odd = odds.get("away_win", "-")
                o25   = odds.get("over_2_5", "")
                btts  = odds.get("btts_yes", "")
                extra = f"  O2.5={o25}" if o25 else ""
                extra += f"  GG={btts}" if btts else ""
                print(f"  {m['home']} vs {m['away']}")
                print(f"    {m['league']} | 1={h_odd} X={d_odd} 2={a_odd}{extra}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
