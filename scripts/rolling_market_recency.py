import sys
from pathlib import Path
import math
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset


DECAYS = [0.0, 0.5, 1.0, 1.5, 2.0]


def softmax(x):
    x = x - np.max(x, axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)


def fit(X, y, iterations=5000, lr=0.03, l2=0.001):

    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]

    for _ in range(iterations):
        p = softmax(X @ beta)
        gradient = X.T @ (p - Y) / len(X)
        gradient += l2 * beta
        beta -= lr * gradient

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
        np.sum(
            (p - actual) ** 2,
            axis=1,
        )
    )

    return acc, ll, brier


def devig(h, d, a):

    if h is None or d is None or a is None:
        return None

    if min(h, d, a) <= 1.0:
        return None

    ih = 1.0 / h
    id_ = 1.0 / d
    ia = 1.0 / a

    total = ih + id_ + ia

    return (
        ih / total,
        id_ / total,
        ia / total,
    )


def decay_weight(days, decay):

    if decay <= 0:
        return 1.0

    return math.exp(
        -decay * days / 365.0
    )


def load_rows():

    loader = FootballDataLoader()

    matches = loader.load(
        "data/football/raw/E0_2025_2026.csv"
    )

    dataset = FootballHistoricalDataset(matches)

    completed = [
        x for x in dataset.all()
        if x.is_completed
    ]

    rows = []

    for i, item in enumerate(completed):

        previous = completed[:i]

        home_history = [
            x for x in previous
            if (
                x.match.home.id == item.match.home.id
                or
                x.match.away.id == item.match.home.id
            )
        ]

        away_history = [
            x for x in previous
            if (
                x.match.home.id == item.match.away.id
                or
                x.match.away.id == item.match.away.id
            )
        ]

        market = devig(
            item.odds.home,
            item.odds.draw,
            item.odds.away,
        )

        if (
            not home_history
            or not away_history
            or market is None
        ):
            continue

        rows.append(
            {
                "date": item.date,
                "home": item.match.home.id,
                "away": item.match.away.id,
                "home_history": home_history,
                "away_history": away_history,
                "market": market,
                "result": {
                    "HOME": 0,
                    "DRAW": 1,
                    "AWAY": 2,
                }[item.result],
            }
        )

    rows.sort(key=lambda x: x["date"])

    return rows


def stats(history, team, date, decay):

    wins = 0.0
    gf_total = 0.0
    ga_total = 0.0
    weight_total = 0.0

    for item in history:

        if (
            item.match.home_goals is None
            or item.match.away_goals is None
        ):
            continue

        days = max(
            0,
            (date - item.date).days,
        )

        w = decay_weight(
            days,
            decay,
        )

        if item.match.home.id == team:
            gf = item.match.home_goals
            ga = item.match.away_goals
        else:
            gf = item.match.away_goals
            ga = item.match.home_goals

        if gf > ga:
            wins += w

        gf_total += w * gf
        ga_total += w * ga
        weight_total += w

    if weight_total <= 0:
        return None

    return (
        wins / weight_total,
        (gf_total - ga_total) / weight_total,
    )


def features(rows, decay):

    X = []
    y = []

    for row in rows:

        home = stats(
            row["home_history"],
            row["home"],
            row["date"],
            decay,
        )

        away = stats(
            row["away_history"],
            row["away"],
            row["date"],
            decay,
        )

        if home is None or away is None:
            continue

        win_diff = home[0] - away[0]
        goal_diff = home[1] - away[1]

        mh, md, ma = row["market"]

        X.append([
            1.0,
            win_diff,
            goal_diff,
            mh,
            md,
            ma,
        ])

        y.append(row["result"])

    return (
        np.asarray(X, dtype=float),
        np.asarray(y, dtype=int),
    )


def main():

    rows = load_rows()

    print()
    print("ROLLING MARKET + RECENCY TEST")
    print("TOTAL:", len(rows))

    n = len(rows)

    if n < 200:
        print("NOT ENOUGH DATA")
        return

    windows = 4
    test_size = n // 8

    all_base = []
    all_best = []

    selected = []

    for w in range(windows):

        train_end = (
            n - (windows - w) * test_size
        )

        test_end = min(
            train_end + test_size,
            n,
        )

        train = rows[:train_end]
        test = rows[train_end:test_end]

        print()
        print("=" * 50)
        print(f"WINDOW {w + 1}")
        print(
            "TRAIN:",
            len(train),
            "TEST:",
            len(test),
        )

        candidates = []

        for decay in DECAYS:

            X_train, y_train = features(
                train,
                decay,
            )

            X_test, y_test = features(
                test,
                decay,
            )

            beta = fit(
                X_train,
                y_train,
            )

            metrics = evaluate(
                beta,
                X_test,
                y_test,
            )

            candidates.append(
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

        best = min(
            candidates,
            key=lambda x: (
                x[1][1],
                x[1][2],
            ),
        )

        selected.append(best[0])
        all_best.append(best[1])

        base = next(
            x[1]
            for x in candidates
            if x[0] == 0.0
        )

        all_base.append(base)

        print()
        print(
            f"SELECTED DECAY: {best[0]:.2f}"
        )

        print(
            f"BASE     ACC={base[0]:.6f} "
            f"LL={base[1]:.6f} "
            f"BRIER={base[2]:.6f}"
        )

        print(
            f"SELECTED ACC={best[1][0]:.6f} "
            f"LL={best[1][1]:.6f} "
            f"BRIER={best[1][2]:.6f}"
        )

        print(
            f"DELTA LL={best[1][1] - base[1]:+.6f} "
            f"BRIER={best[1][2] - base[2]:+.6f}"
        )

    base_ll = np.mean(
        [x[1] for x in all_base]
    )

    base_brier = np.mean(
        [x[2] for x in all_base]
    )

    best_ll = np.mean(
        [x[1] for x in all_best]
    )

    best_brier = np.mean(
        [x[2] for x in all_best]
    )

    base_acc = np.mean(
        [x[0] for x in all_base]
    )

    best_acc = np.mean(
        [x[0] for x in all_best]
    )

    print()
    print("=" * 50)
    print("# ROLLING SUMMARY")
    print("=" * 50)

    print(
        f"BASE "
        f"ACC={base_acc:.6f} "
        f"LL={base_ll:.6f} "
        f"BRIER={base_brier:.6f}"
    )

    print(
        f"BEST "
        f"ACC={best_acc:.6f} "
        f"LL={best_ll:.6f} "
        f"BRIER={best_brier:.6f}"
    )

    print()
    print("# DELTA BEST - BASE")

    print(
        "ACCURACY:",
        best_acc - base_acc,
    )

    print(
        "LOG LOSS:",
        best_ll - base_ll,
    )

    print(
        "BRIER:",
        best_brier - base_brier,
    )

    print()
    print("# SELECTED DECAYS")

    for i, value in enumerate(selected, 1):
        print(
            f"WINDOW {i}: {value:+.2f}"
        )

    positive = sum(
        1
        for i in range(len(all_base))
        if (
            all_best[i][1]
            < all_base[i][1]
            and
            all_best[i][2]
            < all_base[i][2]
        )
    )

    print()
    print(
        "WINDOWS IMPROVED:",
        positive,
        "/",
        windows,
    )

    if (
        positive >= 3
        and best_ll < base_ll
        and best_brier < base_brier
    ):
        print()
        print(
            "DECISION: LOCK MARKET + RECENCY"
        )
    else:
        print()
        print(
            "DECISION: DO NOT LOCK YET"
        )


if __name__ == "__main__":
    main()
