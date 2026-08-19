import re
import unicodedata
from typing import Dict, Optional


def normalize_name(name: str) -> str:
    value = unicodedata.normalize(
        "NFKD",
        name
    )

    value = value.encode(
        "ascii",
        "ignore"
    ).decode()

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]",
        "",
        value
    )

    return value


class PlayerMapping:

    def __init__(
        self,
        rankings: Dict[str, int]
    ):
        self._rankings = rankings

        self._normalized = {
            normalize_name(name): (
                name,
                rank
            )
            for name, rank in rankings.items()
        }

    def find(
        self,
        player_name: str
    ) -> Optional[int]:

        key = normalize_name(
            player_name
        )

        result = self._normalized.get(key)

        if result is None:
            return None

        return result[1]