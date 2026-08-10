from models.football_odds import FootballMatchOdds


def test_odds_store_1x2():

    odds = FootballMatchOdds(
        home=1.30,
        draw=6.00,
        away=8.50,
    )

    assert odds.home == 1.30
    assert odds.draw == 6.00
    assert odds.away == 8.50

    assert odds.is_1x2_available


def test_odds_store_over_under():

    odds = FootballMatchOdds(
        over_2_5=1.36,
        under_2_5=3.20,
    )

    assert odds.over_2_5 == 1.36
    assert odds.under_2_5 == 3.20


def test_missing_1x2_odds_are_not_available():

    odds = FootballMatchOdds()

    assert not odds.is_1x2_available
