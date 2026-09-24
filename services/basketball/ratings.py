"""Rating di squadra calcolati solo con le partite già giocate."""

from __future__ import annotations

from dataclasses import dataclass, field

from services.basketball.gamelog import PairedGame


@dataclass(frozen=True)
class TeamRating:
    team: str
    games: int
    pace: float
    offensive_rating: float
    defensive_rating: float


@dataclass
class _TeamTotals:
    games: int = 0
    points: float = 0.0
    points_allowed: float = 0.0
    possessions: float = 0.0
    last_date: object | None = None


@dataclass
class RatingBook:
    """Possessi, punti segnati e punti subiti. Lo snapshot non include la giornata in corso."""

    _teams: dict[str, _TeamTotals] = field(default_factory=dict)

    def snapshot(self) -> dict[str, TeamRating]:
        ratings: dict[str, TeamRating] = {}
        for team, totals in self._teams.items():
            if totals.games == 0 or totals.possessions <= 0:
                continue
            ratings[team] = TeamRating(
                team=team,
                games=totals.games,
                pace=totals.possessions / totals.games,
                offensive_rating=100.0 * totals.points / totals.possessions,
                defensive_rating=100.0 * totals.points_allowed / totals.possessions,
            )
        return ratings

    def league_average_rating(self) -> float | None:
        points = 0.0
        possessions = 0.0
        for totals in self._teams.values():
            points += totals.points
            possessions += totals.possessions
        if possessions <= 0:
            return None
        return 100.0 * points / possessions

    def last_played(self, team: str):
        totals = self._teams.get(team)
        if totals is None:
            return None
        return totals.last_date

    def update(self, game: PairedGame) -> None:
        self._add(game.home, game.home_points, game.away_points, game.possessions, game.game_date)
        self._add(game.away, game.away_points, game.home_points, game.possessions, game.game_date)

    def _add(self, team: str, points: float, allowed: float, possessions: float, game_date) -> None:
        totals = self._teams.setdefault(team, _TeamTotals())
        totals.games += 1
        totals.points += points
        totals.points_allowed += allowed
        totals.possessions += possessions
        totals.last_date = game_date
