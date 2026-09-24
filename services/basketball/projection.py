"""Proiezione di margine e totale da pace e quattro fattori di squadra."""

from __future__ import annotations

from dataclasses import dataclass

from services.basketball.ratings import TeamRating


@dataclass(frozen=True)
class ScoreProjection:
    home_points: float
    away_points: float
    pace: float
    home_court: float

    @property
    def margin(self) -> float:
        return self.home_points - self.away_points

    @property
    def total(self) -> float:
        return self.home_points + self.away_points


def project_score(
    home: TeamRating,
    away: TeamRating,
    league_average: float,
    home_court: float = 0.0,
) -> ScoreProjection:
    """Punti attesi = pace comune × rating di scontro.

    Il rating di scontro è offensivo proprio + difensivo avversario − media lega,
    così il livello medio del campionato non viene contato due volte.
    Il vantaggio del campo si divide a metà sui due punteggi e non cambia il totale.
    """
    pace = (home.pace + away.pace) / 2
    home_rating = home.offensive_rating + away.defensive_rating - league_average
    away_rating = away.offensive_rating + home.defensive_rating - league_average
    return ScoreProjection(
        home_points=pace * home_rating / 100.0 + home_court / 2,
        away_points=pace * away_rating / 100.0 - home_court / 2,
        pace=pace,
        home_court=home_court,
    )
