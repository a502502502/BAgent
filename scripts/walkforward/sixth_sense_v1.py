import sys
from pathlib import Path
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from services.football_data_loader import FootballDataLoader


DECAY = 2.0

ITERATIONS = 8000
LEARNING_RATE = 0.03
L2 = 0.001

TRAIN_SEASONS = [
    "E0_2021.csv",
    "E0_2122.csv",
    "E0_2223.csv",
    "E0_2324.csv",
]

VALIDATION_SEASON = "E0_2425.csv"
TEST_SEASON = "E0_2025_2026.csv"

THRESHOLDS = [
    0.00,
    0.02,
    0.04,
    0.06,
    0.08,
    0.10,
    0.12,
    0.15,
    0.20,
]


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
        p = softmax(X @ beta)

        gradient = (
            X.T @ (p - Y)
            / len(X)
        )

        gradient += L2 * beta

        beta -= (
            LEARNING_RATE
            * gradient
        )

    return beta


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
        -DECAY
        * max(days, 0)
        / 365.0
    )


def team_stats(
    history,
    team_id,
    date,
):
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

        days = (
            date - item.date
        ).days

        weight = decay_weight(days)

        if item.match.home.id == team_id:
            gf = item.match.home_goals
            ga = item.match.away_goals
        else:
            gf = item.match.away_goals
            ga = item.match.home_goals

        if gf > ga:
            wins += weight

        gf_total += weight * gf
        ga_total += weight * ga
        weight_total += weight

    if weight_total <= 0:
        return None

    return (
        wins / weight_total,
        (gf_total - ga_total)
        / weight_total,
    )


def make_row(item, previous):
    home_id = item.match.home.id
    away_id = item.match.away.id

    home_history = [
        x
        for x in previous
        if (
            x.match.home.id == home_id
            or x.match.away.id == home_id
        )
    ]

    away_history = [
        x
        for x in previous
        if (
            x.match.home.id == away_id
            or x.match.away.id == away_id
        )
    ]

    home = team_stats(
        home_history,
        home_id,
        item.date,
    )

    away = team_stats(
        away_history,
        away_id,
        item.date,
    )

    if home is None or away is None:
        return None

    if item.odds is None:
        return None

    market = devig(
        item.odds.home,
        item.odds.draw,
        item.odds.away,
    )

    if market is None:
        return None

    result = {
        "HOME": 0,
        "DRAW": 1,
        "AWAY": 2,
    }.get(item.result)

    if result is None:
        return None

    return {
        "date": item.date,
        "win_difference":
            home[0] - away[0],
        "goal_difference":
            home[1] - away[1],
        "market_home": market[0],
        "market_draw": market[1],
        "market_away": market[2],
        "result": result,
    }


def build_season_rows(
    matches,
    history_pool=None,
):
    completed = [
        x
        for x in matches
        if x.is_completed
    ]

    completed.sort(
        key=lambda x: x.date
    )

    if history_pool is None:
        history_pool = []

    rows = []

    for item in completed:
        previous = [
            x
            for x in history_pool
            if x.date < item.date
        ]

        previous += [
            x
            for x in completed
            if x.date < item.date
        ]

        row = make_row(
            item,
            previous,
        )

        if row is not None:
            rows.append(row)

    return rows


def make_X_y(rows):
    X = np.asarray(
        [
            [
                1.0,
                r["win_difference"],
                r["goal_difference"],
                r["market_home"],
                r["market_draw"],
                r["market_away"],
            ]
            for r in rows
        ],
        dtype=float,
    )

    y = np.asarray(
        [
            r["result"]
            for r in rows
        ],
        dtype=int,
    )

    return X, y


def metrics(probabilities, y, mask=None):
    if mask is not None:
        probabilities = probabilities[mask]
        y = y[mask]

    if len(y) == 0:
        return None

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
        len(y),
        accuracy,
        log_loss,
        brier,
    )


def sense_score(
    probabilities,
    market,
):
    return float(
        np.max(
            np.abs(
                probabilities
                - market
            )
        )
    )


