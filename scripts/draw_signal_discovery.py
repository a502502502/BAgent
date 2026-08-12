import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile


def safe(value):
    return value if value is not None else 0.0


raw_dir = Path("data/football/raw")
files = sorted(raw_dir.glob("E0_*.csv"))

loader = FootballDataLoader()

all_matches = []
for f in files:
    all_matches.extend(loader.load(f))

dataset = FootballHistoricalDataset(all_matches)
profile = FootballHistoricalProfile(dataset)

rows = []

for hm in dataset.all():

    if not hm.is_completed:
        continue

    home = profile.get_team_profile(hm.match.home.id, hm.date)
    away = profile.get_team_profile(hm.match.away.id, hm.date)

    if home is None or away is None:
        continue

    if home.matches < 5 or away.matches < 5:
        continue

    # Wide feature set: every signal already tracked by the profile.
    features = {
        "win_rate_diff": safe(home.win_rate) - safe(away.win_rate),
        "win_rate_abs_diff": abs(safe(home.win_rate) - safe(away.win_rate)),
        "draw_rate_avg": (safe(home.draw_rate) + safe(away.draw_rate)) / 2.0,
        "draw_rate_diff": abs(safe(home.draw_rate) - safe(away.draw_rate)),
        "loss_rate_avg": (safe(home.loss_rate) + safe(away.loss_rate)) / 2.0,

        "goals_for_diff": safe(home.goals_for_per_match) - safe(away.goals_for_per_match),
        "goals_against_diff": safe(home.goals_against_per_match) - safe(away.goals_against_per_match),
        "goal_strength_diff": (
            (safe(home.goals_for_per_match) - safe(home.goals_against_per_match))
            - (safe(away.goals_for_per_match) - safe(away.goals_against_per_match))
        ),
        "goal_strength_abs_diff": abs(
            (safe(home.goals_for_per_match) - safe(home.goals_against_per_match))
            - (safe(away.goals_for_per_match) - safe(away.goals_against_per_match))
        ),
        "combined_goal_expectancy": safe(home.goals_for_per_match) + safe(away.goals_for_per_match),

        "clean_sheet_rate_avg": (safe(home.clean_sheet_rate) + safe(away.clean_sheet_rate)) / 2.0,
        "clean_sheet_rate_diff": abs(safe(home.clean_sheet_rate) - safe(away.clean_sheet_rate)),

        "btts_rate_avg": (safe(home.btts_rate) + safe(away.btts_rate)) / 2.0,

        "corners_diff": safe(home.average_corners_for) - safe(away.average_corners_for),
        "corners_avg": (safe(home.average_corners_for) + safe(away.average_corners_for)) / 2.0,

        "yellow_cards_avg": (safe(home.average_yellow_cards) + safe(away.average_yellow_cards)) / 2.0,
        "yellow_cards_diff": abs(safe(home.average_yellow_cards) - safe(away.average_yellow_cards)),

        "home_specific_win_rate": (
            home.home_wins / home.home_matches if home.home_matches > 0 else 0.0
        ),
        "away_specific_win_rate": (
            away.away_wins / away.away_matches if away.away_matches > 0 else 0.0
        ),
        "home_specific_draw_rate": (
            home.home_draws / home.home_matches if home.home_matches > 0 else 0.0
        ),
        "away_specific_draw_rate": (
            away.away_draws / away.away_matches if away.away_matches > 0 else 0.0
        ),

        "matches_seen_min": min(home.matches, away.matches),
    }

    features["is_draw"] = 1 if hm.result == "DRAW" else 0

    rows.append(features)

print("TOTAL ROWS:", len(rows))
print("DRAW ROWS:", sum(r["is_draw"] for r in rows))
print()

feature_names = [k for k in rows[0].keys() if k != "is_draw"]

draw_vals = {name: [] for name in feature_names}
nondraw_vals = {name: [] for name in feature_names}

for row in rows:
    target = draw_vals if row["is_draw"] == 1 else nondraw_vals
    for name in feature_names:
        target[name].append(row[name])

print(f"{'FEATURE':30s} {'DRAW_MEAN':>12s} {'NONDRAW_MEAN':>14s} {'COHENS_D':>10s}")
print("-" * 70)

results = []

for name in feature_names:
    d = np.array(draw_vals[name])
    nd = np.array(nondraw_vals[name])

    d_mean = d.mean()
    nd_mean = nd.mean()

    pooled_std = np.sqrt(
        ((len(d) - 1) * d.std(ddof=1) ** 2 + (len(nd) - 1) * nd.std(ddof=1) ** 2)
        / (len(d) + len(nd) - 2)
    )

    cohens_d = (d_mean - nd_mean) / pooled_std if pooled_std > 0 else 0.0

    results.append((name, d_mean, nd_mean, cohens_d))

results.sort(key=lambda r: abs(r[3]), reverse=True)

for name, d_mean, nd_mean, cohens_d in results:
    print(f"{name:30s} {d_mean:12.4f} {nd_mean:14.4f} {cohens_d:10.4f}")

print()
print("Interpretazione: |Cohen's d| > 0.2 = effetto piccolo ma reale,")
print("> 0.5 = effetto medio, > 0.8 = effetto grande.")
print("Valori vicini a 0 = il segnale non distingue DRAW da non-DRAW.")
