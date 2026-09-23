"""Le interfacce di dominio hanno un'implementazione calcio."""

import sqlite3

from application.analyzers.poisson_analyzer import PoissonAnalyzer
from application.strategies.strict_ticket_strategy import StrictTicketStrategy
from domain.models.competition import Competition
from domain.models.competitor import Competitor
from domain.models.event import Event
from domain.models.match import Match
from infrastructure.providers.football_fixture_provider import FootballFixtureProvider
from infrastructure.repositories.sqlite_match_repository import SqliteMatchRepository
from services.betting.strict_ticket_pipeline import MarketCandidate
from services.database.schema import _create_tables


def test_provider_maps_fixtures_to_events():
    provider = FootballFixtureProvider(
        [{"id": 10, "league": "Serie A", "home": "Lecce", "away": "Monza", "start_time": "2026-09-23T20:45:00"}]
    )
    events = provider.fetch_events()
    assert len(events) == 1
    assert events[0].competitors[0].name == "Lecce"
    assert events[0].competition.name == "Serie A"


def test_repository_saves_a_match():
    conn = sqlite3.connect(":memory:")
    _create_tables(conn)
    repo = SqliteMatchRepository(conn)
    competition = Competition(id="serie-a", name="Serie A", country="Italy")
    home = Competitor(id="lecce", name="Lecce")
    away = Competitor(id="monza", name="Monza")
    repo.save_competition(competition)
    repo.save_competitor(home)
    repo.save_match(
        Match(
            id="m1",
            competition=competition,
            home=home,
            away=away,
            start_time="2026-09-23",
            status="scheduled",
        )
    )
    row = conn.execute("SELECT home_team, away_team FROM matches").fetchone()
    assert row == ("Lecce", "Monza")


def test_strategy_drops_candidates_the_engine_cannot_price():
    strategy = StrictTicketStrategy()
    candidate = MarketCandidate(
        match_name="Lecce vs Monza",
        tournament="Serie A",
        market_name="Over 1.5",
        bookmaker_odd=1.40,
        sixth_sense_analysis="Volume offensivo reale della stagione in corso, ritmo aperto.",
    )
    assert strategy.select([candidate]) == []


def test_analyzer_prices_when_xg_is_present():
    event = Event(
        id="10",
        competition=Competition(id="serie-a", name="Serie A"),
        competitors=[Competitor(id="h", name="Lecce"), Competitor(id="a", name="Monza")],
        start_time="2026-09-23T20:45:00",
    )
    event.xg_home = 1.4
    event.xg_away = 1.1
    result = PoissonAnalyzer().analyze(event)
    assert result["priced"] is True
    assert "Over 2.5" in result["markets"]
