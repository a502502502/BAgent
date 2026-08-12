import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile


def softmax(scores):
    scores = scores - np.max(scores, axis=1, keepdims=True)
    exp = np.exp(scores)
    return exp / exp.sum(axis=1, keepdims=True)


def fit(X, y, iterations=6000, learning_rate=0.03, l2=0.001):
    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]

    for _ in range(iterations):
        p = softmax(X @ beta)
        gradient = X.T @ (p - Y) / len(X)
        gradient += l2 * beta
        beta -= learning_rate * gradient

    return beta


def metrics(p, y):
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
        np.sum((p - actual) ** 2, axis=1)
    )

    return accuracy, log_loss, brier


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
            avg_draw_rate,
            result,
        )
    )


rows.sort(key=lambda x: x[0])

split = int(len(rows) * 0.70)

train = rows[:split]
test = rows[split:]


# ---------------------------------------------------------
# STEP 1
# Fit HOME / DRAW / AWAY directional model.
# ---------------------------------------------------------

X_train = np.array(
    [
        [1.0, win, goal]
        for _, win, goal, _, _ in train
    ]
)

y_train = np.array(
    [r[-1] for r in train]
)

X_test = np.array(
    [
        [1.0, win, goal]
        for _, win, goal, _, _ in test
    ]
)

y_test = np.array(
    [r[-1] for r in test]
)

beta = fit(
    X_train,
    y_train,
)

base_test = softmax(
    X_test @ beta
)


# ---------------------------------------------------------
# STEP 2
# Calibrate DRAW separately using training data.
#
# We model a DRAW multiplier:
#
# draw_score =
#     base_draw *
#     exp(
#         a
#         + b * avg_draw_rate
#         + c * abs(win_difference)
#     )
#
# HOME/AWAY are then renormalized.
# ---------------------------------------------------------

draw_X_train = np.array(
    [
        [
            1.0,
            avg_draw,
            abs(win),
        ]
        for _, win, _, avg_draw, _ in train
    ]
)

draw_y_train = (
    y_train == 1
).astype(float)


draw_beta = np.zeros(3)

for _ in range(6000):

    z = draw_X_train @ draw_beta

    # Binary logistic probability.
    z = np.clip(z, -20.0, 20.0)

    q = 1.0 / (
        1.0 + np.exp(-z)
    )

    gradient = (
        draw_X_train.T
        @ (q - draw_y_train)
        / len(draw_y_train)
    )

    gradient += 0.001 * draw_beta

    draw_beta -= (
        0.03 * gradient
    )


draw_X_test = np.array(
    [
        [
            1.0,
            avg_draw,
            abs(win),
        ]
        for _, win, _, avg_draw, _ in test
    ]
)

draw_adjustment = (
    draw_X_test @ draw_beta
)

draw_multiplier = np.exp(
    np.clip(
        draw_adjustment,
        -1.5,
        1.5,
    )
)


# Apply multiplier only to DRAW.
p = base_test.copy()

p[:, 1] *= draw_multiplier

# Preserve HOME/AWAY relative proportions
# while allowing DRAW to change.
total = p.sum(axis=1, keepdims=True)

p /= total


accuracy, log_loss, brier = metrics(
    p,
    y_test,
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
print(
    "AVG DRAW PROB:",
    np.mean(p[:, 1]),
)

print(
    "AVG DRAW PROB | REAL DRAW:",
    np.mean(
        p[y_test == 1, 1]
    ),
)

print(
    "AVG DRAW PROB | NON-DRAW:",
    np.mean(
        p[y_test != 1, 1]
    ),
)

print()
print("DRAW CALIBRATION COEFFICIENTS:")

print(
    "INTERCEPT:",
    draw_beta[0],
)

print(
    "AVG DRAW RATE:",
    draw_beta[1],
)

print(
    "ABS WIN DIFFERENCE:",
    draw_beta[2],
)
