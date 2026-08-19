import json
from pathlib import Path

from providers.tennis.atp.models.raw_match import RawMatch
from providers.tennis.atp.models.raw_player import RawPlayer
from providers.tennis.atp.models.raw_tournament import RawTournament


class ATPParser:

    def __init__(self):

        self.snapshot = Path(
            "storage/snapshots/atp/livematches.json"
        )

    def load(self):

        with open(self.snapshot, "r", encoding="utf-8") as f:

            return json.load(f)

    def parse(self):

        data = self.load()

        tournaments = []

        for tournament in data["Data"]["LiveMatchesTournamentsOrdered"]:

            raw_tournament = RawTournament(

                tournament_id=str(
                    tournament.get("EventId", "")
                ),

               name=tournament.get("EventTitle", ""),

                city=tournament.get("EventCity", ""),

                country=tournament.get("EventCountry", "")

            )

            for match in tournament.get("LiveMatches", []):

                player = match["PlayerTeam"]["Player"]

                opponent = match["OpponentTeam"]["Player"]

                raw_player = RawPlayer(

                    player_id=str(player.get("PlayerId", "")),

                    first_name=player.get(
                        "PlayerFirstName",
                        ""
                    ),

                    last_name=player.get(
                        "PlayerLastName",
                        ""
                    ),

                    country=player.get(
                        "PlayerCountry",
                        ""
                    )
                )

                raw_opponent = RawPlayer(

                    player_id=str(
                        opponent.get("PlayerId", "")
                    ),

                    first_name=opponent.get(
                        "PlayerFirstName",
                        ""
                    ),

                    last_name=opponent.get(
                        "PlayerLastName",
                        ""
                    ),

                    country=opponent.get(
                        "PlayerCountry",
                        ""
                    )
                )

                raw_match = RawMatch(

                    match_id=str(
                        match.get("MatchId", "")
                    ),

                    round_name=match.get(
                        "RoundName",
                        ""
                    ),

                    court_name=match.get(
                        "CourtName",
                        ""
                    ),

                    status=match.get(
                        "MatchStatus",
                        ""
                    ),

                    player=raw_player,

                    opponent=raw_opponent

                )

                raw_tournament.matches.append(
                    raw_match
                )

            tournaments.append(raw_tournament)

        return tournaments