def main():

    print()
    print("=" * 60)
    print(
        "SIXTH SENSE V1"
    )
    print(
        "MODEL / MARKET CONFLICT FILTER"
    )
    print("=" * 60)

    loader = FootballDataLoader()

    raw_dir = (
        ROOT
        / "data"
        / "football"
        / "raw"
    )

    train_matches = []

    for filename in TRAIN_SEASONS:
        path = raw_dir / filename

        matches = loader.load(path)

        print(
            f"{filename}: "
            f"{len(matches)} matches"
        )

        train_matches.extend(matches)

    validation_matches = loader.load(
        raw_dir / VALIDATION_SEASON
    )

    test_matches = loader.load(
        raw_dir / TEST_SEASON
    )

    print(
        f"{VALIDATION_SEASON}: "
        f"{len(validation_matches)} matches"
    )

    print(
        f"{TEST_SEASON}: "
        f"{len(test_matches)} matches"
    )

    # --------------------------------------------------
    # TRAIN
    # --------------------------------------------------

    train_rows = build_season_rows(
        train_matches
    )

    X_train, y_train = make_X_y(
        train_rows
    )

    beta = fit(
        X_train,
        y_train,
    )

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    validation_rows = []

    historical_pool = list(
        train_matches
    )

    for item in sorted(
        validation_matches,
        key=lambda x: x.date,
    ):
        previous = [
            x
            for x in historical_pool
            if x.date < item.date
        ]

        row = make_row(
            item,
            previous,
        )

        if row is not None:
            validation_rows.append(row)

    X_validation, y_validation = make_X_y(
        validation_rows
    )

    validation_probabilities = softmax(
        X_validation @ beta
    )

    validation_market = np.asarray(
        [
            [
                r["market_home"],
                r["market_draw"],
                r["market_away"],
            ]
            for r in validation_rows
        ],
        dtype=float,
    )

    validation_sense = np.asarray(
        [
            sense_score(
                validation_probabilities[i],
                validation_market[i],
            )
            for i in range(
                len(validation_rows)
            )
        ],
        dtype=float,
    )

    print()
    print("=" * 60)
    print(
        "VALIDATION SEARCH"
    )
    print("=" * 60)

    candidates = []

    for threshold in THRESHOLDS:

        mask = (
            validation_sense
            <= threshold
        )

        result = metrics(
            validation_probabilities,
            y_validation,
            mask,
        )

        if result is None:
            continue

        count, acc, ll, brier = result

        coverage = (
            count
            / len(y_validation)
        )

        candidates.append(
            (
                threshold,
                count,
                coverage,
                acc,
                ll,
                brier,
            )
        )

        print(
            f"THRESHOLD={threshold:.2f} "
            f"MATCHES={count} "
            f"COVERAGE={coverage:.3f} "
            f"ACC={acc:.6f} "
            f"LL={ll:.6f} "
            f"BRIER={brier:.6f}"
        )

    # Richiediamo almeno il 50% di coverage.
    eligible = [
        x
        for x in candidates
        if x[2] >= 0.50
    ]

    if not eligible:
        eligible = candidates

    selected = min(
        eligible,
        key=lambda x: (
            x[4],
            x[5],
            -x[2],
        ),
    )

    (
        selected_threshold,
        selected_count,
        selected_coverage,
        selected_acc,
        selected_ll,
        selected_brier,
    ) = selected

    print()
    print("=" * 60)
    print(
        "SELECTED SIXTH SENSE"
    )
    print("=" * 60)

    print(
        f"THRESHOLD="
        f"{selected_threshold:.2f}"
    )

    print(
        f"VALIDATION MATCHES="
        f"{selected_count}"
    )

    print(
        f"VALIDATION COVERAGE="
        f"{selected_coverage:.6f}"
    )

    print(
        f"VALIDATION ACC="
        f"{selected_acc:.6f}"
    )

    print(
        f"VALIDATION LL="
        f"{selected_ll:.6f}"
    )

    print(
        f"VALIDATION BRIER="
        f"{selected_brier:.6f}"
    )

    # --------------------------------------------------
    # FINAL OOS
    # --------------------------------------------------

    print()
    print("=" * 60)
    print(
        "FINAL OOS TEST"
    )
    print("=" * 60)

    final_train_rows = build_season_rows(
        train_matches
    )

    X_final_train, y_final_train = make_X_y(
        final_train_rows
    )

    final_beta = fit(
        X_final_train,
        y_final_train,
    )

    test_rows = []

    for item in sorted(
        test_matches,
        key=lambda x: x.date,
    ):

        previous = [
            x
            for x in train_matches
            if x.date < item.date
        ]

        row = make_row(
            item,
            previous,
        )

        if row is not None:
            test_rows.append(row)

    X_test, y_test = make_X_y(
        test_rows
    )

    test_probabilities = softmax(
        X_test @ final_beta
    )

    test_market = np.asarray(
        [
            [
                r["market_home"],
                r["market_draw"],
                r["market_away"],
            ]
            for r in test_rows
        ],
        dtype=float,
    )

    test_sense = np.asarray(
        [
            sense_score(
                test_probabilities[i],
                test_market[i],
            )
            for i in range(
                len(test_rows)
            )
        ],
        dtype=float,
    )

    all_metrics = metrics(
        test_probabilities,
        y_test,
    )

    test_mask = (
        test_sense
        <= selected_threshold
    )

    filtered_metrics = metrics(
        test_probabilities,
        y_test,
        test_mask,
    )

    print(
        "TEST MATCHES:",
        len(test_rows),
    )

    print()
    print(
        "WITHOUT SIXTH SENSE"
    )

    print(
        f"MATCHES={all_metrics[0]} "
        f"ACC={all_metrics[1]:.6f} "
        f"LL={all_metrics[2]:.6f} "
        f"BRIER={all_metrics[3]:.6f}"
    )

    print()
    print(
        "WITH SIXTH SENSE"
    )

    if filtered_metrics is None:
        print(
            "NO MATCHES ACCEPTED"
        )
    else:
        print(
            f"MATCHES={filtered_metrics[0]}"
        )

        print(
            f"COVERAGE="
            f"{filtered_metrics[0] / len(y_test):.6f}"
        )

        print(
            f"ACC={filtered_metrics[1]:.6f} "
            f"LL={filtered_metrics[2]:.6f} "
            f"BRIER={filtered_metrics[3]:.6f}"
        )

    print()
    print("=" * 60)
    print(
        "SIXTH SENSE DECISION"
    )
    print("=" * 60)

    if filtered_metrics is None:
        print(
            "DO NOT LOCK"
        )
    elif (
        filtered_metrics[2]
        < all_metrics[2]
        and
        filtered_metrics[3]
        < all_metrics[3]
    ):
        print(
            "LOCK SIXTH SENSE V1"
        )
    else:
        print(
            "DO NOT LOCK"
        )

    print()
    print(
        "RECENCY=2.0"
    )

    print(
        "MARKET INPUT=DEVIG 1X2"
    )

    print(
        "VALIDATION=E0_2425.csv"
    )

    print(
        "OOS TEST=E0_2025_2026.csv"
    )

    print(
        "THRESHOLD SELECTED BEFORE OOS=YES"
    )


if __name__ == "__main__":
    main()
