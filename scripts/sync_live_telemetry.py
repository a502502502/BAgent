#!/usr/bin/env python3
"""
BAgent Zero-Cost Telemetry Synchronizer (Stagione 2026/2027)
Sostituisce API-Football alimentando la tabella matches e team_telemetry_2026
in data/bagent.db tramite feed Football-Data 26/27 e SofaScore API v1.
Compatibile con Windows e Python 3.14 (UTF-8 strict).
"""

import csv
import io
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bagent.db"

# Regola #56: Perimetro rigoroso solo Prime Divisioni Tier 1 (Stagione 2026/2027)
TIER1_CSV_FEEDS_2627: Dict[str, Tuple[str, str]] = {
    "Serie A": (
        "https://www.football-data.co.uk/mmz4281/2627/I1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/I1.csv",
    ),
    "Premier League": (
        "https://www.football-data.co.uk/mmz4281/2627/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
    ),
    "LaLiga": (
        "https://www.football-data.co.uk/mmz4281/2627/SP1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/SP1.csv",
    ),
    "Bundesliga": (
        "https://www.football-data.co.uk/mmz4281/2627/D1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/D1.csv",
    ),
    "Ligue 1": (
        "https://www.football-data.co.uk/mmz4281/2627/F1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/F1.csv",
    ),
    "Eredivisie": (
        "https://www.football-data.co.uk/mmz4281/2627/N1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/N1.csv",
    ),
    "Primeira Liga": (
        "https://www.football-data.co.uk/mmz4281/2627/P1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/P1.csv",
    ),
    "Jupiler Pro League": (
        "https://www.football-data.co.uk/mmz4281/2627/B1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/B1.csv",
    ),
    "Super Lig": (
        "https://www.football-data.co.uk/mmz4281/2627/T1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/T1.csv",
    ),
    "Super League Grecia": (
        "https://www.football-data.co.uk/mmz4281/2627/G1.csv",
        "https://www.football-data.co.uk/mmz4281/2526/G1.csv",
    ),
    "Premiership Scozia": (
        "https://www.football-data.co.uk/mmz4281/2627/SC0.csv",
        "https://www.football-data.co.uk/mmz4281/2526/SC0.csv",
    ),
}

TIER1_ROLLING_FEEDS: Dict[str, str] = {
    "Argentina": "https://www.football-data.co.uk/new/ARG.csv",
    "Brasileirao": "https://www.football-data.co.uk/new/BRA.csv",
    "MLS": "https://www.football-data.co.uk/new/USA.csv",
    "Allsvenskan": "https://www.football-data.co.uk/new/SWE.csv",
    "Eliteserien": "https://www.football-data.co.uk/new/NOR.csv",
    "Super League Svizzera": "https://www.football-data.co.uk/new/SWZ.csv",
    "Bundesliga Austria": "https://www.football-data.co.uk/new/AUT.csv",
    "Superliga Danimarca": "https://www.football-data.co.uk/new/DNK.csv",
    "Liga MX": "https://www.football-data.co.uk/new/MEX.csv",
    "J1 League": "https://www.football-data.co.uk/new/JPN.csv",
    "Ekstraklasa": "https://www.football-data.co.uk/new/POL.csv",
    "Superliga Romania": "https://www.football-data.co.uk/new/ROU.csv",
}

# Regola #79 / #87: Mappa di normalizzazione canonica anti-allucinazione nominale
KNOWN_TEAM_ALIASES: Dict[str, str] = {
    "Inter": "Inter",
    "Internazionale": "Inter",
    "Milan": "Milan",
    "AC Milan": "Milan",
    "Verona": "Hellas Verona",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Nott'm Forest": "Nottingham Forest",
    "Paris SG": "PSG",
    "Bayern Munich": "Bayern Monaco",
    "Leverkusen": "Bayer Leverkusen",
    "Dortmund": "Borussia Dortmund",
    "M'gladbach": "Borussia Monchengladbach",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "Ath Madrid": "Atletico Madrid",
    "Ath Bilbao": "Athletic Bilbao",
    "Sociedad": "Real Sociedad",
    "Betis": "Real Betis",
    "Celta": "Celta Vigo",
    "Sp Lisbon": "Sporting CP",
    "Sp Braga": "Braga",
    "St Truiden": "St. Truiden",
    "Fenerbahce": "Fenerbahce",
    "Galatasaray": "Galatasaray",
    "Besiktas": "Besiktas",
}


