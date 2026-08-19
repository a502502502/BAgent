from domain.models.competition import Competition
from domain.models.competitor import Competitor
from domain.models.match import Match


competition = Competition(
    id="1",
    name="ATP Montreal"
)

sinner = Competitor(
    id="1",
    name="Jannik Sinner",
    country="ITA"
)

alcaraz = Competitor(
    id="2",
    name="Carlos Alcaraz",
    country="ESP"
)

match = Match(
    id="100",
    competition=competition,
    home=sinner,
    away=alcaraz,
    round_name="Quarter Final",
    status="Scheduled"
)

print()

print(match)