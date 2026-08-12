import pandas as pd
from pathlib import Path

root = Path("data/football/raw/serie_b")

for f in sorted(root.glob("BRB_*.csv")):
    df = pd.read_csv(f)

    required = [
        "timestamp",
        "home_team_name",
        "away_team_name",
        "home_team_goal_count",
        "away_team_goal_count",
        "odds_ft_home_team_win",
        "odds_ft_draw",
        "odds_ft_away_team_win",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    print()
    print("=" * 60)
    print(f.name)
    print("ROWS:", len(df))
    print("MISSING:", missing)
    print(
        "ODDS:",
        df[
            [
                "odds_ft_home_team_win",
                "odds_ft_draw",
                "odds_ft_away_team_win",
            ]
        ].notna().all(axis=1).sum(),
    )

    teams = sorted(
        set(df["home_team_name"].dropna())
        | set(df["away_team_name"].dropna())
    )

    for team in teams:
        if "Ava" in str(team) or "CRB" in str(team):
            print("TEAM:", repr(team))
