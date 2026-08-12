import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile


def softmax(scores):
    scores = scores - np.max(
        scores,
        axis=1,
        keepdims=True,
    )
    exp = np.exp(scores)
    return exp / exp.sum(axis=1, keepdims=True)


def fit(X, y, iterations=8000, learning_rate=0.03, l2=0.001):
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
        np.log(
            np.maximum(
                p[np.arange(len(y)), y],
                1e-15,
            )
        )
    )

    actual = np.eye(3)[y]

    brier = np.mean(
        np.sum(
            (p - actual) ** 2,
            axis=1,
        )
    )

    return accuracy, log_loss, brier, p


loader = FootballDataLoader()

matches = loader.load(
    "data/football/raw/E0_2025_2026.csv"
)

dataset = FootballHistoricalDataset(matches)
profile = FootballHistoricalProfile(dataset)

rows = []

for hm in dataset.all():

    if not hm.is_completed:
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

    if home.matches <= 0 or away.matches <= 0:
        continue

    home_wr = (
        home.wins + 5.0 * 0.5
    ) / (home.matches + 5.0)

    away_wr = (
        away.wins + 5.0 * 0.5
    ) / (away.matches + 5.0)

    win_diff = home_wr - away_wr

    home_gs = (
        home.goals_for_per_match
        - home.goals_against_per_match
    )

    away_gs = (
        away.goals_for_per_match
        - away.goals_against_per_match
    )

    goal_diff = home_gs - away_gs

    avg_draw_rate = (
        home.draw_rate
        + away.draw_rate
    ) / 2.0

    draw_rate_diff = abs(
        home.draw_rate
        - away.draw_rate
    )

    win_balance = 1.0 - abs(win_diff)

    goal_balance = (
        1.0
        / (1.0 + abs(goal_diff))
    )

    result = {
        "HOME": 0,
        "DRAW": 1,
        "AWAY": 2,
    }[hm.result]

    rows.append(
        (
            hm.date,
            win_diff,
            goal_diff,
            win_balance,
            avg_draw_rate,
            draw_rate_diff,
            goal_balance,
            result,
        )
    )


rows.sort(key=lambda x: x[0])

split = int(len(rows) * 0.70)

train = rows[:split]
test = rows[split:]


def make_X(rows):
    return np.array(
        [
            [
                1.0,
                win,
                goal,
                balance,
                draw_rate,
                draw_diff,
                goal_balance,
            ]
            for (
                _,
                win,
                goal,
                balance,
                draw_rate,
                draw_diff,
                goal_balance,
                _,
            ) in rows
        ]
    )


X_train = make_X(train)
X_test = make_X(test)

y_train = np.array(
    [r[-1] for r in train]
)

y_test = np.array(
    [r[-1] for r in test]
)


beta = fit(
    X_train,
    y_train,
)


accuracy, log_loss, brier, p = metrics(
    X_test,
    y_test,
    beta,
)


predicted = np.argmax(
    p,
    axis=1,
)

actual_draws = np.sum(
    y_test == 1
)

predicted_draws = np.sum(
    predicted == 1
)

correct_draws = np.sum(
    (predicted == 1)
    & (y_test == 1)
)


print()
print("TRAIN:", len(train))
print("TEST:", len(test))

print()
print("ACCURACY:", accuracy)
print("LOG LOSS:", log_loss)
print("BRIER:", brier)

print()
print("ACTUAL DRAW:", actual_draws)
print("PREDICTED DRAW:", predicted_draws)
print("CORRECT DRAW:", correct_draws)

print()
print("AVG DRAW PROB:",
      np.mean(p[:, 1]))

print(
    "AVG DRAW PROB | REAL DRAW:",
    np.mean(p[y_test == 1, 1]),
)

print(
    "AVG DRAW PROB | NON-DRAW:",
    np.mean(p[y_test != 1, 1]),
)

print()
print("COEFFICIENTS:")

names = [
    "INTERCEPT",
    "WIN_DIFF",
    "GOAL_DIFF",
    "WIN_BALANCE",
    "AVG_DRAW_RATE",
    "DRAW_RATE_DIFF",
    "GOAL_BALANCE",
]

for i, name in enumerate(names):
    print(
        name,
        "HOME=", beta[i, 0],
        "DRAW=", beta[i, 1],
        "AWAY=", beta[i, 2],
    )
