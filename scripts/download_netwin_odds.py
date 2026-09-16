#!/usr/bin/env python3
"""
scripts/download_netwin_odds.py — CLI Scarico Quote Ufficiali Netwin.it.

Scarica e decodifica in tempo reale il palinsesto quote di Netwin per i tornei specificati.
Sincronizza automaticamente data/netwin_live_odds.json e data/netwin_odds_cache.json.

Uso:
    python scripts/download_netwin_odds.py --tournament "Europa League"
    python scripts/download_netwin_odds.py --tournament "LaLiga"
    python scripts/download_netwin_odds.py --all
"""

from __future__ import annotations
import sys
import argparse
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.netwin_odds_downloader import NetwinOddsDownloader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Netwin Live Odds Downloader CLI")
    parser.add_argument("--tournament", type=str, help="Nome del torneo (es. 'Europa League', 'LaLiga', 'Serie A')")
    parser.add_argument("--all", action="store_true", help="Scarica tutti i tornei principali attivi")
    parser.add_argument("--headless", action="store_true", default=True, help="Modalità headless per browser")

    args = parser.parse_args()

    if args.all:
        tournaments = ["Europa League", "LaLiga", "Serie A", "Premier League", "Bundesliga"]
    elif args.tournament:
        tournaments = [args.tournament]
    else:
        # Default sui due tornei chiave di oggi/domani
        tournaments = ["Europa League", "LaLiga"]

    print("=" * 75)
    print(f"📥 NETWIN LIVE ODDS DOWNLOADER — Avvio Scarico Quote: {tournaments}")
    print("=" * 75)

    downloader = NetwinOddsDownloader(headless=args.headless)
    matches = downloader.download_tournaments(tournaments)

    print("\n" + "=" * 75)
    print(f"✅ SCARICO COMPLETATO! Trovate {len(matches)} partite con quote ufficiali:")
    print("=" * 75)

    for idx, m in enumerate(matches, 1):
        print(f"\n{idx}. ⚽ {m['match_name']} ({m['tournament']}) — Kickoff: {m['kickoff']}")
        print(f"   Palinsesto AAMS: {m['palinsesto']} | Avvenimento: {m['avvenimento']}")
        mkts = m.get("markets", {})
        
        if "1X2" in mkts:
            o1x2 = mkts["1X2"]
            print(f"   • 1X2: 1 @ {o1x2.get('1')} | X @ {o1x2.get('X')} | 2 @ {o1x2.get('2')}")
        
        if "DOPPIA_CHANCE" in mkts:
            odc = mkts["DOPPIA_CHANCE"]
            print(f"   • Doppia Chance: 1X @ {odc.get('1X')} | X2 @ {odc.get('X2')} | 12 @ {odc.get('12')}")
            
        if "UNDER_OVER" in mkts:
            uo_25 = mkts["UNDER_OVER"].get("2.5", {})
            uo_05 = mkts["UNDER_OVER"].get("0.5", {})
            print(f"   • Under/Over 2.5: Under @ {uo_25.get('Under')} | Over @ {uo_25.get('Over')}")
            if uo_05:
                print(f"   • Under/Over 0.5: Under @ {uo_05.get('Under')} | Over @ {uo_05.get('Over')}")
                
        if "GOL_NOGOL" in mkts:
            gng = mkts["GOL_NOGOL"]
            print(f"   • Gol/NoGol: Gol @ {gng.get('Gol')} | NoGol @ {gng.get('NoGol')}")

    print("\n" + "=" * 75)
    print("📁 Quote archiviate e sincronizzate in:")
    print("   • data/netwin_live_odds.json (Palinsesto Completo)")
    print("   • data/netwin_odds_cache.json (Cache per NetwinOddsChecker & StrictTicketPipeline)")
    print("=" * 75)

if __name__ == "__main__":
    main()
