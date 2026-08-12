import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset


FORM_WINDOW = 5


def points(result, is_home):
    if result == "DRAW":
        return 1
    if (result == "HOME" and is_home) or (result == "AWAY" and not is_home):
        return 3
    return 0


raw_dir = Path("data/football/raw")
files = sorted(raw_dir.glob("E0_*.csv"))

loader = FootballDataLoader()

all_matches = []
for f in files:
    all_matches.extend(loader.load(f))

dataset = FootballHistoricalDataset(all_matches)
completed = [m for m in dataset.all() if m.is_completed]
completed.sort(key=lambda m: m.date)

# Per-team chronological history: list of (date, opponent, is_home, gf, ga, result)
team_history = defaultdict(list)

# Head-to-head history: key = frozenset({home_id, away_id}) -> list of results
h2h_history = defaultdict(list)

rows = []

for hm in completed:

    home_id = hm.match.home.id
    away_id = hm.match.away.id

    home_hist = team_history[home_id]
    away_hist = team_history[away_id]

    if len(home_hist) < FORM_WINDOW or len(away_hist) < FORM_WINDOW:
        # Still record history, but skip building a feature row.
        pass
    else:
        home_recent = home_hist[-FORM_WINDOW:]
        away_recent = away_hist[-FORM_WINDOW:]

        home_pts = [p for (_, _, _, _, _, p) in home_recent]
        away_pts = [p for (_, _, _, _, _, p) in away_recent]

        home_form_avg = np.mean(home_pts)
        away_form_avg = np.mean(away_pts)

        home_form_std = np.std(home_pts)
        away_form_std = np.std(away_pts)

        home_gd_recent = np.mean([gf - ga for (_, _, gf, ga, _, _) in home_recent])
        away_gd_recent = np.mean([gf - ga for (_, _, gf, ga, _, _) in away_recent])

        h2h_key = frozenset({home_id, away_id})
        h2h_results = h2h_history[h2h_key]

        if len(h2h_results) >= 2:
            h2h_draw_rate = sum(1 for r in h2h_results if r == "DRAW") / len(h2h_results)
        else:
            h2h_draw_rate = None

        features = {
            "form_points_diff": home_form_avg - away_form_avg,
            "form_points_abs_diff": abs(home_form_avg - away_form_avg),
            "form_points_avg": (home_form_avg + away_form_avg) / 2.0,
            "form_volatility_avg": (home_form_std + away_form_std) / 2.0,
            "form_volatility_diff": abs(home_form_std - away_form_std),
            "form_goal_diff_diff": home_gd_recent - away_gd_recent,
            "form_goal_diff_abs_diff": abs(home_gd_recent - away_gd_recent),
            "form_combined_stability": 1.0 / (1.0 + home_form_std + away_form_std),
        }

        if h2h_draw_rate is not None:
            features["h2h_draw_rate"] = h2h_draw_rate
            features["h2h_matches"] = len(h2h_results)

        features["is_draw"] = 1 if hm.result == "DRAW" else 0

        rows.append(features)

    # Update history AFTER building features (no leakage).
    home_pts_earned = points(hm.result, True)
    away_pts_earned = points(hm.result, False)

    team_history[home_id].append(
        (hm.date, away_id, True, hm.match.home_goals, hm.match.away_goals, home_pts_earned)
    )
    team_history[away_id].append(
        (hm.date, home_id, False, hm.match.away_goals, hm.match.home_goals, away_pts_earned)
    )

    h2h_history[frozenset({home_id, away_id})].append(hm.result)


print("TOTAL ROWS (with 5+ prior matches):", len(rows))
print("DRAW ROWS:", sum(r["is_draw"] for r in rows))

rows_with_h2h = [r for r in rows if "h2h_draw_rate" in r]
print("ROWS WITH H2H HISTORY (2+ prior meetings):", len(rows_with_h2h))
print()

feature_names = sorted(
    {k for r in rows for k in r.keys() if k not in ("is_draw", "h2h_matches")}
)

print(f"{'FEATURE':30s} {'DRAW_MEAN':>12s} {'NONDRAW_MEAN':>14s} {'COHENS_D':>10s} {'N':>8s}")
print("-" * 80)

results_out = []

for name in feature_names:
    subset = [r for r in rows if name in r]

    d = np.array([r[name] for r in subset if r["is_draw"] == 1])
    nd = np.array([r[name] for r in subset if r["is_draw"] == 0])

    if len(d) < 5 or len(nd) < 5:
        continue

    d_mean = d.mean()
    nd_mean = nd.mean()

    pooled_std = np.sqrt(
        ((len(d) - 1) * d.std(ddof=1) ** 2 + (len(nd) - 1) * nd.std(ddof=1) ** 2)
        / (len(d) + len(nd) - 2)
    )

    cohens_d = (d_mean - nd_mean) / pooled_std if pooled_std > 0 else 0.0

    results_out.append((name, d_mean, nd_mean, cohens_d, len(subset)))

results_out.sort(key=lambda r: abs(r[3]), reverse=True)

for name, d_mean, nd_mean, cohens_d, n in results_out:
    print(f"{name:30s} {d_mean:12.4f} {nd_mean:14.4f} {cohens_d:10.4f} {n:8d}")
