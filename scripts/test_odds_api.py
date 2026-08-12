"""
Test rapido The Odds API — verifica chiave e disponibilità eventi.

Utilizzo:
    python scripts/test_odds_api.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from pprint import pprint

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

from services.football.external.sources.odds_api import OddsAPICollector, SPORT_KEYS

TODAY = "2026-08-12"

def test_conference_league():
    print("=" * 60)
    print("TEST: The Odds API — Conference League")
    print("=" * 60)

    collector = OddsAPICollector()

    # 0. Lista tutti gli sport soccer disponibili
    print("\n[0] Sport soccer disponibili:")
    try:
        all_sports = collector.list_sports()
        soccer = [s for s in all_sports if "soccer" in s.get("key", "")]
        for s in soccer:
            active = "✓" if s.get("active") else "○"
            print(f"  {active} {s['key']:55} — {s.get('title', '')}")
    except Exception as e:
        print(f"  ERRORE: {e}")
        return

    # Trova il key giusto per Conference/Europa League
    cl_keys = [s["key"] for s in soccer if "conference" in s["key"] or "europa" in s["key"]]
    print(f"\nKey UEFA trovati: {cl_keys}")

    sport_key = SPORT_KEYS["conference_league"]
    print(f"\nUso sport key: {sport_key}")

    # 1. Lista eventi disponibili oggi
    print(f"\n[1] Lista eventi disponibili oggi ({TODAY})...")
    try:
        events = collector.list_events(sport_key, TODAY)
        if not events:
            print("  Nessun evento trovato per oggi. Provo senza filtro data...")
            events = collector.list_events(sport_key)

        print(f"  Trovati {len(events)} eventi:")
        for ev in events[:10]:
            print(f"    {ev.get('home_team')} vs {ev.get('away_team')} — {ev.get('commence_time', '')[:16]}")
    except Exception as e:
        print(f"  ERRORE list_events: {e}")
        # Prova tutti i key UEFA trovati
        for k in cl_keys:
            if k == sport_key:
                continue
            print(f"\n  Provo con key alternativo: {k}")
            try:
                events = collector.list_events(k)
                print(f"  Trovati {len(events)} eventi:")
                for ev in events[:5]:
                    print(f"    {ev.get('home_team')} vs {ev.get('away_team')}")
            except Exception as e2:
                print(f"  ERRORE: {e2}")
        return

    # 2. Cerca partite specifiche
    partite = [
        ("FC Copenhagen", "Debreceni VSC"),
        ("GKS Katowice", "Hapoel Tel Aviv"),
        ("Rapid Vienna", "Paide Linnameeskond"),
    ]

    for home, away in partite:
        print(f"\n[2] Cerca evento: {home} vs {away}")
        event_id = collector.find_event(sport_key, home, away, TODAY)
        if event_id:
            print(f"  ✓ Trovato — event_id: {event_id}")

            # Raccoglie tutte le quote
            data = collector.collect(
                sport_key=sport_key,
                home=home,
                away=away,
                match_date=TODAY,
                include_corners=True,
                include_qualify=True,
            )
            print(f"  Quota principale:")
            pprint(data.get("market_odds", {}), indent=4)
            print(f"  Quote corner:")
            pprint(data.get("corner_odds", {}), indent=4)
            print(f"  Qualificazione:")
            pprint(data.get("qualify_odds", {}), indent=4)
        else:
            print(f"  ✗ Non trovato")


if __name__ == "__main__":
    try:
        test_conference_league()
    except RuntimeError as e:
        print(f"\n[ERRORE] {e}")
        print("\nAggiungi ODDS_API_KEY al file .env:")
        print("  echo 'ODDS_API_KEY=la_tua_chiave' >> .env")
