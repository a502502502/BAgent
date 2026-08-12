import pandas as pd
import numpy as np
import math
from pathlib import Path

ROOT = Path("data/football/raw/serie_b")

DECAY = 2.0
ITER = 8000
LR = 0.03
L2 = 0.001


def softmax(z):
    z = z - np.max(z, axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def fit(X, y):
    b = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]

    for _ in range(ITER):
        p = softmax(X @ b)
        g = X.T @ (p - Y) / len(X)
        g += L2 * b
        b -= LR * g

    return b


def devig(h, d, a):
    if min(h, d, a) <= 1:
        return None
    x = np.array([1.0 / h, 1.0 / d, 1.0 / a])
    return x / x.sum()


matches = []

for path in sorted(ROOT.glob("BRB_*.csv")):
    df = pd.read_csv(path)

    for _, r in df.iterrows():

        if str(r["status"]).lower() != "complete":
            continue

        odds = devig(
            float(r["odds_ft_home_team_win"]),
            float(r["odds_ft_draw"]),
            float(r["odds_ft_away_team_win"]),
        )

        if odds is None:
            continue

        hg = int(r["home_team_goal_count"])
        ag = int(r["away_team_goal_count"])

        matches.append({
            "date": pd.to_datetime(
                int(r["timestamp"]),
                unit="s",
            ),
            "home": str(r["home_team_name"]),
            "away": str(r["away_team_name"]),
            "hg": hg,
            "ag": ag,
            "odds": odds,
            "xg_home": float(r["Home Team Pre-Match xG"]),
            "xg_away": float(r["Away Team Pre-Match xG"]),
            "ppg_home": float(r["Pre-Match PPG (Home)"]),
            "ppg_away": float(r["Pre-Match PPG (Away)"]),
            "result": (
                0 if hg > ag
                else 2 if hg < ag
                else 1
            ),
        })

matches.sort(key=lambda x: x["date"])


def team_stats(history, team, date):
    wins = gf = ga = total = 0.0

    for r in history:

        if team not in (r["home"], r["away"]):
            continue

        days = max(0, (date - r["date"]).days)
        w = math.exp(-DECAY * days / 365.0)

        if r["home"] == team:
            scored, conceded = r["hg"], r["ag"]
        else:
            scored, conceded = r["ag"], r["hg"]

        wins += w * (scored > conceded)
        gf += w * scored
        ga += w * conceded
        total += w

    if total <= 0:
        return None

    return (
        wins / total,
        (gf - ga) / total,
    )


def build_rows():
    rows = []

    for i, r in enumerate(matches):

        previous = matches[:i]

        hs = team_stats(
            previous,
            r["home"],
            r["date"],
        )

        aw = team_stats(
            previous,
            r["away"],
            r["date"],
        )

        if hs is None or aw is None:
            continue

        base = [
            1.0,
            hs[0] - aw[0],
            hs[1] - aw[1],
            *r["odds"],
        ]

        xg_diff = r["xg_home"] - r["xg_away"]
        ppg_diff = r["ppg_home"] - r["ppg_away"]

        rows.append({
            "year": r["date"].year,
            "base": base,
            "xg": base + [xg_diff],
            "ppg": base + [ppg_diff],
            "y": r["result"],
        })

    return rows


def make_xy(rows, start, end, model):
    q = [
        r for r in rows
        if start <= r["year"] <= end
    ]

    X = np.asarray(
        [r[model] for r in q],
        dtype=float,
    )

    y = np.asarray(
        [r["y"] for r in q],
        dtype=int,
    )

    return X, y


def evaluate(X, y, beta):
    p = softmax(X @ beta)
    pred = np.argmax(p, axis=1)

    acc = np.mean(pred == y)

    ll = -np.mean(
        np.log(
            np.maximum(
                p[np.arange(len(y)), y],
                1e-15,
            )
        )
    )

    actual = np.eye(3)[y]

    brier = np.mean(
        np.sum(
            (p - actual) ** 2,
            axis=1,
        )
    )

    return acc, ll, brier


def main():

    rows = build_rows()

    print()
    print("=" * 70)
    print("SÉRIE B — V3 vs XG vs PPG")
    print("=" * 70)
    print("ROWS:", len(rows))
    print("RECENCY:", DECAY)

    windows = [
        (2022, 2023, 2024),
        (2023, 2024, 2025),
        (2024, 2025, 2026),
    ]

    models = [
        ("V3", "base"),
        ("V3+XG", "xg"),
        ("V3+PPG", "ppg"),
    ]

    results = {
        name: []
        for name, _ in models
    }

    for w, (train_end, val_year, test_year) in enumerate(windows, 1):

        print()
        print(
            f"WINDOW {w}: "
            f"TRAIN 2021-{train_end} | "
            f"VALID {val_year} | "
            f"OOS {test_year}"
        )

        for name, key in models:

            Xtr, ytr = make_xy(
                rows,
                2021,
                train_end,
                key,
            )

            Xt, yt = make_xy(
                rows,
                test_year,
                test_year,
                key,
            )

            beta = fit(Xtr, ytr)

            acc, ll, brier = evaluate(
                Xt,
                yt,
                beta,
            )

            results[name].append(
                (acc, ll, brier)
            )

            print(
                f"{name:<7} "
                f"ACC={acc:.6f} "
                f"LL={ll:.6f} "
                f"BRIER={brier:.6f}"
            )

    print()
    print("=" * 70)
    print("ROLLING SUMMARY")
    print("=" * 70)

    summary = {}

    for name, _ in models:

        avg = np.mean(
            results[name],
            axis=0,
        )

        summary[name] = avg

        print(
            f"{name:<7} "
            f"ACC={avg[0]:.6f} "
            f"LL={avg[1]:.6f} "
            f"BRIER={avg[2]:.6f}"
        )

    print()
    print("DELTA vs V3")

    base = summary["V3"]

    for name in ("V3+XG", "V3+PPG"):

        r = summary[name]

        print()
        print(name)
        print("ACC  =", r[0] - base[0])
        print("LL   =", r[1] - base[1])
        print("BRIER=", r[2] - base[2])

    best = min(
        summary,
        key=lambda k: (
            summary[k][1],
            summary[k][2],
        ),
    )

    print()
    print("BEST BY LOG LOSS + BRIER:", best)

    if best == "V3":
        print("DECISION: KEEP V3")
    else:
        print("DECISION: PROMISING EXTENSION")


if __name__ == "__main__":
    main()
