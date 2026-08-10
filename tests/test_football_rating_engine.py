from models.contribution import Contribution

from services.football_rating_engine import (
    FootballRatingEngine,
)


def test_rating_with_single_contribution():

    contribution = Contribution(
        factor="TeamStrength",
        value=0.8,
        confidence=1.0,
        explanation="test",
        details={},
    )

    rating = FootballRatingEngine().calculate(
        [contribution]
    )

    assert rating == 0.8


def test_rating_is_confidence_weighted():

    contributions = [
        Contribution(
            factor="Strength",
            value=1.0,
            confidence=1.0,
            explanation="test",
            details={},
        ),
        Contribution(
            factor="Form",
            value=0.0,
            confidence=0.5,
            explanation="test",
            details={},
        ),
    ]

    rating = FootballRatingEngine().calculate(
        contributions
    )

    assert rating == 2.0 / 3.0


def test_zero_confidence_is_ignored():

    contributions = [
        Contribution(
            factor="Strength",
            value=1.0,
            confidence=0.0,
            explanation="test",
            details={},
        ),
        Contribution(
            factor="Form",
            value=0.5,
            confidence=1.0,
            explanation="test",
            details={},
        ),
    ]

    rating = FootballRatingEngine().calculate(
        contributions
    )

    assert rating == 0.5


def test_empty_contributions_return_zero():

    rating = FootballRatingEngine().calculate([])

    assert rating == 0.0


def test_all_zero_confidence_returns_zero():

    contributions = [
        Contribution(
            factor="Strength",
            value=1.0,
            confidence=0.0,
            explanation="test",
            details={},
        ),
    ]

    rating = FootballRatingEngine().calculate(
        contributions
    )

    assert rating == 0.0
