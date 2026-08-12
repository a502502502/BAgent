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
    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]

    for _ in range(ITER):
        p = softmax(X @ beta)
        gradient = X.T @ (p - Y) / len(X)
        gradient += L2 * beta
        beta -= LR * gradient

    return beta


def devig(h, d, a):
    if min(h, d, a) <= 1:
        return None

    x = np.array([1.0 / h, 1.0 / d, 1.0 / a])
    return x / x.sum()


def team_stats(history, team, date):
    wins = 0.0
    gf = 0.0
    ga = 0.0
    total = 0.0

    for r in history:
        if team not in (r["home"], r["away"]):
            continue

        days = max(0, (date - r["date"]).days)
        weight = math.exp(-DECAY * days / 365.0)

        if r["home"] == team:
            scored = r["hg"]
            conceded = r["ag"]
        else:
            scored = r["ag"]
            conceded = r["hg"]

        wins += weight * (scored > conceded)
        gf += weight * scored
        ga += weight * conceded
        total += weight

    if total <= 0:
        return None

    return (
        wins / total,
        (gf - ga) / total,
    )


def load_rows():
    matches = []

    for path in sorted(ROOT.glob("BRB_*.csv")):
        df = pd.read_csv(path)

        for _, r in df.iterrows():
            if str(r["status"]).lower() != "complete":
                continue

            h = float(r["odds_ft_home_team_win"])
            d = float(r["odds_ft_draw"])
            a = float(r["odds_ft_away_team_win"])

            odds = devig(h, d, a)

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
                "result": (
                    0 if hg > ag
                    else 2 if hg < ag
                    else 1
                ),
            })

    matches.sort(key=lambda x: x["date"])

    rows = []

    for i, match in enumerate(matches):
        previous = matches[:i]

        home_stats = team_stats(
            previous,
            match["home"],
            match["date"],
        )

        away_stats = team_stats(
            previous,
            match["away"],
            match["date"],
        )

        if home_stats is None or away_stats is None:
            continue

        rows.append({
            "date": match["date"],
            "X": [
                1.0,
                home_stats[0] - away_stats[0],
                home_stats[1] - away_stats[1],
                *match["odds"],
            ],
            "y": match["result"],
        })

    return rows


def make_set(rows, start_year, end_year):
    selected = [
        r for r in rows
        if start_year <= r["date"].year <= end_year
    ]

    X = np.asarray(
        [r["X"] for r in selected],
        dtype=float,
    )

    y = np.asarray(
        [r["y"] for r in selected],
        dtype=int,
    )

    return X, y


def evaluate(X, y, beta):
    p = softmax(X @ beta)
    pred = np.argmax(p, axis=1)

    accuracy = np.mean(pred == y)

    log_loss = -np.mean(
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

    return accuracy, log_loss, brier, p, pred


def calibrate_draw(p, y):
    best = None

    for multiplier in np.arange(
        0.60,
        1.81,
        0.05,
    ):
        q = p.copy()

        q[:, 1] *= multiplier
        q /= q.sum(
            axis=1,
            keepdims=True,
        )

        log_loss = -np.mean(
            np.log(
                np.maximum(
                    q[np.arange(len(y)), y],
                    1e-15,
                )
            )
        )

        actual = np.eye(3)[y]

        brier = np.mean(
            np.sum(
                (q - actual) ** 2,
                axis=1,
            )
        )

        score = (
            log_loss,
            brier,
        )

        if best is None or score < best[0]:
            best = (
                score,
                multiplier,
            )

    return best[1]


def apply_draw_calibration(p, multiplier):
    q = p.copy()
    q[:, 1] *= multiplier
    q /= q.sum(
        axis=1,
        keepdims=True,
    )
    return q


def main():
    rows = load_rows()

    print()
    print("=" * 60)
    print("SÉRIE B V3 ROLLING + DRAW CALIBRATION")
    print("=" * 60)
    print("ROWS:", len(rows))
    print("RECENCY:", DECAY)

    windows = [
        (2022, 2023, 2024),
        (2023, 2024, 2025),
        (2024, 2025, 2026),
    ]

    base_results = []
    calibrated_results = []

    for number, (
        train_end,
        validation_year,
        test_year,
    ) in enumerate(windows, 1):

        X_train, y_train = make_set(
            rows,
            2021,
            train_end,
        )

        X_val, y_val = make_set(
            rows,
            validation_year,
            validation_year,
        )

        X_test, y_test = make_set(
            rows,
            test_year,
            test_year,
        )

        beta = fit(
            X_train,
            y_train,
        )

        _, val_ll, val_brier, val_p, _ = evaluate(
            X_val,
            y_val,
            beta,
        )

        multiplier = calibrate_draw(
            val_p,
            y_val,
        )

        base_acc, base_ll, base_brier, base_p, base_pred = evaluate(
            X_test,
            y_test,
            beta,
        )

        cal_p = apply_draw_calibration(
            base_p,
            multiplier,
        )

        cal_pred = np.argmax(
            cal_p,
            axis=1,
        )

        cal_acc = np.mean(
            cal_pred == y_test
        )

        cal_ll = -np.mean(
            np.log(
                np.maximum(
                    cal_p[
                        np.arange(len(y_test)),
                        y_test,
                    ],
                    1e-15,
                )
            )
        )

        actual = np.eye(3)[y_test]

        cal_brier = np.mean(
            np.sum(
                (cal_p - actual) ** 2,
                axis=1,
            )
        )

        base_results.append(
            (
                base_acc,
                base_ll,
                base_brier,
            )
        )

        calibrated_results.append(
            (
                cal_acc,
                cal_ll,
                cal_brier,
            )
        )

        print()
        print(
            f"WINDOW {number}: "
            f"TRAIN 2021-{train_end} | "
            f"VALID {validation_year} | "
            f"OOS {test_year}"
        )

        print(
            f"VALIDATION LL={val_ll:.6f} "
            f"BRIER={val_brier:.6f}"
        )

        print(
            f"DRAW MULTIPLIER={multiplier:.2f}"
        )

        print(
            f"BASE       "
            f"ACC={base_acc:.6f} "
            f"LL={base_ll:.6f} "
            f"BRIER={base_brier:.6f} "
            f"DRAW={np.sum(base_pred == 1)}"
        )

        print(
            f"CALIBRATED "
            f"ACC={cal_acc:.6f} "
            f"LL={cal_ll:.6f} "
            f"BRIER={cal_brier:.6f} "
            f"DRAW={np.sum(cal_pred == 1)}"
        )

    base = np.mean(
        base_results,
        axis=0,
    )

    calibrated = np.mean(
        calibrated_results,
        axis=0,
    )

    print()
    print("=" * 60)
    print("ROLLING SUMMARY")
    print("=" * 60)

    print(
        f"BASE       "
        f"ACC={base[0]:.6f} "
        f"LL={base[1]:.6f} "
        f"BRIER={base[2]:.6f}"
    )

    print(
        f"CALIBRATED "
        f"ACC={calibrated[0]:.6f} "
        f"LL={calibrated[1]:.6f} "
        f"BRIER={calibrated[2]:.6f}"
    )

    print()
    print(
        "DELTA ACC =",
        calibrated[0] - base[0],
    )

    print(
        "DELTA LL =",
        calibrated[1] - base[1],
    )

    print(
        "DELTA BRIER =",
        calibrated[2] - base[2],
    )

    if (
        calibrated[1] < base[1]
        and calibrated[2] < base[2]
    ):
        print(
            "DECISION: CALIBRATION PROMISING"
        )
    else:
        print(
            "DECISION: KEEP ORIGINAL"
        )


if __name__ == "__main__":
    main()
