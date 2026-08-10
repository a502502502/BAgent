from datetime import datetime

import pytest

from models.football import (
    FootballMatch,
    FootballTeam,
)

from models.historical_match import (
    HistoricalFootballMatch,
)

from services.football_backtester import (
    FootballBacktester,
)

from services.football_historical_dataset import (
    FootballHistoricalDataset,
)


def make_match(
    match_id: str,
    date: str,
    home_id: str,
    away_id: str,
    home_goals: int,
    away_goals: int,
) -> HistoricalFootballMatch:

    match = FootballMatch(
        id=match_id,
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id=home_id,
            name=home_id,
        ),
        away=FootballTeam(
            id=away_id,
            name=away_id,
        ),
        start_time=date,
        home_goals=home_goals,
        away_goals=away_goals,
        status="Completed",
    )

    return HistoricalFootballMatch(
        match=match,
        date=datetime.fromisoformat(date),
        winner=match.result,
    )


def test_backtester_produces_results():

    matches = [
        make_match(
            "MATCH-1",
            "2026-07-01T20:00:00",
            "TeamA",
            "TeamB",
            2,
            0,
        ),
        make_match(
            "MATCH-2",
            "2026-07-05T20:00:00",
            "TeamA",
            "TeamC",
            2,
            0,
        ),
        make_match(
            "MATCH-3",
            "2026-07-10T20:00:00",
            "TeamB",
            "TeamC",
            0,
            1,
        ),
        make_match(
            "MATCH-4",
            "2026-07-15T20:00:00",
            "TeamC",
            "TeamA",
            0,
            2,
        ),
        make_match(
            "MATCH-5",
            "2026-07-20T20:00:00",
            "TeamA",
            "TeamB",
            3,
            1,
        ),
        make_match(
            "MATCH-6",
            "2026-07-25T20:00:00",
            "TeamB",
            "TeamC",
            1,
            1,
        ),
    ]

    dataset = FootballHistoricalDataset(
        matches
    )

    results = FootballBacktester().run(
        dataset
    )

    assert len(results) > 0

    for result in results:

        assert result.actual_result in {
            "HOME",
            "DRAW",
            "AWAY",
        }

        assert result.log_loss >= 0.0

        assert result.brier_score >= 0.0

        assert (
            result.prediction.probability.home
            + result.prediction.probability.draw
            + result.prediction.probability.away
        ) == pytest.approx(1.0)


def test_backtester_uses_only_previous_matches():

    matches = [
        make_match(
            "MATCH-1",
            "2026-07-01T20:00:00",
            "TeamA",
            "TeamB",
            5,
            0,
        ),
        make_match(
            "MATCH-2",
            "2026-07-20T20:00:00",
            "TeamA",
            "TeamB",
            0,
            5,
        ),
    ]

    dataset = FootballHistoricalDataset(
        matches
    )

    results = FootballBacktester().run(
        dataset
    )

    assert len(results) == 1

    result = results[0]

    assert result.match_id == "MATCH-2"

    assert result.actual_result == "AWAY"

    assert result.prediction.rating > 0

    assert (
        result.prediction.probability.home
        > result.prediction.probability.away
    )


def test_backtester_skips_first_match_without_history():

    matches = [
        make_match(
            "MATCH-1",
            "2026-07-01T20:00:00",
            "TeamA",
            "TeamB",
            2,
            0,
        ),
    ]

    dataset = FootballHistoricalDataset(
        matches
    )

    results = FootballBacktester().run(
        dataset
    )

    assert results == []


def test_log_loss_is_zero_like_for_certain_correct_prediction():

    backtester = FootballBacktester()

    class Probability:
        home = 1.0
        draw = 0.0
        away = 0.0

    class Prediction:
        probability = Probability()

    loss = backtester._log_loss(
        Prediction(),
        "HOME",
    )

    assert loss == pytest.approx(
        0.0
    )


def test_brier_score_for_certain_correct_prediction():

    backtester = FootballBacktester()

    class Probability:
        home = 1.0
        draw = 0.0
        away = 0.0

    class Prediction:
        probability = Probability()

    score = backtester._brier_score(
        Prediction(),
        "HOME",
    )

    assert score == pytest.approx(
        0.0
    )


def test_brier_score_for_equal_probabilities():

    backtester = FootballBacktester()

    class Probability:
        home = 1.0 / 3.0
        draw = 1.0 / 3.0
        away = 1.0 / 3.0

    class Prediction:
        probability = Probability()

    score = backtester._brier_score(
        Prediction(),
        "HOME",
    )

    assert score == pytest.approx(
        2.0 / 3.0
    )
