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
    total_home_goals = 0
    total_away_goals = 0
    completed = 0

    for item in matches:

        match = item.match

        if not match.is_completed:
            continue

        home = match.home.id
        away = match.away.id

        if home not in teams:
            teams[home] = {
                "home_for": 0.0,
                "home_against": 0.0,
                "home_matches": 0,
                "away_for": 0.0,
                "away_against": 0.0,
                "away_matches": 0,
            }

        if away not in teams:
            teams[away] = {
                "home_for": 0.0,
                "home_against": 0.0,
                "home_matches": 0,
                "away_for": 0.0,
                "away_against": 0.0,
                "away_matches": 0,
            }

        teams[home]["home_for"] += match.home_goals
        teams[home]["home_against"] += match.away_goals
        teams[home]["home_matches"] += 1

        teams[away]["away_for"] += match.away_goals
        teams[away]["away_against"] += match.home_goals
        teams[away]["away_matches"] += 1

        total_home_goals += match.home_goals
        total_away_goals += match.away_goals
        completed += 1

    if completed == 0:
        return None

    league_home = total_home_goals / completed
    league_away = total_away_goals / completed

    return teams, league_home, league_away


def smoothed(value, matches, prior):
    return (
        value + PRIOR_WEIGHT * prior
    ) / (
        matches + PRIOR_WEIGHT
    )


def predict(
    home_id,
    away_id,
    profile,
):
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
        smoothed(
            home["home_for"],
            home["home_matches"],
            league_home,
        )
        / max(league_home, EPSILON)
    )

    home_defence = (
        smoothed(
            home["home_against"],
            home["home_matches"],
            league_away,
        )
        / max(league_away, EPSILON)
    )

    away_attack = (
        smoothed(
            away["away_for"],
            away["away_matches"],
            league_away,
        )
        / max(league_away, EPSILON)
    )

    away_defence = (
        smoothed(
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

    lambda_home = max(0.05, min(5.0, lambda_home))
    lambda_away = max(0.05, min(5.0, lambda_away))

    home_probability = 0.0
    draw_probability = 0.0
    away_probability = 0.0

    for hg in range(MAX_GOALS + 1):
        ph = poisson_pmf(hg, lambda_home)

        for ag in range(MAX_GOALS + 1):
            pa = poisson_pmf(ag, lambda_away)
            probability = ph * pa

            if hg > ag:
                home_probability += probability
            elif hg == ag:
                draw_probability += probability
            else:
                away_probability += probability

    total = (
        home_probability
        + draw_probability
        + away_probability
    )

    return (
        home_probability / total,
        draw_probability / total,
        away_probability / total,
        lambda_home,
        lambda_away,
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

        # Only matches before the prediction date.
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

        home_p, draw_p, away_p, lh, la = prediction

        probabilities = {
            "HOME": home_p,
            "DRAW": draw_p,
            "AWAY": away_p,
        }

        predicted = max(
            probabilities,
            key=probabilities.get,
        )

        actual = item.result

        log_loss = -math.log(
            max(
                EPSILON,
                probabilities[actual],
            )
        )

        brier = (
            (home_p - (1.0 if actual == "HOME" else 0.0)) ** 2
            + (draw_p - (1.0 if actual == "DRAW" else 0.0)) ** 2
            + (away_p - (1.0 if actual == "AWAY" else 0.0)) ** 2
        )

        results.append(
            (
                actual,
                predicted,
                home_p,
                draw_p,
                away_p,
                log_loss,
                brier,
                lh,
                la,
            )
        )

    if not results:
        print("NO RESULTS")
        return

    accuracy = sum(
        x[0] == x[1]
        for x in results
    ) / len(results)

    log_loss = sum(
        x[5] for x in results
    ) / len(results)

    brier = sum(
        x[6] for x in results
    ) / len(results)

    predicted_counter = Counter(
        x[1] for x in results
    )

    actual_counter = Counter(
        x[0] for x in results
    )

    draw_rows = [
        x for x in results
        if x[0] == "DRAW"
    ]

    draw_predicted = sum(
        x[1] == "DRAW"
        for x in results
    )

    draw_correct = sum(
        x[0] == "DRAW"
        and x[1] == "DRAW"
        for x in results
    )

    print()
    print("POISSON V2")
    print("Predictions:", len(results))
    print("Accuracy:", accuracy)
    print("Log loss:", log_loss)
    print("Brier:", brier)

    print()
    print("ACTUAL:", actual_counter)
    print("PREDICTED:", predicted_counter)

    print()
    print("DRAW PREDICTED:", draw_predicted)
    print("DRAW CORRECT:", draw_correct)

    print()
    print(
        "AVG DRAW PROB:",
        sum(x[3] for x in results) / len(results),
    )

    if draw_rows:
        print(
            "AVG DRAW PROB | REAL DRAW:",
            sum(x[3] for x in draw_rows)
            / len(draw_rows),
        )

    print()
    print("LAMBDA HOME AVG:",
          sum(x[7] for x in results) / len(results))

    print("LAMBDA AWAY AVG:",
          sum(x[8] for x in results) / len(results))


if __name__ == "__main__":
    main()
