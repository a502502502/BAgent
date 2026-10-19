#!/usr/bin/env python3
"""
sync_all_2026_rosters.py — Scarica e sincronizza le rose ufficiali 2026/2027
di tutti i massimi campionati (Tier 1) da FootyStats API, popolando:
- player_registry_2026 (per Reality Gate Guardian)
- players (per metriche quantitative, ruoli e presenze)
- teams (per anagrafica club)
in data/bagent.db e storage/database/bagent.db.
"""

from __future__ import annotations
import os
import sys
import time
import sqlite3
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# Carica .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.getenv("FOOTYSTATS_API_KEY")
if not API_KEY:
    print("ERRORE: FOOTYSTATS_API_KEY non configurata.")
    sys.exit(1)

PRIMARY_DB = ROOT / "data" / "bagent.db"
SECONDARY_DB = ROOT / "storage" / "database" / "bagent.db"

# Mappa campionati Tier 1 stagione 2026/2027
TIER1_LEAGUES_2026 = {
    17084: ("Serie A", "Italy", "2026/2027"),
    17146: ("Premier League", "England", "2026/2027"),
    17199: ("La Liga", "Spain", "2026/2027"),
    17210: ("Bundesliga", "Germany", "2026/2027"),
    17102: ("Ligue 1", "France", "2026/2027"),
    17217: ("Primeira Liga", "Portugal", "2026/2027"),
    17265: ("Super Lig", "Turkey", "2026/2027"),
    17097: ("Eredivisie", "Netherlands", "2026/2027"),
    17091: ("Superliga", "Denmark", "2026/2027"),
    16576: ("Allsvenskan", "Sweden", "2026"),
}

