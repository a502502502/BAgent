"""Walk-forward: ogni proiezione usa solo le partite precedenti della stessa stagione."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from services.basketball.gamelog import PairedGame
from services.basketball.pricing import choose_side, home_cover_probability, over_probability
from services.basketball.projection import project_score
from services.basketball.ratings import RatingBook


@dataclass(frozen=True)
class ClosingLine:
    game_date: date
    home: str
    away: str
    home_spread: float
    total: float | None = None
    home_spread_odds: float | None = None
    away_spread_odds: float | None = None
    over_odds: float | None = None
    under_odds: float | None = None


@dataclass(frozen=True)
class ProjectionRow:
    season: str
    game_date: date
    home: str
    away: str
    predicted_margin: float
    predicted_total: float
    margin_sigma: float
    total_sigma: float
    actual_margin: int
    actual_total: int
    home_spread: float | None = None
    total_line: float | None = None
    spread_side: str | None = None
    spread_edge: float | None = None
    spread_odds: float | None = None
    spread_result: str | None = None
    total_side: str | None = None
    total_edge: float | None = None
    total_odds: float | None = None
    total_result: str | None = None


@dataclass
class BacktestSummary:
    projections: int
    margin_mae: float
    total_mae: float
    spread_bets: int = 0
    spread_pushes: int = 0
    spread_hit_rate: float | None = None
    spread_roi: float | None = None
    total_bets: int = 0
    total_pushes: int = 0
    total_hit_rate: float | None = None
    total_roi: float | None = None
    lines_joined: int = 0


@dataclass
class WalkForwardBacktest:
    """Prior di lega, poi sostituiti dai residui della stagione già osservata.

    2.5 punti di campo e sigma 12/15 sono priori di scala, non numeri letti
    da una stagione futura. Con poche partite pesano; dopo si spengono.
    """

    min_games: int = 10
    min_edge: float = 0.04
    default_odds: float = 1.87
    home_court_prior: float = 2.5
    home_court_strength: float = 10.0
    margin_sigma_prior: float = 12.0
    total_sigma_prior: float = 15.0
    sigma_strength: float = 20.0
    _home_court_residuals: list[float] = field(default_factory=list)
    _margin_residuals: list[float] = field(default_factory=list)
    _total_residuals: list[float] = field(default_factory=list)

    def run(
        self,
        games: list[PairedGame],
        lines: list[ClosingLine] | None = None,
    ) -> list[ProjectionRow]:
        by_line = {
            (line.game_date, line.home.upper(), line.away.upper()): line
            for line in (lines or [])
        }
        rows: list[ProjectionRow] = []
        ordered = sorted(games, key=lambda game: (game.season, game.game_date, game.game_id))
        book = RatingBook()
        current_season: str | None = None
        index = 0
        while index < len(ordered):
            season = ordered[index].season
            if season != current_season:
                book = RatingBook()
                self._home_court_residuals.clear()
                self._margin_residuals.clear()
                self._total_residuals.clear()
                current_season = season
            slate_date = ordered[index].game_date
            slate: list[PairedGame] = []
            while index < len(ordered) and ordered[index].season == season and ordered[index].game_date == slate_date:
                slate.append(ordered[index])
                index += 1
            ratings = book.snapshot()
            league_average = book.league_average_rating()
            home_court = _shrunk_mean(
                self._home_court_residuals,
                self.home_court_prior,
                self.home_court_strength,
            )
            margin_sigma = _shrunk_std(
                self._margin_residuals,
                self.margin_sigma_prior,
                self.sigma_strength,
            )
            total_sigma = _shrunk_std(
                self._total_residuals,
                self.total_sigma_prior,
                self.sigma_strength,
            )
            for game in slate:
                home = ratings.get(game.home)
                away = ratings.get(game.away)
                if (
                    league_average is None
                    or home is None
                    or away is None
                    or home.games < self.min_games
                    or away.games < self.min_games
                ):
                    continue
                raw = project_score(home, away, league_average, home_court=0.0)
                projected = project_score(home, away, league_average, home_court=home_court)
                line = by_line.get((game.game_date, game.home, game.away))
                row = _grade(
                    game,
                    projected.margin,
                    projected.total,
                    margin_sigma,
                    total_sigma,
                    line,
                    self.min_edge,
                    self.default_odds,
                )
                rows.append(row)
                self._home_court_residuals.append(game.margin - raw.margin)
                self._margin_residuals.append(game.margin - projected.margin)
                self._total_residuals.append(game.total - projected.total)
            for game in slate:
                book.update(game)
        return rows


def summarize(rows: list[ProjectionRow]) -> BacktestSummary:
    if not rows:
        return BacktestSummary(0, 0.0, 0.0)
    margin_mae = sum(abs(row.actual_margin - row.predicted_margin) for row in rows) / len(rows)
    total_mae = sum(abs(row.actual_total - row.predicted_total) for row in rows) / len(rows)
    spread = [row for row in rows if row.spread_result is not None]
    totals = [row for row in rows if row.total_result is not None]
    return BacktestSummary(
        projections=len(rows),
        margin_mae=margin_mae,
        total_mae=total_mae,
        spread_bets=len(spread),
        spread_pushes=sum(row.spread_result == "push" for row in spread),
        spread_hit_rate=_hit_rate(row.spread_result for row in spread),
        spread_roi=_roi(spread, "spread"),
        total_bets=len(totals),
        total_pushes=sum(row.total_result == "push" for row in totals),
        total_hit_rate=_hit_rate(row.total_result for row in totals),
        total_roi=_roi(totals, "total"),
        lines_joined=sum(row.home_spread is not None for row in rows),
    )


def _grade(
    game: PairedGame,
    predicted_margin: float,
    predicted_total: float,
    margin_sigma: float,
    total_sigma: float,
    line: ClosingLine | None,
    min_edge: float,
    default_odds: float,
) -> ProjectionRow:
    spread_side = spread_edge = spread_odds = spread_result = None
    total_side = total_edge = total_odds = total_result = None
    home_spread = total_line = None
    if line is not None:
        home_spread = line.home_spread
        home_probability = home_cover_probability(predicted_margin, margin_sigma, line.home_spread)
        spread_choice = choose_side(
            {
                "home": (home_probability, line.home_spread_odds or default_odds),
                "away": (1.0 - home_probability, line.away_spread_odds or default_odds),
            },
            min_edge,
        )
        if spread_choice is not None:
            spread_side = spread_choice.side
            spread_edge = spread_choice.edge
            spread_odds = spread_choice.decimal_odds
            spread_result = _settle_spread(game.margin, line.home_spread, spread_choice.side)
        if line.total is not None:
            total_line = line.total
            over = over_probability(predicted_total, total_sigma, line.total)
            total_choice = choose_side(
                {
                    "over": (over, line.over_odds or default_odds),
                    "under": (1.0 - over, line.under_odds or default_odds),
                },
                min_edge,
            )
            if total_choice is not None:
                total_side = total_choice.side
                total_edge = total_choice.edge
                total_odds = total_choice.decimal_odds
                total_result = _settle_total(game.total, line.total, total_choice.side)
    return ProjectionRow(
        season=game.season,
        game_date=game.game_date,
        home=game.home,
        away=game.away,
        predicted_margin=predicted_margin,
        predicted_total=predicted_total,
        margin_sigma=margin_sigma,
        total_sigma=total_sigma,
        actual_margin=game.margin,
        actual_total=game.total,
        home_spread=home_spread,
        total_line=total_line,
        spread_side=spread_side,
        spread_edge=spread_edge,
        spread_odds=spread_odds,
        spread_result=spread_result,
        total_side=total_side,
        total_edge=total_edge,
        total_odds=total_odds,
        total_result=total_result,
    )


def _settle_spread(margin: int, home_spread: float, side: str) -> str:
    adjusted = margin + home_spread
    if abs(adjusted) < 1e-6:
        return "push"
    home_covers = adjusted > 0
    won = home_covers if side == "home" else not home_covers
    return "win" if won else "loss"


def _settle_total(actual: int, line: float, side: str) -> str:
    if abs(actual - line) < 1e-6:
        return "push"
    went_over = actual > line
    won = went_over if side == "over" else not went_over
    return "win" if won else "loss"


def _hit_rate(results) -> float | None:
    decided = [result for result in results if result in {"win", "loss"}]
    if not decided:
        return None
    return sum(result == "win" for result in decided) / len(decided)


def _roi(rows: list[ProjectionRow], market: str) -> float | None:
    profit = 0.0
    stakes = 0
    for row in rows:
        result = row.spread_result if market == "spread" else row.total_result
        odds = row.spread_odds if market == "spread" else row.total_odds
        if result not in {"win", "loss"} or odds is None:
            continue
        stakes += 1
        if result == "win":
            profit += odds - 1.0
        else:
            profit -= 1.0
    if stakes == 0:
        return None
    return profit / stakes


def _shrunk_mean(values: list[float], prior: float, strength: float) -> float:
    count = len(values)
    if count + strength == 0:
        return prior
    observed = sum(values) / count if count else prior
    return (count * observed + strength * prior) / (count + strength)


def _shrunk_std(values: list[float], prior: float, strength: float) -> float:
    count = len(values)
    if count == 0:
        return prior
    mean = sum(values) / count
    variance = sum((value - mean) ** 2 for value in values) / count
    blended = (count * variance + strength * prior ** 2) / (count + strength)
    return blended ** 0.5
