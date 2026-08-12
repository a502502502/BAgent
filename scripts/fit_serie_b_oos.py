import sys
from pathlib import Path
import math
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset


DECAY = 2.0
ITERATIONS = 8000
LEARNING_RATE = 0.03
L2 = 0.001


def softmax(scores):
    scores = scores - np.max(scores, axis=1, keepdims=True)
    exp = np.exp(scores)
    return exp / exp.sum(axis=1, keepdims=True)


def fit(X, y, iterations=ITERATIONS, learning_rate=LEARNING_RATE, l2=L2):
    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]

    for _ in range(iterations):
        p = softmax(X @ beta)

        gradient = (
            X.T @ (p - Y) / len(X)
        )

        gradient += l2 * beta

        beta -= learning_rate * gradient

    return beta


def metrics(X, y, beta):
    p = softmax(X @ beta)

    predicted = np.argmax(p, axis=1)

    accuracy = np.mean(
        predicted == y
    )

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


def devig(home, draw, away):
    if (
        home is None
        or draw is None
        or away is None
    ):
        return None

    if min(home, draw, away) <= 1.0:
        return None

    ih = 1.0 / home
    id_ = 1.0 / draw
    ia = 1.0 / away

    total = ih + id_ + ia

    return (
        ih / total,
        id_ / total,
        ia / total,
    )


def decay_weight(days):
    return math.exp(
        -DECAY * days / 365.0
    )


def team_stats(history, team_id, date):
    wins = 0.0
    goals_for = 0.0
    goals_against = 0.0
    weight_total = 0.0

    for item in history:

        if not item.is_completed:
            continue

        if (
            item.match.home_goals is None
            or item.match.away_goals is None
        ):
            continue

        days = max(
            0,
            (date - item.date).days,
        )

        weight = decay_weight(days)

        if item.match.home.id == team_id:
            gf = item.match.home_goals
            ga = item.match.away_goals

        elif item.match.away.id == team_id:
            gf = item.match.away_goals
            ga = item.match.home_goals

        else:
            continue

        if gf > ga:
            wins += weight

        goals_for += weight * gf
        goals_against += weight * ga
        weight_total += weight

    if weight_total <= 0:
        return None

    win_rate = (
        wins / weight_total
    )

    goal_difference = (
        goals_for - goals_against
    ) / weight_total

    return (
        win_rate,
        goal_difference,
    )


def load_matches():
    raw_dir = Path(
        "data/football/raw"
    )

    files = sorted(
        (raw_dir / "serie_b").glob("BRB_*.csv")
    )

    loader = FootballDataLoader()

    all_matches = []

    for file in files:
        all_matches.extend(
            loader.load(file)
        )

    dataset = FootballHistoricalDataset(
        all_matches
    )

    return [
        item
        for item in dataset.all()
        if item.is_completed
    ]


def build_rows():
    completed = load_matches()

    rows = []

    for i, item in enumerate(completed):

        previous = completed[:i]

        home_id = (
            item.match.home.id
        )

        away_id = (
            item.match.away.id
        )

        home_history = [
            x
            for x in previous
            if (
                x.match.home.id == home_id
                or
                x.match.away.id == home_id
            )
        ]

        away_history = [
            x
            for x in previous
            if (
                x.match.home.id == away_id
                or
                x.match.away.id == away_id
            )
        ]

        home_stats = team_stats(
            home_history,
            home_id,
            item.date,
        )

        away_stats = team_stats(
            away_history,
            away_id,
            item.date,
        )

        if (
            home_stats is None
            or away_stats is None
        ):
            continue

        odds = devig(
            item.odds.home,
            item.odds.draw,
            item.odds.away,
        )

        if odds is None:
            continue

        win_difference = (
            home_stats[0]
            - away_stats[0]
        )

        goal_difference = (
            home_stats[1]
            - away_stats[1]
        )

        result = {
            "HOME": 0,
            "DRAW": 1,
            "AWAY": 2,
        }[item.result]

        rows.append(
            (
                item.date,
                win_difference,
                goal_difference,
                odds[0],
                odds[1],
                odds[2],
                result,
            )
        )

    rows.sort(
        key=lambda row: row[0]
    )

    return rows


def make_features(rows):
    X = []
    y = []

    for (
        date,
        win_difference,
        goal_difference,
        market_home,
        market_draw,
        market_away,
        result,
    ) in rows:

        X.append(
            [
                1.0,
                win_difference,
                goal_difference,
                market_home,
                market_draw,
                market_away,
            ]
        )

        y.append(result)

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

    rows = build_rows()

    print()
    print(
        "=== S?RIE B V3 FINAL OOS: HISTORY + RECENCY + MARKET ==="
    )
    print(
        "RECENCY DECAY:",
        DECAY,
    )
    print(
        "TOTAL ROWS:",
        len(rows),
    )

    if len(rows) < 100:
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

    X_train, y_train = make_features(
        train
    )

    X_test, y_test = make_features(
        test
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
    print(
        "=== V3 TEST ==="
    )

    print(
        "ACCURACY:",
        accuracy,
    )

    print(
        "LOG LOSS:",
        log_loss,
    )

    print(
        "BRIER:",
        brier,
    )

    print()
    print(
        "ACTUAL DRAW:",
        actual_draws,
    )

    print(
        "PREDICTED DRAW:",
        predicted_draws,
    )

    print(
        "CORRECT DRAW:",
        correct_draws,
    )

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
    print(
        "=== V3 COEFFICIENTS ==="
    )

    print(
        "INTERCEPT"
    )

    print(
        "HOME =",
        beta[0, 0],
    )

    print(
        "DRAW =",
        beta[0, 1],
    )

    print(
        "AWAY =",
        beta[0, 2],
    )

    print()
    print(
        "RECENCY WIN_DIFF"
    )

    print(
        "HOME =",
        beta[1, 0],
    )

    print(
        "DRAW =",
        beta[1, 1],
    )

    print(
        "AWAY =",
        beta[1, 2],
    )

    print()
    print(
        "RECENCY GOAL_DIFF"
    )

    print(
        "HOME =",
        beta[2, 0],
    )

    print(
        "DRAW =",
        beta[2, 1],
    )

    print(
        "AWAY =",
        beta[2, 2],
    )

    print()
    print(
        "MARKET_HOME"
    )

    print(
        "HOME =",
        beta[3, 0],
    )

    print(
        "DRAW =",
        beta[3, 1],
    )

    print(
        "AWAY =",
        beta[3, 2],
    )

    print()
    print(
        "MARKET_DRAW"
    )

    print(
        "HOME =",
        beta[4, 0],
    )

    print(
        "DRAW =",
        beta[4, 1],
    )

    print(
        "AWAY =",
        beta[4, 2],
    )

    print()
    print(
        "MARKET_AWAY"
    )

    print(
        "HOME =",
        beta[5, 0],
    )

    print(
        "DRAW =",
        beta[5, 1],
    )

    print(
        "AWAY =",
        beta[5, 2],
    )

    print()
    print(
        "RECENCY=2.0"
    )

    print(
        "MARKET INPUT=DEVIG 1X2"
    )


if __name__ == "__main__":
    main()

