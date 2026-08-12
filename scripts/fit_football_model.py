import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile
from services.football_team_strength_factor import FootballTeamStrengthFactor


def softmax(scores):
    scores = scores - np.max(
        scores,
        axis=1,
        keepdims=True,
    )

    exp = np.exp(scores)

    return exp / exp.sum(
        axis=1,
        keepdims=True,
    )


def fit(
    X,
    y,
    iterations=5000,
    learning_rate=0.03,
    l2=0.001,
):
    beta = np.zeros(
        (X.shape[1], 3)
    )

    Y = np.eye(3)[y]

    for _ in range(iterations):

        probabilities = softmax(
            X @ beta
        )

        gradient = (
            X.T @ (
                probabilities - Y
            )
            / len(X)
        )

        gradient += l2 * beta

        beta -= (
            learning_rate
            * gradient
        )

    return beta


def metrics(
    X,
    y,
    beta,
):
    probabilities = softmax(
        X @ beta
    )

    predictions = np.argmax(
        probabilities,
        axis=1,
    )

    accuracy = np.mean(
        predictions == y
    )

    log_loss = -np.mean(
        np.log(
            np.maximum(
                probabilities[
                    np.arange(len(y)),
                    y,
                ],
                1e-15,
            )
        )
    )

    actual = np.eye(3)[y]

    brier = np.mean(
        np.sum(
            (
                probabilities
                - actual
            ) ** 2,
            axis=1,
        )
    )

    return (
        accuracy,
        log_loss,
        brier,
    )


loader = FootballDataLoader()

matches = loader.load(
    "data/football/raw/E0_2025_2026.csv"
)

dataset = FootballHistoricalDataset(
    matches
)

profile = FootballHistoricalProfile(
    dataset
)

factor = FootballTeamStrengthFactor()

rows = []

for historical_match in dataset.all():

    if not historical_match.is_completed:
        continue

    home = profile.get_team_profile(
        historical_match.match.home.id,
        historical_match.date,
    )

    away = profile.get_team_profile(
        historical_match.match.away.id,
        historical_match.date,
    )

    if home is None or away is None:
        continue

    contribution = factor.evaluate(
        home,
        away,
    )

    if contribution is None:
        continue

    details = contribution.details

    win_difference = (
        details["difference"]
    )

    goal_difference = (
        details["goal_difference"]
    )

    result = {
        "HOME": 0,
        "DRAW": 1,
        "AWAY": 2,
    }[historical_match.result]

    rows.append(
        (
            historical_match.date,
            win_difference,
            goal_difference,
            result,
        )
    )


rows.sort(
    key=lambda row: row[0]
)

split = int(
    len(rows) * 0.70
)

train = rows[:split]
test = rows[split:]


X_train = np.array(
    [
        [1.0, win, goal]
        for _, win, goal, _ in train
    ]
)

y_train = np.array(
    [
        result
        for _, _, _, result in train
    ]
)

X_test = np.array(
    [
        [1.0, win, goal]
        for _, win, goal, _ in test
    ]
)

y_test = np.array(
    [
        result
        for _, _, _, result in test
    ]
)


beta = fit(
    X_train,
    y_train,
)


accuracy, log_loss, brier = metrics(
    X_test,
    y_test,
    beta,
)


print()
print("TRAIN:", len(train))
print("TEST:", len(test))
print()

print("COEFFICIENTS:")

print(
    "INTERCEPT HOME:",
    beta[0, 0],
)

print(
    "INTERCEPT DRAW:",
    beta[0, 1],
)

print(
    "INTERCEPT AWAY:",
    beta[0, 2],
)

print()

print("WIN DIFF:")

print(
    "HOME:",
    beta[1, 0],
)

print(
    "DRAW:",
    beta[1, 1],
)

print(
    "AWAY:",
    beta[1, 2],
)

print()

print("GOAL DIFF:")

print(
    "HOME:",
    beta[2, 0],
)

print(
    "DRAW:",
    beta[2, 1],
)

print(
    "AWAY:",
    beta[2, 2],
)

print()

print(
    "TEST ACCURACY:",
    accuracy,
)

print(
    "TEST LOG LOSS:",
    log_loss,
)

print(
    "TEST BRIER:",
    brier,
)
