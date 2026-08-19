from dataclasses import dataclass

from providers.tennis.atp.models.raw_player import RawPlayer


@dataclass
class RawMatch:

    match_id: str

    round_name: str

    court_name: str

    status: str

    player: RawPlayer

    opponent: RawPlayer