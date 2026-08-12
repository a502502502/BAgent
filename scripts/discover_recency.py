import sys
from pathlib import Path
import math
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset


DECAYS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]


def softmax(x):
    x = x - np.max(x, axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)


def fit(X, y, iterations=4000, lr=0.03, l2=0.001):

    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]

    for _ in range(iterations):
        p = softmax(X @ beta)
        g = X.T @ (p - Y) / len(X)
        g += l2 * beta
        beta -= lr * g

    return beta


def evaluate(beta, X, y):

    p = softmax(X @ beta)

    pred = np.argmax(p, axis=1)

    acc = np.mean(pred == y)

    ll = -np.mean(
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

    return acc, ll, brier


def decay_weight(days, decay):

    if decay <= 0:
        return 1.0

    return math.exp(
        -decay * days / 365.0
    )


def build_rows():

    loader = FootballDataLoader()

    matches = loader.load(
        "data/football/raw/E0_2025_2026.csv"
    )

    dataset = FootballHistoricalDataset(matches)

    rows = []

    completed = []

    for item in dataset.all():

        if not item.is_completed:
            continue

        completed.append(item)

    for index, item in enumerate(completed):

        date = item.date

        prior = [
            x for x in completed[:index]
            if x.date < date
        ]

        if len(prior) < 10:
            continue

        def team_stats(team):

            team_matches = [
                x for x in prior
                if (
                    x.match.home.id == team
                    or x.match.away.id == team
                )
            ]

            if not team_matches:
                return None

            return team_matches

        home_matches = team_stats(
            item.match.home.id
        )

        away_matches = team_stats(
            item.match.away.id
        )

        if not home_matches or not away_matches:
            continue

        def weighted_stats(
            matches,
            team,
            decay,
        ):

            win = 0.0
            goals_for = 0.0
            goals_against = 0.0
            weight_total = 0.0

            for match in matches:

                days = max(
                    0.0,
                    (
                        date - match.date
                    ).days,
                )

                w = decay_weight(
                    days,
                    decay,
                )

                if match.match.home.id == team:

                    gf = match.match.home_goals
                    ga = match.match.away_goals

                else:

                    gf = match.match.away_goals
                    ga = match.match.home_goals

                if gf is None or ga is None:
                    continue

                if gf > ga:
                    win_value = 1.0
                elif gf == ga:
                    win_value = 0.0
                else:
                    win_value = 0.0

                win += w * win_value
                goals_for += w * gf
                goals_against += w * ga
                weight_total += w

            if weight_total <= 0:
                return None

            return (
                win / weight_total,
                goals_for / weight_total,
                goals_against / weight_total,
            )

        # Store the raw match context. Decay is applied later,
        # so every decay uses exactly the same observations.
        rows.append(
            {
                "date": date,
                "home": item.match.home.id,
                "away": item.match.away.id,
                "home_matches": home_matches,
                "away_matches": away_matches,
                "result": {
                    "HOME": 0,
                    "DRAW": 1,
                    "AWAY": 2,
                }[item.result],
                "weighted_stats": weighted_stats,
            }
        )

    return rows


def make_dataset(rows, decay):

    X = []
    y = []

    for row in rows:

        home = row["weighted_stats"](
            row["home_matches"],
            row["home"],
            decay,
        )

        away = row["weighted_stats"](
            row["away_matches"],
            row["away"],
            decay,
        )

        if home is None or away is None:
            continue

        home_win, home_gf, home_ga = home
        away_win, away_gf, away_ga = away

        win_diff = (
            home_win
            - away_win
        )

        goal_diff = (
            (home_gf - home_ga)
            - (away_gf - away_ga)
        )

        X.append(
            [
                1.0,
                win_diff,
                goal_diff,
            ]
        )

        y.append(
            row["result"]
        )

    return (
        np.asarray(X, dtype=float),
        np.asarray(y, dtype=int),
    )


def main():

    rows = build_rows()

    print()
    print("RECENCY / FORM DISCOVERY")
    print("TOTAL:", len(rows))

    results = []

    for decay in DECAYS:

        X, y = make_dataset(
            rows,
            decay,
        )

        split = int(
            len(X) * 0.70
        )

        train_X = X[:split]
        train_y = y[:split]

        test_X = X[split:]
        test_y = y[split:]

        beta = fit(
            train_X,
            train_y,
        )

        metrics = evaluate(
            beta,
            test_X,
            test_y,
        )

        results.append(
            (
                decay,
                metrics,
            )
        )

        print(
            f"DECAY={decay:.2f} "
            f"ACC={metrics[0]:.6f} "
            f"LL={metrics[1]:.6f} "
            f"BRIER={metrics[2]:.6f}"
        )

    results.sort(
        key=lambda x: (
            x[1][1],
            x[1][2],
        )
    )

    best_decay, best_metrics = results[0]

    base = next(
        metrics
        for decay, metrics in results
        if decay == 0.0
    )

    print()
    print("# BEST")
    print(
        "DECAY:",
        best_decay,
    )

    print(
        f"ACC={best_metrics[0]:.6f} "
        f"LL={best_metrics[1]:.6f} "
        f"BRIER={best_metrics[2]:.6f}"
    )

    print()
    print("# DELTA VS BASE")

    print(
        "ACC:",
        best_metrics[0] - base[0],
    )

    print(
        "LOG LOSS:",
        best_metrics[1] - base[1],
    )

    print(
        "BRIER:",
        best_metrics[2] - base[2],
    )

    print()

    if (
        best_metrics[1] < base[1]
        and best_metrics[2] < base[2]
    ):
        print(
            "DECISION: RECENCY CANDIDATE"
        )
    else:
        print(
            "DECISION: RECENCY REJECTED"
        )


if __name__ == "__main__":
    main()
