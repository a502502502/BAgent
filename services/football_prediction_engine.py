from datetime import datetime
from typing import Optional

from models.football import FootballMatch
from models.football_prediction import FootballPrediction

from services.football_historical_profile import (
    FootballHistoricalProfile,
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
    ) -> Optional[FootballPrediction]:

        prediction_date = (
            date
            if date is not None
            else datetime.fromisoformat(
                match.start_time
            )
        )

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

        contribution = (
            self.strength_factor.evaluate(
                home_profile,
                away_profile,
            )
        )

        if contribution is None:
            return None

        contributions = [
            contribution
        ]

        rating = self.rating_engine.calculate(
            contributions
        )

        probability = (
            self.probability_engine.calculate(
                rating
            )
        )

        confidence = (
            contribution.confidence
        )

        return FootballPrediction(
            match_id=match.id,
            home_team=match.home.name,
            away_team=match.away.name,
            probability=probability,
            rating=rating,
            confidence=confidence,
            contributions=contributions,
        )
