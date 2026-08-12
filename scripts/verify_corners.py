import sys
import math
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset

EPSILON = 1e-12
PRIOR_WEIGHT = 5.0
MAX_CORNERS = 20


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def build_profile(matches):
    teams = {}
    total_h = 0.0
    total_a = 0.0
    completed = 0

    for item in matches:
        m = item.match

        if not m.is_completed:
            continue

        if m.home_corners is None or m.away_corners is None:
            continue

        h = m.home.id
        a = m.away.id

        for team in (h, a):
            teams.setdefault(team, {
                "home_for": 0.0,
                "home_against": 0.0,
                "home_matches": 0,
                "away_for": 0.0,
                "away_against": 0.0,
                "away_matches": 0,
            })

        teams[h]["home_for"] += m.home_corners
        teams[h]["home_against"] += m.away_corners
        teams[h]["home_matches"] += 1

        teams[a]["away_for"] += m.away_corners
        teams[a]["away_against"] += m.home_corners
        teams[a]["away_matches"] += 1

        total_h += m.home_corners
        total_a += m.away_corners
        completed += 1

    if completed == 0:
        return None

    return (
        teams,
        total_h / completed,
        total_a / completed,
    )


def smooth(value, matches, prior):
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

    if (
        home["home_matches"] == 0
        or away["away_matches"] == 0
    ):
        return None

    home_attack = (
        smooth(
            home["home_for"],
            home["home_matches"],
            league_home,
        )
        / max(league_home, EPSILON)
    )

    home_defence = (
        smooth(
            home["home_against"],
            home["home_matches"],
            league_away,
        )
        / max(league_away, EPSILON)
    )

    away_attack = (
        smooth(
            away["away_for"],
            away["away_matches"],
            league_away,
        )
        / max(league_away, EPSILON)
    )

    away_defence = (
        smooth(
            away["away_against"],
            away["away_matches"],
            league_home,
        )
        / max(league_home, EPSILON)
    )

    lambda_home = (
        league_home
        * home_attack
        * away_defence
    )

    lambda_away = (
        league_away
        * away_attack
        * home_defence
    )

    lambda_home = max(
        0.5,
        min(15.0, lambda_home),
    )

    lambda_away = max(
        0.5,
        min(15.0, lambda_away),
    )

    return lambda_home, lambda_away


def corner_distribution(lambda_home, lambda_away):

    matrix = []

    for hc in range(MAX_CORNERS + 1):

        ph = poisson_pmf(
            hc,
            lambda_home,
        )

        for ac in range(MAX_CORNERS + 1):

            pa = poisson_pmf(
                ac,
                lambda_away,
            )

            matrix.append(
                (
                    hc,
                    ac,
                    ph * pa,
                )
            )

    total = sum(
        p for _, _, p in matrix
    )

    return [
        (hc, ac, p / total)
        for hc, ac, p in matrix
    ]


def market_probability(matrix, line):

    return sum(
        p
        for hc, ac, p in matrix
        if hc + ac > line
    )


def brier_binary(probability, actual):

    return (
        probability
        - float(actual)
    ) ** 2


def evaluate(results, key, actual_key):

    n = len(results)

    log_loss = 0.0
    brier = 0.0
    correct = 0

    for r in results:

        p = max(
            EPSILON,
            min(1.0 - EPSILON, r[key]),
        )

        actual = r[actual_key]

        log_loss += -math.log(
            p if actual else 1.0 - p
        )

        brier += brier_binary(
            p,
            actual,
        )

        predicted = p >= 0.5

        if predicted == actual:
            correct += 1

    return (
        correct / n,
        log_loss / n,
        brier / n,
        sum(r[key] for r in results) / n,
        sum(
            float(r[actual_key])
            for r in results
        ) / n,
    )


def main():

    raw_dir = Path(
        "data/football/raw"
    )

    files = sorted(
        raw_dir.glob("E0_*.csv")
    )

    loader = FootballDataLoader()

    all_matches = []

    for f in files:
        all_matches.extend(
            loader.load(f)
        )

    dataset = FootballHistoricalDataset(
        all_matches
    )

    completed = [
        x for x in dataset.all()
        if (
            x.is_completed
            and x.match.home_corners is not None
            and x.match.away_corners is not None
        )
    ]

    completed.sort(
        key=lambda x: x.date
    )

    split = int(
        len(completed) * 0.70
    )

    train = completed[:split]
    test = completed[split:]

    print(
        "TOTAL CORNER MATCHES:",
        len(completed),
    )

    print(
        "TRAIN:",
        len(train),
    )

    print(
        "TEST:",
        len(test),
    )

    results = []

    for item in test:

        historical = [
            x
            for x in completed
            if x.date < item.date
        ]

        profile = build_profile(
            historical
        )

        if profile is None:
            continue

        prediction = predict(
            item.home_team_id,
            item.away_team_id,
            profile,
        )

        if prediction is None:
            continue

        lambda_home, lambda_away = (
            prediction
        )

        matrix = corner_distribution(
            lambda_home,
            lambda_away,
        )

        total_corners = (
            item.match.home_corners
            + item.match.away_corners
        )

        results.append({
            "o7_5": market_probability(
                matrix,
                7.5,
            ),

            "o8_5": market_probability(
                matrix,
                8.5,
            ),

            "o9_5": market_probability(
                matrix,
                9.5,
            ),

            "o10_5": market_probability(
                matrix,
                10.5,
            ),

            "total": total_corners,

            "lambda_home": lambda_home,
            "lambda_away": lambda_away,
        })

    print()

    print("# CORNER MARKETS")

    for label, key, line in [
        ("OVER 7.5", "o7_5", 7.5),
        ("OVER 8.5", "o8_5", 8.5),
        ("OVER 9.5", "o9_5", 9.5),
        ("OVER 10.5", "o10_5", 10.5),
    ]:

        actual_key = f"actual_{key}"

        for r in results:
            r[actual_key] = (
                r["total"] > line
            )

        acc, ll, br, pred, actual = (
            evaluate(
                results,
                key,
                actual_key,
            )
        )

        print(
            f"{label:10s}"
            f" ACC={acc:.6f}"
            f" LOGLOSS={ll:.6f}"
            f" BRIER={br:.6f}"
            f" P={pred:.4f}"
            f" ACTUAL={actual:.4f}"
        )

    print()

    print("# LAMBDA")

    print(
        "HOME AVG:",
        sum(
            r["lambda_home"]
            for r in results
        ) / len(results),
    )

    print(
        "AWAY AVG:",
        sum(
            r["lambda_away"]
            for r in results
        ) / len(results),
    )

    print(
        "TOTAL AVG:",
        sum(
            r["lambda_home"]
            + r["lambda_away"]
            for r in results
        ) / len(results),
    )


if __name__ == "__main__":
    main()
