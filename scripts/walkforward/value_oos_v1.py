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

TRAIN_FILES = [
    "E0_2021.csv",
    "E0_2122.csv",
    "E0_2223.csv",
    "E0_2324.csv",
]

VALIDATION_FILE = "E0_2425.csv"
TEST_FILE = "E0_2025_2026.csv"

THRESHOLDS = [0.02, 0.05, 0.10]


def softmax(scores):
    scores = scores - np.max(scores, axis=1, keepdims=True)
    exp = np.exp(scores)
    return exp / exp.sum(axis=1, keepdims=True)


def fit(X, y):
    beta = np.zeros((X.shape[1], 3), dtype=float)
    Y = np.eye(3)[y]

    for _ in range(ITERATIONS):
        p = softmax(X @ beta)
        gradient = X.T @ (p - Y) / len(X)
        gradient += L2 * beta
        beta -= LEARNING_RATE * gradient

    return beta


def devig(home, draw, away):
    if home is None or draw is None or away is None:
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
        -DECAY * max(days, 0) / 365.0
    )


def stats(history, team_id, date):
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

        days = max(0, (date - item.date).days)
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
        (gf_total - ga_total) / weight_total,
    )


def make_row(item, previous):
    home_id = item.match.home.id
    away_id = item.match.away.id

    home_history = [
        x for x in previous
        if (
            x.match.home.id == home_id
            or x.match.away.id == home_id
        )
    ]

    away_history = [
        x for x in previous
        if (
            x.match.home.id == away_id
            or x.match.away.id == away_id
        )
    ]

    home = stats(
        home_history,
        home_id,
        item.date,
    )

    away = stats(
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
        "win_difference": home[0] - away[0],
        "goal_difference": home[1] - away[1],
        "market_home": market[0],
        "market_draw": market[1],
        "market_away": market[2],
        "odds_home": item.odds.home,
        "odds_draw": item.odds.draw,
        "odds_away": item.odds.away,
        "result": result,
    }


def build_rows(matches):
    completed = sorted(
        [
            x for x in matches
            if x.is_completed
        ],
        key=lambda x: x.date,
    )

    rows = []

    for index, item in enumerate(completed):
        previous = completed[:index]

        row = make_row(
            item,
            previous,
        )

        if row is not None:
            rows.append(row)

    return rows


def build_oos_rows(
    test_matches,
    historical_matches,
):
    historical = sorted(
        [
            x for x in historical_matches
            if x.is_completed
        ],
        key=lambda x: x.date,
    )

    tests = sorted(
        [
            x for x in test_matches
            if x.is_completed
        ],
        key=lambda x: x.date,
    )

    rows = []

    for item in tests:
        previous = [
            x for x in historical
            if x.date < item.date
        ]

        previous.extend(
            x for x in tests
            if x.date < item.date
        )

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
                row["win_difference"],
                row["goal_difference"],
                row["market_home"],
                row["market_draw"],
                row["market_away"],
            ]
            for row in rows
        ],
        dtype=float,
    )

    y = np.asarray(
        [
            row["result"]
            for row in rows
        ],
        dtype=int,
    )

    return X, y


def predict(beta, rows):
    X, _ = make_X_y(rows)
    return softmax(X @ beta)


def evaluate_value(
    probabilities,
    rows,
    threshold,
):
    bets = 0
    wins = 0
    profit = 0.0
    odds_total = 0.0

    for probability, row in zip(
        probabilities,
        rows,
    ):
        odds = np.asarray(
            [
                row["odds_home"],
                row["odds_draw"],
                row["odds_away"],
            ],
            dtype=float,
        )

        ev = (
            probability * odds
        ) - 1.0

        selection = int(
            np.argmax(ev)
        )

        best_ev = float(
            ev[selection]
        )

        if best_ev < threshold:
            continue

        bets += 1

        selected_odds = odds[selection]
        odds_total += selected_odds

        if selection == row["result"]:
            wins += 1
            profit += selected_odds - 1.0
        else:
            profit -= 1.0

    if bets == 0:
        return None

    return {
        "bets": bets,
        "wins": wins,
        "win_rate": wins / bets,
        "avg_odds": odds_total / bets,
        "profit": profit,
        "roi": profit / bets,
    }


def print_result(label, result):
    if result is None:
        print(f"{label:<10} NO BETS")
        return

    print(
        f"{label:<10}"
        f"BETS={result['bets']:4d} "
        f"WINS={result['wins']:4d} "
        f"WIN_RATE={result['win_rate']:.4f} "
        f"AVG_ODDS={result['avg_odds']:.3f} "
        f"PROFIT={result['profit']:.2f} "
        f"ROI={result['roi']:.4f}"
    )


