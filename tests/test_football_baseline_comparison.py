import pytest

from models.backtest_result import (
    FootballBacktestResult,
)

from models.football_probability import (
    FootballProbability,
)

from services.football_baseline_comparison import (
    FootballBaselineComparison,
)


class Prediction:

    def __init__(
        self,
        home,
        draw,
        away,
    ):

        self.probability = FootballProbability(
            home=home,
            draw=draw,
            away=away,
        )

    @property
    def predicted_result(self):

        return self.probability.most_likely


def make_result(
    match_id,
    actual,
    home,
    draw,
    away,
    log_loss,
    brier_score,
):

    prediction = Prediction(
        home,
        draw,
        away,
    )

    return FootballBacktestResult(
        match_id=match_id,
        actual_result=actual,
        prediction=prediction,
        correct=(
            prediction.predicted_result
            == actual
        ),
        log_loss=log_loss,
        brier_score=brier_score,
    )


def test_comparison_returns_all_metrics():

    results = [
        make_result(
            "1",
            "HOME",
            0.70,
            0.20,
            0.10,
            0.20,
            0.10,
        ),
        make_result(
            "2",
            "AWAY",
            0.20,
            0.20,
            0.60,
            0.40,
            0.30,
        ),
    ]

    comparison = (
        FootballBaselineComparison()
        .compare(results)
    )

    assert comparison["predictions"] == 2

    assert (
        comparison["model_accuracy"]
        == 1.0
    )

    assert (
        comparison["baseline_accuracy"]
        == 0.5
    )

    assert (
        comparison["model_log_loss"]
        == pytest.approx(0.30)
    )

    assert (
        comparison["model_brier_score"]
        == pytest.approx(0.20)
    )


def test_empty_results_return_zero_metrics():

    comparison = (
        FootballBaselineComparison()
        .compare([])
    )

    assert comparison == {
        "predictions": 0,
        "model_accuracy": 0.0,
        "baseline_accuracy": 0.0,
        "model_log_loss": 0.0,
        "baseline_log_loss": 0.0,
        "model_brier_score": 0.0,
        "baseline_brier_score": 0.0,
    }


def test_baseline_metrics_are_calculated_independently():

    results = [
        make_result(
            "1",
            "HOME",
            0.40,
            0.30,
            0.30,
            0.90,
            0.80,
        ),
        make_result(
            "2",
            "DRAW",
            0.20,
            0.60,
            0.20,
            0.50,
            0.40,
        ),
    ]

    comparison = (
        FootballBaselineComparison()
        .compare(results)
    )

    assert (
        comparison["baseline_accuracy"]
        == 0.5
    )

    assert (
        comparison["baseline_log_loss"]
        > 0.0
    )

    assert (
        comparison["baseline_brier_score"]
        > 0.0
    )
