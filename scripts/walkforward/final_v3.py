import sys
from pathlib import Path
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from services.football_data_loader import FootballDataLoader


DECAY = 2.0
TRAIN_SEASONS = [
    "E0_2021.csv",
    "E0_2122.csv",
    "E0_2223.csv",
    "E0_2324.csv",
    "E0_2425.csv",
]
TEST_SEASON = "E0_2025_2026.csv"

ITERATIONS = 8000
LEARNING_RATE = 0.03
L2 = 0.001


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


def fit(X, y):
    beta = np.zeros(
        (X.shape[1], 3),
        dtype=float,
    )

    Y = np.eye(3)[y]

    for _ in range(ITERATIONS):

        probabilities = softmax(
            X @ beta
        )

        gradient = (
            X.T @ (probabilities - Y)
            / len(X)
        )

        gradient += L2 * beta

        beta -= (
            LEARNING_RATE
            * gradient
        )

    return beta


def evaluate(beta, X, y):

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
        probabilities,
    )


def devig(home, draw, away):

    if (
        home is None
        or draw is None
        or away is None
    ):
        return None

    if min(
        home,
        draw,
        away,
    ) <= 1.0:
        return None

    inverse_home = 1.0 / home
    inverse_draw = 1.0 / draw
    inverse_away = 1.0 / away

    total = (
        inverse_home
        + inverse_draw
        + inverse_away
    )

    return (
        inverse_home / total,
        inverse_draw / total,
        inverse_away / total,
    )


def decay_weight(
    days,
):

    if days < 0:
        days = 0

    return math.exp(
        -DECAY * days / 365.0
    )


def team_stats(
    history,
    team_id,
    date,
):

    wins = 0.0
    goals_for = 0.0
    goals_against = 0.0
    weight_total = 0.0

    for item in history:

        if (
            item.match.home_goals is None
            or item.match.away_goals is None
        ):
            continue

        days = (
            date - item.date
        ).days

        weight = decay_weight(
            days
        )

        if (
            item.match.home.id
            == team_id
        ):
            gf = item.match.home_goals
            ga = item.match.away_goals

        else:
            gf = item.match.away_goals
            ga = item.match.home_goals

        if gf > ga:
            wins += weight

        goals_for += (
            weight * gf
        )

        goals_against += (
            weight * ga
        )

        weight_total += weight

    if weight_total <= 0:
        return None

    return (
        wins / weight_total,
        (
            goals_for
            - goals_against
        )
        / weight_total,
    )


def build_rows(
    matches,
    include_market=True,
):

    rows = []

    completed = [
        item
        for item in matches
        if item.is_completed
    ]

    completed.sort(
        key=lambda item: item.date
    )

    for index, item in enumerate(
        completed
    ):

        previous = completed[:index]

        home_history = [
            x
            for x in previous
            if (
                x.match.home.id
                == item.match.home.id
                or
                x.match.away.id
                == item.match.home.id
            )
        ]

        away_history = [
            x
            for x in previous
            if (
                x.match.home.id
                == item.match.away.id
                or
                x.match.away.id
                == item.match.away.id
            )
        ]

        home = team_stats(
            home_history,
            item.match.home.id,
            item.date,
        )

        away = team_stats(
            away_history,
            item.match.away.id,
            item.date,
        )

        if (
            home is None
            or away is None
        ):
            continue

        market = devig(
            item.odds.home
            if item.odds is not None
            else None,
            item.odds.draw
            if item.odds is not None
            else None,
            item.odds.away
            if item.odds is not None
            else None,
        )

        if (
            include_market
            and market is None
        ):
            continue

        win_difference = (
            home[0] - away[0]
        )

        goal_difference = (
            home[1] - away[1]
        )

        result = {
            "HOME": 0,
            "DRAW": 1,
            "AWAY": 2,
        }[item.result]

        if market is None:
            market = (
                1.0 / 3.0,
                1.0 / 3.0,
                1.0 / 3.0,
            )

        rows.append(
            {
                "date": item.date,
                "win_difference": win_difference,
                "goal_difference": goal_difference,
                "market_home": market[0],
                "market_draw": market[1],
                "market_away": market[2],
                "result": result,
            }
        )

    return rows