def main():
    print()
    print("=" * 60)
    print("FINAL OUT-OF-SAMPLE VALUE TEST")
    print("V3 HISTORY + RECENCY(2.0) + MARKET")
    print("=" * 60)

    loader = FootballDataLoader()

    raw_dir = (
        ROOT
        / "data"
        / "football"
        / "raw"
    )

    loaded = {}

    filenames = (
        TRAIN_FILES
        + [VALIDATION_FILE, TEST_FILE]
    )

    for filename in filenames:
        matches = loader.load(
            raw_dir / filename
        )

        loaded[filename] = matches

        print(
            f"{filename}: "
            f"{len(matches)} matches"
        )

    # --------------------------------------------------
    # TRAIN: PRIME 4 STAGIONI
    # --------------------------------------------------

    train_matches = []

    for filename in TRAIN_FILES:
        train_matches.extend(
            loaded[filename]
        )

    train_rows = build_rows(
        train_matches
    )

    X_train, y_train = make_X_y(
        train_rows
    )

    beta = fit(
        X_train,
        y_train
    )

    # --------------------------------------------------
    # VALIDATION: 2024/25
    # --------------------------------------------------

    validation_rows = build_oos_rows(
        loaded[VALIDATION_FILE],
        train_matches,
    )

    validation_probabilities = predict(
        beta,
        validation_rows,
    )

    print()
    print("=" * 60)
    print("VALIDATION: 2024/25")
    print("=" * 60)

    validation_results = {}

    for threshold in THRESHOLDS:
        result = evaluate_value(
            validation_probabilities,
            validation_rows,
            threshold,
        )

        validation_results[
            threshold
        ] = result

        print_result(
            f"EV>={threshold:.0%}",
            result,
        )

    candidates = [
        (
            threshold,
            result,
        )
        for threshold, result
        in validation_results.items()
        if result is not None
    ]

    if not candidates:
        print()
        print("NO VALIDATION BETS")
        return

    selected_threshold, selected_result = max(
        candidates,
        key=lambda item: (
            item[1]["roi"],
            item[1]["bets"],
        ),
    )

    print()
    print(
        "SELECTED THRESHOLD:",
        f"EV>={selected_threshold:.0%}",
    )

    print(
        "VALIDATION ROI:",
        f"{selected_result['roi']:.6f}",
    )

    # --------------------------------------------------
    # FINAL REFIT: PRIME 5 STAGIONI
    # --------------------------------------------------

    pre_test_matches = (
        train_matches
        + loaded[VALIDATION_FILE]
    )

    final_rows = build_rows(
        pre_test_matches
    )

    X_final, y_final = make_X_y(
        final_rows
    )

    final_beta = fit(
        X_final,
        y_final
    )

    # --------------------------------------------------
    # OOS: 2025/26
    # --------------------------------------------------

    test_rows = build_oos_rows(
        loaded[TEST_FILE],
        pre_test_matches,
    )

    test_probabilities = predict(
        final_beta,
        test_rows,
    )

    print()
    print("=" * 60)
    print("FINAL OOS: 2025/26")
    print("=" * 60)

    print(
        "TEST ROWS:",
        len(test_rows),
    )

    print(
        "THRESHOLD FIXED BEFORE OOS:",
        f"EV>={selected_threshold:.0%}",
    )

    print()
    print("ALL FIXED THRESHOLDS")

    for threshold in THRESHOLDS:
        result = evaluate_value(
            test_probabilities,
            test_rows,
            threshold,
        )

        print_result(
            f"EV>={threshold:.0%}",
            result,
        )

    print()
    print("SELECTED THRESHOLD OOS")

    selected_oos = evaluate_value(
        test_probabilities,
        test_rows,
        selected_threshold,
    )

    print_result(
        f"EV>={selected_threshold:.0%}",
        selected_oos,
    )

    print()
    print("=" * 60)
    print("FINAL DECISION")
    print("=" * 60)

    if (
        selected_oos is not None
        and selected_oos["roi"] > 0.0
        and selected_oos["bets"] >= 50
    ):
        print(
            "VALUE CANDIDATE: "
            "POSITIVE OOS ROI"
        )
    else:
        print("DO NOT LOCK VALUE")

    print()
    print("RECENCY=2.0")
    print("MARKET INPUT=DEVIG 1X2")
    print("VALIDATION=E0_2425.csv")
    print("OOS TEST=E0_2025_2026.csv")
    print("THRESHOLD SELECTED BEFORE OOS=YES")


if __name__ == "__main__":
    main()
