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
    if h is None or d is None or a is None or min(h, d, a) <= 1.0:
        return None
    ih, id_, ia = 1.0 / h, 1.0 / d, 1.0 / a
    total = ih + id_ + ia
    return ih / total, id_ / total, ia / total

def weight(days):
    return math.exp(-DECAY * max(0, days) / 365.0)

def load_rows():
    loader = FootballDataLoader()
    raw = Path("data/football/raw")
    files = sorted(raw.glob("E0_*.csv"))
    matches = []
    for f in files:
        matches.extend(loader.load(f))

    dataset = FootballHistoricalDataset(matches)
    completed = [x for x in dataset.all() if x.is_completed]
    completed.sort(key=lambda x: x.date)

    rows = []

    for i, item in enumerate(completed):
        previous = completed[:i]

        home_history = [
            x for x in previous
            if x.match.home.id == item.match.home.id
            or x.match.away.id == item.match.home.id
        ]

        away_history = [
            x for x in previous
            if x.match.home.id == item.match.away.id
            or x.match.away.id == item.match.away.id
        ]

        market = devig(
            item.odds.home,
            item.odds.draw,
            item.odds.away,
        )

        if not home_history or not away_history or market is None:
            continue

        rows.append({
            "season": item.match.season,
            "date": item.date,
            "home": item.match.home.id,
            "away": item.match.away.id,
            "home_history": home_history,
            "away_history": away_history,
            "market": market,
            "result": {"HOME": 0, "DRAW": 1, "AWAY": 2}[item.result],
        })

    return rows

def stats(history, team, date):
    wins = gf = ga = total = 0.0

    for item in history:
        if item.match.home_goals is None or item.match.away_goals is None:
            continue

        w = weight((date - item.date).days)

        if item.match.home.id == team:
            scored = item.match.home_goals
            conceded = item.match.away_goals
        else:
            scored = item.match.away_goals
            conceded = item.match.home_goals

        if scored > conceded:
            wins += w

        gf += w * scored
        ga += w * conceded
        total += w

    if total <= 0:
        return None

    return wins / total, (gf - ga) / total

def features(rows):
    X, y = [], []

    for r in rows:
        home = stats(r["home_history"], r["home"], r["date"])
        away = stats(r["away_history"], r["away"], r["date"])

        if home is None or away is None:
            continue

        mh, md, ma = r["market"]

        X.append([
            1.0,
            home[0] - away[0],
            home[1] - away[1],
            mh, md, ma,
        ])
        y.append(r["result"])

    return np.asarray(X, dtype=float), np.asarray(y, dtype=int)

def main():
    rows = load_rows()

    # Ordine temporale: prime 5 stagioni = sviluppo/validation,
    # ultima stagione = OOS 2025/26.
    dates = sorted(set(r["date"].year for r in rows))

    print()
    print("=" * 60)
    print("V4 SIXTH SENSE")
    print("CONFIDENCE FILTER")
    print("=" * 60)
    print("RECENCY:", DECAY)
    print("YEARS:", dates)

    if len(dates) < 6:
        print("NOT ENOUGH SEASONS")
        return

    oos_year = dates[-1]

    pre_oos = [r for r in rows if r["date"].year < oos_year]
    test_rows = [r for r in rows if r["date"].year == oos_year]

    validation_year = sorted(set(r["date"].year for r in pre_oos))[-1]

    train_rows = [
        r for r in pre_oos
        if r["date"].year < validation_year
    ]

    validation_rows = [
        r for r in pre_oos
        if r["date"].year == validation_year
    ]

    X_train, y_train = features(train_rows)
    X_val, y_val = features(validation_rows)

    print("TRAIN ROWS:", len(y_train))
    print("VALIDATION ROWS:", len(y_val))
    print("OOS ROWS:", len(test_rows))

    if len(y_train) == 0 or len(y_val) == 0:
        print("INVALID SPLIT")
        return

    beta = fit(X_train, y_train)
    p_val = softmax(X_val @ beta)

    print()
    print("VALIDATION SEARCH")

    candidates = []
    confidence = np.max(p_val, axis=1)

    for threshold in THRESHOLDS:
        mask = confidence >= threshold
        m = metrics(p_val[mask], y_val[mask])
        coverage = np.mean(mask)

        print(
            f"THRESHOLD={threshold:.2f} "
            f"MATCHES={mask.sum()} "
            f"COVERAGE={coverage:.3f} "
            f"ACC={m[0]:.6f} "
            f"LL={m[1]:.6f} "
            f"BRIER={m[2]:.6f}"
        )

        candidates.append((threshold, m, coverage))

    best = min(
        candidates,
        key=lambda x: (x[1][1], x[1][2]),
    )

    threshold = best[0]

    print()
    print("SELECTED SIXTH SENSE")
    print("THRESHOLD:", threshold)

    X_pre, y_pre = features(pre_oos)
    X_test, y_test = features(test_rows)

    final_beta = fit(X_pre, y_pre)
    p_test = softmax(X_test @ final_beta)

    base = metrics(p_test, y_test)

    confidence = np.max(p_test, axis=1)
    mask = confidence >= threshold
    filtered = metrics(p_test[mask], y_test[mask])

    print()
    print("=" * 60)
    print("FINAL OOS TEST")
    print("=" * 60)

    print(
        f"WITHOUT SIXTH SENSE "
        f"MATCHES={len(y_test)} "
        f"ACC={base[0]:.6f} "
        f"LL={base[1]:.6f} "
        f"BRIER={base[2]:.6f}"
    )

    print(
        f"WITH SIXTH SENSE "
        f"MATCHES={mask.sum()} "
        f"COVERAGE={np.mean(mask):.6f} "
        f"ACC={filtered[0]:.6f} "
        f"LL={filtered[1]:.6f} "
        f"BRIER={filtered[2]:.6f}"
    )

    print()
    print("DELTA")
    print("ACCURACY:", filtered[0] - base[0])
    print("LOG LOSS:", filtered[1] - base[1])
    print("BRIER:", filtered[2] - base[2])

    lock = (
        filtered[1] < base[1]
        and filtered[2] < base[2]
    )

    print()
    print("DECISION:", "LOCK V4" if lock else "KEEP V3")
    print("RECENCY=2.0")
    print("MARKET INPUT=DEVIG 1X2")
    print("THRESHOLD SELECTED BEFORE OOS=YES")
if __name__ == "__main__":
    main()

