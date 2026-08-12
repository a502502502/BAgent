import pytest

from services.football_probability_engine import (
    FootballProbabilityEngine,
)


def test_probabilities_sum_to_one():
    probability = (
        FootballProbabilityEngine()
        .calculate(0.0)
    )

    assert probability.home + probability.draw + probability.away == pytest.approx(1.0)


def test_equal_rating_keeps_valid_probabilities():
    probability = (
        FootballProbabilityEngine()
        .calculate(0.0)
    )

    assert 0.0 <= probability.home <= 1.0
    assert 0.0 <= probability.draw <= 1.0
    assert 0.0 <= probability.away <= 1.0


def test_positive_rating_favors_home():
    probability = (
        FootballProbabilityEngine()
        .calculate(1.0)
    )

    assert probability.home > probability.away


def test_negative_rating_favors_away():
    probability = (
        FootballProbabilityEngine()
        .calculate(-1.0)
    )

    assert probability.away > probability.home


def test_rating_zero_can_include_home_advantage():
    probability = (
        FootballProbabilityEngine()
        .calculate(0.0)
    )

    assert probability.home > probability.away


def test_most_likely_positive_rating_is_home():
    probability = (
        FootballProbabilityEngine()
        .calculate(1.0)
    )

    assert probability.most_likely == "HOME"


def test_most_likely_negative_rating_is_away():
    probability = (
        FootballProbabilityEngine()
        .calculate(-1.0)
    )

    assert probability.most_likely == "AWAY"
