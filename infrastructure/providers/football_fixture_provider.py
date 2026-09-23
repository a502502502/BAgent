"""Provider calcio: trasforma fixture già raccolte in Event di dominio."""

from domain.interfaces.provider import Provider
from domain.models.competition import Competition
from domain.models.competitor import Competitor
from domain.models.event import Event


class FootballFixtureProvider(Provider):

    def __init__(self, fixtures=None):
        self._fixtures = list(fixtures or [])

    def fetch_events(self) -> list:
        events = []
        for fixture in self._fixtures:
            competition = Competition(
                id=str(fixture.get("league_id", fixture.get("league", "football"))),
                name=str(fixture.get("league", "football")),
                country=fixture.get("country"),
            )
            events.append(
                Event(
                    id=str(fixture["id"]),
                    competition=competition,
                    competitors=[
                        Competitor(id=str(fixture["home"]), name=str(fixture["home"])),
                        Competitor(id=str(fixture["away"]), name=str(fixture["away"])),
                    ],
                    start_time=str(fixture.get("start_time", "")),
                    status=str(fixture.get("status", "scheduled")),
                )
            )
        return events
