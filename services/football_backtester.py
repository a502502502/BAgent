import math
from datetime import datetime
from typing import List

from models.backtest_result import (
    FootballBacktestResult,
)

from models.historical_match import (
    HistoricalFootballMatch,
)

from services.football_historical_dataset import (
    FootballHistoricalDataset,
)

from services.football_historical_profile import (
    FootballHistoricalProfile,
)

from services.football_prediction_engine import (
    FootballPredictionEngine,
)


class FootballBacktester:

    EPSILON = 1e-15

    def __init__(self):

        self.prediction_engine = (
            FootballPredictionEngine()
        )

    def run(
        self,
        dataset: FootballHistoricalDataset,
    ) -> List[FootballBacktestResult]:

        results = []

        for historical_match in dataset.all():

            if not historical_match.is_completed:
                continue

            prediction = self._predict_before_match(
                dataset=dataset,
                historical_match=historical_match,
            )

            if prediction is None:
                continue

            actual_result = (
                self._actual_result(
                    historical_match
                )
            )

            correct = (
                prediction.predicted_result
                == actual_result
            )

            log_loss = self._log_loss(
                prediction,
                actual_result,
            )

            brier_score = self._brier_score(
                prediction,
                actual_result,
            )

            results.append(
                FootballBacktestResult(
                    match_id=historical_match.match_id,
                    actual_result=actual_result,
                    prediction=prediction,
                    correct=correct,
                    log_loss=log_loss,
                    brier_score=brier_score,
                )
            )

        return results

    def _predict_before_match(
        self,
        dataset: FootballHistoricalDataset,
        historical_match: HistoricalFootballMatch,
    ):

        profile = FootballHistoricalProfile(
            dataset
        )

        return self.prediction_engine.predict(
            match=historical_match.match,
            historical_profile=profile,
            date=historical_match.date,
        )

    @staticmethod
    def _actual_result(
        historical_match: HistoricalFootballMatch,
    ) -> str:

        result = historical_match.result

        if result not in {
            "HOME",
            "DRAW",
            "AWAY",
        }:
            raise ValueError(
                "Unexpected football result: "
                f"{result}"
            )

        return result

    def _log_loss(
        self,
        prediction,
        actual_result: str,
    ) -> float:

        probabilities = {
            "HOME": prediction.probability.home,
            "DRAW": prediction.probability.draw,
            "AWAY": prediction.probability.away,
        }

        probability = max(
            self.EPSILON,
            probabilities[actual_result],
        )

        return -math.log(
            probability
        )

    @staticmethod
    def _brier_score(
        prediction,
        actual_result: str,
    ) -> float:

        actual = {
            "HOME": 1.0 if actual_result == "HOME" else 0.0,
            "DRAW": 1.0 if actual_result == "DRAW" else 0.0,
            "AWAY": 1.0 if actual_result == "AWAY" else 0.0,
        }

        predicted = {
            "HOME": prediction.probability.home,
            "DRAW": prediction.probability.draw,
            "AWAY": prediction.probability.away,
        }

        return (
            (
                predicted["HOME"]
                - actual["HOME"]
            ) ** 2
            + (
                predicted["DRAW"]
                - actual["DRAW"]
            ) ** 2
            + (
                predicted["AWAY"]
                - actual["AWAY"]
            ) ** 2
        )
