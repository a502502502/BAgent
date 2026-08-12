import sys
from pathlib import Path

import numpy as np

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile
from services.football_team_strength_factor import FootballTeamStrengthFactor
from services.football_match_balance_factor import FootballMatchBalanceFactor


EPSILON = 1e-15

COEFFICIENTS = [
    -2.0,
    -1.5,
    -1.0,
    -0.75,
    -0.5,
    -0.25,
    0.0,
    0.25,
    0.5,
    0.75,
    1.0,
    1.5,
    2.0,
]


def softmax(scores):

    scores = (
        scores
        - np.max(
            scores,
            axis=1,
            keepdims=True,
        )
    )

    exp = np.exp(scores)

    return (
        exp
        / exp.sum(
            axis=1,
            keepdims=True,
        )
    )


def fit(
    X,
    y,
    iterations=5000,
    learning_rate=0.03,
    l2=0.001,
):

    beta = np.zeros(
        (
            X.shape[1],
            3,
        )
    )

    Y = np.eye(3)[y]

    for _ in range(iterations):

        p = softmax(X @ beta)

        gradient = (
            X.T @ (p - Y)
            / len(X)
        )

        gradient += l2 * beta

        beta -= (
            learning_rate
            * gradient
        )

    return beta


def evaluate(probabilities, y):

    probabilities = np.asarray(
        probabilities
    )

    y = np.asarray(y)

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
                EPSILON,
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


def load_rows():

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

    strength_factor = (
        FootballTeamStrengthFactor()
    )

    balance_factor = (
        FootballMatchBalanceFactor()
    )

    rows = []

    for item in dataset.all():

        if not item.is_completed:
            continue

        home = profile.get_team_profile(
            item.match.home.id,
            item.date,
        )

        away = profile.get_team_profile(
            item.match.away.id,
            item.date,
        )

        if home is None or away is None:
            continue

        strength = strength_factor.evaluate(
            home,
            away,
        )

        balance = balance_factor.evaluate(
            home,
            away,
        )

        if strength is None or balance is None:
            continue

        result = {
            "HOME": 0,
            "DRAW": 1,
            "AWAY": 2,
        }[item.result]

        details = strength.details

        rows.append(
            (
                item.date,
                details["difference"],
                details["goal_difference"],
                balance.value,
                result,
            )
        )

    rows.sort(
        key=lambda x: x[0]
    )

    return rows


def matrix(
    rows,
    coefficient,
):

    return np.asarray(
        [
            [
                1.0,
                row[1],
                row[2],
                row[3] * coefficient,
            ]
            for row in rows
        ],
        dtype=float,
    )


def train_model(
    rows,
    coefficient,
):

    X = matrix(
        rows,
        coefficient,
    )

    y = np.asarray(
        [
            row[4]
            for row in rows
        ]
    )

    beta = fit(
        X,
        y,
    )

    return beta


def evaluate_model(
    beta,
    rows,
    coefficient,
):

    X = matrix(
        rows,
        coefficient,
    )

    y = np.asarray(
        [
            row[4]
            for row in rows
        ]
    )

    probabilities = softmax(
        X @ beta
    )

    return evaluate(
        probabilities,
        y,
    )


def main():

    rows = load_rows()

    print()
    print(
        "WALK-FORWARD FOOTBALL "
        "CALIBRATION"
    )

    print(
        "TOTAL:",
        len(rows),
    )

    if len(rows) < 100:
        print(
            "NOT ENOUGH DATA"
        )
        return

    n = len(rows)

    # Three chronological blocks.
    train_end = int(
        n * 0.50
    )

    validation_end = int(
        n * 0.75
    )

    train = rows[:train_end]

    validation = rows[
        train_end:validation_end
    ]

    test = rows[
        validation_end:
    ]

    print(
        "TRAIN:",
        len(train),
    )

    print(
        "VALIDATION:",
        len(validation),
    )

    print(
        "TEST:",
        len(test),
    )

    # --------------------------------------------------
    # COEFFICIENT SEARCH
    # --------------------------------------------------

    validation_results = []

    print()
    print(
        "# VALIDATION SEARCH"
    )

    for coefficient in COEFFICIENTS:

        beta = train_model(
            train,
            coefficient,
        )

        metrics = evaluate_model(
            beta,
            validation,
            coefficient,
        )

        validation_results.append(
            (
                coefficient,
                metrics,
                beta,
            )
        )

        print(
            f"BALANCE={coefficient:+.2f} "
            f"ACC={metrics[0]:.6f} "
            f"LL={metrics[1]:.6f} "
            f"BRIER={metrics[2]:.6f}"
        )

    # Primary criterion = Log Loss.
    # Secondary = Brier.

    validation_results.sort(
        key=lambda x: (
            x[1][1],
            x[1][2],
        )
    )

    best_coefficient = (
        validation_results[0][0]
    )

    best_validation = (
        validation_results[0][1]
    )

    print()
    print(
        "# SELECTED"
    )

    print(
        "BALANCE COEFFICIENT:",
        best_coefficient,
    )

    print(
        "VALIDATION ACC:",
        best_validation[0],
    )

    print(
        "VALIDATION LOG LOSS:",
        best_validation[1],
    )

    print(
        "VALIDATION BRIER:",
        best_validation[2],
    )

    # --------------------------------------------------
    # FINAL TEST
    #
    # Refit only after the coefficient has been selected.
    # The final test is untouched during selection.
    # --------------------------------------------------

    training_for_final = (
        rows[:validation_end]
    )

    final_beta = train_model(
        training_for_final,
        best_coefficient,
    )

    final_metrics = evaluate_model(
        final_beta,
        test,
        best_coefficient,
    )

    print()
    print(
        "# FINAL TEST"
    )

    print(
        f"BALANCE={best_coefficient:+.2f} "
        f"ACC={final_metrics[0]:.6f} "
        f"LL={final_metrics[1]:.6f} "
        f"BRIER={final_metrics[2]:.6f}"
    )

    # --------------------------------------------------
    # BASE FINAL TEST
    # --------------------------------------------------

    base_beta = train_model(
        training_for_final,
        0.0,
    )

    base_metrics = evaluate_model(
        base_beta,
        test,
        0.0,
    )

    print()
    print(
        "# FINAL BASELINE"
    )

    print(
        f"BASE "
        f"ACC={base_metrics[0]:.6f} "
        f"LL={base_metrics[1]:.6f} "
        f"BRIER={base_metrics[2]:.6f}"
    )

    print()
    print(
        "# FINAL DELTA"
    )

    print(
        "ACCURACY:",
        final_metrics[0]
        - base_metrics[0],
    )

    print(
        "LOG LOSS:",
        final_metrics[1]
        - base_metrics[1],
    )

    print(
        "BRIER:",
        final_metrics[2]
        - base_metrics[2],
    )

    # --------------------------------------------------
    # FINAL COEFFICIENTS
    # --------------------------------------------------

    print()
    print(
        "# FINAL COEFFICIENTS"
    )

    labels = [
        "HOME",
        "DRAW",
        "AWAY",
    ]

    names = [
        "INTERCEPT",
        "WIN_DIFF",
        "GOAL_DIFF",
        "BALANCE",
    ]

    for index, name in enumerate(
        names
    ):

        for class_index, label in enumerate(
            labels
        ):

            print(
                f"{label} {name}:",
                final_beta[
                    index,
                    class_index,
                ]
            )


if __name__ == "__main__":
    main()
