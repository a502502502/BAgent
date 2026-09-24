"""Gol e corner ancora da giocare, prezzati sul tempo che resta.

La probabilità non è una costante del trigger. È la massa della matrice
dei gol residui, dopo il sesto senso, l'espulsione e il momentum dei tiri.
Un mercato già chiuso dal punteggio non viene rivenduto.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.stats import poisson

from services.analysis.xg_poisson_engine import QuantitativeEngine
from services.betting.netwin_market_parser import (
    NetwinMarketAction,
    UnsupportedNetwinMarket,
    parse_netwin_selection,
)
from services.football.sixth_sense.lambda_context import MatchContext, project_attack

RED_CARD_ATTACK = 0.72
RED_CARD_OPPONENT = 1.08
MOMENTUM_FLOOR = 0.85
MOMENTUM_CAP = 1.18
SIEGE_ATTACK = 1.10
CORNER_SIEGE = 1.12
CORNER_PARKED = 0.85
CORNER_PRIOR_HOME = 5.0
CORNER_PRIOR_AWAY = 4.2
KELLY_FRACTION = 0.25
SETTLED = 0.995


@dataclass(frozen=True)
class LiveSweetSpot:
    """Banda live: quota né straccia né speculativa, massa e edge minimi."""

    min_odd: float = 1.35
    max_odd: float = 1.90
    min_probability: float = 0.72
    min_edge: float = 0.05
    min_stake_pct: float = 0.015
    max_stake_pct: float = 0.030


@dataclass(frozen=True)
class ResidualState:
    minute: int
    stoppage: int
    time_fraction: float
    lambda_home: float
    lambda_away: float
    notes: tuple[str, ...]
    matrix: np.ndarray
    favorite: str
    siege: bool
    corner_remaining_home: float
    corner_remaining_away: float


@dataclass(frozen=True)
class PricedLiveMarket:
    market: str
    probability: float
    fair_odd: float
    book_odd: float
    edge: float
    stake_pct: float
    family: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class RejectedLiveMarket:
    market: str
    reason: str


def residual_time_fraction(minute: int, stoppage: int = 4) -> float:
    """Minuti ancora da giocare, recupero compreso, come frazione dei 90."""
    remaining = max(1, (90 + stoppage) - int(minute))
    return remaining / 90.0


def inplay_stake_pct(probability: float, odd: float, spot: LiveSweetSpot | None = None) -> float:
    """Quarter Kelly schiacciato nella banda 1,5%–3% del bankroll."""
    band = spot or LiveSweetSpot()
    net = odd - 1.0
    if net <= 0 or probability <= 0:
        return band.min_stake_pct
    full = (probability * odd - 1.0) / net
    quarter = max(0.0, full) * KELLY_FRACTION
    return min(band.max_stake_pct, max(band.min_stake_pct, quarter))


def project_residual(
    xg_home: float,
    xg_away: float,
    minute: int,
    *,
    stoppage: int = 4,
    home_goals: int = 0,
    away_goals: int = 0,
    home_reds: int = 0,
    away_reds: int = 0,
    home_shots: int = 0,
    away_shots: int = 0,
    home_shots_on_target: int = 0,
    away_shots_on_target: int = 0,
    recent_shots_home: int | None = None,
    recent_shots_away: int | None = None,
    home_corners: int = 0,
    away_corners: int = 0,
    corner_avg_home: float | None = None,
    corner_avg_away: float | None = None,
    favorite: str = "EQUAL",
    context: MatchContext | None = None,
) -> ResidualState:
    """Lambda residui: sesto senso, frazione di tempo, espulsione, momentum, assedio."""
    fraction = residual_time_fraction(minute, stoppage)
    attack = project_attack(xg_home, xg_away, context or MatchContext())
    home = attack.xg_home * fraction
    away = attack.xg_away * fraction
    notes = list(attack.notes)
    notes.append(f"tempo residuo {fraction:.1%} dei 90, dal {minute}'")

    if home_reds > 0:
        home *= RED_CARD_ATTACK
        away *= RED_CARD_OPPONENT
        notes.append("casa in 10: attacco casa -28%, ospite +8%")
    if away_reds > 0:
        away *= RED_CARD_ATTACK
        home *= RED_CARD_OPPONENT
        notes.append("ospite in 10: attacco ospite -28%, casa +8%")

    shot_home = home_shots if recent_shots_home is None else recent_shots_home
    shot_away = away_shots if recent_shots_away is None else recent_shots_away
    home_momentum = _momentum(shot_home, shot_away, home_shots_on_target, away_shots_on_target)
    away_momentum = _momentum(shot_away, shot_home, away_shots_on_target, home_shots_on_target)
    home *= home_momentum
    away *= away_momentum
    if home_momentum != 1.0 or away_momentum != 1.0:
        notes.append(
            f"momentum tiri: casa {home_momentum:.2f}x, ospite {away_momentum:.2f}x"
        )

    side = _favorite(favorite, attack.xg_home, attack.xg_away)
    siege = _under_siege(side, home_goals, away_goals, shot_home, shot_away)
    if siege and side == "HOME":
        home *= SIEGE_ATTACK
        notes.append("assedio della favorita casa: attacco residuo +10%")
    elif siege and side == "AWAY":
        away *= SIEGE_ATTACK
        notes.append("assedio della favorita ospite: attacco residuo +10%")

    home = max(0.01, home)
    away = max(0.01, away)
    matrix = QuantitativeEngine().generate_score_matrix(home, away, max_goals=8)
    corners = _remaining_corners(
        minute,
        fraction,
        home_corners,
        away_corners,
        corner_avg_home,
        corner_avg_away,
        siege,
        side,
    )
    return ResidualState(
        minute=minute,
        stoppage=stoppage,
        time_fraction=fraction,
        lambda_home=home,
        lambda_away=away,
        notes=tuple(notes),
        matrix=matrix,
        favorite=side,
        siege=siege,
        corner_remaining_home=corners[0],
        corner_remaining_away=corners[1],
    )


def next_goal_probabilities(lambda_home: float, lambda_away: float) -> tuple[float, float, float]:
    """Prossimo gol casa, ospite, nessun altro gol. I tre esiti sommano a 1."""
    total = max(0.0, lambda_home) + max(0.0, lambda_away)
    if total <= 1e-9:
        return 0.0, 0.0, 1.0
    none = math.exp(-total)
    contested = 1.0 - none
    return (lambda_home / total) * contested, (lambda_away / total) * contested, none


def price_live_market(
    state: ResidualState,
    market: str,
    *,
    home_goals: int,
    away_goals: int,
    home_corners: int = 0,
    away_corners: int = 0,
    second_half_goals: int | None = None,
) -> float | None:
    """P live del mercato. None se il nome non è un mercato gol o corner mappato."""
    try:
        action = parse_netwin_selection("", market)
    except UnsupportedNetwinMarket:
        return None
    if action.family == "NEXT_GOAL":
        home, away, none = next_goal_probabilities(state.lambda_home, state.lambda_away)
        return {"HOME": home, "AWAY": away, "NONE": none}.get(action.pick or "")
    if action.family == "CORNER":
        return _corner_probability(state, action, home_corners, away_corners)
    if _is_second_half(market):
        if second_half_goals is None:
            return None
        return _count_band(state, action, second_half_goals, scope="TOTAL")
    return _goal_probability(state, action, home_goals, away_goals)


def scan_live_book(
    state: ResidualState,
    book_odds: dict[str, float] | None,
    *,
    home_goals: int,
    away_goals: int,
    home_corners: int = 0,
    away_corners: int = 0,
    second_half_goals: int | None = None,
    suspended: bool = False,
    suspended_markets: set[str] | None = None,
    spot: LiveSweetSpot | None = None,
) -> tuple[tuple[PricedLiveMarket, ...], tuple[RejectedLiveMarket, ...]]:
    """Tiene solo lo sweet spot. Senza quota, o con il mercato sospeso, non esce nulla."""
    band = spot or LiveSweetSpot()
    ranked: list[PricedLiveMarket] = []
    rejected: list[RejectedLiveMarket] = []
    blocked = suspended_markets or set()
    if suspended:
        return (), tuple(
            RejectedLiveMarket(market, "quote sospese") for market in (book_odds or {})
        )
    for market, quoted in (book_odds or {}).items():
        if market in blocked or quoted is None or quoted <= 1.0:
            rejected.append(RejectedLiveMarket(market, "quote sospese"))
            continue
        probability = price_live_market(
            state,
            market,
            home_goals=home_goals,
            away_goals=away_goals,
            home_corners=home_corners,
            away_corners=away_corners,
            second_half_goals=second_half_goals,
        )
        if probability is None:
            rejected.append(RejectedLiveMarket(market, "mercato non mappato"))
            continue
        if probability >= SETTLED or probability <= 1.0 - SETTLED:
            rejected.append(RejectedLiveMarket(market, "esito già determinato dal punteggio"))
            continue
        if quoted < band.min_odd or quoted > band.max_odd:
            rejected.append(
                RejectedLiveMarket(market, f"quota {quoted:.2f} fuori dalla banda {band.min_odd:.2f}-{band.max_odd:.2f}")
            )
            continue
        if probability < band.min_probability:
            rejected.append(RejectedLiveMarket(market, f"probabilità {probability:.1%} sotto la soglia"))
            continue
        edge = probability * quoted - 1.0
        if edge < band.min_edge:
            rejected.append(RejectedLiveMarket(market, f"edge {edge:+.1%} sotto la soglia"))
            continue
        try:
            family = parse_netwin_selection("", market).family
        except UnsupportedNetwinMarket:
            family = ""
        ranked.append(
            PricedLiveMarket(
                market=market,
                probability=probability,
                fair_odd=1.0 / probability,
                book_odd=quoted,
                edge=edge,
                stake_pct=inplay_stake_pct(probability, quoted, band),
                family=family,
                notes=state.notes,
            )
        )
    ranked.sort(key=lambda item: item.edge, reverse=True)
    return tuple(ranked), tuple(rejected)


def _momentum(own_shots: int, other_shots: int, own_on_target: int, other_on_target: int) -> float:
    total = own_shots + other_shots
    if total <= 0:
        return 1.0
    share = own_shots / total
    factor = 1.0 + 0.36 * ((share - 0.5) / 0.5)
    target_total = own_on_target + other_on_target
    if target_total > 0 and own_shots > 0:
        quality = own_on_target / own_shots
        other_quality = other_on_target / other_shots if other_shots else 0.0
        factor += 0.08 * (quality - other_quality)
    return min(MOMENTUM_CAP, max(MOMENTUM_FLOOR, factor))


def _favorite(label: str, xg_home: float, xg_away: float) -> str:
    if label in ("HOME", "AWAY"):
        return label
    if xg_home >= xg_away + 0.35:
        return "HOME"
    if xg_away >= xg_home + 0.35:
        return "AWAY"
    return "EQUAL"


def _under_siege(favorite: str, home_goals: int, away_goals: int, home_shots: int, away_shots: int) -> bool:
    if favorite == "HOME":
        return home_goals <= away_goals and home_shots >= max(4, int(away_shots * 1.5))
    if favorite == "AWAY":
        return away_goals <= home_goals and away_shots >= max(4, int(home_shots * 1.5))
    return False


def _remaining_corners(
    minute: int,
    fraction: float,
    home_corners: int,
    away_corners: int,
    avg_home: float | None,
    avg_away: float | None,
    siege: bool,
    favorite: str,
) -> tuple[float, float]:
    played = min(max(minute, 1), 90) / 90.0
    if avg_home is None or avg_away is None:
        weight = min(0.70, played)
        observed_home = home_corners / played
        observed_away = away_corners / played
        avg_home = (1.0 - weight) * CORNER_PRIOR_HOME + weight * observed_home
        avg_away = (1.0 - weight) * CORNER_PRIOR_AWAY + weight * observed_away
    home = float(avg_home) * fraction
    away = float(avg_away) * fraction
    if siege and favorite == "HOME":
        home *= CORNER_SIEGE
        away *= CORNER_PARKED
    elif siege and favorite == "AWAY":
        away *= CORNER_SIEGE
        home *= CORNER_PARKED
    return max(0.05, home), max(0.05, away)


def _is_second_half(market: str) -> bool:
    name = market.lower()
    return "2°" in name or "2º" in name or "secondo tempo" in name or "2 tempo" in name


def _corner_probability(
    state: ResidualState,
    action: NetwinMarketAction,
    home_corners: int,
    away_corners: int,
) -> float | None:
    if action.specialty_side not in ("OVER", "UNDER") or action.specialty_line is None:
        return None
    if action.specialty_scope == "HOME":
        current = home_corners
        mean = state.corner_remaining_home
    elif action.specialty_scope == "AWAY":
        current = away_corners
        mean = state.corner_remaining_away
    else:
        current = home_corners + away_corners
        mean = state.corner_remaining_home + state.corner_remaining_away
    needed = action.specialty_line - current
    if action.specialty_side == "OVER":
        return _poisson_over(mean, needed)
    return 1.0 - _poisson_over(mean, needed)


def _poisson_over(mean: float, line: float) -> float:
    """P(X > line) per una Poisson dei corner ancora da battere."""
    if line < 0:
        return 1.0
    return float(1.0 - poisson.cdf(math.floor(line), max(1e-6, mean)))


def _goal_probability(
    state: ResidualState,
    action: NetwinMarketAction,
    home_goals: int,
    away_goals: int,
) -> float | None:
    matrix = state.matrix
    total = 0.0
    covered = 0.0
    goals = matrix.shape[0]
    for delta_home in range(goals):
        for delta_away in range(goals):
            weight = float(matrix[delta_home, delta_away])
            total += weight
            final_home = home_goals + delta_home
            final_away = away_goals + delta_away
            if _final_hit(action, final_home, final_away):
                covered += weight
    if total <= 0:
        return None
    return covered / total


def _count_band(state: ResidualState, action: NetwinMarketAction, already: int, scope: str) -> float | None:
    low, high = _range_bounds(action)
    if low is None:
        return None
    matrix = state.matrix
    total = 0.0
    covered = 0.0
    goals = matrix.shape[0]
    for delta_home in range(goals):
        for delta_away in range(goals):
            weight = float(matrix[delta_home, delta_away])
            total += weight
            added = delta_home + delta_away if scope == "TOTAL" else delta_home
            count = already + added
            if low <= count <= high:
                covered += weight
    if total <= 0:
        return None
    return covered / total


def _range_bounds(action: NetwinMarketAction) -> tuple[int | None, int | None]:
    raw = action.multigol_range or action.combo_multigol_range or ""
    parts = raw.split("-")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return None, None
    return int(parts[0]), int(parts[1])


def _final_hit(action: NetwinMarketAction, home: int, away: int) -> bool:
    total = home + away
    if action.family == "OU" and action.ou_line is not None:
        if action.pick == "OVER":
            return total > action.ou_line
        if action.pick == "UNDER":
            return total < action.ou_line
        return False
    if action.family == "MULTIGOL":
        low, high = _range_bounds(action)
        if low is None or high is None:
            return False
        count = total
        if action.multigol_scope == "HOME":
            count = home
        elif action.multigol_scope == "AWAY":
            count = away
        return low <= count <= high
    if action.family == "BTTS":
        both = home >= 1 and away >= 1
        return both if action.pick == "GOL" else not both
    if action.family == "1X2":
        return { "1": home > away, "X": home == away, "2": away > home }.get(action.pick, False)
    if action.family == "DC":
        return { "1X": home >= away, "X2": away >= home, "12": home != away }.get(action.pick, False)
    if action.family == "COMBO":
        return _combo_hit(action, home, away)
    return False


def _combo_hit(action: NetwinMarketAction, home: int, away: int) -> bool:
    result = {
        "1": home > away,
        "X": home == away,
        "2": away > home,
        "1X": home >= away,
        "X2": away >= home,
        "12": home != away,
    }.get(action.combo_result or "", False)
    if not result:
        return False
    total = home + away
    if action.combo_type == "OU" and action.combo_ou_line is not None:
        if action.combo_ou_side == "OVER":
            return total > action.combo_ou_line
        if action.combo_ou_side == "UNDER":
            return total < action.combo_ou_line
        return False
    if action.combo_type == "BTTS":
        both = home >= 1 and away >= 1
        return both if action.combo_ou_side == "GOL" else not both
    if action.combo_type == "MULTIGOL":
        low, high = _range_bounds(action)
        if low is None or high is None:
            return False
        count = total
        if action.combo_multigol_scope == "HOME":
            count = home
        elif action.combo_multigol_scope == "AWAY":
            count = away
        return low <= count <= high
    return False
