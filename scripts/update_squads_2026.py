#!/usr/bin/env python3
"""
update_squads_2026.py — Aggiorna il database giocatori di BAgent con le rose 2026/2027 ufficiali.

Caratteristiche:
- Svuota i giocatori ceduti/trasferiti da ciascun club prima dell'inserimento della nuova rosa
- Supporta aggiornamento per ID squadra, per ID fixture, o per leghe intere
- Salva i dati in storage/database/bagent.db (e data/bagent.db)
"""

from __future__ import annotations
import sqlite3
import requests
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "storage" / "database" / "bagent.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Caricamento credenziali da .env
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

UCL_TODAY_FIXTURES = [1635628, 1635741, 1635705, 1635686, 1635698, 1635736]


def init_db(con: sqlite3.Connection):
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


def fetch_api(endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = f"https://{API_HOST}/{endpoint}"
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=12)
            if r.status_code == 200:
                data = r.json()
                errors = data.get("errors")
                if errors:
                    print(f"⚠️ Errore API su {endpoint} {params}: {errors}")
                    return []
                return data.get("response", [])
            elif r.status_code == 429:
                print("⏳ Rate limit raggiunto, attesa 3 secondi...")
                time.sleep(3)
            else:
                print(f"⚠️ Status HTTP {r.status_code} per {endpoint} {params}")
        except Exception as e:
            print(f"⚠️ Eccezione chiamata API ({attempt+1}/3): {e}")
            time.sleep(1)
    return []


def update_single_team_squad(con: sqlite3.Connection, team_id: int, team_name_fallback: str = "", league_id: int = 0, league_name: str = "") -> int:
    cur = con.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Recupera info team se non esistono o per aggiornamento
    cur.execute("SELECT name, country, league_id, league_name FROM teams WHERE team_id = ?", (team_id,))
    row = cur.fetchone()
    team_name = team_name_fallback
    country = ""

    if row and row[0]:
        team_name = row[0]
        country = row[1] or ""
        if not league_id and row[2]:
            league_id = row[2]
            league_name = row[3] or ""
    else:
        # Fetch team info da API
        team_res = fetch_api("teams", {"id": team_id})
        if team_res:
            t = team_res[0].get("team", {})
            team_name = t.get("name", team_name_fallback)
            code = t.get("code")
            country = t.get("country", "")
            founded = t.get("founded")
            logo = t.get("logo")
            cur.execute("""
            INSERT OR REPLACE INTO teams (team_id, name, code, country, founded, logo, league_id, league_name, season, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 2026, ?)
            """, (team_id, team_name, code, country, founded, logo, league_id, league_name, now_str))
            con.commit()

    # 2. Fetch rosa ufficiale
    squad_res = fetch_api("players/squads", {"team": team_id})
    if not squad_res:
        print(f"   ⚠️ Nessuna rosa restituita da API per team {team_id} ({team_name})")
        return 0

    squad_players = squad_res[0].get("players", [])
    if not squad_players:
        print(f"   ⚠️ Rosa vuota per team {team_id} ({team_name})")
        return 0

    # 3. PURGE: Rimuovi i giocatori attualmente associati a questo team_id
    # Fondamentale per eliminare chi è stato ceduto!
    cur.execute("DELETE FROM players WHERE team_id = ?", (team_id,))

    # 4. Inserimento nuova rosa
    saved_count = 0
    for p in squad_players:
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
        saved_count += 1

    con.commit()
    print(f"   ✅ {team_name} (ID {team_id}): {saved_count} giocatori inseriti/aggiornati.")
    return saved_count


def update_teams_from_fixtures(con: sqlite3.Connection, fixture_ids: List[int]):
    print(f"\n🏆 Aggiornamento rose da {len(fixture_ids)} fixture...")
    seen_teams: Dict[int, str] = {}
    for fid in fixture_ids:
        res = fetch_api("fixtures", {"id": fid})
        if not res:
            continue
        f = res[0]
        home = f.get("teams", {}).get("home", {})
        away = f.get("teams", {}).get("away", {})
        league = f.get("league", {})
        l_id = league.get("id", 0)
        l_name = league.get("name", "")

        for t in [home, away]:
            tid = t.get("id")
            tname = t.get("name", "")
            if tid and tid not in seen_teams:
                seen_teams[tid] = tname
                update_single_team_squad(con, tid, team_name_fallback=tname, league_id=l_id, league_name=l_name)
                time.sleep(0.15)


def update_league(con: sqlite3.Connection, league_id: int, league_name: str, season: int = 2026):
    print(f"\n🌍 Scaricamento squadre per Lega {league_id} ({league_name}, season {season})...")
    teams_res = fetch_api("teams", {"league": league_id, "season": season})
    print(f"   Trovate {len(teams_res)} squadre.")
    for item in teams_res:
        t = item.get("team", {})
        tid = t.get("id")
        tname = t.get("name")
        if tid:
            update_single_team_squad(con, tid, team_name_fallback=tname, league_id=league_id, league_name=league_name)
            time.sleep(0.12)


def main():
    parser = argparse.ArgumentParser(description="Aggiorna il database giocatori di BAgent")
    parser.add_argument("--today-ucl", action="store_true", help="Aggiorna tutte le 12 squadre di Champions League di oggi")
    parser.add_argument("--teams", nargs="+", type=int, help="Elenco ID squadre da aggiornare")
    parser.add_argument("--fixtures", nargs="+", type=int, help="Elenco ID fixtures da cui estrarre e aggiornare squadre")
    parser.add_argument("--boca", action="store_true", help="Aggiorna Boca Juniors e le big argentine")
    parser.add_argument("--league", type=int, help="ID della lega da aggiornare completamente")
    args = parser.parse_args()

    con = sqlite3.connect(DB_PATH)
    init_db(con)

    print(f"=== Avvio Aggiornamento Rose Database BAgent ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    print(f"📁 Percorso DB: {DB_PATH}")

    if args.today_ucl:
        update_teams_from_fixtures(con, UCL_TODAY_FIXTURES)

    if args.fixtures:
        update_teams_from_fixtures(con, args.fixtures)

    if args.teams:
        for tid in args.teams:
            update_single_team_squad(con, tid)
            time.sleep(0.15)

    if args.boca:
        print("\n🇦🇷 Aggiornamento Boca Juniors (ID 451) e River Plate (ID 435)...")
        update_single_team_squad(con, 451, "Boca Juniors", league_id=128, league_name="Liga Profesional Argentina")
        update_single_team_squad(con, 435, "River Plate", league_id=128, league_name="Liga Profesional Argentina")

    if args.league:
        update_league(con, args.league, f"League_{args.league}")

    # Statistiche finali
    cur = con.cursor()
    cur.execute("SELECT COUNT(DISTINCT team_id), COUNT(*) FROM players;")
    t_cnt, p_cnt = cur.fetchone()
    print("\n" + "="*65)
    print(f"✅ AGGIORNAMENTO COMPLETATO!")
    print(f"📊 Squadre censite: {t_cnt}")
    print(f"👤 Giocatori totali registrati nel DB: {p_cnt}")
    print("="*65 + "\n")
    con.close()


if __name__ == "__main__":
    main()
