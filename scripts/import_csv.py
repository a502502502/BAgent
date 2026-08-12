"""
import_csv.py — Importa CSV scaricati da FootyStats nel database BAgent.

Utilizzo:
    python scripts/import_csv.py --dir /path/alla/cartella/csv
    python scripts/import_csv.py --dir data/csv_import

Il nome del file determina il tipo di dati:
    *-matches-*   → tabella matches
    *-teams-*     → tabella teams  (NON teams2)
    *-players-*   → tabella players
    *-league-*    → tabella leagues
"""

import sys, os, csv, argparse, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.database.schema import get_db


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

def safe_int(val):
    try: return int(float(val)) if val and val.strip() not in ('', 'N/A', 'n/a') else None
    except: return None

def safe_float(val):
    try: return float(val) if val and val.strip() not in ('', 'N/A', 'n/a') else None
    except: return None

def guess_league_season(filename: str):
    """Estrae campionato e stagione dal nome del file."""
    name = Path(filename).stem
    # es. europe-uefa-europa-conference-league-matches-2026-to-2027-stats
    m = re.search(r'(\d{4})-to-(\d{4})', name)
    season = f"{m.group(1)}/{m.group(2)}" if m else "unknown"
    # Rimuovi anno e suffisso
    league = re.sub(r'-\d{4}-to-\d{4}-stats.*', '', name)
    league = re.sub(r'-(matches|teams2?|players|league).*', '', league)
    return league, season


# ------------------------------------------------------------------
# Import matches
# ------------------------------------------------------------------

def import_matches(conn, filepath: Path, league: str, season: str):
    imported = skipped = 0
    with open(filepath, encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO matches (
                        league, season, date_gmt, timestamp, status,
                        home_team, away_team,
                        home_goals, away_goals, home_goals_ht, away_goals_ht, total_goals,
                        home_corners, away_corners,
                        home_shots, away_shots, home_shots_on_target, away_shots_on_target,
                        home_xg, away_xg,
                        home_possession, away_possession,
                        home_yellow_cards, away_yellow_cards,
                        home_red_cards, away_red_cards,
                        attendance, referee,
                        odds_home_win, odds_draw, odds_away_win,
                        odds_over25, odds_btts_yes, odds_btts_no,
                        btts_pct_pre_match, over25_pct_pre_match,
                        avg_goals_pre_match, avg_corners_pre_match,
                        home_ppg_pre_match, away_ppg_pre_match
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    league, season,
                    row.get('date_GMT','').strip(),
                    safe_int(row.get('timestamp')),
                    row.get('status','').strip(),
                    row.get('home_team_name','').strip(),
                    row.get('away_team_name','').strip(),
                    safe_int(row.get('home_team_goal_count')),
                    safe_int(row.get('away_team_goal_count')),
                    safe_int(row.get('home_team_goal_count_half_time')),
                    safe_int(row.get('away_team_goal_count_half_time')),
                    safe_int(row.get('total_goal_count')),
                    safe_int(row.get('home_team_corner_count')),
                    safe_int(row.get('away_team_corner_count')),
                    safe_int(row.get('home_team_shots')),
                    safe_int(row.get('away_team_shots')),
                    safe_int(row.get('home_team_shots_on_target')),
                    safe_int(row.get('away_team_shots_on_target')),
                    safe_float(row.get('team_a_xg')),
                    safe_float(row.get('team_b_xg')),
                    safe_float(row.get('home_team_possession')),
                    safe_float(row.get('away_team_possession')),
                    safe_int(row.get('home_team_yellow_cards')),
                    safe_int(row.get('away_team_yellow_cards')),
                    safe_int(row.get('home_team_red_cards')),
                    safe_int(row.get('away_team_red_cards')),
                    safe_int(row.get('attendance')),
                    row.get('referee','').strip(),
                    safe_float(row.get('odds_ft_home_team_win')),
                    safe_float(row.get('odds_ft_draw')),
                    safe_float(row.get('odds_ft_away_team_win')),
                    safe_float(row.get('odds_ft_over25')),
                    safe_float(row.get('odds_btts_yes')),
                    safe_float(row.get('odds_btts_no')),
                    safe_float(row.get('btts_percentage_pre_match')),
                    safe_float(row.get('over_25_percentage_pre_match')),
                    safe_float(row.get('average_goals_per_match_pre_match')),
                    safe_float(row.get('average_corners_per_match_pre_match')),
                    safe_float(row.get('Pre-Match PPG (Home)')),
                    safe_float(row.get('Pre-Match PPG (Away)')),
                ))
                imported += 1
            except Exception as e:
                skipped += 1
    conn.commit()
    return imported, skipped


