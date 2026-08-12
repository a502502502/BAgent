import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset

EPS = 1e-12
MAX_CARDS = 15


def poisson(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)


def weighted_avg(values, dates, target, decay):
    weights = [
        math.exp(
            -decay * max(0, (target - d).days) / 365.0
        )
        for d in dates
    ]

    total = sum(weights)

    if total <= 0:
        return sum(values) / len(values)

    return sum(
        v * w for v, w in zip(values, weights)
    ) / total


def predict(home_id, away_id, history, target, decay):

    home_for = []
    home_against = []
    away_for = []
    away_against = []

    league_home = []
    league_away = []

    for item in history:

        m = item.match

        if not m.is_completed:
            continue

        if (
            m.home_yellow_cards is None
            or m.away_yellow_cards is None
        ):
            continue

        league_home.append(m.home_yellow_cards)
        league_away.append(m.away_yellow_cards)

        if m.home.id == home_id:
            home_for.append(
                (m.home_yellow_cards, item.date)
            )
            home_against.append(
                (m.away_yellow_cards, item.date)
            )

        if m.away.id == away_id:
            away_for.append(
                (m.away_yellow_cards, item.date)
            )
            away_against.append(
                (m.home_yellow_cards, item.date)
            )

    if not home_for or not away_for:
        return None

    lh_league = sum(league_home) / len(league_home)
    la_league = sum(league_away) / len(league_away)

    hf = weighted_avg(
        [v for v, _ in home_for],
        [d for _, d in home_for],
        target,
        decay,
    )

    ha = weighted_avg(
        [v for v, _ in home_against],
        [d for _, d in home_against],
        target,
        decay,
    )

    af = weighted_avg(
        [v for v, _ in away_for],
        [d for _, d in away_for],
        target,
        decay,
    )

    aa = weighted_avg(
        [v for v, _ in away_against],
        [d for _, d in away_against],
        target,
        decay,
    )

    lambda_home = (
        lh_league
        * hf / max(lh_league, EPS)
        * aa / max(la_league, EPS)
    )

    lambda_away = (
        la_league
        * af / max(la_league, EPS)
        * ha / max(lh_league, EPS)
    )

    return (
        max(0.1, min(8.0, lambda_home)),
        max(0.1, min(8.0, lambda_away)),
    )


def over_probability(lh, la, line):

    result = 0.0

    for h in range(MAX_CARDS + 1):

        ph = poisson(h, lh)

        for a in range(MAX_CARDS + 1):

            pa = poisson(a, la)

            if h + a > line:
                result += ph * pa

    return result


def evaluate(rows, key, line):

    n = len(rows)

    log_loss = 0.0
    brier = 0.0
    correct = 0

    for r in rows:

        p = max(
            EPS,
            min(1.0 - EPS, r[key]),
        )

        actual = r["total"] > line

        log_loss += -math.log(
            p if actual else 1.0 - p
        )

        brier += (
            p - float(actual)
        ) ** 2

        if (p >= 0.5) == actual:
            correct += 1

    return (
        correct / n,
        log_loss / n,
        brier / n,
    )


def run(test, all_matches, decay):

    rows = []

    for item in test:

        history = [
            x
            for x in all_matches
            if x.date < item.date
        ]

        prediction = predict(
            item.home_team_id,
            item.away_team_id,
            history,
            item.date,
            decay,
        )

        if prediction is None:
            continue

        lh, la = prediction

        rows.append({
            "total": (
                item.match.home_yellow_cards
                + item.match.away_yellow_cards
            ),
            "o2_5": over_probability(
                lh, la, 2.5
            ),
            "o3_5": over_probability(
                lh, la, 3.5
            ),
            "o4_5": over_probability(
                lh, la, 4.5
            ),
            "o5_5": over_probability(
                lh, la, 5.5
            ),
        })

    return rows


def main():

    loader = FootballDataLoader()

    matches = []

    for f in sorted(
        Path("data/football/raw").glob("E0_*.csv")
    ):
        matches.extend(loader.load(f))

    dataset = FootballHistoricalDataset(matches)

    all_matches = [
        x
        for x in dataset.all()
        if (
            x.is_completed
            and x.match.home_yellow_cards is not None
            and x.match.away_yellow_cards is not None
        )
    ]

    all_matches.sort(
        key=lambda x: x.date
    )

    split = int(
        len(all_matches) * 0.70
    )

    test = all_matches[split:]

    print("TOTAL:", len(all_matches))
    print("TRAIN:", split)
    print("TEST:", len(test))

    for decay in [
        0.0,
        0.25,
        0.50,
        0.75,
        1.0,
        1.5,
        2.0,
    ]:

        rows = run(
            test,
            all_matches,
            decay,
        )

        print()
        print(f"DECAY={decay}")
        print("ROWS:", len(rows))

        for label, key, line in [
            ("O2.5", "o2_5", 2.5),
            ("O3.5", "o3_5", 3.5),
            ("O4.5", "o4_5", 4.5),
            ("O5.5", "o5_5", 5.5),
        ]:

            acc, ll, br = evaluate(
                rows,
                key,
                line,
            )

            print(
                f"{label:5s}"
                f" ACC={acc:.6f}"
                f" LL={ll:.6f}"
                f" BRIER={br:.6f}"
            )


if __name__ == "__main__":
    main()
