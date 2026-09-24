"""Il fit usa solo la stagione chiusa col risultato. Sotto soglia resta il prior."""

from datetime import date

from services.football.sixth_sense.analyzer import SixthSenseEvent
from services.football.sixth_sense.calibration import (
    MIN_GROUP,
    MatchResult,
    events_from_api_injuries,
    fit_factors,
    list_samples,
    load_factors,
    record_projection,
    season_key,
    settle_results,
)
from services.football.sixth_sense.lambda_context import (
    ROTATION_FACTOR,
    FactorSet,
    MatchContext,
    project_attack,
)


def _record(db, day: int, context: MatchContext, home_goals: int, away_goals: int, season: str = "2026-27"):
    record_projection(
        season,
        f"2026-09-{day:02d}",
        f"Home {day}",
        f"Away {day}",
        2.0,
        1.0,
        2.0,
        1.0,
        context,
        db_path=db,
    )
    settle_results(
        [MatchResult(f"Home {day}", f"Away {day}", f"2026-09-{day:02d}", home_goals, away_goals)],
        db,
    )


def test_rerun_keeps_the_settled_score(tmp_path):
    db = tmp_path / "bagent.db"
    context = MatchContext()
    _record(db, 1, context, 3, 0)
    record_projection("2026-27", "2026-09-01", "Home 1", "Away 1", 1.4, 1.1, 1.4, 1.1, context, db_path=db)
    saved = list_samples("2026-27", db)[0]
    assert saved.actual_home_goals == 3
    assert saved.base_xg_home == 1.4


def test_few_matches_keep_the_prior(tmp_path):
    db = tmp_path / "bagent.db"
    for day in range(1, 4):
        _record(db, day, MatchContext(rotation_risk=True), 1, 1)
    fits = {fit.name: fit for fit in fit_factors(list_samples("2026-27", db))}
    assert fits["rotation"].used is False
    assert fits["rotation"].fitted == ROTATION_FACTOR
    assert load_factors("2026-27", db).rotation == ROTATION_FACTOR


def test_enough_rotation_matches_move_the_factor_and_ignore_another_season(tmp_path):
    db = tmp_path / "bagent.db"
    for day in range(1, MIN_GROUP + 1):
        _record(db, day, MatchContext(), 2, 1)
        _record(db, day + 10, MatchContext(rotation_risk=True), 1, 1)
        _record(db, day + 20, MatchContext(rotation_risk=True), 0, 0, season="2025-26")
    from services.football.sixth_sense.calibration import save_fits

    fits = fit_factors(list_samples("2026-27", db))
    rotation = next(fit for fit in fits if fit.name == "rotation")
    assert rotation.used is True
    assert rotation.internal_weight == 0.08
    assert rotation.fitted < ROTATION_FACTOR
    assert rotation.fitted > ROTATION_FACTOR - 0.05
    save_fits("2026-27", fits, db)
    assert load_factors("2026-27", db).rotation == rotation.fitted
    assert load_factors("2025-26", db).rotation == ROTATION_FACTOR


def test_injury_scale_rises_when_the_cut_was_too_deep():
    samples = []
    from services.football.sixth_sense.calibration import LambdaSample

    for day in range(1, MIN_GROUP + 1):
        samples.append(
            LambdaSample(
                season="2026-27",
                match_date=f"2026-09-{day:02d}",
                home_team=f"H{day}",
                away_team=f"A{day}",
                base_xg_home=2.0,
                base_xg_away=1.0,
                projected_xg_home=1.6,
                projected_xg_away=1.0,
                attack_factor_home=0.8,
                actual_home_goals=2,
                actual_away_goals=1,
            )
        )
    injury = next(fit for fit in fit_factors(samples) if fit.name == "injury_scale")
    assert injury.used is True
    assert injury.fitted > 1.0


def test_api_injury_becomes_an_event_and_a_doubt_does_not_move_xg():
    events = events_from_api_injuries(
        [
            {"player": "Striker", "team": "Home FC", "type": "Missing Fixture", "reason": "Knee"},
            {"player": "Winger", "team": "Away FC", "type": "Questionable", "reason": "Knock"},
        ],
        "Home FC",
        "Away FC",
    )
    assert events[0].confidence == 0.8
    assert events[1].confidence == 0.4
    from services.football.sixth_sense.lambda_context import context_from_events

    context = context_from_events(events)
    plain = project_attack(1.8, 1.2, MatchContext())
    hurt = project_attack(1.8, 1.2, context)
    assert hurt.xg_home < plain.xg_home
    assert hurt.xg_away == plain.xg_away


def test_injury_scale_deepens_the_cut():
    from services.football.sixth_sense.lambda_context import context_from_events

    context = context_from_events(
        [SixthSenseEvent("home", "injury", "punta fuori", impact=-2.0, confidence=1.0)]
    )
    mild = project_attack(1.8, 1.2, context, FactorSet(injury_scale=1.0))
    deep = project_attack(1.8, 1.2, context, FactorSet(injury_scale=0.5))
    assert deep.xg_home < mild.xg_home


def test_loaded_history_starts_after_three_matches_each():
    from services.football.sixth_sense.calibration import SeasonMatch, after_third, same_season

    matches = []
    for opp in (1, 2, 3):
        for n in (1, 2, 3):
            matches.append(
                SeasonMatch("2026", f"2026-08-0{opp}", f"Opp {opp}", f"Pad {opp}{n}", 1, 0, "Serie A")
            )
    for day, opp in ((1, 1), (2, 2), (3, 3), (4, 3)):
        matches.append(SeasonMatch("2026", f"2026-09-0{day}", "Home", f"Opp {opp}", 2, 1, "Serie A"))
    kept = after_third(matches)
    assert [match.match_date for match in kept] == ["2026-09-04"]
    assert same_season("2026/2027", "2026-27")
    assert same_season("2025", "2026-27") is False


def test_internal_weight_is_one_percent_per_match_and_caps_at_thirty():
    from services.football.sixth_sense.calibration import INTERNAL_WEIGHT_CAP, internal_weight

    assert internal_weight(3) == 0.0
    assert internal_weight(8) == 0.08
    assert internal_weight(30) == INTERNAL_WEIGHT_CAP
    assert internal_weight(80) == INTERNAL_WEIGHT_CAP


def test_season_key_opens_in_july():
    assert season_key(date(2026, 9, 24)) == "2026-27"
    assert season_key(date(2026, 5, 2)) == "2025-26"