# ------------------------------------------------------------------
# Import teams
# ------------------------------------------------------------------

def import_teams(conn, filepath: Path, league: str, season: str):
    imported = skipped = 0
    with open(filepath, encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO teams (
                        team_name, common_name, league, season, country,
                        matches_played, wins, draws, losses,
                        goals_scored, goals_conceded,
                        goals_scored_home, goals_conceded_home,
                        goals_scored_away, goals_conceded_away,
                        goals_scored_per_match, goals_conceded_per_match,
                        clean_sheets, clean_sheet_pct,
                        btts_count, btts_pct,
                        over15_pct, over25_pct, over35_pct,
                        corners_total, corners_per_match,
                        xg_for_avg, xg_against_avg,
                        win_pct, cards_per_match, ppg,
                        leading_at_ht_pct, btts_ht_pct
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    row.get('team_name','').strip(),
                    row.get('common_name','').strip(),
                    league, season,
                    row.get('country','').strip(),
                    safe_int(row.get('matches_played')),
                    safe_int(row.get('wins')),
                    safe_int(row.get('draws')),
                    safe_int(row.get('losses')),
                    safe_int(row.get('goals_scored')),
                    safe_int(row.get('goals_conceded')),
                    safe_int(row.get('goals_scored_home')),
                    safe_int(row.get('goals_conceded_home')),
                    safe_int(row.get('goals_scored_away')),
                    safe_int(row.get('goals_conceded_away')),
                    safe_float(row.get('goals_scored_per_match')),
                    safe_float(row.get('goals_conceded_per_match')),
                    safe_int(row.get('clean_sheets')),
                    safe_float(row.get('clean_sheet_percentage')),
                    safe_int(row.get('btts_count')),
                    safe_float(row.get('btts_percentage')),
                    safe_float(row.get('over15_percentage')),
                    safe_float(row.get('over25_percentage')),
                    safe_float(row.get('over35_percentage')),
                    safe_int(row.get('corners_total')),
                    safe_float(row.get('corners_per_match')),
                    safe_float(row.get('xg_for_avg_overall')),
                    safe_float(row.get('xg_against_avg_overall')),
                    safe_float(row.get('win_percentage')),
                    safe_float(row.get('cards_per_match')),
                    safe_float(row.get('ppg')),
                    safe_float(row.get('leading_at_half_time_percentage')),
                    safe_float(row.get('btts_half_time_percentage')),
                ))
                imported += 1
            except Exception as e:
                skipped += 1
    conn.commit()
    return imported, skipped


# ------------------------------------------------------------------
# Import players
# ------------------------------------------------------------------

def import_players(conn, filepath: Path, league: str, season: str):
    imported = skipped = 0
    with open(filepath, encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO players (
                        full_name, age, nationality, position, current_club,
                        league, season, minutes_played, appearances,
                        goals, assists, goals_per_90, assists_per_90,
                        xg_per_game, shots_per_90, shots_on_target_per_game,
                        key_passes_per_game, yellow_cards, red_cards,
                        cards_per_90, average_rating, rank_in_club_top_scorer
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    row.get('full_name','').strip(),
                    safe_int(row.get('age')),
                    row.get('nationality','').strip(),
                    row.get('position','').strip(),
                    row.get('Current Club','').strip(),
                    league, season,
                    safe_int(row.get('minutes_played_overall')),
                    safe_int(row.get('appearances_overall')),
                    safe_int(row.get('goals_overall')),
                    safe_int(row.get('assists_overall')),
                    safe_float(row.get('goals_per_90_overall')),
                    safe_float(row.get('assists_per_90_overall')),
                    safe_float(row.get('xg_per_game_overall')),
                    safe_float(row.get('shots_per_90_overall')),
                    safe_float(row.get('shots_on_target_per_game_overall')),
                    safe_float(row.get('key_passes_per_game_overall')),
                    safe_int(row.get('yellow_cards_overall')),
                    safe_int(row.get('red_cards_overall')),
                    safe_float(row.get('cards_per_90_overall')),
                    safe_float(row.get('average_rating_overall')),
                    safe_int(row.get('rank_in_club_top_scorer')),
                ))
                imported += 1
            except Exception as e:
                skipped += 1
    conn.commit()
    return imported, skipped