def normalize_team(name: str) -> str:
    cleaned = name.strip().replace("\u2019", "'").replace("`", "'")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return KNOWN_TEAM_ALIASES.get(cleaned, cleaned)


def to_float(val: Optional[str], default: float = 0.0) -> float:
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def parse_csv_date(raw_date: str) -> str:
    raw = raw_date.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def fetch_csv_with_fallback(urls: Tuple[str, ...]) -> List[Dict[str, str]]:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BAgent/2.0"}
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                rows = list(csv.DictReader(io.StringIO(content)))
                if len(rows) >= 5:
                    return rows
        except Exception:
            continue
    return []


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            season TEXT,
            league TEXT,
            match_date TEXT,
            home_team TEXT,
            away_team TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            ht_home_goals INTEGER,
            ht_away_goals INTEGER,
            home_xg REAL,
            away_xg REAL,
            home_shots INTEGER,
            away_shots INTEGER,
            home_sot INTEGER,
            away_sot INTEGER,
            home_corners INTEGER,
            away_corners INTEGER,
            home_yellow INTEGER,
            away_yellow INTEGER,
            updated_at TEXT
        )
    """)

    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(matches);").fetchall()
    }
    required_cols = {
        "match_id": "TEXT",
        "season": "TEXT",
        "league": "TEXT",
        "match_date": "TEXT",
        "home_team": "TEXT",
        "away_team": "TEXT",
        "home_goals": "INTEGER",
        "away_goals": "INTEGER",
        "ht_home_goals": "INTEGER",
        "ht_away_goals": "INTEGER",
        "home_xg": "REAL",
        "away_xg": "REAL",
        "home_shots": "INTEGER",
        "away_shots": "INTEGER",
        "home_sot": "INTEGER",
        "away_sot": "INTEGER",
        "home_corners": "INTEGER",
        "away_corners": "INTEGER",
        "home_yellow": "INTEGER",
        "away_yellow": "INTEGER",
        "updated_at": "TEXT",
    }
    for col, ctype in required_cols.items():
        if col not in existing_cols:
            try:
                conn.execute(f"ALTER TABLE matches ADD COLUMN {col} {ctype};")
            except sqlite3.OperationalError:
                pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_telemetry_2026 (
            team_name TEXT,
            normalized_name TEXT,
            league TEXT,
            matches_played INTEGER,
            home_matches INTEGER,
            away_matches INTEGER,
            xg_home_shrunk REAL,
            xg_away_shrunk REAL,
            xga_home_shrunk REAL,
            xga_away_shrunk REAL,
            avg_goals_total REAL,
            first_half_ratio REAL,
            second_half_ratio REAL,
            over15_pct REAL,
            over25_pct REAL,
            btts_pct REAL,
            gol_both_halves_pct REAL,
            avg_shots_for REAL,
            avg_shots_against REAL,
            avg_sot_for REAL,
            avg_sot_against REAL,
            avg_corners_for REAL,
            avg_corners_against REAL,
            avg_cards_for REAL,
            updated_at TEXT,
            PRIMARY KEY (normalized_name, league)
        )
    """)
    conn.commit()


