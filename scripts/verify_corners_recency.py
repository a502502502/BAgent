from pathlib import Path
import sys
import math

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset

EPS = 1e-12
MAX_CORNERS = 20

def poisson(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)

def weighted_avg(values, dates, target_date, decay):
    weights = [
        math.exp(-decay * max(0.0, (target_date - d).days / 365.0))
        for d in dates
    ]
    total = sum(weights)
    if total <= 0:
        return sum(values) / len(values)
    return sum(v*w for v,w in zip(values, weights)) / total

def predict(home_id, away_id, historical, decay):
    home_for = []
    home_against = []
    away_for = []
    away_against = []

    for x in historical:
        m = x.match
        if m.home_corners is None or m.away_corners is None:
            continue

        if m.home.id == home_id:
            home_for.append((m.home_corners, x.date))
            home_against.append((m.away_corners, x.date))

        if m.away.id == away_id:
            away_for.append((m.away_corners, x.date))
            away_against.append((m.home_corners, x.date))

    if not home_for or not away_for:
        return None

    league_h_values = [
        x.match.home_corners
        for x in historical
        if x.match.home_corners is not None
    ]

    league_a_values = [
        x.match.away_corners
        for x in historical
        if x.match.away_corners is not None
    ]

    if not league_h_values or not league_a_values:
        return None

    target = historical[-1].date

    league_h = sum(league_h_values) / len(league_h_values)
    league_a = sum(league_a_values) / len(league_a_values)

    hf = weighted_avg(
        [v for v,d in home_for],
        [d for v,d in home_for],
        target,
        decay,
    )

    ha = weighted_avg(
        [v for v,d in home_against],
        [d for v,d in home_against],
        target,
        decay,
    )

    af = weighted_avg(
        [v for v,d in away_for],
        [d for v,d in away_for],
        target,
        decay,
    )

    aa = weighted_avg(
        [v for v,d in away_against],
        [d for v,d in away_against],
        target,
        decay,
    )

    lh = league_h * (hf / league_h) * (aa / league_h)
    la = league_a * (af / league_a) * (ha / league_a)

    return max(.5, min(15, lh)), max(.5, min(15, la))

def probability_over(lh, la, line):
    total = 0.0

    for h in range(MAX_CORNERS + 1):
        ph = poisson(h, lh)
        for a in range(MAX_CORNERS + 1):
            pa = poisson(a, la)
            if h + a > line:
                total += ph * pa

    return total

def evaluate(rows, key, line):
    n = len(rows)
    ll = 0
    br = 0
    correct = 0

    for r in rows:
        p = max(EPS, min(1-EPS, r[key]))
        actual = r["total"] > line

        ll += -math.log(p if actual else 1-p)
        br += (p - float(actual))**2

        if (p >= .5) == actual:
            correct += 1

    return correct/n, ll/n, br/n

def run(test, all_matches, decay):
    rows = []

    for item in test:
        historical = [
            x for x in all_matches
            if x.date < item.date
        ]

        pred = predict(
            item.home_team_id,
            item.away_team_id,
            historical,
            decay,
        )

        if pred is None:
            continue

        lh, la = pred

        rows.append({
            "total": (
                item.match.home_corners
                + item.match.away_corners
            ),
            "o7_5": probability_over(lh, la, 7.5),
            "o8_5": probability_over(lh, la, 8.5),
            "o9_5": probability_over(lh, la, 9.5),
            "o10_5": probability_over(lh, la, 10.5),
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
        x for x in dataset.all()
        if (
            x.is_completed
            and x.match.home_corners is not None
            and x.match.away_corners is not None
        )
    ]

    all_matches.sort(key=lambda x: x.date)

    split = int(len(all_matches) * .70)

    test = all_matches[split:]

    print("TOTAL:", len(all_matches))
    print("TEST:", len(test))

    for decay in [0.0, 0.25, 0.50, 0.75, 1.0, 1.5, 2.0]:

        rows = run(
            test,
            all_matches,
            decay,
        )

        print()
        print(f"DECAY={decay}")

        for label, key, line in [
            ("O7.5", "o7_5", 7.5),
            ("O8.5", "o8_5", 8.5),
            ("O9.5", "o9_5", 9.5),
            ("O10.5", "o10_5", 10.5),
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
