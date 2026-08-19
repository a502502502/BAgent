from domain.interfaces.provider import Provider
from domain.models.competition import Competition
from domain.models.competitor import Competitor
from domain.models.event import Event


class DummyProvider(Provider):

    def fetch_events(self):

        competition = Competition(
            id="ATP001",
            name="ATP Montreal",
            sport="Tennis",
            category="ATP1000",
            season="2026"
        )

        sinner = Competitor(
            id="P001",
            name="Jannik Sinner",
            country="Italy"
        )

        alcaraz = Competitor(
            id="P002",
            name="Carlos Alcaraz",
            country="Spain"
        )

        event = Event(
            id="E001",
            competition=competition,
            competitors=[sinner, alcaraz],
            start_time="2026-08-10 18:00"
        )

        return [event]