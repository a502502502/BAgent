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


def avg(values):
    return sum(values) / len(values) if values else None


def build_profile(history):
    teams = {}

    for item in history:
        m = item.match

        if not m.is_completed:
            continue

        if (
            m.home_yellow_cards is None
            or m.away_yellow_cards is None
        ):
            continue

        for team in (m.home.id, m.away.id):
            teams.setdefault(team, {
                "hf": [],
                "ha": [],
                "af": [],
                "aa": [],
            })

        h = teams[m.home.id]
        a = teams[m.away.id]

        h["hf"].append(m.home_yellow_cards)
        h["ha"].append(m.away_yellow_cards)

        a["af"].append(m.away_yellow_cards)
        a["aa"].append(m.home_yellow_cards)

    return teams


def predict(home_id, away_id, teams):

    if home_id not in teams or away_id not in teams:
        return None

    h = teams[home_id]
    a = teams[away_id]

    if not h["hf"] or not a["af"]:
        return None

    home_for = avg(h["hf"])
    home_against = avg(h["ha"])

    away_for = avg(a["af"])
    away_against = avg(a["aa"])

    league_home = avg([
        x
        for t in teams.values()
        for x in t["hf"]
    ])

    league_away = avg([
        x
        for t in teams.values()
        for x in t["af"]
    ])

    if league_home is None or league_away is None:
        return None

    lambda_home = (
        league_home
        * home_for / league_home
        * away_against / league_away
    )

    lambda_away = (
        league_away
        * away_for / league_away
        * home_against / league_home
    )

    return (
        max(0.1, min(8.0, lambda_home)),
        max(0.1, min(8.0, lambda_away)),
    )


def over_probability(lh, la, line):

    p = 0.0

    for h in range(MAX_CARDS + 1):
        ph = poisson(h, lh)

        for a in range(MAX_CARDS + 1):
            pa = poisson(a, la)

            if h + a > line:
                p += ph * pa

    return p


def evaluate(rows, key, line):

    n = len(rows)

    ll = 0.0
    brier = 0.0
    correct = 0

    for r in rows:

        p = max(
            EPS,
            min(1.0 - EPS, r[key]),
        )

        actual = r["total"] > line

        ll += -math.log(
            p if actual else 1.0 - p
        )

        brier += (
            p - float(actual)
        ) ** 2

        if (p >= 0.5) == actual:
            correct += 1

    return (
        correct / n,
        ll / n,
        brier / n,
        sum(r[key] for r in rows) / n,
        sum(
            float(r["total"] > line)
            for r in rows
        ) / n,
    )


def main():

    loader = FootballDataLoader()

    matches = []

    for f in sorted(
        Path("data/football/raw").glob("E0_*.csv")
    ):
        matches.extend(loader.load(f))

    dataset = FootballHistoricalDataset(matches)

    all_matches = [
        x for x in dataset.all()
        if (
            x.is_completed
            and x.match.home_yellow_cards is not None
            and x.match.away_yellow_cards is not None
        )
    ]

    all_matches.sort(
        key=lambda x: x.date
    )

    split = int(len(all_matches) * 0.70)

    test = all_matches[split:]

    print("TOTAL CARD MATCHES:", len(all_matches))
    print("TRAIN:", split)
    print("TEST:", len(test))

    results = []

    for item in test:

        history = [
            x for x in all_matches
            if x.date < item.date
        ]

        teams = build_profile(history)

        prediction = predict(
            item.home_team_id,
            item.away_team_id,
            teams,
        )

        if prediction is None:
            continue

        lh, la = prediction

        total = (
            item.match.home_yellow_cards
            + item.match.away_yellow_cards
        )

        results.append({
            "total": total,
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
            "lh": lh,
            "la": la,
        })

    print()
    print("# CARD MARKETS")

    for label, key, line in [
        ("OVER 2.5", "o2_5", 2.5),
        ("OVER 3.5", "o3_5", 3.5),
        ("OVER 4.5", "o4_5", 4.5),
        ("OVER 5.5", "o5_5", 5.5),
    ]:

        acc, ll, br, p, actual = evaluate(
            results,
            key,
            line,
        )

        print(
            f"{label:10s}"
            f" ACC={acc:.6f}"
            f" LOGLOSS={ll:.6f}"
            f" BRIER={br:.6f}"
            f" P={p:.4f}"
            f" ACTUAL={actual:.4f}"
        )

    print()
    print("# LAMBDA")

    print(
        "HOME AVG:",
        sum(r["lh"] for r in results)
        / len(results),
    )

    print(
        "AWAY AVG:",
        sum(r["la"] for r in results)
        / len(results),
    )

    print(
        "TOTAL AVG:",
        sum(
            r["lh"] + r["la"]
            for r in results
        ) / len(results),
    )


if __name__ == "__main__":
    main()
