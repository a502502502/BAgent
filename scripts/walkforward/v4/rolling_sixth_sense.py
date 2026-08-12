import sys
from pathlib import Path
import math
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset

DECAY = 2.0
THRESHOLDS = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]

def softmax(x):
    x = x - np.max(x, axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)

def fit(X, y, iterations=6000, lr=0.03, l2=0.001):
    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]
    for _ in range(iterations):
        p = softmax(X @ beta)
        gradient = X.T @ (p - Y) / len(X)
        gradient += l2 * beta
        beta -= lr * gradient
    return beta

def metrics(p, y):
    if len(y) == 0:
        return 0.0, float("inf"), float("inf")
    pred = np.argmax(p, axis=1)
    acc = np.mean(pred == y)
    ll = -np.mean(np.log(np.maximum(p[np.arange(len(y)), y], 1e-15)))
    actual = np.eye(3)[y]
    brier = np.mean(np.sum((p - actual) ** 2, axis=1))
    return acc, ll, brier

def devig(h, d, a):
    if h is None or d is None or a is None or min(h, d, a) <= 1:
        return None
    ih, id_, ia = 1/h, 1/d, 1/a
    total = ih + id_ + ia
    return ih/total, id_/total, ia/total

def load_rows():
    loader = FootballDataLoader()
    raw = Path("data/football/raw")
    matches = []

    for f in sorted(raw.glob("E0_*.csv")):
        matches.extend(loader.load(f))

    dataset = FootballHistoricalDataset(matches)
    completed = sorted(
        [x for x in dataset.all() if x.is_completed],
        key=lambda x: x.date
    )

    rows = []

    for i, item in enumerate(completed):
        previous = completed[:i]

        hh = [
            x for x in previous
            if x.match.home.id == item.match.home.id
            or x.match.away.id == item.match.home.id
        ]

        ah = [
            x for x in previous
            if x.match.home.id == item.match.away.id
            or x.match.away.id == item.match.away.id
        ]

        market = devig(
            item.odds.home,
            item.odds.draw,
            item.odds.away,
        )

        if not hh or not ah or market is None:
            continue

        rows.append({
            "date": item.date,
            "home": item.match.home.id,
            "away": item.match.away.id,
            "hh": hh,
            "ah": ah,
            "market": market,
            "result": {"HOME":0, "DRAW":1, "AWAY":2}[item.result],
        })

    return rows

def stats(history, team, date):
    wins = gf = ga = total = 0.0

    for item in history:
        if item.match.home_goals is None or item.match.away_goals is None:
            continue

        days = max(0, (date - item.date).days)
        w = math.exp(-DECAY * days / 365.0)

        if item.match.home.id == team:
            f = item.match.home_goals
            a = item.match.away_goals
        else:
            f = item.match.away_goals
            a = item.match.home_goals

        wins += w if f > a else 0
        gf += w * f
        ga += w * a
        total += w

    if total == 0:
        return None

    return wins/total, (gf-ga)/total

def features(rows):
    X, y = [], []

    for r in rows:
        h = stats(r["hh"], r["home"], r["date"])
        a = stats(r["ah"], r["away"], r["date"])

        if h is None or a is None:
            continue

        mh, md, ma = r["market"]

        X.append([
            1.0,
            h[0] - a[0],
            h[1] - a[1],
            mh, md, ma
        ])
        y.append(r["result"])

    return np.asarray(X, float), np.asarray(y, int)

