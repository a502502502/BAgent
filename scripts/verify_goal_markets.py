import sys
import math
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset

EPSILON = 1e-12
PRIOR_WEIGHT = 5.0
MAX_GOALS = 10


def poisson_pmf(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def build_profile(matches):
    teams = {}
    total_home = 0
    total_away = 0
    completed = 0

    for item in matches:
        m = item.match

        if not m.is_completed:
            continue

        home = m.home.id
        away = m.away.id

        teams.setdefault(home, {
            "home_for": 0.0, "home_against": 0.0,
            "home_matches": 0,
            "away_for": 0.0, "away_against": 0.0,
            "away_matches": 0,
        })

        teams.setdefault(away, {
            "home_for": 0.0, "home_against": 0.0,
            "home_matches": 0,
            "away_for": 0.0, "away_against": 0.0,
            "away_matches": 0,
        })

        teams[home]["home_for"] += m.home_goals
        teams[home]["home_against"] += m.away_goals
        teams[home]["home_matches"] += 1

        teams[away]["away_for"] += m.away_goals
        teams[away]["away_against"] += m.home_goals
        teams[away]["away_matches"] += 1

        total_home += m.home_goals
        total_away += m.away_goals
        completed += 1

    if completed == 0:
        return None

    return (
        teams,
        total_home / completed,
        total_away / completed,
    )


def smoothed(value, matches, prior):
    return (
        value + PRIOR_WEIGHT * prior
    ) / (
        matches + PRIOR_WEIGHT
    )


def predict(home_id, away_id, profile):
    teams, league_home, league_away = profile

    if home_id not in teams or away_id not in teams:
        return None

    home = teams[home_id]
    away = teams[away_id]

    if home["home_matches"] == 0 or away["away_matches"] == 0:
        return None

    home_attack = (
        smoothed(
            home["home_for"],
            home["home_matches"],
            league_home,
        ) / max(league_home, EPSILON)
    )

    home_defence = (
        smoothed(
            home["home_against"],
            home["home_matches"],
            league_away,
        ) / max(league_away, EPSILON)
    )

    away_attack = (
        smoothed(
            away["away_for"],
            away["away_matches"],
            league_away,
        ) / max(league_away, EPSILON)
    )

    away_defence = (
        smoothed(
            away["away_against"],
            away["away_matches"],
            league_home,
        ) / max(league_home, EPSILON)
    )

    lh = max(
        0.05,
        min(5.0, league_home * home_attack * away_defence),
    )

    la = max(
        0.05,
        min(5.0, league_away * away_attack * home_defence),
    )

    matrix = []

    for hg in range(MAX_GOALS + 1):
        ph = poisson_pmf(hg, lh)

        for ag in range(MAX_GOALS + 1):
            pa = poisson_pmf(ag, la)
            matrix.append((hg, ag, ph * pa))

    total = sum(p for _, _, p in matrix)

    matrix = [
        (hg, ag, p / total)
        for hg, ag, p in matrix
    ]

    return lh, la, matrix


def brier_binary(p, actual):
    return (p - (1.0 if actual else 0.0)) ** 2


def evaluate_binary(results, probability_key, actual_function):
    n = len(results)

    log_loss = 0.0
    brier = 0.0
    correct = 0

    for r in results:
        p = r[probability_key]
        actual = actual_function(r)

        p = max(EPSILON, min(1.0 - EPSILON, p))

        log_loss += -math.log(
            p if actual else 1.0 - p
        )

        brier += brier_binary(p, actual)

        predicted = p >= 0.5

        if predicted == actual:
            correct += 1

    return (
        correct / n,
        log_loss / n,
        brier / n,
    )


def main():
    matches = FootballDataLoader().load(
        "data/football/raw/E0_2025_2026.csv"
    )

    dataset = FootballHistoricalDataset(matches)

    all_matches = [
        x for x in dataset.all()
        if x.is_completed
    ]

    split = int(len(all_matches) * 0.70)

    train = all_matches[:split]
    test = all_matches[split:]

    print("TRAIN:", len(train))
    print("TEST:", len(test))

    results = []

    for item in test:

        historical = [
            x for x in all_matches
            if x.date < item.date
        ]

        profile = build_profile(historical)

        if profile is None:
            continue

        prediction = predict(
            item.home_team_id,
            item.away_team_id,
            profile,
        )

        if prediction is None:
            continue

        lh, la, matrix = prediction

        total_probs = {
            total: sum(
                p for hg, ag, p in matrix
                if hg + ag == total
            )
            for total in range(0, MAX_GOALS + 1)
        }

        over_05 = sum(
            p for hg, ag, p in matrix
            if hg + ag > 0
        )

        over_15 = sum(
            p for hg, ag, p in matrix
            if hg + ag > 1
        )

        over_25 = sum(
            p for hg, ag, p in matrix
            if hg + ag > 2
        )

        over_35 = sum(
            p for hg, ag, p in matrix
            if hg + ag > 3
        )

        btts = sum(
            p for hg, ag, p in matrix
            if hg >= 1 and ag >= 1
        )

        actual_total = (
            item.match.home_goals
            + item.match.away_goals
        )

        actual_btts = (
            item.match.home_goals >= 1
            and item.match.away_goals >= 1
        )

        results.append({
            "actual_total": actual_total,
            "actual_btts": actual_btts,

            "over_05": over_05,
            "over_15": over_15,
            "over_25": over_25,
            "over_35": over_35,
            "btts": btts,

            "lambda_home": lh,
            "lambda_away": la,

            "total_probs": total_probs,
        })

    print()
    print("GOAL DISTRIBUTION")
    print("=================")

    n = len(results)

    for total in range(0, 6):
        values = [
            r["total_probs"][total]
            for r in results
        ]

        actual_rate = sum(
            r["actual_total"] == total
            for r in results
        ) / n

        print(
            f"TOTAL={total}: "
            f"pred={sum(values)/n:.4f} "
            f"actual={actual_rate:.4f}"
        )

    actual_5_plus = sum(
        r["actual_total"] >= 5
        for r in results
    ) / n

    predicted_5_plus = sum(
        sum(
            p for total, p in r["total_probs"].items()
            if total >= 5
        )
        for r in results
    ) / n

    print(
        f"TOTAL=5+: "
        f"pred={predicted_5_plus:.4f} "
        f"actual={actual_5_plus:.4f}"
    )

    print()
    print("GOAL MARKETS")
    print("============")

    markets = [
        ("OVER 0.5", "over_05", lambda r: r["actual_total"] > 0),
        ("OVER 1.5", "over_15", lambda r: r["actual_total"] > 1),
        ("OVER 2.5", "over_25", lambda r: r["actual_total"] > 2),
        ("OVER 3.5", "over_35", lambda r: r["actual_total"] > 3),
        ("BTTS YES", "btts", lambda r: r["actual_btts"]),
    ]

    for name, key, actual_key in markets:
        acc, ll, br = evaluate_binary(
            results,
            key,
            actual_key,
        )

        avg_p = sum(
            r[key] for r in results
        ) / n

        actual_rate = sum(
            actual_key(r) for r in results
        ) / n

        print(
            f"{name:10s} "
            f"ACC={acc:.6f} "
            f"LOGLOSS={ll:.6f} "
            f"BRIER={br:.6f} "
            f"P={avg_p:.4f} "
            f"ACTUAL={actual_rate:.4f}"
        )


    print()
    print("CALIBRATION")
    print("===========")

    for name, key, actual_function in [
        ("OVER 1.5", "over_15", lambda r: r["actual_total"] > 1),
        ("OVER 2.5", "over_25", lambda r: r["actual_total"] > 2),
        ("OVER 3.5", "over_35", lambda r: r["actual_total"] > 3),
        ("BTTS", "btts", lambda r: r["actual_btts"]),
    ]:
        print()
        print(name)

        buckets = [
            (0.00, 0.20),
            (0.20, 0.40),
            (0.40, 0.50),
            (0.50, 0.60),
            (0.60, 0.80),
            (0.80, 1.01),
        ]

        for low, high in buckets:
            rows = [
                r for r in results
                if low <= r[key] < high
            ]

            if not rows:
                continue

            actual_rate = sum(
                actual_function(r)
                for r in rows
            ) / len(rows)

            predicted_rate = sum(
                r[key]
                for r in rows
            ) / len(rows)

            print(
                f"{low:.2f}-{high:.2f}: "
                f"n={len(rows):3d} "
                f"pred={predicted_rate:.4f} "
                f"actual={actual_rate:.4f}"
            )

    print()
    print("LAMBDA")
    print("======")
    print(
        "HOME AVG:",
        sum(r["lambda_home"] for r in results) / n,
    )
    print(
        "AWAY AVG:",
        sum(r["lambda_away"] for r in results) / n,
    )


if __name__ == "__main__":
    main()
