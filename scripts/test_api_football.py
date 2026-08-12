"""
Test rapido API-Football.
Verifica connessione, quota rimanente e ricerca partita.

Utilizzo:
    python scripts/test_api_football.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from datetime import date, timedelta

def load_env(env_path=Path(".env")):
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() and value.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip()

load_env(Path(__file__).parent.parent / ".env")

from services.football.external.collector import FootballExternalCollector

def main():
    print("\n" + "=" * 60)
    print("  TEST API-FOOTBALL")
    print("=" * 60)

    c = FootballExternalCollector()

    # 1. Quota rimanente
    print("\n[1] Stato account e quota...")
    try:
        status = c.quota_status()
        acc = status.get("account", {})
        sub = status.get("subscription", {})
        req = status.get("requests", {})
        print(f"    Account  : {acc.get('firstname','')} {acc.get('lastname','')}")
        print(f"    Piano    : {sub.get('plan', 'N/A')}")
        print(f"    Richieste: {req.get('current','?')} / {req.get('limit_day','?')} oggi")
    except Exception as e:
        print(f"    ERRORE: {e}")
        return

    # 2. Cerca Serie A (senza country)
    print("\n[2] Ricerca campionati 'Serie A'...")
    try:
        leagues = c.search_league("Serie A")
        for l in leagues[:5]:
            print(f"    ID {l['id']:5} — {l['name']:25} ({l['country']}) stagione {l['season']}")
    except Exception as e:
        print(f"    ERRORE: {e}")

    # 3. Cerca fixture nel range consentito dal Free plan (ieri/oggi/domani)
    print("\n[3] Partite disponibili (ieri / oggi / domani)...")
    today = date.today()
    dates_to_check = [today - timedelta(days=1), today, today + timedelta(days=1)]
    found_fixture = None

    for d in dates_to_check:
        try:
            # Cerca in tutti i campionati per quella data
            data = c._get("fixtures", {"date": d.isoformat()})
            fixtures = data.get("response", [])
            if fixtures:
                print(f"\n    {d} — {len(fixtures)} partite trovate")
                for f in fixtures[:5]:
                    teams = f["teams"]
                    h = teams["home"]["name"]
                    a = teams["away"]["name"]
                    fid = f["fixture"]["id"]
                    league = f["league"]["name"]
                    status_f = f["fixture"]["status"]["short"]
                    print(f"      [{fid}] {h} vs {a}  | {league} | {status_f}")
                    # Preferisce partite non ancora iniziate (NS) per avere quote
                    if found_fixture is None and status_f in ("NS", "TBD"):
                        found_fixture = (fid, h, a, d, league)
                if len(fixtures) > 5:
                    print(f"      ... e altre {len(fixtures)-5} partite")
            else:
                print(f"\n    {d} — nessuna partita")
        except Exception as e:
            print(f"\n    {d} — errore: {e}")

    # 4. Test dettagliato su prima partita trovata
    if found_fixture:
        fid, home, away, fdate, league = found_fixture
        print(f"\n[4] Dettagli: {home} vs {away} ({league}, {fdate})")

        print(f"\n    Infortuni...")
        try:
            raw = c.injuries(fid)
            injuries = c.parse_injuries(raw)
            if injuries:
                for inj in injuries[:5]:
                    print(f"      {inj['team']:20} {inj['player']:20} — {inj['type']}")
            else:
                print("      Nessun infortunio registrato")
        except Exception as e:
            print(f"      ERRORE: {e}")

        print(f"\n    Formazioni...")
        try:
            raw_lin = c.lineups(fid)
            lineups = c.parse_lineups(raw_lin)
            if lineups:
                for team, data in lineups.items():
                    print(f"      {team}: {data['formation']} — Coach: {data['coach']}")
            else:
                print("      Non ancora disponibili")
        except Exception as e:
            print(f"      ERRORE: {e}")

        print(f"\n    Quote...")
        try:
            raw_odds = c.odds(fid)
            odds = c.parse_odds(raw_odds)
            if odds:
                for k, v in odds.items():
                    print(f"      {k:15}: {v}")
            else:
                print("      Quote non disponibili")
        except Exception as e:
            print(f"      ERRORE: {e}")

    print("\n" + "=" * 60)
    print("  Test completato.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
