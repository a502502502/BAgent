from domain.models.competition import Competition
from domain.models.competitor import Competitor
from domain.models.match import Match


competition = Competition(
    id="1",
    name="Serie A"
)

home = Competitor(
    id="1",
    name="Juventus",
    country="ITA"
)

away = Competitor(
    id="2",
    name="Milan",
    country="ITA"
)

match = Match(
    id="100",
    competition=competition,
    home=home,
    away=away,
    round_name="Quarter Final",
    status="Scheduled"
)

print()

print(match)