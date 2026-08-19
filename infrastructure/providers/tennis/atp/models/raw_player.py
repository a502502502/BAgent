from dataclasses import dataclass
from typing import Optional


@dataclass
class RawPlayer:

    player_id: str

    first_name: str

    last_name: str

    country: Optional[str] = None