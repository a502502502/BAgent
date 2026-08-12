import sys
import math
from pathlib import Path

import numpy as np

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset


EPS = 1e-15

DECAYS = [
    0.0,
    0.5,
    1.0,
    1.5,
    2.0,
]


def softmax(x):

    x = x - np.max(
        x,
        axis=1,
        keepdims=True,
    )

    e = np.exp(x)

    return e / e.sum(
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
        (
            X.shape[1],
            3,
        )
    )

    Y = np.eye(3)[y]

    for _ in range(iterations):

        p = softmax(
            X @ beta
        )

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


def evaluate(
    beta,
    X,
    y,
):

    p = softmax(
        X @ beta
    )

    prediction = np.argmax(
        p,
        axis=1,
    )

    accuracy = np.mean(
        prediction == y
    )

    logloss = -np.mean(
        np.log(
            np.maximum(
                p[
                    np.arange(len(y)),
                    y,
                ],
                EPS,
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

    return (
        accuracy,
        logloss,
        brier,
    )


def decay_weight(
    days,
    decay,
):

    if decay <= 0:
        return 1.0

    return math.exp(
        -decay
        * days
        / 365.0
    )


def devig(
    home,
    draw,
    away,
):

    if (
        home is None
        or draw is None
        or away is None
    ):
        return None

    if (
        home <= 1.0
        or draw <= 1.0
        or away <= 1.0
    ):
        return None

    ih = 1.0 / home
    idraw = 1.0 / draw
    ia = 1.0 / away

    total = (
        ih
        + idraw
        + ia
    )

    return (
        ih / total,
        idraw / total,
        ia / total,
    )


def load_rows():

    loader = FootballDataLoader()

    matches = loader.load(
        "data/football/raw/E0_2025_2026.csv"
    )

    dataset = FootballHistoricalDataset(
        matches
    )

    completed = [
        item
        for item in dataset.all()
        if item.is_completed
    ]

    rows = []

    for index, item in enumerate(
        completed
    ):

        date = item.date

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

        if (
            not home_history
            or not away_history
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

        if market is None:
            continue

        rows.append(
            {
                "date": date,
                "home": item.match.home.id,
                "away": item.match.away.id,
                "home_history": home_history,
                "away_history": away_history,
                "market": market,
                "result": {
                    "HOME": 0,
                    "DRAW": 1,
                    "AWAY": 2,
                }[
                    item.result
                ],
            }
        )

    rows.sort(
        key=lambda x: x["date"]
    )

    return rows


def team_stats(
    matches,
    team,
    date,
    decay,
):

    wins = 0.0
    goals_for = 0.0
    goals_against = 0.0
    weight_total = 0.0

    for item in matches:

        if (
            item.match.home_goals
            is None
            or
            item.match.away_goals
            is None
        ):
            continue

        days = max(
            0,
            (
                date - item.date
            ).days,
        )

        weight = decay_weight(
            days,
            decay,
        )

        if (
            item.match.home.id
            == team
        ):

            gf = (
                item.match.home_goals
            )

            ga = (
                item.match.away_goals
            )

        else:

            gf = (
                item.match.away_goals
            )

            ga = (
                item.match.home_goals
            )

        if gf > ga:
            win = 1.0
        else:
            win = 0.0

        wins += (
            weight * win
        )

        goals_for += (
            weight * gf
        )

        goals_against += (
            weight * ga
        )

        weight_total += weight

    if weight_total <= 0:
        return None

    win_rate = (
        wins / weight_total
    )

    goal_difference = (
        goals_for
        - goals_against
    ) / weight_total

    return (
        win_rate,
        goal_difference,
    )


def build_features(
    rows,
    decay,
    use_market,
):

    X = []
    y = []

    for row in rows:

        home = team_stats(
            row["home_history"],
            row["home"],
            row["date"],
            decay,
        )

        away = team_stats(
            row["away_history"],
            row["away"],
            row["date"],
            decay,
        )

        if (
            home is None
            or away is None
        ):
            continue

        home_win, home_goal = home
        away_win, away_goal = away

        win_difference = (
            home_win
            - away_win
        )

        goal_difference = (
            home_goal
            - away_goal
        )

        values = [
            1.0,
            win_difference,
            goal_difference,
        ]

        if use_market:

            market_home, market_draw, market_away = (
                row["market"]
            )

            values.extend(
                [
                    market_home,
                    market_draw,
                    market_away,
                ]
            )

        X.append(values)

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


def run_model(
    train,
    test,
    decay,
    use_market,
):

    X_train, y_train = (
        build_features(
            train,
            decay,
            use_market,
        )
    )

    X_test, y_test = (
        build_features(
            test,
            decay,
            use_market,
        )
    )

    if (
        len(X_train) == 0
        or len(X_test) == 0
    ):
        return None

    beta = fit(
        X_train,
        y_train,
    )

    return evaluate(
        beta,
        X_test,
        y_test,
    )


def main():

    rows = load_rows()

    print()
    print(
        "HISTORY + RECENCY + MARKET"
    )

    print(
        "TOTAL:",
        len(rows),
    )

    if len(rows) < 200:

        print(
            "NOT ENOUGH DATA"
        )

        return

    split = int(
        len(rows) * 0.70
    )

    train = rows[:split]
    test = rows[split:]

    print(
        "TRAIN:",
        len(train),
    )

    print(
        "TEST:",
        len(test),
    )

    # --------------------------------------------------
    # 1. HISTORY ONLY
    # --------------------------------------------------

    history = run_model(
        train,
        test,
        0.0,
        False,
    )

    print()
    print(
        "# HISTORY"
    )

    print(
        f"ACC={history[0]:.6f} "
        f"LL={history[1]:.6f} "
        f"BRIER={history[2]:.6f}"
    )

    # --------------------------------------------------
    # 2. MARKET ONLY
    # --------------------------------------------------

    market = run_model(
        train,
        test,
        0.0,
        True,
    )

    print()
    print(
        "# HISTORY + MARKET"
    )

    print(
        f"ACC={market[0]:.6f} "
        f"LL={market[1]:.6f} "
        f"BRIER={market[2]:.6f}"
    )

    # --------------------------------------------------
    # 3. RECENCY SEARCH
    # --------------------------------------------------

    recency_results = []

    print()
    print(
        "# RECENCY"
    )

    for decay in DECAYS:

        result = run_model(
            train,
            test,
            decay,
            False,
        )

        recency_results.append(
            (
                decay,
                result,
            )
        )

        print(
            f"DECAY={decay:.2f} "
            f"ACC={result[0]:.6f} "
            f"LL={result[1]:.6f} "
            f"BRIER={result[2]:.6f}"
        )

    recency_results.sort(
        key=lambda x: (
            x[1][1],
            x[1][2],
        )
    )

    best_decay = (
        recency_results[0][0]
    )

    best_recency = (
        recency_results[0][1]
    )

    # --------------------------------------------------
    # 4. RECENCY + MARKET
    # --------------------------------------------------

    combined_results = []

    print()
    print(
        "# RECENCY + MARKET"
    )

    for decay in DECAYS:

        result = run_model(
            train,
            test,
            decay,
            True,
        )

        combined_results.append(
            (
                decay,
                result,
            )
        )

        print(
            f"DECAY={decay:.2f} "
            f"ACC={result[0]:.6f} "
            f"LL={result[1]:.6f} "
            f"BRIER={result[2]:.6f}"
        )

    combined_results.sort(
        key=lambda x: (
            x[1][1],
            x[1][2],
        )
    )

    best_combined_decay = (
        combined_results[0][0]
    )

    best_combined = (
        combined_results[0][1]
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print()
    print(
        "=================================================="
    )

    print(
        "# SUMMARY"
    )

    print(
        "=================================================="
    )

    print(
        "HISTORY"
    )

    print(
        f"ACC={history[0]:.6f} "
        f"LL={history[1]:.6f} "
        f"BRIER={history[2]:.6f}"
    )

    print()
    print(
        "BEST RECENCY"
    )

    print(
        f"DECAY={best_decay:.2f} "
        f"ACC={best_recency[0]:.6f} "
        f"LL={best_recency[1]:.6f} "
        f"BRIER={best_recency[2]:.6f}"
    )

    print()
    print(
        "HISTORY + MARKET"
    )

    print(
        f"ACC={market[0]:.6f} "
        f"LL={market[1]:.6f} "
        f"BRIER={market[2]:.6f}"
    )

    print()
    print(
        "BEST RECENCY + MARKET"
    )

    print(
        f"DECAY={best_combined_decay:.2f} "
        f"ACC={best_combined[0]:.6f} "
        f"LL={best_combined[1]:.6f} "
        f"BRIER={best_combined[2]:.6f}"
    )

    print()
    print(
        "# DELTA BEST COMBINED VS HISTORY"
    )

    print(
        "ACC:",
        best_combined[0]
        - history[0],
    )

    print(
        "LOG LOSS:",
        best_combined[1]
        - history[1],
    )

    print(
        "BRIER:",
        best_combined[2]
        - history[2],
    )

    print()

    if (
        best_combined[1]
        < history[1]
        and
        best_combined[2]
        < history[2]
    ):

        print(
            "DECISION: COMBINED CANDIDATE"
        )

    else:

        print(
            "DECISION: COMBINED REJECTED"
        )


if __name__ == "__main__":
    main()
