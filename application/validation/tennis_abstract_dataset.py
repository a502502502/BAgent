from pathlib import Path
from typing import Dict, List

from application.validation.tennis_abstract_pipeline import (
    TennisAbstractPipeline,
)

from application.validation.historical_match import (
    HistoricalMatch,
)


class TennisAbstractDataset:

    SNAPSHOT_DIR = Path(
        "infrastructure/providers/tennis/"
        "tennis_abstract/snapshots/players"
    )

    def __init__(self):

        self.pipeline = TennisAbstractPipeline()

        self.SNAPSHOT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    def collect(
        self,
        players: Dict[str, str],
    ) -> List[HistoricalMatch]:

        matches = []

        for player_id, player_name in players.items():

            print()
            print(
                f"Collecting: {player_name}"
            )

            snapshot_path = (
                self._snapshot_path(
                    player_id
                )
            )

            try:

                if snapshot_path.exists():

                    print(
                        f"Using cached snapshot: "
                        f"{snapshot_path}"
                    )

                    player_matches = (
                        self._load_cached_player(
                            snapshot_path=snapshot_path,
                            player_id=player_id,
                            player_name=player_name,
                        )
                    )

                else:

                    print(
                        "No cached snapshot found."
                    )

                    player_matches = (
                        self.pipeline.load_player_matches(
                            player_id=player_id,
                            player_name=player_name,
                        )
                    )

                    if not snapshot_path.exists():

                        raise RuntimeError(
                            "Il collector ha acquisito "
                            "la pagina ma lo snapshot "
                            "individuale non esiste: "
                            f"{snapshot_path}"
                        )

                    print(
                        f"Snapshot created: "
                        f"{snapshot_path}"
                    )

                matches.extend(
                    player_matches
                )

            except Exception as exc:

                print()
                print(
                    "============================================================"
                )
                print(
                    "TENNIS ABSTRACT COLLECTION STOPPED"
                )
                print(
                    "============================================================"
                )

                print(
                    f"Player: {player_name}"
                )

                print(
                    f"Player ID: {player_id}"
                )

                print(
                    f"Reason: {exc}"
                )

                print()
                print(
                    "Gli snapshot già presenti "
                    "rimangono disponibili."
                )

                print(
                    f"Matches collected so far: "
                    f"{len(matches)}"
                )

                print()

                break

        return self._deduplicate(
            matches
        )

    def _load_cached_player(
        self,
        snapshot_path: Path,
        player_id: str,
        player_name: str,
    ) -> List[HistoricalMatch]:

        html = snapshot_path.read_text(
            encoding="utf-8"
        )

        if not html:

            raise RuntimeError(
                f"Snapshot vuoto: "
                f"{snapshot_path}"
            )

        print(
            f"HTML length for "
            f"{player_name}: "
            f"{len(html)}"
        )

        results = (
            self.pipeline.parser.parse_results(
                html
            )
        )

        print(
            f"Parsed results for "
            f"{player_name}: "
            f"{len(results)}"
        )

        matches = (
            self.pipeline.builder.build(
                results=results,
                player_id=player_id,
                player_name=player_name,
            )
        )

        print(
            f"Built matches for "
            f"{player_name}: "
            f"{len(matches)}"
        )

        return matches

    def _snapshot_path(
        self,
        player_id: str,
    ) -> Path:

        return (
            self.SNAPSHOT_DIR
            / f"{player_id}.html"
        )

    def _deduplicate(
        self,
        matches: List[HistoricalMatch],
    ) -> List[HistoricalMatch]:

        unique = {}
        seen_pairs = set()

        for historical in matches:

            match = historical.match

            players = tuple(
                sorted(
                    [
                        match.home.id,
                        match.away.id,
                    ]
                )
            )

            key = (
                historical.date,
                match.competition.name,
                players,
                match.round_name,
            )

            if key in seen_pairs:
                continue

            seen_pairs.add(key)
            unique[key] = historical

        return list(
            unique.values()
        )