def make_features(rows):

    X = []

    y = []

    for row in rows:

        X.append(
            [
                1.0,
                row["win_difference"],
                row["goal_difference"],
                row["market_home"],
                row["market_draw"],
                row["market_away"],
            ]
        )

        y.append(
            row["result"]
        )

    return (
        np.asarray(
            X,
            dtype=float,
        ),
        np.asarray(
            y,
            dtype=int,
        ),
    )


def main():

    print()
    print(
        "=================================================="
    )
    print(
        "FINAL OUT-OF-SAMPLE V3 TEST"
    )
    print(
        "HISTORY + RECENCY + MARKET"
    )
    print(
        "=================================================="
    )

    loader = FootballDataLoader()

    raw_dir = (
        ROOT
        / "data"
        / "football"
        / "raw"
    )

    train_matches = []

    for filename in TRAIN_SEASONS:

        path = (
            raw_dir
            / filename
        )

        matches = loader.load(
            path
        )

        print(
            f"{filename}: "
            f"{len(matches)} matches"
        )

        train_matches.extend(
            matches
        )

    test_path = (
        raw_dir
        / TEST_SEASON
    )

    test_matches = loader.load(
        test_path
    )

    print(
        f"{TEST_SEASON}: "
        f"{len(test_matches)} matches"
    )

    print()
    print(
        "TRAIN MATCHES:",
        len(train_matches),
    )

    print(
        "TEST MATCHES:",
        len(test_matches),
    )

    print(
        "RECENCY DECAY:",
        DECAY,
    )

    print(
        "MARKET:",
        "DEVIG 1X2",
    )

    train_rows = build_rows(
        train_matches,
        include_market=True,
    )

    test_rows = []

    # IMPORTANT:
    # The test match may use ONLY history
    # from seasons before the test season.
    #
    # No test-season result is allowed
    # to enter its own features.

    historical_pool = list(
        train_matches
    )

    for item in sorted(
        test_matches,
        key=lambda x: x.date,
    ):

        previous = [
            x
            for x in historical_pool
            if (
                x.date
                < item.date
            )
        ]

        home_history = [
            x
            for x in previous
            if (
                x.match.home.id
                == item.match.home.id
                or
                x.match.away.id
                == item.match.home.id
            )
        ]

        away_history = [
            x
            for x in previous
            if (
                x.match.home.id
                == item.match.away.id
                or
                x.match.away.id
                == item.match.away.id
            )
        ]

        home = team_stats(
            home_history,
            item.match.home.id,
            item.date,
        )

        away = team_stats(
            away_history,
            item.match.away.id,
            item.date,
        )

        market = devig(
            item.odds.home
            if item.odds is not None
            else None,
            item.odds.draw
            if item.odds is not None
            else None,
            item.odds.away
            if item.odds is not None
            else None,
        )

        if (
            home is None
            or away is None
            or market is None
        ):
            continue

        test_rows.append(
            {
                "date": item.date,
                "win_difference":
                    home[0]
                    - away[0],
                "goal_difference":
                    home[1]
                    - away[1],
                "market_home":
                    market[0],
                "market_draw":
                    market[1],
                "market_away":
                    market[2],
                "result": {
                    "HOME": 0,
                    "DRAW": 1,
                    "AWAY": 2,
                }[item.result],
            }
        )

    print()
    print(
        "TRAIN ROWS:",
        len(train_rows),
    )

    print(
        "TEST ROWS:",
        len(test_rows),
    )

    X_train, y_train = (
        make_features(
            train_rows
        )
    )

    X_test, y_test = (
        make_features(
            test_rows
        )
    )

    beta = fit(
        X_train,
        y_train,
    )

    (
        accuracy,
        log_loss,
        brier,
        probabilities,
    ) = evaluate(
        beta,
        X_test,
        y_test,
    )

    print()
    print(
        "=================================================="
    )
    print(
        "FINAL TEST RESULTS"
    )
    print(
        "=================================================="
    )

    print(
        f"ACCURACY: {accuracy:.6f}"
    )

    print(
        f"LOG LOSS: {log_loss:.6f}"
    )

    print(
        f"BRIER: {brier:.6f}"
    )

    baseline = np.full(
        (
            len(y_test),
            3,
        ),
        1.0 / 3.0,
    )

    baseline_accuracy = (
        np.mean(
            np.argmax(
                baseline,
                axis=1,
            )
            == y_test
        )
    )

    baseline_log_loss = (
        -np.mean(
            np.log(
                baseline[
                    np.arange(
                        len(y_test)
                    ),
                    y_test,
                ]
            )
        )
    )

    actual = np.eye(3)[
        y_test
    ]

    baseline_brier = (
        np.mean(
            np.sum(
                (
                    baseline
                    - actual
                ) ** 2,
                axis=1,
            )
        )
    )

    print()
    print(
        "=================================================="
    )
    print(
        "BASELINE 33/33/33"
    )
    print(
        "=================================================="
    )

    print(
        f"ACCURACY: "
        f"{baseline_accuracy:.6f}"
    )

    print(
        f"LOG LOSS: "
        f"{baseline_log_loss:.6f}"
    )

    print(
        f"BRIER: "
        f"{baseline_brier:.6f}"
    )

    print()
    print(
        "=================================================="
    )
    print(
        "DELTA V3 - BASELINE"
    )
    print(
        "=================================================="
    )

    print(
        "ACCURACY:",
        accuracy
        - baseline_accuracy,
    )

    print(
        "LOG LOSS:",
        log_loss
        - baseline_log_loss,
    )

    print(
        "BRIER:",
        brier
        - baseline_brier,
    )

    print()
    print(
        "=================================================="
    )
    print(
        "RESULT DISTRIBUTION"
    )
    print(
        "=================================================="
    )

    predictions = np.argmax(
        probabilities,
        axis=1,
    )

    for index, name in enumerate(
        [
            "HOME",
            "DRAW",
            "AWAY",
        ]
    ):

        actual_count = int(
            np.sum(
                y_test == index
            )
        )

        predicted_count = int(
            np.sum(
                predictions == index
            )
        )

        print(
            f"{name}: "
            f"ACTUAL={actual_count} "
            f"PREDICTED={predicted_count}"
        )

    print()
    print(
        "AVG PROBABILITIES"
    )

    print(
        "HOME:",
        float(
            np.mean(
                probabilities[:, 0]
            )
        )
    )

    print(
        "DRAW:",
        float(
            np.mean(
                probabilities[:, 1]
            )
        )
    )

    print(
        "AWAY:",
        float(
            np.mean(
                probabilities[:, 2]
            )
        )
    )

    print()
    print(
        "=================================================="
    )
    print(
        "FINAL COEFFICIENTS"
    )
    print(
        "=================================================="
    )

    names = [
        "INTERCEPT",
        "RECENCY WIN_DIFF",
        "RECENCY GOAL_DIFF",
        "MARKET_HOME",
        "MARKET_DRAW",
        "MARKET_AWAY",
    ]

    for row_index, name in enumerate(
        names
    ):

        print(
            name,
            "HOME=",
            beta[
                row_index,
                0,
            ],
            "DRAW=",
            beta[
                row_index,
                1,
            ],
            "AWAY=",
            beta[
                row_index,
                2,
            ],
        )

    print()
    print(
        "RECENCY=2.0"
    )

    print(
        "MARKET INPUT=DEVIG 1X2"
    )

    print(
        "TEST SEASON=2025/26"
    )

    print(
        "COEFFICIENT FIT=2021/22-2024/25"
    )


if __name__ == "__main__":
    main()