def main():
    rows = load_rows()

    # 6 chronological season blocks inferred from match dates.
    seasons = sorted(set(
        (r["date"].year if r["date"].month >= 8 else r["date"].year - 1)
        for r in rows
    ))

    print()
    print("=" * 60)
    print("V4 ROLLING SIXTH SENSE")
    print("=" * 60)
    print("RECENCY:", DECAY)
    print("SEASON BLOCKS:", seasons)

    if len(seasons) < 6:
        print("NOT ENOUGH SEASONS")
        return

    # Four rolling tests:
    # train -> validation -> next-season OOS
    results = []

    for i in range(len(seasons) - 3):
        train_seasons = seasons[:i+2]
        validation_season = seasons[i+2]
        test_season = seasons[i+3]

        train = [
            r for r in rows
            if (r["date"].year if r["date"].month >= 8 else r["date"].year - 1)
            in train_seasons
        ]

        validation = [
            r for r in rows
            if (r["date"].year if r["date"].month >= 8 else r["date"].year - 1)
            == validation_season
        ]

        test = [
            r for r in rows
            if (r["date"].year if r["date"].month >= 8 else r["date"].year - 1)
            == test_season
        ]

        Xtr, ytr = features(train)
        Xv, yv = features(validation)
        Xt, yt = features(test)

        beta = fit(Xtr, ytr)

        pv = softmax(Xv @ beta)
        confidence = np.max(pv, axis=1)

        candidates = []

        for threshold in THRESHOLDS:
            mask = confidence >= threshold
            m = metrics(pv[mask], yv[mask])
            candidates.append((threshold, m))

        selected = min(
            candidates,
            key=lambda x: (x[1][1], x[1][2])
        )

        threshold = selected[0]

        # Refit using train + validation.
        Xpre, ypre = features(train + validation)
        beta_final = fit(Xpre, ypre)

        pt = softmax(Xt @ beta_final)
        base = metrics(pt, yt)

        test_confidence = np.max(pt, axis=1)
        mask = test_confidence >= threshold
        filtered = metrics(pt[mask], yt[mask])

        results.append((base, filtered, threshold, len(yt), mask.sum()))

        print()
        print("=" * 60)
        print(f"WINDOW {i+1}")
        print("=" * 60)
        print("TRAIN SEASONS:", train_seasons)
        print("VALIDATION:", validation_season)
        print("OOS:", test_season)
        print("SELECTED THRESHOLD:", threshold)

        print(
            f"BASE     MATCHES={len(yt)} "
            f"ACC={base[0]:.6f} "
            f"LL={base[1]:.6f} "
            f"BRIER={base[2]:.6f}"
        )

        print(
            f"FILTERED MATCHES={mask.sum()} "
            f"COVERAGE={np.mean(mask):.6f} "
            f"ACC={filtered[0]:.6f} "
            f"LL={filtered[1]:.6f} "
            f"BRIER={filtered[2]:.6f}"
        )

        print(
            f"DELTA ACC={filtered[0]-base[0]:+.6f} "
            f"LL={filtered[1]-base[1]:+.6f} "
            f"BRIER={filtered[2]-base[2]:+.6f}"
        )

    base_acc = np.mean([x[0][0] for x in results])
    base_ll = np.mean([x[0][1] for x in results])
    base_brier = np.mean([x[0][2] for x in results])

    filt_acc = np.mean([x[1][0] for x in results])
    filt_ll = np.mean([x[1][1] for x in results])
    filt_brier = np.mean([x[1][2] for x in results])

    improved = sum(
        x[1][1] < x[0][1] and x[1][2] < x[0][2]
        for x in results
    )

    print()
    print("=" * 60)
    print("ROLLING SUMMARY")
    print("=" * 60)

    print(
        f"BASE     ACC={base_acc:.6f} "
        f"LL={base_ll:.6f} "
        f"BRIER={base_brier:.6f}"
    )

    print(
        f"FILTERED ACC={filt_acc:.6f} "
        f"LL={filt_ll:.6f} "
        f"BRIER={filt_brier:.6f}"
    )

    print()
    print("DELTA ACC:", filt_acc - base_acc)
    print("DELTA LL:", filt_ll - base_ll)
    print("DELTA BRIER:", filt_brier - base_brier)
    print("WINDOWS IMPROVED:", improved, "/", len(results))

    if (
        improved >= 3
        and filt_ll < base_ll
        and filt_brier < base_brier
    ):
        print("DECISION: LOCK V4 SIXTH SENSE")
    else:
        print("DECISION: DO NOT LOCK V4 SIXTH SENSE")

if __name__ == "__main__":
    main()

