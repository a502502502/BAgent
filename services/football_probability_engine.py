import math
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

    LEGACY_HOME_INTERCEPT = 0.2651929680
    LEGACY_DRAW_INTERCEPT = -0.2489197195
    LEGACY_AWAY_INTERCEPT = -0.0162732485

    LEGACY_HOME_WIN_DIFF = 0.5822025965
    LEGACY_DRAW_WIN_DIFF = -0.1422771339
    LEGACY_AWAY_WIN_DIFF = -0.4399254627

    LEGACY_HOME_GOAL_DIFF = 0.3922971208
    LEGACY_DRAW_GOAL_DIFF = -0.0231644822
    LEGACY_AWAY_GOAL_DIFF = -0.3691326386

    EXT_HOME_INTERCEPT = 0.0567940181
    EXT_DRAW_INTERCEPT = -0.1479404962
    EXT_AWAY_INTERCEPT = 0.0911464780

    EXT_HOME_WIN_DIFF = 0.1861200968
    EXT_DRAW_WIN_DIFF = -0.1134477779
    EXT_AWAY_WIN_DIFF = -0.0726723189

    EXT_HOME_GOAL_DIFF = 0.0441877135
    EXT_DRAW_GOAL_DIFF = -0.0124175087
    EXT_AWAY_GOAL_DIFF = -0.0317702048

    EXT_HOME_MARKET_HOME = 1.4750910499
    EXT_DRAW_MARKET_HOME = -0.1880471526
    EXT_AWAY_MARKET_HOME = -1.2870438973

    EXT_HOME_MARKET_DRAW = -0.1955832904
    EXT_DRAW_MARKET_DRAW = 0.1290842096
    EXT_AWAY_MARKET_DRAW = 0.0664990808

    EXT_HOME_MARKET_AWAY = -1.2227137413
    EXT_DRAW_MARKET_AWAY = -0.0889775531
    EXT_AWAY_MARKET_AWAY = 1.3116912944

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
