import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile
from services.football_team_strength_factor import FootballTeamStrengthFactor


def softmax(scores):
    scores = scores - np.max(scores, axis=1, keepdims=True)
    exp = np.exp(scores)
    return exp / exp.sum(axis=1, keepdims=True)


def fit(X, y, iterations=10000, learning_rate=0.03, l2=0.001):
    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]

    for _ in range(iterations):
        p = softmax(X @ beta)
        gradient = X.T @ (p - Y) / len(X)
        gradient += l2 * beta
        beta -= learning_rate * gradient

    return beta


def metrics(X, y, beta):
    p = softmax(X @ beta)
    pred = np.argmax(p, axis=1)

    accuracy = np.mean(pred == y)

    log_loss = -np.mean(
        np.log(np.maximum(p[np.arange(len(y)), y], 1e-15))
    )

    actual = np.eye(3)[y]
    brier = np.mean(np.sum((p - actual) ** 2, axis=1))

    return accuracy, log_loss, brier, p


raw_dir = Path("data/football/raw")
files = sorted(raw_dir.glob("E0_*.csv"))

loader = FootballDataLoader()

all_matches = []
for f in files:
    all_matches.extend(loader.load(f))

dataset = FootballHistoricalDataset(all_matches)
profile = FootballHistoricalProfile(dataset)
factor = FootballTeamStrengthFactor()

rows = []

for hm in dataset.all():

    if not hm.is_completed:
        continue

    if hm.odds is None or not hm.odds.is_1x2_available:
        continue

    home = profile.get_team_profile(hm.match.home.id, hm.date)
    away = profile.get_team_profile(hm.match.away.id, hm.date)

    if home is None or away is None:
        continue

    contribution = factor.evaluate(home, away)

    if contribution is None:
        continue

    details = contribution.details

    win_difference = details["difference"]
    goal_difference = details["goal_difference"]

    inv_h = 1.0 / hm.odds.home
    inv_d = 1.0 / hm.odds.draw
    inv_a = 1.0 / hm.odds.away
    overround = inv_h + inv_d + inv_a

    market_home = inv_h / overround
    market_draw = inv_d / overround
    market_away = inv_a / overround

    favorite_strength = max(market_home, market_draw, market_away)
    home_away_gap = abs(market_home - market_away)

    result = {"HOME": 0, "DRAW": 1, "AWAY": 2}[hm.result]

    rows.append(
        (
            hm.date,
            win_difference,
            goal_difference,
            market_home,
            market_draw,
            market_away,
            favorite_strength,
            home_away_gap,
            result,
        )
    )

rows.sort(key=lambda r: r[0])

split = int(len(rows) * 0.70)
train = rows[:split]
test = rows[split:]

print("TOTAL ROWS:", len(rows))
print("TRAIN:", len(train))
print("TEST:", len(test))


def make_X(rows_subset, include_market):
    if include_market:
        return np.array(
            [
                [1.0, win, goal, mh, md, ma, fav, gap]
                for (_, win, goal, mh, md, ma, fav, gap, _) in rows_subset
            ]
        )
    return np.array(
        [
            [1.0, win, goal]
            for (_, win, goal, _, _, _, _, _, _) in rows_subset
        ]
    )


y_train = np.array([r[-1] for r in train])
y_test = np.array([r[-1] for r in test])

# --- Baseline: without market features (same as before, for comparison) ---
X_train_base = make_X(train, include_market=False)
X_test_base = make_X(test, include_market=False)

beta_base = fit(X_train_base, y_train)
acc_base, ll_base, brier_base, p_base = metrics(X_test_base, y_test, beta_base)

pred_base = np.argmax(p_base, axis=1)
draw_pred_base = np.sum(pred_base == 1)
draw_correct_base = np.sum((pred_base == 1) & (y_test == 1))

print()
print("=== BASELINE (win_diff + goal_diff only) ===")
print("ACCURACY:", acc_base)
print("LOG LOSS:", ll_base)
print("BRIER:", brier_base)
print("DRAW PREDICTED:", draw_pred_base, "/ CORRECT:", draw_correct_base)

# --- With market features ---
X_train_mkt = make_X(train, include_market=True)
X_test_mkt = make_X(test, include_market=True)

beta_mkt = fit(X_train_mkt, y_train)
acc_mkt, ll_mkt, brier_mkt, p_mkt = metrics(X_test_mkt, y_test, beta_mkt)

pred_mkt = np.argmax(p_mkt, axis=1)
draw_pred_mkt = np.sum(pred_mkt == 1)
draw_correct_mkt = np.sum((pred_mkt == 1) & (y_test == 1))

print()
print("=== WITH MARKET FEATURES ===")
print("ACCURACY:", acc_mkt)
print("LOG LOSS:", ll_mkt)
print("BRIER:", brier_mkt)
print("DRAW PREDICTED:", draw_pred_mkt, "/ CORRECT:", draw_correct_mkt)

print()
print("AVG DRAW PROB:", np.mean(p_mkt[:, 1]))
print("AVG DRAW PROB | REAL DRAW:", np.mean(p_mkt[y_test == 1, 1]))
print("AVG DRAW PROB | NON-DRAW:", np.mean(p_mkt[y_test != 1, 1]))
print("DRAW PROB RANGE:", p_mkt[:, 1].min(), "-", p_mkt[:, 1].max())

print()
print("COEFFICIENTS (with market):")
names = ["INTERCEPT", "WIN_DIFF", "GOAL_DIFF", "MARKET_HOME", "MARKET_DRAW", "MARKET_AWAY", "FAV_STRENGTH", "HOME_AWAY_GAP"]
for i, name in enumerate(names):
    print(f"{name:15s} HOME={beta_mkt[i,0]:+.4f}  DRAW={beta_mkt[i,1]:+.4f}  AWAY={beta_mkt[i,2]:+.4f}")

print()
print("=== BASELINE (33/33/33) FOR REFERENCE ===")
baseline_p = np.full((len(y_test), 3), 1.0 / 3.0)
actual = np.eye(3)[y_test]
baseline_ll = -np.mean(np.log(baseline_p[np.arange(len(y_test)), y_test]))
baseline_brier = np.mean(np.sum((baseline_p - actual) ** 2, axis=1))
print("LOG LOSS:", baseline_ll)
print("BRIER:", baseline_brier)
