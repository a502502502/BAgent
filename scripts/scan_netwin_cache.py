#!/usr/bin/env python3
"""Scansione istantanea del palinsesto Netwin già scaricato in cache.

Legge `data/netwin_live_odds.json` e classifica le Hidden Gems con la matrice dei gol.
Il browser si apre solo con `--sync`, e solo se la cache manca o ha più di 12 ore.

Uso:
    python scripts/scan_netwin_cache.py
    python scripts/scan_netwin_cache.py --tournament "Liga Profesional" --min-edge 0.045
    python scripts/scan_netwin_cache.py --sync
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.netwin_cache_reader import (  # noqa: E402
    DEFAULT_CACHE,
    cache_is_stale,
    load_cached_matches,
    scan_netwin_matches,
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Scanner quote Netwin da cache locale.")
    parser.add_argument("--tournament", type=str, default=None, help="Filtro torneo, anche parziale.")
    parser.add_argument("--min-edge", type=float, default=0.045, help="Edge minimo, default 0.045.")
    parser.add_argument("--min-prob", type=float, default=0.70, help="Probabilità minima, default 0.70.")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Scarica da Netwin solo se la cache manca o ha più di 12 ore.",
    )
    parser.add_argument("--cache", type=str, default=str(DEFAULT_CACHE), help="Percorso del JSON di cache.")
    args = parser.parse_args()

    cache_path = Path(args.cache)
    if args.sync and cache_is_stale(cache_path):
        _sync_cache(args.tournament)
    elif args.sync:
        print(f"Cache ancora fresca: {cache_path}")

    matches = load_cached_matches(args.tournament, cache_path)
    print(f"Partite in memoria: {len(matches)}")
    gems = scan_netwin_matches(matches, min_edge=args.min_edge, min_probability=args.min_prob)
    if not gems:
        print("Nessun mercato prezzabile sopra quota 1.20.")
        return

    header = (
        f"{'#':>3} | {'Verdetto':<8} | {'Torneo':<22} | {'Partita':<36} | {'Mercato':<22} | "
        f"{'Quota':>6} | {'Fair':>6} | {'P_matrix':>8} | {'Edge':>7} | Note tattiche"
    )
    print(header)
    print("-" * len(header))
    for index, gem in enumerate(gems, 1):
        note = gem.notes.replace("\n", " ")
        if len(note) > 80:
            note = note[:77] + "..."
        print(
            f"{index:>3} | {(gem.verdict or '—'):<8} | {gem.tournament[:22]:<22} | {gem.match_name[:36]:<36} | "
            f"{gem.market[:22]:<22} | {gem.book_odd:6.2f} | {gem.fair_odd:6.2f} | "
            f"{gem.probability:8.1%} | {gem.edge:+7.1%} | {note}"
        )


def _sync_cache(tournament: str | None) -> None:
    from services.betting.netwin_odds_downloader import NetwinOddsDownloader

    names = [tournament] if tournament else [
        "Europa League",
        "LaLiga",
        "Serie A",
        "Premier League",
        "Bundesliga",
        "Argentina",
        "Brasile",
    ]
    print(f"Cache assente o vecchia. Scarico: {names}")
    NetwinOddsDownloader(headless=True).download_tournaments(names)


if __name__ == "__main__":
    main()
