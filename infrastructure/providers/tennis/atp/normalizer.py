from domain.models.competition import Competition
from domain.models.competitor import Competitor
from domain.models.match import Match


class ATPNormalizer:

    def competition(self, raw):

        return Competition(
            id=raw.tournament_id,
            name=raw.name,
            city=raw.city,
            country=raw.country
        )

    def competitor(self, raw):

        return Competitor(
            id=raw.player_id,
            name=f"{raw.first_name} {raw.last_name}".strip(),
            country=raw.country
        )

    def match(self, raw_match, competition):

        home = self.competitor(raw_match.player)

        away = self.competitor(raw_match.opponent)

        return Match(
            id=raw_match.match_id,
            competition=competition,
            home=home,
            away=away,
            round_name=raw_match.round_name,
            court_name=raw_match.court_name,
            status=raw_match.status
        )