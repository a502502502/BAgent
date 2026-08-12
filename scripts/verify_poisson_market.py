import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset

EPSILON = 1e-12
PRIOR_WEIGHT = 5.0
MAX_GOALS = 10


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def build_profile(matches):
    teams = {}
    total_h = total_a = completed = 0

    for item in matches:
        m = item.match
        if not m.is_completed:
            continue

        h, a = m.home.id, m.away.id

        for team in (h, a):
            teams.setdefault(team, {
                "hf": 0.0, "ha": 0.0, "hm": 0,
                "af": 0.0, "aa": 0.0, "am": 0,
            })

        teams[h]["hf"] += m.home_goals
        teams[h]["ha"] += m.away_goals
        teams[h]["hm"] += 1

        teams[a]["af"] += m.away_goals
        teams[a]["aa"] += m.home_goals
        teams[a]["am"] += 1

        total_h += m.home_goals
        total_a += m.away_goals
        completed += 1

    if not completed:
        return None

    return teams, total_h / completed, total_a / completed


def smooth(value, matches, prior):
    return (value + PRIOR_WEIGHT * prior) / (matches + PRIOR_WEIGHT)


def historical_lambdas(home_id, away_id, profile):
    teams, league_h, league_a = profile

    if home_id not in teams or away_id not in teams:
        return None

    h = teams[home_id]
    a = teams[away_id]

    if h["hm"] == 0 or a["am"] == 0:
        return None

    h_attack = smooth(h["hf"], h["hm"], league_h) / league_h
    h_defence = smooth(h["ha"], h["hm"], league_a) / league_a
    a_attack = smooth(a["af"], a["am"], league_a) / league_a
    a_defence = smooth(a["aa"], a["am"], league_h) / league_h

    lh = league_h * h_attack * a_defence
    la = league_a * a_attack * h_defence

    return (
        max(0.05, min(5.0, lh)),
        max(0.05, min(5.0, la)),
    )


def market_probs(odds):
    if odds is None or not odds.is_1x2_available:
        return None

    ih = 1.0 / odds.home
    id_ = 1.0 / odds.draw
    ia = 1.0 / odds.away

    total = ih + id_ + ia

    return ih / total, id_ / total, ia / total


def market_adjusted_lambdas(lh, la, mh, md, ma):
    """
    Market gives relative strength information.
    We adjust the historical lambdas conservatively.

    The geometric centre is preserved so this is not allowed
    to arbitrarily inflate the total-goal expectation.
    """

    historical_home = lh / (lh + la)
    historical_away = la / (lh + la)

    market_home = mh / (mh + ma)

    # Blend historical and market relative strength.
    weight = 0.50

    blended_home = (
        (1.0 - weight) * historical_home
        + weight * market_home
    )

    blended_away = 1.0 - blended_home

    total_lambda = lh + la

    new_lh = total_lambda * blended_home
    new_la = total_lambda * blended_away

    return (
        max(0.05, min(5.0, new_lh)),
        max(0.05, min(5.0, new_la)),
    )


def goal_matrix(lh, la):
    rows = []

    for hg in range(MAX_GOALS + 1):
        ph = poisson_pmf(hg, lh)

        for ag in range(MAX_GOALS + 1):
            pa = poisson_pmf(ag, la)
            rows.append((hg, ag, ph * pa))

    total = sum(p for _, _, p in rows)

    return [
        (hg, ag, p / total)
        for hg, ag, p in rows
    ]


def markets(matrix):
    return {
        "o15": sum(
            p for h, a, p in matrix
            if h + a > 1
        ),
        "o25": sum(
            p for h, a, p in matrix
            if h + a > 2
        ),
        "o35": sum(
            p for h, a, p in matrix
            if h + a > 3
        ),
        "btts": sum(
            p for h, a, p in matrix
            if h >= 1 and a >= 1
        ),
    }


def evaluate(results, key, actual):
    n = len(results)

    ll = 0.0
    br = 0.0
    correct = 0

    for r in results:
        p = max(EPSILON, min(1.0 - EPSILON, r[key]))
        a = actual(r)

        ll += -math.log(p if a else 1.0 - p)
        br += (p - float(a)) ** 2

        if (p >= 0.5) == a:
            correct += 1

    return (
        correct / n,
        ll / n,
        br / n,
        sum(r[key] for r in results) / n,
        sum(actual(r) for r in results) / n,
    )


def run(test, all_matches, use_market):
    results = []

    for item in test:
        historical = [
            x for x in all_matches
            if x.date < item.date
        ]

        profile = build_profile(historical)

        if profile is None:
            continue

        lambdas = historical_lambdas(
            item.home_team_id,
            item.away_team_id,
            profile,
        )

        if lambdas is None:
            continue

        lh, la = lambdas

        if use_market:
            mp = market_probs(item.odds)

            if mp is None:
                continue

            mh, md, ma = mp

            lh, la = market_adjusted_lambdas(
                lh, la, mh, md, ma
            )

        matrix = goal_matrix(lh, la)
        m = markets(matrix)

        total = (
            item.match.home_goals
            + item.match.away_goals
        )

        results.append({
            **m,
            "total": total,
            "btts_actual": (
                item.match.home_goals >= 1
                and item.match.away_goals >= 1
            ),
        })

    return results


def report(name, results):
    print()
    print(name)
    print("=" * len(name))

    for label, key, actual in [
        ("OVER 1.5", "o15", lambda r: r["total"] > 1),
        ("OVER 2.5", "o25", lambda r: r["total"] > 2),
        ("OVER 3.5", "o35", lambda r: r["total"] > 3),
        ("BTTS", "btts", lambda r: r["btts_actual"]),
    ]:
        acc, ll, br, avg, real = evaluate(
            results,
            key,
            actual,
        )

        print(
            f"{label:10s} "
            f"ACC={acc:.6f} "
            f"LOGLOSS={ll:.6f} "
            f"BRIER={br:.6f} "
            f"P={avg:.4f} "
            f"ACTUAL={real:.4f}"
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

    historical = run(
        test,
        all_matches,
        use_market=False,
    )

    market = run(
        test,
        all_matches,
        use_market=True,
    )

    report(
        "POISSON HISTORY ONLY",
        historical,
    )

    report(
        "POISSON + MARKET",
        market,
    )

    print()
    print("DELTA MARKET - HISTORY")

    for label, key, actual in [
        ("OVER 1.5", "o15", lambda r: r["total"] > 1),
        ("OVER 2.5", "o25", lambda r: r["total"] > 2),
        ("OVER 3.5", "o35", lambda r: r["total"] > 3),
        ("BTTS", "btts", lambda r: r["btts_actual"]),
    ]:
        h = evaluate(historical, key, actual)
        m = evaluate(market, key, actual)

        print(
            f"{label:10s} "
            f"LL={m[1]-h[1]:+.6f} "
            f"BRIER={m[2]-h[2]:+.6f}"
        )


if __name__ == "__main__":
    main()
