"""La pipeline usa il motore Poisson e il Kelly, non una probabilità passata a mano."""

from services.analysis.xg_poisson_engine import QuantitativeEngine
from services.betting.strict_ticket_pipeline import MarketCandidate, StrictTicketPipeline


SENSE = "Volume offensivo reale della stagione in corso, ritmo aperto su entrambi i fronti."


def _candidate(**overrides) -> MarketCandidate:
    data = dict(
        match_name="Home FC vs Away FC",
        tournament="Serie A",
        market_name="Over 1.5",
        bookmaker_odd=1.40,
        xg_home=1.7,
        xg_away=1.2,
        sixth_sense_analysis=SENSE,
        estimated_p_90=0.99,
        home_matches_played=3,
        away_matches_played=3,
    )
    data.update(overrides)
    return MarketCandidate(**data)


def test_a_team_with_two_matches_does_not_start(tmp_path):
    from services.football.sixth_sense.calibration import SeasonMatch

    history = [
        SeasonMatch("2026", f"2026-09-0{day}", "Home FC", f"Side {day}", 1, 0, "Serie A")
        for day in range(1, 3)
    ]
    pipeline = StrictTicketPipeline(season_matches=history)
    report = pipeline.validate_candidate(
        _candidate(
            kickoff_time="2026-09-24 20:45",
            tournament="Serie A",
            home_matches_played=10,
            away_matches_played=10,
        )
    )
    assert report.passed is False
    assert report.stage_failed == 0
    assert "dopo 3 partite" in report.rejection_reason.lower()


def test_striker_absence_lowers_the_priced_probability():
    pipeline = StrictTicketPipeline()
    plain = pipeline._probability_from_model(_candidate())
    hurt = _candidate(
        sixth_sense_events=[
            {
                "team": "home",
                "event_type": "injury",
                "description": "punta titolare fuori",
                "impact": -2.0,
                "confidence": 1.0,
            }
        ]
    )
    priced = pipeline._probability_from_model(hurt)
    _, _, report = pipeline.calculate_joint_probability(hurt)
    assert priced < plain
    assert hurt.xg_home == 1.7
    assert "assenza offensiva casa" in report


def test_injury_alarm_without_a_side_keeps_the_base_xg():
    pipeline = StrictTicketPipeline()
    flagged = _candidate(sixth_sense_risk_flags=["INJURY_ALARM"])
    assert pipeline._probability_from_model(flagged) == pipeline._probability_from_model(_candidate())


def test_missing_xg_is_rejected():
    pipeline = StrictTicketPipeline()
    report = pipeline.validate_candidate(_candidate(xg_home=None, xg_away=None))
    assert report.passed is False
    assert report.stage_failed == 5


def test_probability_comes_from_the_engine_not_the_caller():
    pipeline = StrictTicketPipeline()
    candidate = _candidate()
    expected = QuantitativeEngine().goal_market_probability(1.7, 1.2, "Over 1.5")
    report = pipeline.validate_candidate(candidate)
    assert report.real_probability == expected
    assert report.real_probability != candidate.estimated_p_90


def test_stake_follows_fractional_kelly():
    pipeline = StrictTicketPipeline()
    stake = pipeline.calculate_recommended_stake(
        current_bankroll=100.0,
        total_odds=3.0,
        num_selections=2,
        estimated_prob=0.40,
    )
    assert stake == 2.5
    assert stake <= 8.0


def test_negative_edge_stake_is_zero():
    pipeline = StrictTicketPipeline()
    stake = pipeline.calculate_recommended_stake(
        current_bankroll=100.0,
        total_odds=2.0,
        num_selections=1,
        estimated_prob=0.20,
    )
    assert stake == 0.0


def test_same_match_markets_use_the_intersection_not_the_product():
    pipeline = StrictTicketPipeline()
    engine = QuantitativeEngine()
    home = _candidate(market_name="Over 1.5", fixture_id=10)
    away = _candidate(market_name="Over 2.5", fixture_id=10)
    joint = pipeline.ticket_joint_probability([home, away])
    over_15 = engine.goal_market_probability(1.7, 1.2, "Over 1.5")
    over_25 = engine.goal_market_probability(1.7, 1.2, "Over 2.5")
    assert joint == over_25
    assert joint > over_15 * over_25


def test_different_matches_still_multiply():
    pipeline = StrictTicketPipeline()
    engine = QuantitativeEngine()
    first = _candidate(match_name="Home FC vs Away FC", fixture_id=10)
    second = _candidate(match_name="Other FC vs Side FC", fixture_id=11)
    joint = pipeline.ticket_joint_probability([first, second])
    single = engine.goal_market_probability(1.7, 1.2, "Over 1.5")
    assert joint == single * single


def test_same_match_goal_and_corner_is_not_priced_as_independent():
    pipeline = StrictTicketPipeline()
    goals = _candidate(market_name="Over 1.5", fixture_id=10)
    corners = _candidate(
        market_name="Over 8.5 Corner Totali",
        fixture_id=10,
        avg_corners_home=6.0,
        avg_corners_away=5.0,
    )
    assert pipeline.ticket_joint_probability([goals, corners]) is None
