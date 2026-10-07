"""
scripts/scan_oddspedia_signals.py — Scanner CLI dei segnali di mercato da Oddspedia.

Scansiona in tempo reale:
1. Quote in calo (Dropping Odds) su scala globale.
2. Scommesse di valore matematico (Value Bets).
3. Evidenzia ritardi di allineamento e presenza sui bookmaker italiani (SNAI, Sisal, Eurobet).

Uso:
    python scripts/scan_oddspedia_signals.py
    python scripts/scan_oddspedia_signals.py --min-drop 15.0 --limit 15
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Assicura corretta codifica output console su Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from services.football.external.sources.oddspedia import OddspediaSource

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("scan_oddspedia")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scansiona Dropping Odds e Value Bets da Oddspedia")
    parser.add_argument("--sport", type=str, default="football", help="Sport da analizzare (default: football)")
    parser.add_argument("--min-drop", type=float, default=12.0, help="Soglia minima di calo percentuale (default: 12.0)")
    parser.add_argument("--min-value", type=float, default=3.5, help="Soglia minima overvalue percentuale (default: 3.5)")
    parser.add_argument("--max-value", type=float, default=20.0, help="Soglia massima overvalue (filtro anti-errore, default: 20.0)")
    parser.add_argument("--limit", type=int, default=20, help="Numero massimo di segnali per categoria (default: 20)")
    parser.add_argument("--out", type=str, default=None, help="Percorso di salvataggio JSON personalizzato")

    args = parser.parse_args()

    print("=" * 80)
    print("ODDSPEDIA MARKET RADAR — SCANSIONE SEGNALI IN TEMPO REALE")
    print(f"Sport: {args.sport.upper()} | Min Drop: -{args.min_drop}% | Range Value: +{args.min_value}% / +{args.max_value}%")
    print("=" * 80)

    source = OddspediaSource(headless=True)

    print("\n[1/2] Estrazione Dropping Odds (Quote in Rapido Calo)...")
    dropping_signals = source.fetch_dropping_odds(
        sport=args.sport,
        min_drop_pct=args.min_drop,
        limit=args.limit,
    )
    print(f"Trovati {len(dropping_signals)} segnali di quote in calo con drop >= {args.min_drop}%.")

    print("\n[2/2] Estrazione Value Bets (Scommesse a Valore Matematico)...")
    value_signals = source.fetch_value_bets(
        sport=args.sport,
        min_overvalue_pct=args.min_value,
        max_overvalue_pct=args.max_value,
        limit=args.limit,
    )
    print(f"Trovate {len(value_signals)} value bets con overvalue tra {args.min_value}% e {args.max_value}%.")

    all_signals = dropping_signals + value_signals
    out_path = Path(args.out) if args.out else None
    saved_file = source.export_signals_to_json(all_signals, output_file=out_path)

    # Stampa Report Dropping Odds
    print("\n" + "=" * 80)
    print("TOP QUOTE IN CALO (DROPPING ODDS)")
    print("=" * 80)
    if not dropping_signals:
        print("Nessun calo rilevato sopra la soglia impostata.")
    else:
        for idx, s in enumerate(dropping_signals[:15], 1):
            adm_names = [b["name"] for b in s.italian_bookmakers]
            adm_str = f" [ADM: {', '.join(adm_names)}]" if adm_names else ""
            init_str = f"{s.initial_odd:.2f}" if s.initial_odd else "N/D"
            curr_str = f"{s.current_odd:.2f}" if s.current_odd else "N/D"

            print(f"{idx}. {s.home_team} vs {s.away_team} ({s.league})")
            print(f"   Calcio d'inizio: {s.kickoff_utc} UTC")
            print(f"   Mercato: {s.market} | Selezione: {s.selection}")
            print(f"   Crollo Quota: -{s.drop_percentage}% (da {init_str} a {curr_str}) | Best: {s.best_bookmaker}{adm_str}")
            print("-" * 80)

    # Stampa Report Value Bets
    print("\n" + "=" * 80)
    print("TOP SCOMMESSE DI VALORE (VALUE BETS)")
    print("=" * 80)
    if not value_signals:
        print("Nessuna value bet rilevata nel range impostato.")
    else:
        for idx, s in enumerate(value_signals[:10], 1):
            adm_names = [b["name"] for b in s.italian_bookmakers]
            adm_str = f" [ADM: {', '.join(adm_names)}]" if adm_names else ""
            print(f"{idx}. {s.home_team} vs {s.away_team} ({s.league})")
            print(f"   Mercato: {s.market} | Selezione: {s.selection} @ {s.current_odd}")
            print(f"   Valore Stimato (Edge): +{s.overvalue_pct}% | Probabilita stimata: {s.fair_probability_pct}% | Best: {s.best_bookmaker}{adm_str}")
            print("-" * 80)

    print(f"\nReport completo esportato in: {saved_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
