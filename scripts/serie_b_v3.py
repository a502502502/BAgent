import pandas as pd
import numpy as np
import math
from pathlib import Path

ROOT = Path("data/football/raw/serie_b")
DECAY = 2.0

def devig(h, d, a):
    if min(h, d, a) <= 1:
        return None
    x = np.array([1/h, 1/d, 1/a])
    return x / x.sum()

def softmax(x):
    x = x - np.max(x, axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)

def fit(X, y, iterations=8000, lr=0.03, l2=0.001):
    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]

    for _ in range(iterations):
        p = softmax(X @ beta)
        g = X.T @ (p - Y) / len(X)
        g += l2 * beta
        beta -= lr * g

    return beta

def stats(history, team, date):
    wins = gf = ga = wt = 0.0

    for r in history:
        days = max(0, (date - r["date"]).days)
        w = math.exp(-DECAY * days / 365.0)

        if r["home"] == team:
            f, against = r["hg"], r["ag"]
        else:
            f, against = r["ag"], r["hg"]

        wins += w * (f > against)
        gf += w * f
        ga += w * against
        wt += w

    if wt == 0:
        return None

    return wins / wt, (gf - ga) / wt

rows = []

for path in sorted(ROOT.glob("BRB_*.csv")):

    df = pd.read_csv(path)

    for _, r in df.iterrows():

        if r["status"] != "complete":
            continue

        market = devig(
            float(r["odds_ft_home_team_win"]),
            float(r["odds_ft_draw"]),
            float(r["odds_ft_away_team_win"]),
        )

        if market is None:
            continue

        rows.append({
            "date": pd.to_datetime(r["timestamp"], unit="s"),
            "home": str(r["home_team_name"]),
            "away": str(r["away_team_name"]),
            "hg": int(r["home_team_goal_count"]),
            "ag": int(r["away_team_goal_count"]),
            "market": market,
            "result": (
                0 if r["home_team_goal_count"] > r["away_team_goal_count"]
                else 2 if r["home_team_goal_count"] < r["away_team_goal_count"]
                else 1
            ),
        })

rows.sort(key=lambda x: x["date"])

X = []
y = []

for i, r in enumerate(rows):

    previous = rows[:i]

    home_history = [
        x for x in previous
        if x["home"] == r["home"] or x["away"] == r["home"]
    ]

    away_history = [
        x for x in previous
        if x["home"] == r["away"] or x["away"] == r["away"]
    ]

    hs = stats(home_history, r["home"], r["date"])
    ass = stats(away_history, r["away"], r["date"])

    if hs is None or ass is None:
        continue

    win_diff = hs[0] - ass[0]
    goal_diff = hs[1] - ass[1]

    X.append([
        1.0,
        win_diff,
        goal_diff,
        *r["market"],
    ])
    y.append(r["result"])

X = np.asarray(X, float)
y = np.asarray(y, int)

split = int(len(X) * 0.80)

X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

beta = fit(X_train, y_train)

p = softmax(X_test @ beta)
pred = np.argmax(p, axis=1)

acc = np.mean(pred == y_test)
ll = -np.mean(np.log(np.maximum(p[np.arange(len(y_test)), y_test], 1e-15)))
actual = np.eye(3)[y_test]
brier = np.mean(np.sum((p - actual) ** 2, axis=1))

print()
print("=" * 60)
print("SÉRIE B V3 — HISTORY + RECENCY + MARKET")
print("=" * 60)
print("TOTAL ROWS:", len(X))
print("TRAIN:", len(X_train))
print("TEST:", len(X_test))
print("RECENCY:", DECAY)
print()
print("ACCURACY:", acc)
print("LOG LOSS:", ll)
print("BRIER:", brier)
print()
print("ACTUAL:", np.bincount(y_test, minlength=3))
print("PREDICTED:", np.bincount(pred, minlength=3))
print()
print("AVG PROBS:", p.mean(axis=0))
