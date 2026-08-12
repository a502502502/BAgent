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


def lambdas(home_id, away_id, profile):
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

    lh = max(0.05, min(5.0, league_h * h_attack * a_defence))
    la = max(0.05, min(5.0, league_a * a_attack * h_defence))

    return lh, la


def dc_tau(hg, ag, lh, la, rho):
    if hg == 0 and ag == 0:
        return 1.0 - lh * la * rho

    if hg == 0 and ag == 1:
        return 1.0 + lh * rho

    if hg == 1 and ag == 0:
        return 1.0 + la * rho

    if hg == 1 and ag == 1:
        return 1.0 - rho

    return 1.0


def dc_matrix(lh, la, rho):
    rows = []

    for hg in range(MAX_GOALS + 1):
        ph = poisson_pmf(hg, lh)

        for ag in range(MAX_GOALS + 1):
            pa = poisson_pmf(ag, la)

            p = ph * pa * dc_tau(
                hg, ag, lh, la, rho
            )

            rows.append((hg, ag, max(0.0, p)))

    total = sum(p for _, _, p in rows)

    return [
        (hg, ag, p / total)
        for hg, ag, p in rows
    ]


def market_probs(matrix):
    over = {}

    for line in (0.5, 1.5, 2.5, 3.5):
        over[line] = sum(
            p for hg, ag, p in matrix
            if hg + ag > line
        )

    btts = sum(
        p for hg, ag, p in matrix
        if hg >= 1 and ag >= 1
    )

    return over, btts


def evaluate(results, key, actual):
    n = len(results)
    ll = 0.0
    br = 0.0
    correct = 0

    for r in results:
        p = max(EPSILON, min(1 - EPSILON, r[key]))
        a = actual(r)

        ll += -math.log(p if a else 1 - p)
        br += (p - float(a)) ** 2

        if (p >= 0.5) == a:
            correct += 1

    return correct / n, ll / n, br / n


def run_model(test, all_matches, rho):
    results = []

    for item in test:
        historical = [
            x for x in all_matches
            if x.date < item.date
        ]

        profile = build_profile(historical)

        if profile is None:
            continue

        ls = lambdas(
            item.home_team_id,
            item.away_team_id,
            profile,
        )

        if ls is None:
            continue

        lh, la = ls
        matrix = dc_matrix(lh, la, rho)
        over, btts = market_probs(matrix)

        total = item.match.home_goals + item.match.away_goals

        results.append({
            "o15": over[1.5],
            "o25": over[2.5],
            "o35": over[3.5],
            "btts": btts,
            "total": total,
            "btts_actual": (
                item.match.home_goals >= 1
                and item.match.away_goals >= 1
            ),
        })

    return results


def print_results(name, results):
    print()
    print(name)
    print("=" * len(name))

    markets = [
        ("OVER 1.5", "o15", lambda r: r["total"] > 1),
        ("OVER 2.5", "o25", lambda r: r["total"] > 2),
        ("OVER 3.5", "o35", lambda r: r["total"] > 3),
        ("BTTS", "btts", lambda r: r["btts_actual"]),
    ]

    for name, key, actual in markets:
        acc, ll, br = evaluate(results, key, actual)

        print(
            f"{name:10s} "
            f"ACC={acc:.6f} "
            f"LOGLOSS={ll:.6f} "
            f"BRIER={br:.6f} "
            f"P={sum(r[key] for r in results)/len(results):.4f}"
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

    # Baseline Poisson: rho = 0
    poisson = run_model(test, all_matches, 0.0)

    # Dixon-Coles V1:
    # conservative low-score correction.
    for rho in (-0.10, -0.05, 0.05, 0.10):
        dc = run_model(test, all_matches, rho)

        print_results(
            f"DIXON-COLES rho={rho:+.2f}",
            dc,
        )

    print_results(
        "POISSON BASELINE rho=0",
        poisson,
    )


if __name__ == "__main__":
    main()
