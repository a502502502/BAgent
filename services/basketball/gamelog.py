"""Box score di squadra accoppiati in una partita, senza stats future."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class TeamBox:
    game_id: str
    game_date: date
    season: str
    team: str
    is_home: bool
    points: int
    fga: float
    fta: float
    oreb: float
    tov: float

    @property
    def possessions(self) -> float:
        return estimate_possessions(self.fga, self.oreb, self.tov, self.fta)


@dataclass(frozen=True)
class PairedGame:
    game_id: str
    game_date: date
    season: str
    home: str
    away: str
    home_points: int
    away_points: int
    possessions: float

    @property
    def margin(self) -> int:
        return self.home_points - self.away_points

    @property
    def total(self) -> int:
        return self.home_points + self.away_points


def estimate_possessions(fga: float, oreb: float, tov: float, fta: float) -> float:
    """Stima di Dean Oliver: FGA - ORB + TOV + 0.44 * FTA."""
    return fga - oreb + tov + 0.44 * fta


def pair_team_boxes(rows: list[TeamBox]) -> list[PairedGame]:
    """Una partita vale solo se ci sono entrambe le squadre, con possessi > 0."""
    grouped: dict[tuple[str, str], list[TeamBox]] = {}
    for row in rows:
        grouped.setdefault((row.season, row.game_id), []).append(row)

    games: list[PairedGame] = []
    for boxes in grouped.values():
        home = [box for box in boxes if box.is_home]
        away = [box for box in boxes if not box.is_home]
        if len(home) != 1 or len(away) != 1:
            continue
        possessions = (home[0].possessions + away[0].possessions) / 2
        if possessions <= 0:
            continue
        games.append(
            PairedGame(
                game_id=home[0].game_id,
                game_date=home[0].game_date,
                season=home[0].season,
                home=home[0].team,
                away=away[0].team,
                home_points=home[0].points,
                away_points=away[0].points,
                possessions=possessions,
            )
        )
    games.sort(key=lambda game: (game.season, game.game_date, game.game_id))
    return games


def load_team_boxes(path: Path) -> list[TeamBox]:
    boxes: list[TeamBox] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            boxes.append(
                TeamBox(
                    game_id=row["game_id"].strip(),
                    game_date=_parse_date(row["date"]),
                    season=row["season"].strip(),
                    team=row["team"].strip().upper(),
                    is_home=_parse_bool(row["is_home"]),
                    points=int(row["points"]),
                    fga=float(row["fga"]),
                    fta=float(row["fta"]),
                    oreb=float(row["oreb"]),
                    tov=float(row["tov"]),
                )
            )
    return boxes


def _parse_date(value: str) -> date:
    return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "home"}
