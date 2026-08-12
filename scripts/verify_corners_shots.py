import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset


EPS = 1e-12
MAX_CORNERS = 20


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def avg(values):
    return sum(values) / len(values) if values else None


def build_team_profile(history):
    teams = {}

    for item in history:
        m = item.match

        if not m.is_completed:
            continue

        if (
            m.home_corners is None
            or m.away_corners is None
        ):
            continue

        for team in (m.home.id, m.away.id):
            teams.setdefault(team, {
                "home_corners_for": [],
                "home_corners_against": [],
                "away_corners_for": [],
                "away_corners_against": [],
                "home_shots_for": [],
                "home_shots_against": [],
                "away_shots_for": [],
                "away_shots_against": [],
                "home_sot_for": [],
                "home_sot_against": [],
                "away_sot_for": [],
                "away_sot_against": [],
            })

        h = teams[m.home.id]
        a = teams[m.away.id]

        h["home_corners_for"].append(m.home_corners)
        h["home_corners_against"].append(m.away_corners)

        a["away_corners_for"].append(m.away_corners)
        a["away_corners_against"].append(m.home_corners)

        if (
            item.statistics is not None
            and m.home_corners is not None
        ):
            s = item.statistics

            if (
                s.home_shots is not None
                and s.away_shots is not None
            ):
                h["home_shots_for"].append(s.home_shots)
                h["home_shots_against"].append(s.away_shots)

                a["away_shots_for"].append(s.away_shots)
                a["away_shots_against"].append(s.home_shots)

            if (
                s.home_shots_on_target is not None
                and s.away_shots_on_target is not None
            ):
                h["home_sot_for"].append(
                    s.home_shots_on_target
                )
                h["home_sot_against"].append(
                    s.away_shots_on_target
                )

                a["away_sot_for"].append(
                    s.away_shots_on_target
                )
                a["away_sot_against"].append(
                    s.home_shots_on_target
                )

    return teams


def league_averages(history):
    corner_h = []
    corner_a = []
    shots_h = []
    shots_a = []
    sot_h = []
    sot_a = []

    for item in history:
        m = item.match

        if not m.is_completed:
            continue

        if (
            m.home_corners is None
            or m.away_corners is None
        ):
            continue

        corner_h.append(m.home_corners)
        corner_a.append(m.away_corners)

        s = item.statistics

        if s is not None:
            if (
                s.home_shots is not None
                and s.away_shots is not None
            ):
                shots_h.append(s.home_shots)
                shots_a.append(s.away_shots)

            if (
                s.home_shots_on_target is not None
                and s.away_shots_on_target is not None
            ):
                sot_h.append(s.home_shots_on_target)
                sot_a.append(s.away_shots_on_target)

    return {
        "corner_h": avg(corner_h),
        "corner_a": avg(corner_a),
        "shots_h": avg(shots_h),
        "shots_a": avg(shots_a),
        "sot_h": avg(sot_h),
        "sot_a": avg(sot_a),
    }


