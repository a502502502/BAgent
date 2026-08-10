import pytest

from services.football_baseline import (
    FootballBaseline,
)


def test_baseline_probabilities_sum_to_one():

    probability = (
        FootballBaseline().predict()
    )

    assert (
        probability.home
        + probability.draw
        + probability.away
    ) == pytest.approx(1.0)


def test_baseline_returns_expected_probabilities():

    probability = (
        FootballBaseline().predict()
    )

    assert probability.home == 0.45
    assert probability.draw == 0.27
    assert probability.away == 0.28


def test_baseline_most_likely_result_is_home():

    probability = (
        FootballBaseline().predict()
    )

    assert probability.most_likely == "HOME"
