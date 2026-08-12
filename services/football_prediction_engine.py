from datetime import datetime
from typing import Optional

from models.football import FootballMatch
from models.football_odds import FootballMatchOdds
from models.football_prediction import FootballPrediction
from models.football_probability import FootballProbability

from services.football_historical_profile import (
    FootballHistoricalProfile,
)

from services.football_match_balance_factor import (
    FootballMatchBalanceFactor,
)

from services.football_probability_engine import (
    FootballProbabilityEngine,
)

from services.football_rating_engine import (
    FootballRatingEngine,
)

from services.football_team_strength_factor import (
    FootballTeamStrengthFactor,
)


class FootballPredictionEngine:

    def __init__(self):

        self.strength_factor = (
            FootballTeamStrengthFactor()
        )

        self.balance_factor = (
            FootballMatchBalanceFactor()
        )

        self.rating_engine = (
            FootballRatingEngine()
        )

        self.probability_engine = (
            FootballProbabilityEngine()
        )

    def predict(
        self,
        match: FootballMatch,
        historical_profile: FootballHistoricalProfile,
        date: Optional[datetime] = None,
        odds: Optional[FootballMatchOdds] = None,
        recency_decay: Optional[float] = None,
    ) -> Optional[FootballPrediction]:

        prediction_date = (
            date
            if date is not None
            else datetime.fromisoformat(
                match.start_time
            )
        )

        # ==================================================
        # HISTORICAL PROFILE
        # ==================================================

        if recency_decay is not None:

            home_profile = (
                historical_profile.get_team_profile_recency(
                    team_id=match.home.id,
                    date=prediction_date,
                    decay=recency_decay,
                )
            )

            away_profile = (
                historical_profile.get_team_profile_recency(
                    team_id=match.away.id,
                    date=prediction_date,
                    decay=recency_decay,
                )
            )

        else:

            home_profile = (
                historical_profile.get_team_profile(
                    team_id=match.home.id,
                    date=prediction_date,
                )
            )

            away_profile = (
                historical_profile.get_team_profile(
                    team_id=match.away.id,
                    date=prediction_date,
                )
            )

        # ==================================================
        # TEAM STRENGTH
        # ==================================================

        strength_contribution = (
            self.strength_factor.evaluate(
                home_profile,
                away_profile,
            )
        )

        # ==================================================
        # MARKET FALLBACK
        # ==================================================

        if strength_contribution is None:

            if (
                odds is not None
                and odds.is_1x2_available
            ):

                inv_h = 1.0 / odds.home
                inv_d = 1.0 / odds.draw
                inv_a = 1.0 / odds.away

                overround = (
                    inv_h
                    + inv_d
                    + inv_a
                )

                probability = FootballProbability(
                    home=inv_h / overround,
                    draw=inv_d / overround,
                    away=inv_a / overround,
                )

                return FootballPrediction(
                    match_id=match.id,
                    home_team=match.home.name,
                    away_team=match.away.name,
                    probability=probability,
                    rating=0.0,
                    confidence=0.0,
                    match_balance=0.0,
                    contributions=[],
                    is_market_fallback=True,
                )

            return None

        # ==================================================
        # BALANCE
        # ==================================================

        balance_contribution = (
            self.balance_factor.evaluate(
                home_profile,
                away_profile,
            )
        )

        contributions = [
            strength_contribution,
        ]

        rating = (
            self.rating_engine.calculate(
                contributions
            )
        )

        balance = (
            balance_contribution.value
            if balance_contribution is not None
            else 0.0
        )

        details = (
            strength_contribution.details
        )

        # ==================================================
        # MARKET FEATURES
        # ==================================================

        market_home = None
        market_draw = None
        market_away = None

        if (
            odds is not None
            and odds.is_1x2_available
        ):

            inv_h = 1.0 / odds.home
            inv_d = 1.0 / odds.draw
            inv_a = 1.0 / odds.away

            overround = (
                inv_h
                + inv_d
                + inv_a
            )

            market_home = (
                inv_h / overround
            )

            market_draw = (
                inv_d / overround
            )

            market_away = (
                inv_a / overround
            )

        # ==================================================
        # PROBABILITY
        # ==================================================

        probability = (
            self.probability_engine.calculate(
                rating=details["difference"],
                balance=balance,
                goal_difference=details[
                    "goal_difference"
                ],
                market_home=market_home,
                market_draw=market_draw,
                market_away=market_away,
            )
        )

        confidence = (
            strength_contribution.confidence
        )

        return FootballPrediction(
            match_id=match.id,
            home_team=match.home.name,
            away_team=match.away.name,
            probability=probability,
            rating=rating,
            confidence=confidence,
            match_balance=balance,
            contributions=contributions,
            is_market_fallback=False,
        )
