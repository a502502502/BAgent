from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FootballMatchOdds:

    home: Optional[float] = None
    draw: Optional[float] = None
    away: Optional[float] = None

    over_2_5: Optional[float] = None
    under_2_5: Optional[float] = None

    asian_handicap_home: Optional[float] = None
    asian_handicap_away: Optional[float] = None

    @property
    def is_1x2_available(self) -> bool:
        return (
            self.home is not None
            and self.draw is not None
            and self.away is not None
        )
