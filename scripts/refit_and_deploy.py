import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile
from services.football_team_strength_factor import FootballTeamStrengthFactor


def softmax(scores):
    scores = scores - np.max(scores, axis=1, keepdims=True)
    exp = np.exp(scores)
    return exp / exp.sum(axis=1, keepdims=True)


def fit(X, y, iterations=12000, learning_rate=0.03, l2=0.001):
    beta = np.zeros((X.shape[1], 3))
    Y = np.eye(3)[y]
    for _ in range(iterations):
        p = softmax(X @ beta)
        gradient = X.T @ (p - Y) / len(X)
        gradient += l2 * beta
        beta -= learning_rate * gradient
    return beta


raw_dir = Path("data/football/raw")
files = sorted(raw_dir.glob("E0_*.csv"))

loader = FootballDataLoader()
all_matches = []
for f in files:
    all_matches.extend(loader.load(f))

dataset = FootballHistoricalDataset(all_matches)
profile = FootballHistoricalProfile(dataset)
factor = FootballTeamStrengthFactor()

rows = []

for hm in dataset.all():

    if not hm.is_completed:
        continue

    home = profile.get_team_profile(hm.match.home.id, hm.date)
    away = profile.get_team_profile(hm.match.away.id, hm.date)

    if home is None or away is None:
        continue

    contribution = factor.evaluate(home, away)

    if contribution is None:
        continue

    details = contribution.details
    win_difference = details["difference"]
    goal_difference = details["goal_difference"]

    market_home = market_draw = market_away = None

    if hm.odds is not None and hm.odds.is_1x2_available:
        inv_h = 1.0 / hm.odds.home
        inv_d = 1.0 / hm.odds.draw
        inv_a = 1.0 / hm.odds.away
        overround = inv_h + inv_d + inv_a
        market_home = inv_h / overround
        market_draw = inv_d / overround
        market_away = inv_a / overround

    result = {"HOME": 0, "DRAW": 1, "AWAY": 2}[hm.result]

    rows.append((win_difference, goal_difference, market_home, market_draw, market_away, result))

print("TOTAL ROWS:", len(rows))

rows_with_market = [r for r in rows if r[2] is not None]
print("ROWS WITH MARKET ODDS:", len(rows_with_market))

X_legacy = np.array([[1.0, r[0], r[1]] for r in rows])
y_legacy = np.array([r[5] for r in rows])
beta_legacy = fit(X_legacy, y_legacy)

X_ext = np.array(
    [
        [1.0, r[0], r[1], r[2], r[3], r[4]]
        for r in rows_with_market
    ]
)
y_ext = np.array([r[5] for r in rows_with_market])
beta_ext = fit(X_ext, y_ext)

print()
print("LEGACY COEFFICIENTS:")
print(beta_legacy)
print()
print("EXTENDED COEFFICIENTS:")
print(beta_ext)


def fmt(v):
    return f"{v:.10f}"


