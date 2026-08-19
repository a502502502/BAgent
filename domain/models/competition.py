from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Competition:

    id: str

    name: str

    category: Optional[str] = None

    city: Optional[str] = None

    country: Optional[str] = None

    surface: Optional[str] = None

    start_date: Optional[str] = None

    end_date: Optional[str] = None