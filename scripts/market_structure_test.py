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


def evaluate(X, y, beta):
    p = softmax(X @ beta)
    pred = np.argmax(p, axis=1)

    accuracy = np.mean(pred == y)

    log_loss = -np.mean(
        np.log(np.maximum(p[np.arange(len(y)), y], 1e-15))
    )

    actual = np.eye(3)[y]
    brier = np.mean(np.sum((p - actual) ** 2, axis=1))

    return accuracy, log_loss, brier


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

    home = profile.get_team_profile(
        hm.match.home.id,
        hm.date,
    )

    away = profile.get_team_profile(
        hm.match.away.id,
        hm.date,
    )

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

    favorite_strength = max(
        market_home,
        market_draw,
        market_away,
    )

    home_away_gap = abs(
        market_home - market_away
    )

    result = {
        "HOME": 0,
        "DRAW": 1,
        "AWAY": 2,
    }[hm.result]

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

y_train = np.array([r[-1] for r in train])
y_test = np.array([r[-1] for r in test])


def make_X(data, mode):

    X = []

    for (
        _,
        win,
        goal,
        mh,
        md,
        ma,
        fav,
        gap,
        _,
    ) in data:

        if mode == "BASE":
            row = [1.0, win, goal]

        elif mode == "MARKET":
            row = [
                1.0,
                win,
                goal,
                mh,
                md,
                ma,
            ]

        elif mode == "FAV":
            row = [
                1.0,
                win,
                goal,
                mh,
                md,
                ma,
                fav,
            ]

        elif mode == "GAP":
            row = [
                1.0,
                win,
                goal,
                mh,
                md,
                ma,
                gap,
            ]

        elif mode == "BOTH":
            row = [
                1.0,
                win,
                goal,
                mh,
                md,
                ma,
                fav,
                gap,
            ]

        X.append(row)

    return np.array(X)


print()
print("MARKET STRUCTURE ABLATION")
print("==========================")
print("TOTAL:", len(rows))
print("TRAIN:", len(train))
print("TEST :", len(test))
print()

for mode in [
    "BASE",
    "MARKET",
    "FAV",
    "GAP",
    "BOTH",
]:

    X_train = make_X(train, mode)
    X_test = make_X(test, mode)

    beta = fit(X_train, y_train)

    acc, ll, brier = evaluate(
        X_test,
        y_test,
        beta,
    )

    print(
        f"{mode:7s}"
        f"  ACC={acc:.6f}"
        f"  LOGLOSS={ll:.6f}"
        f"  BRIER={brier:.6f}"
    )

print()
print("REFERENCE V2")
print("ACCURACY:  0.5407")
print("LOG LOSS:  0.96954")
print("BRIER:     0.57620")