def ensure_tables(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_registry_2026 (
        canonical_name TEXT PRIMARY KEY,
        display_name TEXT,
        team_name TEXT NOT NULL,
        former_teams TEXT,
        role TEXT,
        number INTEGER,
        source TEXT DEFAULT 'FOOTYSTATS_2026',
        last_verified TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS official_team_managers_2026 (
        team_name TEXT PRIMARY KEY,
        manager_name TEXT NOT NULL,
        aliases TEXT,
        nationality TEXT,
        appointed_date TEXT,
        contract_until TEXT,
        former_managers_banned TEXT,
        formation TEXT,
        source TEXT DEFAULT 'TRANSFERMARKT_VERIFIED',
        last_verified TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS departed_players_blacklist (
        player_name TEXT,
        former_club TEXT,
        departure_year INTEGER,
        status TEXT,
        PRIMARY KEY (player_name, former_club)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        age INTEGER,
        nationality TEXT,
        position TEXT,
        current_club TEXT,
        league TEXT,
        season TEXT,
        minutes_played INTEGER,
        appearances INTEGER,
        goals INTEGER,
        assists INTEGER,
        goals_per_90 REAL,
        assists_per_90 REAL,
        xg_per_game REAL,
        shots_per_90 REAL,
        shots_on_target_per_game REAL,
        key_passes_per_game REAL,
        yellow_cards INTEGER,
        red_cards INTEGER,
        cards_per_90 REAL,
        average_rating REAL,
        rank_in_club_top_scorer INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        league TEXT,
        country TEXT,
        season TEXT
    )
    """)
    conn.commit()

def fetch_json(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"https://api.football-data-api.com/{endpoint}"
    params["key"] = API_KEY
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                time.sleep(3)
        except Exception as e:
            time.sleep(1)
    return {}

def sync_league(conn: sqlite3.Connection, league_id: int, league_name: str, country: str, season_str: str) -> Dict[str, int]:
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    
    # 1. Fetch Teams
    print(f"\n--- SINCRONIZZAZIONE {league_name.upper()} ({country}, {season_str}) [ID: {league_id}] ---")
    teams_res = fetch_json("league-teams", {"league_id": league_id})
    teams_data = teams_res.get("data", [])
    if not teams_data:
        print(f"  Nessun dato squadre per lega {league_id}")
        return {"teams": 0, "players": 0}
    
    # Check teams and players schema
    team_cols = [r[1] for r in cur.execute("PRAGMA table_info(teams)").fetchall()]
    player_cols = [r[1] for r in cur.execute("PRAGMA table_info(players)").fetchall()]
    teams_map = {}
    for t in teams_data:
        t_id = t.get("id")
        t_name = t.get("cleanName") or t.get("name") or "Unknown"
        teams_map[t_id] = t_name
        if "team_name" in team_cols:
            cur.execute("""
                INSERT OR IGNORE INTO teams (team_name, common_name, league, country, season)
                VALUES (?, ?, ?, ?, ?)
            """, (t_name, t.get("name"), league_name, country, season_str))
        elif "name" in team_cols:
            cur.execute("""
                INSERT OR REPLACE INTO teams (team_id, name, country, league_name, season)
                VALUES (?, ?, ?, ?, ?)
            """, (t_id, t_name, country, league_name, season_str))
    
    print(f"  Squadre caricate: {len(teams_map)}")

    # 2. Fetch Players (paginated)
    total_players = 0
    page = 1
    while True:
        p_res = fetch_json("league-players", {"league_id": league_id, "page": page})
        p_data = p_res.get("data")
        if not p_data or len(p_data) == 0:
            break
        
        for p in p_data:
            full_name = p.get("full_name") or p.get("known_as") or ""
            if not full_name:
                continue
            
            c_id = p.get("club_team_id")
            team_name = teams_map.get(c_id, "Unknown")
            pos = p.get("position") or "Unknown"
            apps = p.get("appearances_overall") or 0
            goals = p.get("goals_overall") or 0
            assists = p.get("assists_overall") or 0
            g90 = p.get("goals_per_90_overall") or 0.0
            a90 = p.get("assists_per_90_overall") or 0.0
            mins = p.get("minutes_played_overall") or 0
            yc = p.get("yellow_cards_overall") or 0
            rc = p.get("red_cards_overall") or 0
            age = p.get("age") or None
            nat = p.get("nationality") or None
            
            # Popola player_registry_2026
            cur.execute("""
                INSERT OR REPLACE INTO player_registry_2026 (
                    canonical_name, display_name, team_name, former_teams, role, number, source, last_verified
                ) VALUES (?, ?, ?, ?, ?, ?, 'FOOTYSTATS_2026', ?)
            """, (full_name, p.get("known_as"), team_name, None, pos, None, now_iso))
            
            # Popola tabella players generale
            if "full_name" in player_cols:
                cur.execute("""
                    DELETE FROM players WHERE full_name = ? AND season = ?
                """, (full_name, season_str))
                cur.execute("""
                    INSERT INTO players (
                        full_name, age, nationality, position, current_club, league, season,
                        minutes_played, appearances, goals, assists, goals_per_90, assists_per_90,
                        xg_per_game, shots_per_90, shots_on_target_per_game, key_passes_per_game,
                        yellow_cards, red_cards, cards_per_90, average_rating, rank_in_club_top_scorer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name, age, nat, pos, team_name, league_name, season_str,
                    mins, apps, goals, assists, g90, a90,
                    None, None, None, None,
                    yc, rc, None, None, p.get("rank_in_club_top_scorer")
                ))
            elif "player_id" in player_cols and "name" in player_cols:
                p_id = p.get("id") or hash(full_name) % 10000000
                cur.execute("""
                    INSERT OR REPLACE INTO players (
                        player_id, name, age, position, team_id, team_name, league_id, league_name, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p_id, full_name, age, pos, c_id, team_name, league_id, league_name, now_iso))
            total_players += 1
            
        page += 1
        time.sleep(0.05)

    conn.commit()
    print(f"  Giocatori inseriti/aggiornati in {league_name}: {total_players}")
    return {"teams": len(teams_map), "players": total_players}

def main():
    print("================================================================================")
    print("BAGENT — AGGIORNAMENTO GLOBALE ROSE 2026/2027 PER TUTTI I CAMPIONATI TIER 1")
    print("================================================================================")
    
    for db_path in [PRIMARY_DB, SECONDARY_DB]:
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
        print(f"\nTarget Database: {db_path.name}")
        conn = sqlite3.connect(db_path)
        ensure_tables(conn)
        
        summary = {}
        for lid, (lname, country, s_year) in TIER1_LEAGUES_2026.items():
            res = sync_league(conn, lid, lname, country, s_year)
            summary[lname] = res
            
        conn.close()
        
    print("\n================================================================================")
    print("REPORT FINALE DI SINCRONIZZAZIONE ROSE 2026/2027:")
    for l, d in summary.items():
        print(f"  - {l}: {d['teams']} squadre, {d['players']} giocatori certificati")
    print("================================================================================")

if __name__ == "__main__":
    main()
