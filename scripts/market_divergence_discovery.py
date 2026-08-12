import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile
from services.football_prediction_engine import FootballPredictionEngine


raw_dir = Path("data/football/raw")
files = sorted(raw_dir.glob("E0_*.csv"))

loader = FootballDataLoader()

all_matches = []
for f in files:
    all_matches.extend(loader.load(f))

dataset = FootballHistoricalDataset(all_matches)
profile = FootballHistoricalProfile(dataset)
engine = FootballPredictionEngine()

rows = []

for hm in dataset.all():

    if not hm.is_completed:
        continue

    if hm.odds is None or not hm.odds.is_1x2_available:
        continue

    prediction = engine.predict(
        match=hm.match,
        historical_profile=profile,
        date=hm.date,
    )

    if prediction is None:
        continue

    # Market implied probabilities, de-vigged (remove bookmaker margin
    # proportionally so the three probabilities sum to 1).
    inv_h = 1.0 / hm.odds.home
    inv_d = 1.0 / hm.odds.draw
    inv_a = 1.0 / hm.odds.away

    overround = inv_h + inv_d + inv_a

    market_home = inv_h / overround
    market_draw = inv_d / overround
    market_away = inv_a / overround

    model_home = prediction.probability.home
    model_draw = prediction.probability.draw
    model_away = prediction.probability.away

    features = {
        "market_draw_prob": market_draw,
        "model_draw_prob": model_draw,
        "divergence_draw_signed": model_draw - market_draw,
        "divergence_draw_abs": abs(model_draw - market_draw),
        "divergence_home_signed": model_home - market_home,
        "divergence_home_abs": abs(model_home - market_home),
        "divergence_away_signed": model_away - market_away,
        "divergence_away_abs": abs(model_away - market_away),
        "overround": overround,
        "market_favorite_strength": max(market_home, market_draw, market_away),
        "market_home_away_gap": abs(market_home - market_away),
    }

    features["is_draw"] = 1 if hm.result == "DRAW" else 0

    rows.append(features)

print("TOTAL ROWS WITH ODDS:", len(rows))
print("DRAW ROWS:", sum(r["is_draw"] for r in rows))
print()

feature_names = [k for k in rows[0].keys() if k != "is_draw"]

print(f"{'FEATURE':30s} {'DRAW_MEAN':>12s} {'NONDRAW_MEAN':>14s} {'COHENS_D':>10s}")
print("-" * 70)

results_out = []

for name in feature_names:
    d = np.array([r[name] for r in rows if r["is_draw"] == 1])
    nd = np.array([r[name] for r in rows if r["is_draw"] == 0])

    d_mean = d.mean()
    nd_mean = nd.mean()

    pooled_std = np.sqrt(
        ((len(d) - 1) * d.std(ddof=1) ** 2 + (len(nd) - 1) * nd.std(ddof=1) ** 2)
        / (len(d) + len(nd) - 2)
    )

    cohens_d = (d_mean - nd_mean) / pooled_std if pooled_std > 0 else 0.0

    results_out.append((name, d_mean, nd_mean, cohens_d))

results_out.sort(key=lambda r: abs(r[3]), reverse=True)

for name, d_mean, nd_mean, cohens_d in results_out:
    print(f"{name:30s} {d_mean:12.4f} {nd_mean:14.4f} {cohens_d:10.4f}")

# --- Bucket analysis on the signed divergence, the core hypothesis ---
print()
print("=== DRAW RATE BY MODEL-VS-MARKET DIVERGENCE (signed) ===")
print("(divergenza positiva = il modello vede più DRAW di quanto prezzi il mercato)")
print()

divs = np.array([r["divergence_draw_signed"] for r in rows])
is_draw = np.array([r["is_draw"] for r in rows])

quantile_edges = np.quantile(divs, np.linspace(0, 1, 11))

for i in range(10):
    low, high = quantile_edges[i], quantile_edges[i + 1]
    mask = (divs >= low) & (divs <= high if i == 9 else divs < high)
    n = mask.sum()
    if n == 0:
        continue
    draw_rate = is_draw[mask].mean()
    print(f"decile {i+1:2d}  [{low:+.4f}, {high:+.4f})  n={n:4d}  draw_rate={draw_rate:.4f}")

print()
print("=== DRAW RATE BY MARKET DRAW PROBABILITY (baseline di confronto) ===")
print()

market_d = np.array([r["market_draw_prob"] for r in rows])
quantile_edges2 = np.quantile(market_d, np.linspace(0, 1, 11))

for i in range(10):
    low, high = quantile_edges2[i], quantile_edges2[i + 1]
    mask = (market_d >= low) & (market_d <= high if i == 9 else market_d < high)
    n = mask.sum()
    if n == 0:
        continue
    draw_rate = is_draw[mask].mean()
    print(f"decile {i+1:2d}  [{low:.4f}, {high:.4f})  n={n:4d}  draw_rate={draw_rate:.4f}")
