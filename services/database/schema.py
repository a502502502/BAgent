"""
Schema e connessione database SQLite per BAgent.

Tabelle:
  matches  — partite con risultati, gol, corner, xG, quote pre-match
  teams    — stats aggregate per squadra/campionato/stagione
  players  — stats individuali giocatori
  leagues  — stats campionato

Utilizzo:
    from services.database.schema import get_db
    conn = get_db()  # apre/crea bagent.db
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "bagent.db"


def get_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Apre la connessione al DB, crea le tabelle se non esistono."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    -- ----------------------------------------------------------------
    -- Partite
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS matches (
        id                          INTEGER PRIMARY KEY AUTOINCREMENT,
        league                      TEXT NOT NULL,
        season                      TEXT NOT NULL,
        date_gmt                    TEXT,
        timestamp                   INTEGER,
        status                      TEXT,
        home_team                   TEXT NOT NULL,
        away_team                   TEXT NOT NULL,
        home_goals                  INTEGER,
        away_goals                  INTEGER,
        home_goals_ht               INTEGER,
        away_goals_ht               INTEGER,
        total_goals                 INTEGER,
        home_corners                INTEGER,
        away_corners                INTEGER,
        home_shots                  INTEGER,
        away_shots                  INTEGER,
        home_shots_on_target        INTEGER,
        away_shots_on_target        INTEGER,
        home_xg                     REAL,
        away_xg                     REAL,
        home_possession             REAL,
        away_possession             REAL,
        home_yellow_cards           INTEGER,
        away_yellow_cards           INTEGER,
        home_red_cards              INTEGER,
        away_red_cards              INTEGER,
        attendance                  INTEGER,
        referee                     TEXT,
        -- Quote pre-match
        odds_home_win               REAL,
        odds_draw                   REAL,
        odds_away_win               REAL,
        odds_over25                 REAL,
        odds_btts_yes               REAL,
        odds_btts_no                REAL,
        -- Statistiche pre-match
        btts_pct_pre_match          REAL,
        over25_pct_pre_match        REAL,
        avg_goals_pre_match         REAL,
        avg_corners_pre_match       REAL,
        home_ppg_pre_match          REAL,
        away_ppg_pre_match          REAL,
        UNIQUE(league, season, home_team, away_team, date_gmt)
    );

    -- ----------------------------------------------------------------
    -- Squadre (stats aggregate per stagione)
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS teams (
        id                          INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name                   TEXT NOT NULL,
        common_name                 TEXT,
        league                      TEXT NOT NULL,
        season                      TEXT NOT NULL,
        country                     TEXT,
        matches_played              INTEGER,
        wins                        INTEGER,
        draws                       INTEGER,
        losses                      INTEGER,
        goals_scored                INTEGER,
        goals_conceded              INTEGER,
        goals_scored_home           INTEGER,
        goals_conceded_home         INTEGER,
        goals_scored_away           INTEGER,
        goals_conceded_away         INTEGER,
        goals_scored_per_match      REAL,
        goals_conceded_per_match    REAL,
        clean_sheets                INTEGER,
        clean_sheet_pct             REAL,
        btts_count                  INTEGER,
        btts_pct                    REAL,
        over15_pct                  REAL,
        over25_pct                  REAL,
        over35_pct                  REAL,
        corners_total               INTEGER,
        corners_per_match           REAL,
        xg_for_avg                  REAL,
        xg_against_avg              REAL,
        win_pct                     REAL,
        cards_per_match             REAL,
        ppg                         REAL,
        -- HT stats
        leading_at_ht_pct           REAL,
        btts_ht_pct                 REAL,
        UNIQUE(team_name, league, season)
    );

    -- ----------------------------------------------------------------
    -- Giocatori
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS players (
        id                          INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name                   TEXT NOT NULL,
        age                         INTEGER,
        nationality                 TEXT,
        position                    TEXT,
        current_club                TEXT,
        league                      TEXT NOT NULL,
        season                      TEXT NOT NULL,
        minutes_played              INTEGER,
        appearances                 INTEGER,
        goals                       INTEGER,
        assists                     INTEGER,
        goals_per_90                REAL,
        assists_per_90              REAL,
        xg_per_game                 REAL,
        shots_per_90                REAL,
        shots_on_target_per_game    REAL,
        key_passes_per_game         REAL,
        yellow_cards                INTEGER,
        red_cards                   INTEGER,
        cards_per_90                REAL,
        average_rating              REAL,
        rank_in_club_top_scorer     INTEGER,
        UNIQUE(full_name, current_club, league, season)
    );

    -- ----------------------------------------------------------------
    -- Campionati (stats generali)
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS leagues (
        id                          INTEGER PRIMARY KEY AUTOINCREMENT,
        name                        TEXT NOT NULL,
        season                      TEXT NOT NULL,
        country                     TEXT,
        avg_goals_per_match         REAL,
        btts_pct                    REAL,
        avg_corners_per_match       REAL,
        over25_pct                  REAL,
        matches_completed           INTEGER,
        UNIQUE(name, season)
    );

    -- ----------------------------------------------------------------
    -- Tennis: partite (singolare e doppio)
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS tennis_matches (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        tourney_id          TEXT,
        tourney_name        TEXT NOT NULL,
        surface             TEXT,          -- clay | grass | hard | carpet
        tourney_level       TEXT,          -- G=GrandSlam A=Masters250 M=Masters1000 F=Finals D=Davis
        tourney_date        TEXT,          -- YYYY-MM-DD
        match_type          TEXT DEFAULT 'singles',  -- singles | doubles
        round               TEXT,          -- R128 R64 R32 R16 QF SF F
        best_of             INTEGER,
        winner_name         TEXT NOT NULL,
        winner_rank         INTEGER,
        winner_rank_pts     INTEGER,
        loser_name          TEXT NOT NULL,
        loser_rank          INTEGER,
        loser_rank_pts      INTEGER,
        score               TEXT,          -- es. "6-3 7-5"
        minutes             INTEGER,
        -- Statistiche servizio vincitore
        w_ace               INTEGER,
        w_df                INTEGER,
        w_1stIn             INTEGER,
        w_1stWon            INTEGER,
        w_2ndWon            INTEGER,
        w_svpt              INTEGER,
        w_bpSaved           INTEGER,
        w_bpFaced           INTEGER,
        -- Statistiche servizio perdente
        l_ace               INTEGER,
        l_df                INTEGER,
        l_1stIn             INTEGER,
        l_1stWon            INTEGER,
        l_2ndWon            INTEGER,
        l_svpt              INTEGER,
        l_bpSaved           INTEGER,
        l_bpFaced           INTEGER,
        UNIQUE(tourney_id, match_type, round, winner_name, loser_name)
    );

    -- ----------------------------------------------------------------
    -- Tennis: giocatori (stats aggregate per anno/superficie)
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS tennis_players (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name         TEXT NOT NULL,
        year                INTEGER NOT NULL,
        surface             TEXT NOT NULL,  -- clay | grass | hard | all
        matches_played      INTEGER DEFAULT 0,
        matches_won         INTEGER DEFAULT 0,
        win_pct             REAL,
        avg_rank            REAL,
        -- Statistiche servizio (medie per partita)
        avg_ace             REAL,
        avg_df              REAL,
        avg_1st_in_pct      REAL,
        avg_1st_won_pct     REAL,
        avg_2nd_won_pct     REAL,
        avg_bp_saved_pct    REAL,
        -- Statistiche return (medie come avversario)
        avg_bp_converted_pct REAL,
        UNIQUE(player_name, year, surface)
    );

    -- ----------------------------------------------------------------
    -- Tennis: tornei
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS tennis_tournaments (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        tourney_id          TEXT UNIQUE,
        tourney_name        TEXT NOT NULL,
        surface             TEXT,
        tourney_level       TEXT,
        country             TEXT,
        city                TEXT
    );

    -- ----------------------------------------------------------------
    -- Sesto Senso: articoli grezzi
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS sixth_sense_news (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        home_team       TEXT NOT NULL,
        away_team       TEXT NOT NULL,
        match_date      TEXT,
        collected_at    TEXT NOT NULL,
        team_tag        TEXT,          -- 'home' | 'away' | 'match'
        title           TEXT NOT NULL,
        url             TEXT,
        source          TEXT,
        snippet         TEXT,
        language        TEXT
    );

    -- ----------------------------------------------------------------
    -- Sesto Senso: eventi strutturati (output LLM)
    -- ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS sixth_sense_events (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        home_team       TEXT NOT NULL,
        away_team       TEXT NOT NULL,
        match_date      TEXT,
        created_at      TEXT NOT NULL,
        team            TEXT,          -- nome squadra a cui si riferisce
        player          TEXT,          -- nome giocatore (se applicabile)
        event_type      TEXT,          -- injury | suspension | lineup | morale | fatigue | other
        impact          REAL,          -- -3..+3
        confidence      REAL,          -- 0.0..1.0
        notes           TEXT,
        summary         TEXT,          -- sintesi generale dell'analisi
        overall_confidence REAL
    );

    -- ----------------------------------------------------------------
    -- Indici per query veloci
    -- ----------------------------------------------------------------
    CREATE INDEX IF NOT EXISTS idx_matches_teams
        ON matches(home_team, away_team);
    CREATE INDEX IF NOT EXISTS idx_matches_league
        ON matches(league, season);
    CREATE INDEX IF NOT EXISTS idx_teams_name
        ON teams(team_name, league, season);
    CREATE INDEX IF NOT EXISTS idx_players_club
        ON players(current_club, league, season);
    CREATE INDEX IF NOT EXISTS idx_ss_news_teams
        ON sixth_sense_news(home_team, away_team, match_date);
    CREATE INDEX IF NOT EXISTS idx_ss_events_teams
        ON sixth_sense_events(home_team, away_team, match_date);
    CREATE INDEX IF NOT EXISTS idx_ss_events_type
        ON sixth_sense_events(event_type, team);
    CREATE INDEX IF NOT EXISTS idx_tennis_matches_players
        ON tennis_matches(winner_name, loser_name);
    CREATE INDEX IF NOT EXISTS idx_tennis_matches_tourney
        ON tennis_matches(tourney_name, tourney_date);
    CREATE INDEX IF NOT EXISTS idx_tennis_players_name
        ON tennis_players(player_name, year, surface);
    """)
    conn.commit()


if __name__ == "__main__":
    conn = get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    print(f"Database creato: {DB_PATH}")
    print(f"Tabelle: {[t['name'] for t in tables]}")
    conn.close()
