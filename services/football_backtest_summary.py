from typing import Iterable

from models.backtest_result import (
    FootballBacktestResult,
)

from models.backtest_summary import (
    FootballBacktestSummary,
)


class FootballBacktestSummaryBuilder:

    def build(
        self,
        results: Iterable[FootballBacktestResult],
    ) -> FootballBacktestSummary:

        results = list(results)

        total = len(results)

        if total == 0:

            return FootballBacktestSummary(
                total_predictions=0,
                accuracy=0.0,
                average_log_loss=0.0,
                average_brier_score=0.0,
                home_predictions=0,
                home_correct=0,
                draw_predictions=0,
                draw_correct=0,
                away_predictions=0,
                away_correct=0,
            )

        correct = sum(
            1
            for result in results
            if result.correct
        )

        average_log_loss = (
            sum(
                result.log_loss
                for result in results
            )
            / total
        )

        average_brier_score = (
            sum(
                result.brier_score
                for result in results
            )
            / total
        )

        home_predictions = sum(
            1
            for result in results
            if result.prediction.predicted_result
            == "HOME"
        )

        home_correct = sum(
            1
            for result in results
            if (
                result.prediction.predicted_result
                == "HOME"
                and result.actual_result
                == "HOME"
            )
        )

        draw_predictions = sum(
            1
            for result in results
            if result.prediction.predicted_result
            == "DRAW"
        )

        draw_correct = sum(
            1
            for result in results
            if (
                result.prediction.predicted_result
                == "DRAW"
                and result.actual_result
                == "DRAW"
            )
        )

        away_predictions = sum(
            1
            for result in results
            if result.prediction.predicted_result
            == "AWAY"
        )

        away_correct = sum(
            1
            for result in results
            if (
                result.prediction.predicted_result
                == "AWAY"
                and result.actual_result
                == "AWAY"
            )
        )

        return FootballBacktestSummary(
            total_predictions=total,
            accuracy=correct / total,
            average_log_loss=average_log_loss,
            average_brier_score=average_brier_score,
            home_predictions=home_predictions,
            home_correct=home_correct,
            draw_predictions=draw_predictions,
            draw_correct=draw_correct,
            away_predictions=away_predictions,
            away_correct=away_correct,
        )
