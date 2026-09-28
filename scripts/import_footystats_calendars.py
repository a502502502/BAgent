"""Scarica i calendari FootyStats delle prime divisioni e li scrive in matches."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
import sys

sys.path.insert(0, str(ROOT))

from services.database.schema import get_db  # noqa: E402

# name, country, FootyStats season_id della stagione corrente
TARGETS = [
    ("Serie A", "Italy", 17084),
    ("Premier League", "England", 17146),
    ("La Liga", "Spain", 17199),
    ("Bundesliga", "Germany", 17210),
    ("Ligue 1", "France", 17102),
    ("Primeira Liga", "Portugal", 17217),
    ("Eredivisie", "Netherlands", 17097),
    ("Scottish Premiership", "Scotland", 17148),
    ("Jupiler Pro League", "Belgium", 17171),
    ("Superliga DEN", "Denmark", 17091),
    ("Eliteserien", "Norway", 16558),
    ("Allsvenskan", "Sweden", 16576),
    ("Super League Greece", "Greece", 17356),
    ("Super Lig", "Turkey", 17265),
    ("Swiss Super League", "Switzerland", 17129),
    ("Brazil Serie A", "Brazil", 16544),
    ("Primera Division ARG", "Argentina", 16571),
    ("Champions League", "Europe", 17128),
    ("Europa League", "Europe", 17127),
    ("Conference League", "Europe", 17130),
]

COLUMNS = [
    "league", "season", "date_gmt", "timestamp", "status",
    "home_team", "away_team",
    "home_goals", "away_goals", "home_goals_ht", "away_goals_ht", "total_goals",
    "home_corners", "away_corners",
    "home_shots", "away_shots",
    "home_shots_on_target", "away_shots_on_target",
    "home_xg", "away_xg",
    "home_possession", "away_possession",
    "home_yellow_cards", "away_yellow_cards",
    "home_red_cards", "away_red_cards",
    "attendance",
    "odds_home_win", "odds_draw", "odds_away_win",
    "odds_over25", "odds_btts_yes", "odds_btts_no",
    "btts_pct_pre_match", "over25_pct_pre_match",
    "home_ppg_pre_match", "away_ppg_pre_match",
]


def _load_key() -> str:
    key = os.environ.get("FOOTYSTATS_API_KEY", "")
    if key:
        return key
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("FOOTYSTATS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("FOOTYSTATS_API_KEY mancante")


def _num(value, *, allow_zero: bool = True):
    if value is None or value == "" or value == -1:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not allow_zero and number <= 0:
        return None
    return number


def _as_int(value):
    number = _num(value)
    return None if number is None else int(number)


def fetch_matches(key: str, season_id: int) -> list[dict]:
    rows: list[dict] = []
    page = 1
    session = requests.Session()
    session.headers["Expect"] = ""
    while True:
        response = None
        for attempt in range(4):
            response = session.get(
                "https://api.football-data-api.com/league-matches",
                params={"key": key, "league_id": season_id, "page": page},
                timeout=40,
            )
            if response.status_code not in (417, 429, 500, 502, 503):
                break
            time.sleep(2 + attempt * 2)
        if response is None or response.status_code >= 400:
            code = response.status_code if response is not None else "nessuna risposta"
            raise RuntimeError(f"FootyStats league_id={season_id} pagina {page}: HTTP {code}")
        body = response.json()
        rows.extend(body.get("data") or [])
        pager = body.get("pager") or {}
        if page >= int(pager.get("max_page") or 1):
            return rows
        page += 1
        time.sleep(0.4)


def main() -> None:
    key = _load_key()
    conn = get_db()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    placeholders = ",".join("?" for _ in COLUMNS)
    updates = ", ".join(f"{col}=excluded.{col}" for col in COLUMNS if col not in {
        "league", "season", "home_team", "away_team", "date_gmt",
    })
    sql = f"""
        INSERT INTO matches ({", ".join(COLUMNS)})
        VALUES ({placeholders})
        ON CONFLICT(league, season, home_team, away_team, date_gmt) DO UPDATE SET
            {updates}
    """
    wanted = {arg.casefold() for arg in sys.argv[1:]}
    targets = [
        row for row in TARGETS
        if not wanted or row[0].casefold() in wanted
    ]
    print(f"{'Lega':<24} {'Stagione':<12} {'N':>5} {'FT':>5} {'NS':>5} {'Prima':<12} {'Ultima'}")
    saved = 0
    for name, country, season_id in targets:
        raw = fetch_matches(key, season_id)
        time.sleep(0.6)
        seasons: set[str] = set()
        dates: list[str] = []
        played = upcoming = 0
        for match in raw:
            home = (match.get("home_name") or "").strip()
            away = (match.get("away_name") or "").strip()
            timestamp = match.get("date_unix")
            if not home or not away or not timestamp:
                continue
            kickoff = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            date_gmt = kickoff.strftime("%Y-%m-%d")
            season = str(match.get("season") or "")
            status_raw = (match.get("status") or "").lower()
            finished = status_raw == "complete"
            if finished:
                status = "FT"
                played += 1
                goals = (
                    _as_int(match.get("homeGoalCount")),
                    _as_int(match.get("awayGoalCount")),
                    _as_int(match.get("ht_goals_team_a")),
                    _as_int(match.get("ht_goals_team_b")),
                    _as_int(match.get("totalGoalCount")),
                )
            else:
                status = "NS" if status_raw == "incomplete" else (status_raw.upper() or "NS")
                upcoming += 1
                goals = (None, None, None, None, None)
            seasons.add(season)
            dates.append(date_gmt)
            row = {
                "league": name,
                "season": season,
                "date_gmt": date_gmt,
                "timestamp": int(timestamp),
                "status": status,
                "home_team": home,
                "away_team": away,
                "home_goals": goals[0],
                "away_goals": goals[1],
                "home_goals_ht": goals[2],
                "away_goals_ht": goals[3],
                "total_goals": goals[4],
                "home_corners": _as_int(match.get("team_a_corners")),
                "away_corners": _as_int(match.get("team_b_corners")),
                "home_shots": _as_int(match.get("team_a_shots")),
                "away_shots": _as_int(match.get("team_b_shots")),
                "home_shots_on_target": _as_int(match.get("team_a_shotsOnTarget")),
                "away_shots_on_target": _as_int(match.get("team_b_shotsOnTarget")),
                "home_xg": _num(match.get("team_a_xg")),
                "away_xg": _num(match.get("team_b_xg")),
                "home_possession": _num(match.get("team_a_possession")),
                "away_possession": _num(match.get("team_b_possession")),
                "home_yellow_cards": _as_int(match.get("team_a_yellow_cards")),
                "away_yellow_cards": _as_int(match.get("team_b_yellow_cards")),
                "home_red_cards": _as_int(match.get("team_a_red_cards")),
                "away_red_cards": _as_int(match.get("team_b_red_cards")),
                "attendance": _as_int(match.get("attendance")),
                "odds_home_win": _num(match.get("odds_ft_1"), allow_zero=False),
                "odds_draw": _num(match.get("odds_ft_x"), allow_zero=False),
                "odds_away_win": _num(match.get("odds_ft_2"), allow_zero=False),
                "odds_over25": _num(match.get("odds_ft_over25"), allow_zero=False),
                "odds_btts_yes": _num(match.get("odds_btts_yes"), allow_zero=False),
                "odds_btts_no": _num(match.get("odds_btts_no"), allow_zero=False),
                "btts_pct_pre_match": _num(match.get("btts_potential")),
                "over25_pct_pre_match": _num(match.get("o25_potential")),
                "home_ppg_pre_match": _num(match.get("pre_match_home_ppg")),
                "away_ppg_pre_match": _num(match.get("pre_match_away_ppg")),
            }
            conn.execute(sql, tuple(row[col] for col in COLUMNS))
            saved += 1
        for season in seasons:
            done = conn.execute(
                "SELECT COUNT(*) FROM matches WHERE league=? AND season=? AND status='FT'",
                (name, season),
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO leagues (name, season, country, matches_completed)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name, season) DO UPDATE SET
                    country = excluded.country,
                    matches_completed = excluded.matches_completed
                """,
                (name, season, country, done),
            )
        conn.commit()
        season_label = ",".join(sorted(seasons)) or "-"
        first = min(dates) if dates else "-"
        last = max(dates) if dates else "-"
        print(f"{name:<24} {season_label:<12} {len(dates):>5} {played:>5} {upcoming:>5} {first:<12} {last}")
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    total = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    print(f"Salvate {saved} partite. Tabella matches: {total}.")
    conn.close()


if __name__ == "__main__":
    main()
