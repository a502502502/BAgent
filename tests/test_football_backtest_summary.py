import pytest
from models.backtest_result import (
    FootballBacktestResult,
)

from models.backtest_summary import (
    FootballBacktestSummary,
)

from services.football_backtest_summary import (
    FootballBacktestSummaryBuilder,
)


class Probability:

    def __init__(self, home, draw, away):
        self.home = home
        self.draw = draw
        self.away = away

    @property
    def most_likely(self):
        values = {
            "HOME": self.home,
            "DRAW": self.draw,
            "AWAY": self.away,
        }
        return max(values, key=values.get)


class Prediction:

    def __init__(self, home, draw, away):
        self.probability = Probability(
            home,
            draw,
            away,
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
    brier,
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
        brier_score=brier,
    )


def test_summary_calculates_accuracy():

    results = [
        make_result(
            "1",
            "HOME",
            0.7,
            0.2,
            0.1,
            0.3,
            0.2,
        ),
        make_result(
            "2",
            "AWAY",
            0.2,
            0.2,
            0.6,
            0.5,
            0.3,
        ),
        make_result(
            "3",
            "DRAW",
            0.2,
            0.5,
            0.3,
            0.6,
            0.4,
        ),
    ]

    summary = (
        FootballBacktestSummaryBuilder()
        .build(results)
    )

    assert summary.total_predictions == 3
    assert summary.accuracy == 1.0


def test_summary_calculates_average_metrics():

    results = [
        make_result(
            "1",
            "HOME",
            0.7,
            0.2,
            0.1,
            0.2,
            0.1,
        ),
        make_result(
            "2",
            "AWAY",
            0.2,
            0.2,
            0.6,
            0.4,
            0.3,
        ),
    ]

    summary = (
        FootballBacktestSummaryBuilder()
        .build(results)
    )

    assert summary.average_log_loss == pytest.approx(0.3)
    assert summary.average_brier_score == 0.2


def test_summary_tracks_result_classes():

    results = [
        make_result(
            "1",
            "HOME",
            0.7,
            0.2,
            0.1,
            0.2,
            0.1,
        ),
        make_result(
            "2",
            "DRAW",
            0.2,
            0.6,
            0.2,
            0.3,
            0.2,
        ),
        make_result(
            "3",
            "AWAY",
            0.1,
            0.2,
            0.7,
            0.4,
            0.3,
        ),
        make_result(
            "4",
            "HOME",
            0.6,
            0.2,
            0.2,
            0.5,
            0.4,
        ),
    ]

    summary = (
        FootballBacktestSummaryBuilder()
        .build(results)
    )

    assert summary.home_predictions == 2
    assert summary.home_correct == 2
    assert summary.home_accuracy == 1.0

    assert summary.draw_predictions == 1
    assert summary.draw_correct == 1
    assert summary.draw_accuracy == 1.0

    assert summary.away_predictions == 1
    assert summary.away_correct == 1
    assert summary.away_accuracy == 1.0


def test_summary_handles_empty_results():

    summary = (
        FootballBacktestSummaryBuilder()
        .build([])
    )

    assert isinstance(
        summary,
        FootballBacktestSummary,
    )

    assert summary.total_predictions == 0
    assert summary.accuracy == 0.0
    assert summary.average_log_loss == 0.0
    assert summary.average_brier_score == 0.0

    assert summary.home_accuracy == 0.0
    assert summary.draw_accuracy == 0.0
    assert summary.away_accuracy == 0.0