# ------------------------------------------------------------------
# Import leagues
# ------------------------------------------------------------------

def import_leagues(conn, filepath: Path, league: str, season: str):
    imported = skipped = 0
    with open(filepath, encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO leagues (
                        name, season, avg_goals_per_match, btts_pct,
                        avg_corners_per_match, over25_pct, matches_completed
                    ) VALUES (?,?,?,?,?,?,?)
                """, (
                    row.get('name', league).strip(),
                    season,
                    safe_float(row.get('average_goals_per_match')),
                    safe_float(row.get('btts_percentage')),
                    safe_float(row.get('average_corners_per_match')),
                    safe_float(row.get('over25_percentage')),
                    safe_int(row.get('matches_completed')),
                ))
                imported += 1
            except Exception as e:
                skipped += 1
    conn.commit()
    return imported, skipped


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def process_file(conn, filepath: Path):
    name = filepath.name.lower()
    league, season = guess_league_season(filepath.name)

    # Salta teams2 (contiene colonne diverse, già coperto da teams)
    if 'teams2' in name:
        return None

    if 'matches' in name:
        kind = 'matches'
        imp, skip = import_matches(conn, filepath, league, season)
    elif 'teams' in name:
        kind = 'teams'
        imp, skip = import_teams(conn, filepath, league, season)
    elif 'players' in name:
        kind = 'players'
        imp, skip = import_players(conn, filepath, league, season)
    elif 'league' in name:
        kind = 'league'
        imp, skip = import_leagues(conn, filepath, league, season)
    else:
        return None

    return kind, imp, skip


def main():
    parser = argparse.ArgumentParser(description='Importa CSV FootyStats nel DB BAgent')
    parser.add_argument('--dir', default='data/csv_import',
                        help='Cartella contenente i file CSV')
    parser.add_argument('--db', default=None,
                        help='Percorso DB SQLite (default: data/bagent.db)')
    args = parser.parse_args()

    csv_dir = Path(args.dir)
    if not csv_dir.exists():
        print(f"Errore: cartella {csv_dir} non trovata")
        print(f"Crea la cartella e metti i CSV dentro:")
        print(f"  mkdir -p {csv_dir}")
        sys.exit(1)

    from services.database.schema import get_db, DB_PATH
    db_path = Path(args.db) if args.db else DB_PATH
    conn = get_db(db_path)

    csv_files = sorted(csv_dir.glob('*.csv'))
    if not csv_files:
        print(f"Nessun CSV trovato in {csv_dir}")
        sys.exit(1)

    print(f"Database: {db_path}")
    print(f"CSV trovati: {len(csv_files)}")
    print()

    totals = {'matches': 0, 'teams': 0, 'players': 0, 'league': 0}

    for f in csv_files:
        result = process_file(conn, f)
        if result is None:
            print(f"  ⏭️  {f.name} (saltato)")
            continue
        kind, imp, skip = result
        totals[kind] = totals.get(kind, 0) + imp
        status = "✅" if imp > 0 else "⚠️"
        print(f"  {status} {f.name}")
        print(f"     → {imp} righe importate, {skip} saltate [{kind}]")

    print()
    print("=" * 50)
    print("  RIEPILOGO IMPORT")
    print("=" * 50)
    for kind, count in totals.items():
        print(f"  {kind:<12}: {count} righe")

    # Verifica DB
    for table in ['matches', 'teams', 'players', 'leagues']:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  DB {table:<10}: {n} record totali")

    conn.close()
    print()
    print(f"✅ Database aggiornato: {db_path}")


if __name__ == "__main__":
    main()
