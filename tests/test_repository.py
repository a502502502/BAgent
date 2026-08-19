from core.repository.sqlite_repository import SQLiteRepository

from providers.tennis.atp.parser import ATPParser
from providers.tennis.atp.normalizer import ATPNormalizer


repository = SQLiteRepository()

parser = ATPParser()

normalizer = ATPNormalizer()


for raw_tournament in parser.parse():

    competition = normalizer.competition(raw_tournament)

    repository.save_competition(
        competition
    )

    for raw_match in raw_tournament.matches:

        match = normalizer.match(
            raw_match,
            competition
        )

        repository.save_competitor(
            match.home
        )

        repository.save_competitor(
            match.away
        )

        repository.save_match(
            match
        )

print()

print("Repository aggiornato.")

print()