def predict(
    home_id,
    away_id,
    teams,
    league,
    mode,
):
    if (
        home_id not in teams
        or away_id not in teams
    ):
        return None

    h = teams[home_id]
    a = teams[away_id]

    if (
        not h["home_corners_for"]
        or not a["away_corners_for"]
    ):
        return None

    lh = (
        avg(h["home_corners_for"])
        * avg(a["away_corners_against"])
        / max(league["corner_a"], EPS)
    )

    la = (
        avg(a["away_corners_for"])
        * avg(h["home_corners_against"])
        / max(league["corner_h"], EPS)
    )

    # Historical corner baseline.
    base_lh = lh
    base_la = la

    if mode in ("SHOTS", "SHOTS_SOT"):

        if (
            not h["home_shots_for"]
            or not a["away_shots_against"]
        ):
            return None

        hs = avg(h["home_shots_for"])
        aas = avg(a["away_shots_against"])

        shot_reference = (
            league["shots_h"]
            + league["shots_a"]
        ) / 2.0

        if shot_reference > 0:
            shot_signal_home = (
                (hs + aas) / 2.0
            ) / shot_reference

            lh *= shot_signal_home

        if (
            not a["away_shots_for"]
            or not h["home_shots_against"]
        ):
            return None

        aws = avg(a["away_shots_for"])
        has = avg(h["home_shots_against"])

        shot_reference_away = (
            league["shots_h"]
            + league["shots_a"]
        ) / 2.0

        if shot_reference_away > 0:
            shot_signal_away = (
                (aws + has) / 2.0
            ) / shot_reference_away

            la *= shot_signal_away

    if mode == "SHOTS_SOT":

        if (
            not h["home_sot_for"]
            or not a["away_sot_against"]
            or not a["away_sot_for"]
            or not h["home_sot_against"]
        ):
            return None

        sot_reference = (
            league["sot_h"]
            + league["sot_a"]
        ) / 2.0

        if sot_reference > 0:

            sot_home = (
                avg(h["home_sot_for"])
                + avg(a["away_sot_against"])
            ) / 2.0

            sot_away = (
                avg(a["away_sot_for"])
                + avg(h["home_sot_against"])
            ) / 2.0

            lh *= sot_home / sot_reference
            la *= sot_away / sot_reference

    return (
        max(0.5, min(15.0, lh)),
        max(0.5, min(15.0, la)),
        base_lh,
        base_la,
    )


def over_probability(lh, la, line):
    probability = 0.0

    for hc in range(MAX_CORNERS + 1):
        ph = poisson_pmf(hc, lh)

        for ac in range(MAX_CORNERS + 1):
            pa = poisson_pmf(ac, la)

            if hc + ac > line:
                probability += ph * pa

    return probability


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


def run(test, all_matches, mode):
    results = []

    for index, item in enumerate(test):

        history = [
            x for x in all_matches
            if x.date < item.date
        ]

        teams = build_team_profile(history)
        league = league_averages(history)

        if (
            league["corner_h"] is None
            or league["corner_a"] is None
        ):
            continue

        prediction = predict(
            item.home_team_id,
            item.away_team_id,
            teams,
            league,
            mode,
        )

        if prediction is None:
            continue

        lh, la, _, _ = prediction

        results.append({
            "total": (
                item.match.home_corners
                + item.match.away_corners
            ),
            "o7_5": over_probability(
                lh, la, 7.5
            ),
            "o8_5": over_probability(
                lh, la, 8.5
            ),
            "o9_5": over_probability(
                lh, la, 9.5
            ),
            "o10_5": over_probability(
                lh, la, 10.5
            ),
        })

    return results


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

    modes = [
        "BASE",
        "SHOTS",
        "SHOTS_SOT",
    ]

    all_results = {}

    for mode in modes:

        print()
        print("=" * 60)
        print(mode)
        print("=" * 60)

        rows = run(
            test,
            all_matches,
            mode,
        )

        all_results[mode] = rows

        print(
            "ROWS:",
            len(rows),
        )

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

    print()
    print("# DELTA VS BASE")

    base = all_results["BASE"]

    for mode in modes[1:]:

        rows = all_results[mode]

        print()
        print(mode)

        for label, key, line in [
            ("O7.5", "o7_5", 7.5),
            ("O8.5", "o8_5", 8.5),
            ("O9.5", "o9_5", 9.5),
            ("O10.5", "o10_5", 10.5),
        ]:

            _, base_ll, base_br = evaluate(
                base,
                key,
                line,
            )

            _, new_ll, new_br = evaluate(
                rows,
                key,
                line,
            )

            print(
                f"{label:5s}"
                f" LL={new_ll-base_ll:+.6f}"
                f" BRIER={new_br-base_br:+.6f}"
            )


if __name__ == "__main__":
    main()
