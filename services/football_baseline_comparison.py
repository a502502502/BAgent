import math
from typing import Iterable

from models.backtest_result import (
    FootballBacktestResult,
)

from models.football_probability import (
    FootballProbability,
)

from services.football_baseline import (
    FootballBaseline,
)


class FootballBaselineComparison:

    EPSILON = 1e-15

    def compare(
        self,
        results: Iterable[FootballBacktestResult],
    ) -> dict:

        results = list(results)

        if not results:
            return {
                "predictions": 0,
                "model_accuracy": 0.0,
                "baseline_accuracy": 0.0,
                "model_log_loss": 0.0,
                "baseline_log_loss": 0.0,
                "model_brier_score": 0.0,
                "baseline_brier_score": 0.0,
            }

        baseline = FootballBaseline()

        baseline_correct = 0
        baseline_log_loss = 0.0
        baseline_brier_score = 0.0

        for result in results:

            probability = baseline.predict()

            actual = result.actual_result

            if (
                probability.most_likely
                == actual
            ):
                baseline_correct += 1

            baseline_log_loss += (
                self._log_loss(
                    probability,
                    actual,
                )
            )

            baseline_brier_score += (
                self._brier_score(
                    probability,
                    actual,
                )
            )

        total = len(results)

        model_accuracy = (
            sum(
                1
                for result in results
                if result.correct
            )
            / total
        )

        model_log_loss = (
            sum(
                result.log_loss
                for result in results
            )
            / total
        )

        model_brier_score = (
            sum(
                result.brier_score
                for result in results
            )
            / total
        )

        return {
            "predictions": total,

            "model_accuracy": model_accuracy,
            "baseline_accuracy": (
                baseline_correct / total
            ),

            "model_log_loss": model_log_loss,
            "baseline_log_loss": (
                baseline_log_loss / total
            ),

            "model_brier_score": model_brier_score,
            "baseline_brier_score": (
                baseline_brier_score / total
            ),
        }

    def _log_loss(
        self,
        probability: FootballProbability,
        actual: str,
    ) -> float:

        probabilities = {
            "HOME": probability.home,
            "DRAW": probability.draw,
            "AWAY": probability.away,
        }

        value = max(
            self.EPSILON,
            probabilities[actual],
        )

        return -math.log(value)

    @staticmethod
    def _brier_score(
        probability: FootballProbability,
        actual: str,
    ) -> float:

        actual_values = {
            "HOME": 1.0 if actual == "HOME" else 0.0,
            "DRAW": 1.0 if actual == "DRAW" else 0.0,
            "AWAY": 1.0 if actual == "AWAY" else 0.0,
        }

        return (
            (probability.home - actual_values["HOME"]) ** 2
            + (probability.draw - actual_values["DRAW"]) ** 2
            + (probability.away - actual_values["AWAY"]) ** 2
        )
