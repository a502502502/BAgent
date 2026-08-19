from infrastructure.providers.tennis.tennis_abstract.collector import (
    TennisAbstractCollector,
)

from infrastructure.providers.tennis.tennis_abstract.player_parser import (
    TennisAbstractPlayerParser,
)

from application.validation.tennis_abstract_match_builder import (
    TennisAbstractMatchBuilder,
)


class TennisAbstractPipeline:

    def __init__(self):
        self.collector = TennisAbstractCollector()
        self.parser = TennisAbstractPlayerParser()
        self.builder = TennisAbstractMatchBuilder()

    def load_player_matches(
        self,
        player_id: str,
        player_name: str,
    ):

        html = self.collector.collect(
            player_id
        )

        print(
            f"HTML length for {player_name}: "
            f"{len(html) if html else 0}"
        )

        results = self.parser.parse_results(
            html
        )

        print(
            f"Parsed results for {player_name}: "
            f"{len(results)}"
        )

        matches = self.builder.build(
            results=results,
            player_id=player_id,
            player_name=player_name,
        )

        print(
            f"Built matches for {player_name}: "
            f"{len(matches)}"
        )

        return matches