import pytest
from datetime import datetime

from models.football import (
    FootballMatch,
    FootballTeam,
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


def make_match(
    match_id,
    start_time,
    home_team,
    away_team,
    home_goals,
    away_goals,
):
    match = FootballMatch(
        id=match_id,
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id=home_team,
            name=home_team,
        ),
        away=FootballTeam(
            id=away_team,
            name=away_team,
        ),
        start_time=start_time,
        home_goals=home_goals,
        away_goals=away_goals,
        status="Completed",
    )

    return HistoricalFootballMatch(
        match=match,
        date=datetime.fromisoformat(start_time),
    )


def test_prediction_engine_produces_1x2_prediction():

    historical = [
        make_match(
            "H-001",
            "2026-07-01T20:00:00",
            "StrongTeam",
            "WeakTeam",
            3,
            0,
        ),
        make_match(
            "H-002",
            "2026-07-05T20:00:00",
            "StrongTeam",
            "OtherTeam",
            2,
            0,
        ),
        make_match(
            "H-003",
            "2026-07-10T20:00:00",
            "WeakTeam",
            "OtherTeam",
            0,
            2,
        ),
        make_match(
            "H-004",
            "2026-07-15T20:00:00",
            "OtherTeam",
            "StrongTeam",
            0,
            2,
        ),
    ]

    dataset = FootballHistoricalDataset(historical)

    historical_profile = FootballHistoricalProfile(
        dataset
    )

    prediction_match = FootballMatch(
        id="PRED-001",
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id="StrongTeam",
            name="Strong Team",
        ),
        away=FootballTeam(
            id="WeakTeam",
            name="Weak Team",
        ),
        start_time="2026-08-01T20:00:00",
        status="Scheduled",
    )

    prediction = FootballPredictionEngine().predict(
        match=prediction_match,
        historical_profile=historical_profile,
    )

    assert prediction is not None

    assert prediction.match_id == "PRED-001"
    assert prediction.home_team == "Strong Team"
    assert prediction.away_team == "Weak Team"

    assert (
        prediction.probability.home
        + prediction.probability.draw
        + prediction.probability.away
    ) == pytest.approx(1.0)

    assert prediction.probability.home > (
        prediction.probability.away
    )

    assert prediction.rating > 0
    assert prediction.confidence > 0

    assert len(prediction.contributions) == 1

    factors = {
        contribution.factor
        for contribution in prediction.contributions
    }

    assert factors == {"TeamStrength"}


def test_prediction_returns_none_without_history():

    dataset = FootballHistoricalDataset([])

    historical_profile = FootballHistoricalProfile(
        dataset
    )

    prediction_match = FootballMatch(
        id="PRED-002",
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id="UnknownA",
            name="Unknown A",
        ),
        away=FootballTeam(
            id="UnknownB",
            name="Unknown B",
        ),
        start_time="2026-08-01T20:00:00",
        status="Scheduled",
    )

    prediction = FootballPredictionEngine().predict(
        match=prediction_match,
        historical_profile=historical_profile,
    )

    assert prediction is None


def test_prediction_does_not_use_current_match():

    historical = [
        make_match(
            "H-001",
            "2026-07-01T20:00:00",
            "TeamA",
            "TeamB",
            3,
            0,
        ),
    ]

    dataset = FootballHistoricalDataset(historical)

    historical_profile = FootballHistoricalProfile(
        dataset
    )

    prediction_match = FootballMatch(
        id="PRED-003",
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id="TeamA",
            name="Team A",
        ),
        away=FootballTeam(
            id="TeamB",
            name="Team B",
        ),
        start_time="2026-06-01T20:00:00",
        status="Scheduled",
    )

    prediction = FootballPredictionEngine().predict(
        match=prediction_match,
        historical_profile=historical_profile,
    )

    assert prediction is None


def test_prediction_uses_explicit_reference_date():

    historical = [
        make_match(
            "H-001",
            "2026-07-01T20:00:00",
            "TeamA",
            "TeamB",
            3,
            0,
        ),
    ]

    dataset = FootballHistoricalDataset(historical)

    historical_profile = FootballHistoricalProfile(
        dataset
    )

    prediction_match = FootballMatch(
        id="PRED-004",
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id="TeamA",
            name="Team A",
        ),
        away=FootballTeam(
            id="TeamB",
            name="Team B",
        ),
        start_time="2026-08-01T20:00:00",
        status="Scheduled",
    )

    prediction = FootballPredictionEngine().predict(
        match=prediction_match,
        historical_profile=historical_profile,
        date=datetime.fromisoformat(
            "2026-06-15T20:00:00"
        ),
    )

    assert prediction is None

