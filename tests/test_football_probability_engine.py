import pytest

from models.football_probability import (
    FootballProbability,
)

from services.football_probability_engine import (
    FootballProbabilityEngine,
)


def test_probability_sums_to_one():

    probability = (
        FootballProbabilityEngine()
        .calculate(0.0)
    )

    assert (
        probability.home
        + probability.draw
        + probability.away
    ) == pytest.approx(1.0)


def test_equal_rating_has_equal_home_away_probability():

    probability = (
        FootballProbabilityEngine()
        .calculate(0.0)
    )

    assert probability.home == pytest.approx(
        probability.away
    )

    assert probability.draw == pytest.approx(
        0.27
    )


def test_positive_rating_favors_home():

    probability = (
        FootballProbabilityEngine()
        .calculate(1.0)
    )

    assert probability.home > probability.away
    assert probability.home > probability.draw


def test_negative_rating_favors_away():

    probability = (
        FootballProbabilityEngine()
        .calculate(-1.0)
    )

    assert probability.away > probability.home
    assert probability.away > probability.draw


def test_probability_values_are_valid():

    probability = (
        FootballProbabilityEngine()
        .calculate(2.0)
    )

    assert 0.0 <= probability.home <= 1.0
    assert 0.0 <= probability.draw <= 1.0
    assert 0.0 <= probability.away <= 1.0


def test_most_likely_result():

    engine = FootballProbabilityEngine()

    assert (
        engine.calculate(1.0).most_likely
        == "HOME"
    )

    assert (
        engine.calculate(0.0).most_likely
        == "HOME"
    )

    assert (
        engine.calculate(-1.0).most_likely
        == "AWAY"
    )


def test_probability_model_rejects_invalid_values():

    with pytest.raises(ValueError):

        FootballProbability(
            home=0.7,
            draw=0.2,
            away=0.2,
        )