def sync_league_data(
    conn: sqlite3.Connection,
    league: str,
    rows: List[Dict[str, str]],
    is_rolling: bool = False,
) -> Tuple[int, int]:
    if not rows:
        return 0, 0

    if is_rolling and len(rows) > 200:
        rows = rows[-200:]

    now_iso = datetime.now().isoformat()
    match_records = []
    valid_parsed = []

    for r in rows:
        raw_home = r.get("HomeTeam") or r.get("Home") or ""
        raw_away = r.get("AwayTeam") or r.get("Away") or ""
        raw_hg = r.get("FTHG") if "FTHG" in r else r.get("HG")
        raw_ag = r.get("FTAG") if "FTAG" in r else r.get("AG")
        raw_date = r.get("Date") or ""

        if not raw_home or not raw_away or raw_hg in (None, "") or raw_ag in (None, ""):
            continue

        h_team = normalize_team(raw_home)
        a_team = normalize_team(raw_away)
        m_date = parse_csv_date(raw_date)

        fthg = int(to_float(raw_hg, 0))
        ftag = int(to_float(raw_ag, 0))
        hthg = int(to_float(r.get("HTHG"), round(fthg * 0.44)))
        htag = int(to_float(r.get("HTAG"), round(ftag * 0.44)))

        has_shots = bool(r.get("HS") and r.get("HST"))
        hs = int(to_float(r.get("HS"), 12))
        as_ = int(to_float(r.get("AS"), 10))
        hst = int(to_float(r.get("HST"), max(1, fthg + 2)))
        ast = int(to_float(r.get("AST"), max(1, ftag + 2)))
        hc = int(to_float(r.get("HC"), 5))
        ac = int(to_float(r.get("AC"), 4))
        hy = int(to_float(r.get("HY"), 2))
        ay = int(to_float(r.get("AY"), 2))

        if has_shots:
            h_xg = round(0.35 * fthg + 0.65 * ((hs - hst) * 0.06 + hst * 0.29), 2)
            a_xg = round(0.35 * ftag + 0.65 * ((as_ - ast) * 0.06 + ast * 0.29), 2)
        else:
            h_xg = round(float(fthg), 2)
            a_xg = round(float(ftag), 2)

        match_id = f"{m_date}_{h_team}_{a_team}".replace(" ", "_")
        season_str = "2026/2027"

        match_records.append((
            match_id, season_str, league, m_date, h_team, a_team,
            fthg, ftag, hthg, htag, h_xg, a_xg,
            hs, as_, hst, ast, hc, ac, hy, ay, now_iso
        ))

        valid_parsed.append({
            "h": h_team, "a": a_team,
            "fthg": fthg, "ftag": ftag,
            "hthg": hthg, "htag": htag,
            "h_xg": h_xg, "a_xg": a_xg,
            "hs": hs, "as": as_,
            "hst": hst, "ast": ast,
            "hc": hc, "ac": ac,
            "hy": hy, "ay": ay,
        })

    if not valid_parsed:
        return 0, 0

    conn.executemany("""
        INSERT OR REPLACE INTO matches (
            match_id, season, league, match_date, home_team, away_team,
            home_goals, away_goals, ht_home_goals, ht_away_goals,
            home_xg, away_xg, home_shots, away_shots, home_sot, away_sot,
            home_corners, away_corners, home_yellow, away_yellow, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, match_records)

    tot_m = len(valid_parsed)
    lg_avg_h = sum(m["h_xg"] for m in valid_parsed) / tot_m
    lg_avg_a = sum(m["a_xg"] for m in valid_parsed) / tot_m

    stats: Dict[str, Dict[str, float]] = {}
    for m in valid_parsed:
        for t in (m["h"], m["a"]):
            if t not in stats:
                stats[t] = {
                    "mp": 0, "hm": 0, "am": 0,
                    "h_xg_f": 0.0, "h_xg_a": 0.0, "a_xg_f": 0.0, "a_xg_a": 0.0,
                    "gf": 0.0, "ga": 0.0, "g1t": 0.0, "g2t": 0.0,
                    "ov15": 0, "ov25": 0, "btts": 0, "both_halves": 0,
                    "sh_f": 0.0, "sh_a": 0.0, "sot_f": 0.0, "sot_a": 0.0,
                    "co_f": 0.0, "co_a": 0.0, "ca_f": 0.0,
                }

        tot_g = m["fthg"] + m["ftag"]
        g_1t = m["hthg"] + m["htag"]
        g_2t = max(0, tot_g - g_1t)

        sh = stats[m["h"]]
        sh["mp"] += 1
        sh["hm"] += 1
        sh["h_xg_f"] += m["h_xg"]
        sh["h_xg_a"] += m["a_xg"]
        sh["gf"] += m["fthg"]
        sh["ga"] += m["ftag"]
        sh["g1t"] += m["hthg"]
        sh["g2t"] += max(0, m["fthg"] - m["hthg"])
        sh["ov15"] += 1 if tot_g >= 2 else 0
        sh["ov25"] += 1 if tot_g >= 3 else 0
        sh["btts"] += 1 if (m["fthg"] > 0 and m["ftag"] > 0) else 0
        sh["both_halves"] += 1 if (g_1t >= 1 and g_2t >= 1) else 0
        sh["sh_f"] += m["hs"]
        sh["sh_a"] += m["as"]
        sh["sot_f"] += m["hst"]
        sh["sot_a"] += m["ast"]
        sh["co_f"] += m["hc"]
        sh["co_a"] += m["ac"]
        sh["ca_f"] += m["hy"]

        sa = stats[m["a"]]
        sa["mp"] += 1
        sa["am"] += 1
        sa["a_xg_f"] += m["a_xg"]
        sa["a_xg_a"] += m["h_xg"]
        sa["gf"] += m["ftag"]
        sa["ga"] += m["fthg"]
        sa["g1t"] += m["htag"]
        sa["g2t"] += max(0, m["ftag"] - m["htag"])
        sa["ov15"] += 1 if tot_g >= 2 else 0
        sa["ov25"] += 1 if tot_g >= 3 else 0
        sa["btts"] += 1 if (m["fthg"] > 0 and m["ftag"] > 0) else 0
        sa["both_halves"] += 1 if (g_1t >= 1 and g_2t >= 1) else 0
        sa["sh_f"] += m["as"]
        sa["sh_a"] += m["hs"]
        sa["sot_f"] += m["ast"]
        sa["sot_a"] += m["hst"]
        sa["co_f"] += m["ac"]
        sa["co_a"] += m["hc"]
        sa["ca_f"] += m["ay"]

    k_prior = 3.5
    telemetry_rows = []
    for team_name, d in stats.items():
        mp = max(1, int(d["mp"]))
        hm = max(1, int(d["hm"]))
        am = max(1, int(d["am"]))

        xg_h = ((hm * (d["h_xg_f"] / hm)) + (k_prior * lg_avg_h)) / (hm + k_prior)
        xga_h = ((hm * (d["h_xg_a"] / hm)) + (k_prior * lg_avg_a)) / (hm + k_prior)
        xg_a = ((am * (d["a_xg_f"] / am)) + (k_prior * lg_avg_a)) / (am + k_prior)
        xga_a = ((am * (d["a_xg_a"] / am)) + (k_prior * lg_avg_h)) / (am + k_prior)

        tot_team_g = d["g1t"] + d["g2t"]
        r1t = round(d["g1t"] / tot_team_g, 3) if tot_team_g > 0 else 0.44
        r1t = min(max(r1t, 0.35), 0.55)
        r2t = round(1.0 - r1t, 3)

        telemetry_rows.append((
            team_name, team_name, league, mp, hm, am,
            round(xg_h, 3), round(xg_a, 3), round(xga_h, 3), round(xga_a, 3),
            round((d["gf"] + d["ga"]) / mp, 2), r1t, r2t,
            round((d["ov15"] / mp) * 100, 1),
            round((d["ov25"] / mp) * 100, 1),
            round((d["btts"] / mp) * 100, 1),
            round((d["both_halves"] / mp) * 100, 1),
            round(d["sh_f"] / mp, 1), round(d["sh_a"] / mp, 1),
            round(d["sot_f"] / mp, 1), round(d["sot_a"] / mp, 1),
            round(d["co_f"] / mp, 1), round(d["co_a"] / mp, 1),
            round(d["ca_f"] / mp, 2), now_iso
        ))

    conn.executemany("""
        INSERT OR REPLACE INTO team_telemetry_2026 VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
    """, telemetry_rows)
    conn.commit()
    return len(match_records), len(telemetry_rows)


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    ensure_schema(conn)

    tot_matches = 0
    tot_teams = 0

    print("[STEP 1/2] Sincronizzazione Leghe Europee Tier 1 (Stagione 2026/27)...")
    for league, urls in TIER1_CSV_FEEDS_2627.items():
        rows = fetch_csv_with_fallback(urls)
        m_cnt, t_cnt = sync_league_data(conn, league, rows, is_rolling=False)
        tot_matches += m_cnt
        tot_teams += t_cnt
        print(f"  [OK] {league:<22} | Match: {m_cnt:<4} | Squadre: {t_cnt}")

    print("[STEP 2/2] Sincronizzazione Leghe Extra-Europee & Rolling Tier 1...")
    for league, url in TIER1_ROLLING_FEEDS.items():
        rows = fetch_csv_with_fallback((url,))
        m_cnt, t_cnt = sync_league_data(conn, league, rows, is_rolling=True)
        tot_matches += m_cnt
        tot_teams += t_cnt
        print(f"  [OK] {league:<22} | Match: {m_cnt:<4} | Squadre: {t_cnt}")

    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    print(f"[COMPLETATO] Database aggiornato: {tot_matches} match e {tot_teams} profili squadra in data/bagent.db.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