probability_engine_code = f'''import math
from typing import Optional

from models.football_probability import (
    FootballProbability,
)


class FootballProbabilityEngine:
    """
    Two coefficient sets, fitted by multinomial softmax regression
    on 6 seasons of Premier League data (2020/21-2025/26):

    - LEGACY: used when market odds are not available. Uses only
      the TeamStrength win/goal-difference signal.

    - EXTENDED: used when 1X2 market odds are available. Adds the
      de-vigged market-implied probabilities as features, since
      testing showed the market carries much stronger HOME/AWAY
      signal than any historical team-strength feature. The DRAW
      class remains close to its base rate in both cases: extensive
      testing (team strength, recent form, head-to-head, corners,
      cards, market divergence) found no linear signal for DRAW
      discrimination.
    """

    LEGACY_HOME_INTERCEPT = {fmt(beta_legacy[0,0])}
    LEGACY_DRAW_INTERCEPT = {fmt(beta_legacy[0,1])}
    LEGACY_AWAY_INTERCEPT = {fmt(beta_legacy[0,2])}

    LEGACY_HOME_WIN_DIFF = {fmt(beta_legacy[1,0])}
    LEGACY_DRAW_WIN_DIFF = {fmt(beta_legacy[1,1])}
    LEGACY_AWAY_WIN_DIFF = {fmt(beta_legacy[1,2])}

    LEGACY_HOME_GOAL_DIFF = {fmt(beta_legacy[2,0])}
    LEGACY_DRAW_GOAL_DIFF = {fmt(beta_legacy[2,1])}
    LEGACY_AWAY_GOAL_DIFF = {fmt(beta_legacy[2,2])}

    EXT_HOME_INTERCEPT = {fmt(beta_ext[0,0])}
    EXT_DRAW_INTERCEPT = {fmt(beta_ext[0,1])}
    EXT_AWAY_INTERCEPT = {fmt(beta_ext[0,2])}

    EXT_HOME_WIN_DIFF = {fmt(beta_ext[1,0])}
    EXT_DRAW_WIN_DIFF = {fmt(beta_ext[1,1])}
    EXT_AWAY_WIN_DIFF = {fmt(beta_ext[1,2])}

    EXT_HOME_GOAL_DIFF = {fmt(beta_ext[2,0])}
    EXT_DRAW_GOAL_DIFF = {fmt(beta_ext[2,1])}
    EXT_AWAY_GOAL_DIFF = {fmt(beta_ext[2,2])}

    EXT_HOME_MARKET_HOME = {fmt(beta_ext[3,0])}
    EXT_DRAW_MARKET_HOME = {fmt(beta_ext[3,1])}
    EXT_AWAY_MARKET_HOME = {fmt(beta_ext[3,2])}

    EXT_HOME_MARKET_DRAW = {fmt(beta_ext[4,0])}
    EXT_DRAW_MARKET_DRAW = {fmt(beta_ext[4,1])}
    EXT_AWAY_MARKET_DRAW = {fmt(beta_ext[4,2])}

    EXT_HOME_MARKET_AWAY = {fmt(beta_ext[5,0])}
    EXT_DRAW_MARKET_AWAY = {fmt(beta_ext[5,1])}
    EXT_AWAY_MARKET_AWAY = {fmt(beta_ext[5,2])}

    def calculate(
        self,
        rating: float = 0.0,
        balance: float = 1.0,
        goal_difference: float = 0.0,
        market_home: Optional[float] = None,
        market_draw: Optional[float] = None,
        market_away: Optional[float] = None,
    ) -> FootballProbability:

        win_difference = rating

        if market_home is not None and market_draw is not None and market_away is not None:

            home_score = (
                self.EXT_HOME_INTERCEPT
                + self.EXT_HOME_WIN_DIFF * win_difference
                + self.EXT_HOME_GOAL_DIFF * goal_difference
                + self.EXT_HOME_MARKET_HOME * market_home
                + self.EXT_HOME_MARKET_DRAW * market_draw
                + self.EXT_HOME_MARKET_AWAY * market_away
            )

            draw_score = (
                self.EXT_DRAW_INTERCEPT
                + self.EXT_DRAW_WIN_DIFF * win_difference
                + self.EXT_DRAW_GOAL_DIFF * goal_difference
                + self.EXT_DRAW_MARKET_HOME * market_home
                + self.EXT_DRAW_MARKET_DRAW * market_draw
                + self.EXT_DRAW_MARKET_AWAY * market_away
            )

            away_score = (
                self.EXT_AWAY_INTERCEPT
                + self.EXT_AWAY_WIN_DIFF * win_difference
                + self.EXT_AWAY_GOAL_DIFF * goal_difference
                + self.EXT_AWAY_MARKET_HOME * market_home
                + self.EXT_AWAY_MARKET_DRAW * market_draw
                + self.EXT_AWAY_MARKET_AWAY * market_away
            )

        else:

            home_score = (
                self.LEGACY_HOME_INTERCEPT
                + self.LEGACY_HOME_WIN_DIFF * win_difference
                + self.LEGACY_HOME_GOAL_DIFF * goal_difference
            )

            draw_score = (
                self.LEGACY_DRAW_INTERCEPT
                + self.LEGACY_DRAW_WIN_DIFF * win_difference
                + self.LEGACY_DRAW_GOAL_DIFF * goal_difference
            )

            away_score = (
                self.LEGACY_AWAY_INTERCEPT
                + self.LEGACY_AWAY_WIN_DIFF * win_difference
                + self.LEGACY_AWAY_GOAL_DIFF * goal_difference
            )

        maximum = max(home_score, draw_score, away_score)

        home_probability = math.exp(home_score - maximum)
        draw_probability = math.exp(draw_score - maximum)
        away_probability = math.exp(away_score - maximum)

        total = home_probability + draw_probability + away_probability

        return FootballProbability(
            home=home_probability / total,
            draw=draw_probability / total,
            away=away_probability / total,
        )
'''

Path("services/football_probability_engine.py").write_text(probability_engine_code, encoding="utf-8")
print()
print("WRITTEN: services/football_probability_engine.py")
