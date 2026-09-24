"""Backtest NBA walk-forward su handicap e totale.

Lo scarico `--fetch` legge i box score regular season da Basketball-Reference.

Non certifica ticket e non passa da StrictTicketPipeline.
Senza closing line stampa solo l'errore del modello. L'edge sulla quota
italiana si calcola solo se il file linee è presente.

Esempio:
  python scripts/nba_closing_backtest.py --fetch --seasons 2023-24 2024-25 2025-26
  python scripts/nba_closing_backtest.py --games data/nba/game_logs.csv --lines data/nba/closing_lines.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.basketball.backtest import ClosingLine, WalkForwardBacktest, summarize
from services.basketball.fetch import CANONICAL, TEAMS, fetch_team_boxes, write_team_boxes
from services.basketball.gamelog import load_team_boxes, pair_team_boxes


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest closing line NBA, solo ricerca.")
    parser.add_argument("--games", type=Path, default=ROOT / "data" / "nba" / "game_logs.csv")
    parser.add_argument("--lines", type=Path, default=None)
    parser.add_argument("--fetch", action="store_true", help="Scarica i box score e sovrascrive --games")
    parser.add_argument("--seasons", nargs="+", default=["2023-24", "2024-25", "2025-26"])
    parser.add_argument("--min-games", type=int, default=10)
    parser.add_argument("--min-edge", type=float, default=0.04)
    parser.add_argument("--odds", type=float, default=1.87, help="Quota decimale se la linea non ha un prezzo")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "nba_closing_backtest.csv")
    args = parser.parse_args()

    if args.fetch:
        boxes = _fetch_missing_seasons(args.games, args.seasons)
        print(f"Box score pronti: {len(boxes)} righe squadra in {args.games}")

    if not args.games.exists():
        raise SystemExit(
            f"Manca {args.games}. Lancia con --fetch oppure passa un CSV di box score."
        )

    games = pair_team_boxes(load_team_boxes(args.games))
    lines = _load_lines(args.lines) if args.lines else []
    rows = WalkForwardBacktest(
        min_games=args.min_games,
        min_edge=args.min_edge,
        default_odds=args.odds,
    ).run(games, lines)
    summary = summarize(rows)
    _write_rows(rows, args.output)
    _print_summary(summary, args)


def _fetch_missing_seasons(path: Path, seasons: list[str]) -> list:
    boxes = load_team_boxes(path) if path.exists() else []
    saved_homes = {(box.season, box.team) for box in boxes if box.is_home}
    for season in seasons:
        missing = [team for team in TEAMS if (season, CANONICAL.get(team, team)) not in saved_homes]
        if not missing:
            print(f"{season}: gia' completo")
            continue
        print(f"Scarico {season}: {len(missing)} squadre...")
        for index, team in enumerate(missing, start=1):
            boxes.extend(fetch_team_boxes(season, teams=[team], pause_seconds=0))
            paired = write_team_boxes(boxes, path)
            print(f"  {season} {CANONICAL.get(team, team)} ({index}/{len(missing)}) -> {paired} partite", flush=True)
            if index < len(missing):
                time.sleep(1.5)
    return boxes


def _load_lines(path: Path) -> list[ClosingLine]:
    if not path.exists():
        raise SystemExit(f"File linee assente: {path}")
    lines: list[ClosingLine] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            lines.append(
                ClosingLine(
                    game_date=datetime.strptime(row["date"].strip()[:10], "%Y-%m-%d").date(),
                    home=row["home"].strip().upper(),
                    away=row["away"].strip().upper(),
                    home_spread=float(row["home_spread"]),
                    total=_optional_float(row.get("total")),
                    home_spread_odds=_optional_float(row.get("home_spread_odds")),
                    away_spread_odds=_optional_float(row.get("away_spread_odds")),
                    over_odds=_optional_float(row.get("over_odds")),
                    under_odds=_optional_float(row.get("under_odds")),
                )
            )
    return lines


def _optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def _write_rows(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "season",
        "date",
        "home",
        "away",
        "predicted_margin",
        "predicted_total",
        "margin_sigma",
        "total_sigma",
        "actual_margin",
        "actual_total",
        "home_spread",
        "total_line",
        "spread_side",
        "spread_edge",
        "spread_result",
        "total_side",
        "total_edge",
        "total_result",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "season": row.season,
                    "date": row.game_date.isoformat(),
                    "home": row.home,
                    "away": row.away,
                    "predicted_margin": round(row.predicted_margin, 3),
                    "predicted_total": round(row.predicted_total, 3),
                    "margin_sigma": round(row.margin_sigma, 3),
                    "total_sigma": round(row.total_sigma, 3),
                    "actual_margin": row.actual_margin,
                    "actual_total": row.actual_total,
                    "home_spread": row.home_spread,
                    "total_line": row.total_line,
                    "spread_side": row.spread_side,
                    "spread_edge": None if row.spread_edge is None else round(row.spread_edge, 4),
                    "spread_result": row.spread_result,
                    "total_side": row.total_side,
                    "total_edge": None if row.total_edge is None else round(row.total_edge, 4),
                    "total_result": row.total_result,
                }
            )


def _print_summary(summary, args) -> None:
    print(f"Proiezioni walk-forward: {summary.projections}")
    print(f"MAE margine: {summary.margin_mae:.2f} punti")
    print(f"MAE totale:  {summary.total_mae:.2f} punti")
    print(f"Dettaglio: {args.output}")
    if args.lines is None:
        print(
            "Test edge non eseguito: senza closing line il MAE non dice se Netwin paga il modello."
        )
        return
    print(f"Linee agganciate: {summary.lines_joined}")
    print(
        f"Handicap @ {args.odds:.2f} se la riga non ha prezzo, soglia edge {args.min_edge:.0%}: "
        f"{summary.spread_bets} giocate, hit { _fmt(summary.spread_hit_rate) }, ROI { _fmt(summary.spread_roi) }"
    )
    print(
        f"Totale: {summary.total_bets} giocate, hit { _fmt(summary.total_hit_rate) }, ROI { _fmt(summary.total_roi) }"
    )


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/d"
    return f"{value:.1%}"


if __name__ == "__main__":
    main()
