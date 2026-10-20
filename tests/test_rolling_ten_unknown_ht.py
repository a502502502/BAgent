"""I tempi sconosciuti non vanno trattati come 0-0, e il profilo squadra preferisce il nome esatto."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from services.analysis.rolling_ten_engine import RollingTenEngine, summarize_team_flow


def _matches_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE matches (
            id INTEGER PRIMARY KEY,
            league TEXT,
            match_date TEXT,
            date_gmt TEXT,
            home_team TEXT,
            away_team TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            ht_home_goals INTEGER,
            ht_away_goals INTEGER,
            home_goals_ht INTEGER,
            away_goals_ht INTEGER,
            home_corners INTEGER,
            away_corners INTEGER,
            home_shots INTEGER,
            away_shots INTEGER,
            home_sot INTEGER,
            away_sot INTEGER,
            home_shots_on_target INTEGER,
            away_shots_on_target INTEGER,
            home_yellow INTEGER,
            away_yellow INTEGER,
            home_yellow_cards INTEGER,
            away_yellow_cards INTEGER,
            home_red_cards INTEGER,
            away_red_cards INTEGER
        )
        """
    )


def test_unknown_halftime_does_not_inflate_second_half(tmp_path: Path):
    db_path = tmp_path / "rolling.db"
    conn = sqlite3.connect(db_path)
    _matches_schema(conn)
    for i in range(5):
        conn.execute(
            """
            INSERT INTO matches (
                league, match_date, home_team, away_team, home_goals, away_goals
            ) VALUES ('Serie A', ?, 'Alpha', 'Beta', 2, 0)
            """,
            (f"2026-10-{10 + i:02d}",),
        )
    for i in range(5):
        conn.execute(
            """
            INSERT INTO matches (
                league, match_date, home_team, away_team,
                home_goals, away_goals, ht_home_goals, ht_away_goals
            ) VALUES ('Serie A', ?, 'Gamma', 'Delta', 2, 0, 0, 0)
            """,
            (f"2026-09-{10 + i:02d}",),
        )
    conn.commit()
    conn.close()

    engine = RollingTenEngine(db_path=db_path)
    assert engine.compute_all_teams_rolling_ten(min_matches=5) >= 2

    unknown = engine.get_team_profile("Alpha")
    known = engine.get_team_profile("Gamma")
    assert unknown is not None and known is not None
    assert unknown["hr_over_05_sh_match"] == 0.0
    assert unknown["avg_goals_sh"] == 0.0
    assert unknown["hr_btts"] == 0.0
    assert unknown["hr_home_unbeaten"] == 100.0
    assert unknown["cards_sample"] == 0
    assert known["hr_over_05_sh_match"] == 100.0
    assert known["hr_over_15_match"] == 100.0


def test_summarize_skips_unknown_cards_and_counts_home_results():
    rows = [
        {"home_team": "Alpha", "away_team": "Beta", "home_goals": 2, "away_goals": 0, "hy": 3, "ay": 1, "hr": 0, "ar": 0},
        {"home_team": "Alpha", "away_team": "Beta", "home_goals": 1, "away_goals": 1, "hy": 1, "ay": 2, "hr": None, "ar": None},
        {"home_team": "Beta", "away_team": "Alpha", "home_goals": 0, "away_goals": 1, "hy": None, "ay": None, "hr": None, "ar": None},
        {"home_team": "Alpha", "away_team": "Beta", "home_goals": 0, "away_goals": 2, "hy": 2, "ay": 0, "hr": 1, "ar": 0},
    ]
    flow = summarize_team_flow(rows, "Alpha")
    assert flow["matches"] == 4
    assert flow["unbeaten_hr"] == 75.0
    assert flow["btts_hr"] == 25.0
    assert flow["dc_and_ov15_hr"] == 50.0
    assert flow["home_n"] == 3
    assert flow["home_unbeaten_hr"] == 66.7
    assert flow["home_dc_and_ov15_hr"] == 66.7
    assert flow["cards_n"] == 3
    assert flow["avg_team_cards"] == 2.33
    assert flow["team_cards_ov15_hr"] == 66.7


def test_team_profile_prefers_exact_name(tmp_path: Path):
    db_path = tmp_path / "profiles.db"
    engine = RollingTenEngine(db_path=db_path)
    conn = sqlite3.connect(db_path)
    zeros = ", ".join("0" for _ in range(28))
    conn.execute(
        f"""
        INSERT INTO team_rolling_ten_telemetry (
            team_name, league, matches_count,
            avg_goals_scored, avg_goals_conceded, avg_total_goals,
            avg_shots_for, avg_shots_against, avg_sot_for, avg_sot_against,
            avg_corners_for, avg_corners_against, avg_saves_gk, avg_cards_match,
            hr_multigol_1_3_team, hr_multigol_1_5_match, hr_multigol_2_5_match,
            hr_chance_mix_dc_ov15, hr_chance_mix_x_gg, hr_over_15_match, hr_under_35_match,
            hr_both_halves_over_05, hr_mg_ht_02_sh_13,
            hr_over_95_shots_team, hr_over_115_shots_team, hr_over_125_shots_team,
            hr_over_35_sot_team, hr_over_35_corners_team, hr_over_45_corners_team,
            hr_over_15_saves_gk, hr_over_35_cards_match,
            top_stat_market, top_stat_hit_rate, updated_at
        ) VALUES ('Inter Miami', 'MLS', 10, {zeros}, 'x', 1, 'now')
        """
    )
    conn.execute(
        f"""
        INSERT INTO team_rolling_ten_telemetry (
            team_name, league, matches_count,
            avg_goals_scored, avg_goals_conceded, avg_total_goals,
            avg_shots_for, avg_shots_against, avg_sot_for, avg_sot_against,
            avg_corners_for, avg_corners_against, avg_saves_gk, avg_cards_match,
            hr_multigol_1_3_team, hr_multigol_1_5_match, hr_multigol_2_5_match,
            hr_chance_mix_dc_ov15, hr_chance_mix_x_gg, hr_over_15_match, hr_under_35_match,
            hr_both_halves_over_05, hr_mg_ht_02_sh_13,
            hr_over_95_shots_team, hr_over_115_shots_team, hr_over_125_shots_team,
            hr_over_35_sot_team, hr_over_35_corners_team, hr_over_45_corners_team,
            hr_over_15_saves_gk, hr_over_35_cards_match,
            top_stat_market, top_stat_hit_rate, updated_at
        ) VALUES ('Inter', 'Serie A', 10, {zeros}, 'x', 1, 'now')
        """
    )
    conn.commit()
    conn.close()

    profile = engine.get_team_profile("Inter")
    assert profile is not None
    assert profile["team_name"] == "Inter"
    assert profile["league"] == "Serie A"
