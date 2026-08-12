from dataclasses import dataclass
from typing import List

from models.contribution import Contribution
from models.football_probability import FootballProbability


@dataclass(frozen=True)
class FootballPrediction:

    match_id: str
    home_team: str
    away_team: str

    probability: FootballProbability

    rating: float
    confidence: float
    match_balance: float

    contributions: List[Contribution]

    is_market_fallback: bool = False

    @property
    def predicted_result(self) -> str:

        return self.probability.most_likely
