from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ValueResult:
    probability: float
    fair_odds: float
    market_odds: float
    edge: float
    expected_value: float
    value: bool


class ValueEngine:

    EPSILON = 1e-12

    def calculate(
        self,
        probability: float,
        market_odds: Optional[float],
        min_edge: float = 0.0,
    ) -> Optional[ValueResult]:

        if market_odds is None:
            return None

        if probability <= 0.0 or probability >= 1.0:
            return None

        if market_odds <= 1.0:
            return None

        fair_odds = 1.0 / probability

        edge = (
            market_odds / fair_odds
        ) - 1.0

        expected_value = (
            probability * market_odds
        ) - 1.0

        return ValueResult(
            probability=probability,
            fair_odds=fair_odds,
            market_odds=market_odds,
            edge=edge,
            expected_value=expected_value,
            value=edge >= min_edge,
        )
