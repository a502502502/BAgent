"""
import_tennis_csv.py — Importa CSV Jeff Sackmann nel DB BAgent.

Dataset gratuiti (ATP, WTA, Doppio):
  https://github.com/JeffSackmann/tennis_atp
  https://github.com/JeffSackmann/tennis_wta
  https://github.com/JeffSackmann/tennis_MatchChartingProject  (doppio)

Formato CSV Sackmann:
  atp_matches_YYYY.csv / wta_matches_YYYY.csv
  Colonne: tourney_id, tourney_name, surface, best_of, round,
           winner_name, winner_rank, loser_name, loser_rank, score,
           minutes, w_ace, w_df, w_1stIn, w_1stWon, ... l_ace, ...

Utilizzo:
    # Singolo file
    python scripts/import_tennis_csv.py --file data/tennis/atp_matches_2025.csv

    # Cartella intera (tutti i CSV)
    python scripts/import_tennis_csv.py --dir data/tennis/atp/

    # WTA
    python scripts/import_tennis_csv.py --dir data/tennis/wta/ --type wta

    # Doppio
    python scripts/import_tennis_csv.py --dir data/tennis/doubles/ --type doubles

    # Solo ultimi N anni
    python scripts/import_tennis_csv.py --dir data/tennis/atp/ --from-year 2020

    # Download automatico da GitHub Sackmann
    python scripts/import_tennis_csv.py --download atp --from-year 2020
    python scripts/import_tennis_csv.py --download wta --from-year 2020

Nota: i CSV vengono scaricati dal GitHub ufficiale di Sackmann in data/tennis/.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from services.database.schema import get_db, _create_tables

# ── Mapping colonne Sackmann ──────────────────────────────────────────────────

MATCH_COLS = [
    "tourney_id", "tourney_name", "surface", "draw_size", "tourney_level",
    "tourney_date", "match_num",
    "winner_id", "winner_seed", "winner_entry", "winner_name",
    "winner_hand", "winner_ht", "winner_ioc", "winner_age",
    "loser_id",  "loser_seed",  "loser_entry",  "loser_name",
    "loser_hand",  "loser_ht",  "loser_ioc",  "loser_age",
    "score", "best_of", "round", "minutes",
    "w_ace", "w_df", "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon",
    "w_SvGms", "w_bpSaved", "w_bpFaced",
    "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon", "l_2ndWon",
    "l_SvGms", "l_bpSaved", "l_bpFaced",
    "winner_rank", "winner_rank_points", "loser_rank", "loser_rank_points",
]

def _safe_int(v):
    try: return int(float(v)) if v not in ("", None, "NA", "N/A") else None
    except: return None

def _safe_float(v):
    try: return float(v) if v not in ("", None, "NA", "N/A") else None
    except: return None

def _surface_norm(s: str) -> str:
    s = (s or "").strip().lower()
    if s in ("clay", "terra"): return "clay"
    if s in ("grass", "erba"): return "grass"
    if s in ("hard", "dura"): return "hard"
    if s in ("carpet", "moquette"): return "carpet"
    return s or "hard"

def _date_from_tourney(tourney_date: str) -> str:
    """Converte YYYYMMDD → YYYY-MM-DD."""
    d = str(tourney_date or "").strip()
    if len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:]}"
    return d

# ── Import singola riga ───────────────────────────────────────────────────────

def _row_to_match(row: dict, match_type: str = "singles") -> tuple | None:
    winner = row.get("winner_name", "").strip()
    loser  = row.get("loser_name",  "").strip()
    if not winner or not loser:
        return None

    tourney_date = _date_from_tourney(row.get("tourney_date", ""))
    surface = _surface_norm(row.get("surface", ""))

    return (
        row.get("tourney_id", ""),
        row.get("tourney_name", "").strip(),
        surface,
        row.get("tourney_level", "").strip(),
        tourney_date,
        match_type,
        row.get("round", "").strip(),
        _safe_int(row.get("best_of")),
        winner,
        _safe_int(row.get("winner_rank")),
        _safe_int(row.get("winner_rank_points")),
        loser,
        _safe_int(row.get("loser_rank")),
        _safe_int(row.get("loser_rank_points")),
        row.get("score", "").strip(),
        _safe_int(row.get("minutes")),
        _safe_int(row.get("w_ace")),
        _safe_int(row.get("w_df")),
        _safe_int(row.get("w_1stIn")),
        _safe_int(row.get("w_1stWon")),
        _safe_int(row.get("w_2ndWon")),
        _safe_int(row.get("w_svpt")),
        _safe_int(row.get("w_bpSaved")),
        _safe_int(row.get("w_bpFaced")),
        _safe_int(row.get("l_ace")),
        _safe_int(row.get("l_df")),
        _safe_int(row.get("l_1stIn")),
        _safe_int(row.get("l_1stWon")),
        _safe_int(row.get("l_2ndWon")),
        _safe_int(row.get("l_svpt")),
        _safe_int(row.get("l_bpSaved")),
        _safe_int(row.get("l_bpFaced")),
    )

# ── Import file ───────────────────────────────────────────────────────────────

def import_file(conn: sqlite3.Connection, path: Path, match_type: str = "singles") -> int:
    rows_inserted = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            t = _row_to_match(row, match_type)
            if t:
                batch.append(t)
            if len(batch) >= 500:
                rows_inserted += _upsert_batch(conn, batch)
                batch = []
        if batch:
            rows_inserted += _upsert_batch(conn, batch)
    return rows_inserted

def _upsert_batch(conn: sqlite3.Connection, batch: list) -> int:
    try:
        conn.executemany("""
            INSERT INTO tennis_matches (
                tourney_id, tourney_name, surface, tourney_level, tourney_date,
                match_type, round, best_of,
                winner_name, winner_rank, winner_rank_pts,
                loser_name, loser_rank, loser_rank_pts,
                score, minutes,
                w_ace, w_df, w_1stIn, w_1stWon, w_2ndWon, w_svpt, w_bpSaved, w_bpFaced,
                l_ace, l_df, l_1stIn, l_1stWon, l_2ndWon, l_svpt, l_bpSaved, l_bpFaced
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(tourney_id, match_type, round, winner_name, loser_name) DO UPDATE SET
                score    = excluded.score,
                minutes  = COALESCE(excluded.minutes, tennis_matches.minutes),
                w_ace    = COALESCE(excluded.w_ace,   tennis_matches.w_ace),
                l_ace    = COALESCE(excluded.l_ace,   tennis_matches.l_ace)
        """, batch)
        conn.commit()
        return len(batch)
    except Exception as e:
        print(f"  ⚠️  Errore batch: {e}")
        conn.rollback()
        return 0

# ── Download da GitHub Sackmann ───────────────────────────────────────────────

def download_sackmann(tour: str, from_year: int, to_year: int, out_dir: Path) -> list[Path]:
    """Scarica i CSV da GitHub Sackmann (atp o wta)."""
    import urllib.request

    base_url = {
        "atp":     "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master",
        "wta":     "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master",
    }.get(tour.lower())

    if not base_url:
        print(f"Tour non supportato per download: {tour}")
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []

    for year in range(from_year, to_year + 1):
        prefix = "atp" if tour.lower() == "atp" else "wta"
        fname  = f"{prefix}_matches_{year}.csv"
        url    = f"{base_url}/{fname}"
        dest   = out_dir / fname

        if dest.exists():
            print(f"  ↩  {fname} già presente, skip")
            downloaded.append(dest)
            continue

        try:
            print(f"  ↓  Download {fname}...", end=" ", flush=True)
            urllib.request.urlretrieve(url, dest)
            print(f"OK ({dest.stat().st_size // 1024} KB)")
            downloaded.append(dest)
        except Exception as e:
            print(f"ERRORE: {e}")

    return downloaded

# ── Aggiorna stats giocatori ──────────────────────────────────────────────────

def rebuild_player_stats(conn: sqlite3.Connection) -> int:
    """
    Ricalcola tennis_players dalle partite importate.
    Aggrega per giocatore + anno + superficie.
    """
    print("Ricalcolo statistiche giocatori...", end=" ", flush=True)

    surfaces = ["clay", "grass", "hard", "carpet", "all"]
    rows_updated = 0

    for surface in surfaces:
        where = "" if surface == "all" else f"AND surface = '{surface}'"

        # Vittorie
        wins = conn.execute(f"""
            SELECT winner_name as player,
                   SUBSTR(tourney_date, 1, 4) as year,
                   COUNT(*) as w,
                   AVG(winner_rank) as avg_rank,
                   AVG(CAST(w_ace AS REAL)) as avg_ace,
                   AVG(CAST(w_df  AS REAL)) as avg_df,
                   AVG(CASE WHEN w_svpt > 0 THEN CAST(w_1stIn  AS REAL)/w_svpt ELSE NULL END) as avg_1st_in,
                   AVG(CASE WHEN w_1stIn > 0 THEN CAST(w_1stWon AS REAL)/w_1stIn ELSE NULL END) as avg_1st_won,
                   AVG(CASE WHEN w_svpt-w_1stIn > 0 THEN CAST(w_2ndWon AS REAL)/(w_svpt-w_1stIn) ELSE NULL END) as avg_2nd_won,
                   AVG(CASE WHEN w_bpFaced > 0 THEN CAST(w_bpSaved AS REAL)/w_bpFaced ELSE NULL END) as avg_bp_saved
            FROM tennis_matches
            WHERE winner_name != '' AND tourney_date != '' {where}
            GROUP BY winner_name, year
        """).fetchall()

        # Sconfitte (per conteggio partite totali)
        losses = conn.execute(f"""
            SELECT loser_name as player,
                   SUBSTR(tourney_date, 1, 4) as year,
                   COUNT(*) as l
            FROM tennis_matches
            WHERE loser_name != '' AND tourney_date != '' {where}
            GROUP BY loser_name, year
        """).fetchall()

        loss_map: dict[tuple, int] = {}
        for r in losses:
            loss_map[(r["player"], r["year"])] = r["l"]

        for r in wins:
            player, year = r["player"], r["year"]
            w = r["w"]
            l = loss_map.get((player, year), 0)
            mp = w + l

            conn.execute("""
                INSERT INTO tennis_players
                    (player_name, year, surface, matches_played, matches_won, win_pct,
                     avg_rank, avg_ace, avg_df, avg_1st_in_pct, avg_1st_won_pct,
                     avg_2nd_won_pct, avg_bp_saved_pct)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(player_name, year, surface) DO UPDATE SET
                    matches_played    = excluded.matches_played,
                    matches_won       = excluded.matches_won,
                    win_pct           = excluded.win_pct,
                    avg_rank          = excluded.avg_rank,
                    avg_ace           = excluded.avg_ace,
                    avg_df            = excluded.avg_df,
                    avg_1st_in_pct    = excluded.avg_1st_in_pct,
                    avg_1st_won_pct   = excluded.avg_1st_won_pct,
                    avg_2nd_won_pct   = excluded.avg_2nd_won_pct,
                    avg_bp_saved_pct  = excluded.avg_bp_saved_pct
            """, (
                player, int(year), surface, mp, w,
                round(w/mp, 3) if mp else None,
                r["avg_rank"],
                r["avg_ace"], r["avg_df"],
                r["avg_1st_in"], r["avg_1st_won"],
                r["avg_2nd_won"], r["avg_bp_saved"],
            ))
            rows_updated += 1

        conn.commit()

    print(f"{rows_updated} righe")
    return rows_updated

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Importa CSV Sackmann nel DB BAgent.")
    parser.add_argument("--file",       type=str, help="Singolo file CSV")
    parser.add_argument("--dir",        type=str, help="Cartella con CSV")
    parser.add_argument("--download",   type=str, help="Download da GitHub: 'atp' o 'wta'")
    parser.add_argument("--from-year",  type=int, default=2015)
    parser.add_argument("--to-year",    type=int, default=datetime.now().year)
    parser.add_argument("--type",       type=str, default="singles",
                        choices=["singles", "doubles"],
                        help="Tipo partita (default: singles)")
    parser.add_argument("--db",         type=str, default=str(ROOT / "data" / "bagent.db"))
    parser.add_argument("--no-stats",   action="store_true",
                        help="Salta ricalcolo statistiche giocatori")
    args = parser.parse_args()

    db_path = Path(args.db)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    _create_tables(conn)

    total = 0

    # Download automatico
    if args.download:
        tour = args.download.lower()
        out_dir = ROOT / "data" / "tennis" / tour
        files = download_sackmann(tour, args.from_year, args.to_year, out_dir)
        print(f"\nImport {len(files)} file scaricati...")
        for f in sorted(files):
            n = import_file(conn, f, match_type="singles")
            print(f"  {f.name}: {n} partite")
            total += n

    # File singolo
    elif args.file:
        f = Path(args.file)
        print(f"Import {f.name}...")
        n = import_file(conn, f, match_type=args.type)
        print(f"  {n} partite importate")
        total = n

    # Cartella
    elif args.dir:
        d = Path(args.dir)
        files = sorted(d.glob("*.csv"))
        print(f"Trovati {len(files)} file CSV in {d}")
        for f in files:
            if args.from_year and args.from_year > 2000:
                # Prova a estrarre l'anno dal nome file
                parts = f.stem.split("_")
                year_part = next((p for p in parts if p.isdigit() and len(p) == 4), None)
                if year_part and int(year_part) < args.from_year:
                    print(f"  ⏭  {f.name} (anno {year_part} < {args.from_year})")
                    continue
            n = import_file(conn, f, match_type=args.type)
            print(f"  {f.name}: {n} partite")
            total += n
    else:
        parser.print_help()
        return

    print(f"\nTotale partite importate: {total}")

    if not args.no_stats and total > 0:
        rebuild_player_stats(conn)

    conn.close()

    # Verifica
    conn2 = sqlite3.connect(str(db_path))
    n_matches = conn2.execute("SELECT COUNT(*) FROM tennis_matches").fetchone()[0]
    n_players = conn2.execute("SELECT COUNT(*) FROM tennis_players").fetchone()[0]
    conn2.close()
    print(f"DB: {n_matches} partite tennis, {n_players} profili giocatori")
    print(f"Percorso: {db_path}")


if __name__ == "__main__":
    main()
