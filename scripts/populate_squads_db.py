#!/usr/bin/env python3
"""
populate_squads_db.py — Popola il Database di BAgent con tutti i giocatori
di tutte le squadre di Premier League, Serie A e Bundesliga (e LaLiga/Ligue 1).
"""

from __future__ import annotations
import sqlite3
import requests
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Path setup
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "storage" / "database" / "bagent.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Carica .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_HOST = "v3.football.api-sports.io"

HEADERS = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key": API_KEY,
    "x-apisports-key": API_KEY,
}

LEAGUES = {
    39: ("Premier League", "England", 2026),
    135: ("Serie A", "Italy", 2026),
    78: ("Bundesliga", "Germany", 2026),
    140: ("La Liga", "Spain", 2026),
    61: ("Ligue 1", "France", 2026),
}

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        team_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT,
        country TEXT,
        founded INTEGER,
        logo TEXT,
        league_id INTEGER,
        league_name TEXT,
        season INTEGER,
        last_updated TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER,
        name TEXT NOT NULL,
        age INTEGER,
        number INTEGER,
        position TEXT,
        photo TEXT,
        team_id INTEGER,
        team_name TEXT,
        league_id INTEGER,
        league_name TEXT,
        last_updated TEXT,
        PRIMARY KEY (player_id, team_id),
        FOREIGN KEY (team_id) REFERENCES teams(team_id)
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_player_name ON players(name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_player_team ON players(team_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_player_league ON players(league_id);")
    
    con.commit()
    con.close()

def fetch_teams_for_league(league_id: int, season: int) -> List[Dict[str, Any]]:
    url = f"https://{API_HOST}/teams?league={league_id}&season={season}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json().get("response", [])
        else:
            print(f"Errore {r.status_code} per lega {league_id}: {r.text[:80]}")
    except Exception as e:
        print(f"Exception per lega {league_id}:", e)
    return []

def fetch_squad_for_team(team_id: int) -> List[Dict[str, Any]]:
    url = f"https://{API_HOST}/players/squads?team={team_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            res = r.json().get("response", [])
            if res:
                return res[0].get("players", [])
        else:
            print(f"Errore {r.status_code} per team {team_id}: {r.text[:80]}")
    except Exception as e:
        print(f"Exception per team {team_id}:", e)
    return []

def main():
    print(f"=== Avvio Popolamento Rose Database BAgent ({datetime.now().strftime('%H:%M:%S')}) ===")
    init_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    total_teams_saved = 0
    total_players_saved = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for league_id, (league_name, country, season) in LEAGUES.items():
        print(f"\n🏆 Scaricamento squadre per {league_name} ({country}, Stagione {season})...")
        teams_data = fetch_teams_for_league(league_id, season)
        print(f"   Trovate {len(teams_data)} squadre.")

        for item in teams_data:
            t = item.get("team", {})
            team_id = t.get("id")
            team_name = t.get("name")
            code = t.get("code")
            founded = t.get("founded")
            logo = t.get("logo")

            cur.execute("""
            INSERT OR REPLACE INTO teams (team_id, name, code, country, founded, logo, league_id, league_name, season, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (team_id, team_name, code, country, founded, logo, league_id, league_name, season, now_str))
            con.commit()
            total_teams_saved += 1

            # Scarica la rosa completa
            players = fetch_squad_for_team(team_id)
            for p in players:
                p_id = p.get("id")
                p_name = p.get("name")
                p_age = p.get("age")
                p_num = p.get("number")
                p_pos = p.get("position")
                p_photo = p.get("photo")

                cur.execute("""
                INSERT OR REPLACE INTO players (player_id, name, age, number, position, photo, team_id, team_name, league_id, league_name, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p_id, p_name, p_age, p_num, p_pos, p_photo, team_id, team_name, league_id, league_name, now_str))
                total_players_saved += 1

            print(f"   • {team_name} (ID: {team_id}): salvati {len(players)} giocatori.")
            time.sleep(0.1) # Micro-pausa per rispettare il rate-limit

        con.commit()

    print(f"\n=======================================================")
    print(f"✅ POPOLAMENTO COMPLETATO CON SUCCESSO!")
    print(f"📊 Totale Squadre nel DB: {total_teams_saved}")
    print(f"👤 Totale Giocatori nel DB: {total_players_saved}")
    print(f"📁 Database: {DB_PATH}")
    print(f"=======================================================")
    con.close()

if __name__ == "__main__":
    main()
