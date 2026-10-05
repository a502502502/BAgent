"""Scarico completo di tutti i mercati, quote e infortuni da Sportmicro per le partite di oggi."""

import json
import logging
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SportmicroDownloader")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from services.betting.sportmicro_client import SportmicroClient

client = SportmicroClient()
CACHE_DIR = ROOT / "data" / "cache" / "sportmicro"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = CACHE_DIR / "sportmicro_today_markets.json"


def main():
    print("=" * 80)
    print("🚀 SCARICO MERCATI E QUOTE SPORTMICRO IN CORSO...")
    print("=" * 80)

    if not client.is_configured:
        print("❌ SPORTMICRO_API_KEY non configurata!")
        return 1

    date_str = "2026-10-05"
    print(f"📅 Recupero partite per la data: {date_str}")
    matches = client.get_matches_for_date(date_str)
    print(f"✅ Trovate {len(matches)} partite su Sportmicro per oggi.\n")

    # Filtra partite di interesse (Nations League e principali campionati)
    target_matches = []
    for m in matches:
        tname = m.get("tournament_name", "")
        mname = m.get("name", "")
        # Priorità a Nations League, Sudamerica, U21 e leghe maggiori
        target_matches.append(m)

    print(f"📊 Download quote speciali e infortuni per {len(target_matches)} partite...")

    full_data = []

    for idx, m in enumerate(target_matches, 1):
        mid = m.get("id")
        name = m.get("name", "")
        tourn = m.get("tournament_name", "")
        start = m.get("start_time", "")

        print(f"[{idx}/{len(target_matches)}] Match ID {mid}: {name} ({tourn})")

        # 1. To Score In Both Halves
        both_halves = client.get_score_in_both_halves_odds(mid)

        # 2. To Win Both Halves
        win_both = client.get_to_win_both_halves_odds(mid)

        # 3. To Win To Nil
        win_nil = client.get_to_win_to_nil_odds(mid)

        # 4. Clean Sheet
        clean_sheet = client.get_clean_sheet_odds(mid)

        # 5. Infortuni
        injuries = client.get_injuries(mid)

        match_record = {
            "match_id": mid,
            "name": name,
            "home_team": m.get("home_team_name"),
            "away_team": m.get("away_team_name"),
            "tournament": tourn,
            "start_time": start,
            "odds_to_score_both_halves": both_halves,
            "odds_to_win_both_halves": win_both,
            "odds_to_win_to_nil": win_nil,
            "odds_clean_sheet": clean_sheet,
            "injuries": injuries,
        }

        full_data.append(match_record)

        if both_halves:
            print(f"   🎯 Segna Entrambi i Tempi: {both_halves}")
        if win_both:
            print(f"   🏆 Vince Entrambi i Tempi: {win_both}")
        if win_nil:
            print(f"   🛡️ Vince a Zero: {win_nil}")
        if injuries:
            print(f"   🏥 Infortuni registrati: {len(injuries)}")
            for inj in injuries[:3]:
                print(f"      - {inj.get('player_name')} ({inj.get('reason')})")

        time.sleep(0.1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"💾 SALVATO IN: {OUTPUT_FILE}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
