"""Classifica le combo gol solo contro una quota vera del banco.

Senza quota non c'è edge: la fair odd non viene travestita da prezzo.
Il sesto senso, se c'è, modifica i gol attesi e toglie le combo fragili
prima della classifica.

Il cacciatore di mercati nascosti (`find_hidden_gems`) tiene solo lo sweet spot:
probabilità di matrice almeno 70%, edge almeno +4.5%, quota tra 1.35 e 1.80,
e nessun veto tattico. I corner, se la media è fornita, usano la binomiale
negativa congiunta sui valori già spostati da `project_corners`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from services.analysis.xg_poisson_engine import QuantitativeEngine, _goal_market_mask
from services.football.sixth_sense.lambda_context import (
    AttackProjection,
    MatchContext,
    market_context_veto,
    project_attack,
    project_corners,
)

COMBO_CATALOG: tuple[str, ...] = (
    "Chance Mix: 1X o Over 1.5",
    "Chance Mix: X2 o Over 1.5",
    "Chance Mix: 1X o Gol",
    "Chance Mix: X2 o Gol",
    "Gol o Over 2.5",
    "1X + Over 1.5",
    "1X + Under 3.5",
    "X2 + Over 1.5",
    "X2 + Under 3.5",
    "1X + Gol",
    "X2 + Gol",
    "1X + MultiGol 1-4",
    "X2 + MultiGol 1-5",
    "1 + Over 1.5",
    "2 + Over 1.5",
    "MultiGol 1-2 Casa",
    "MultiGol 1-3 Casa",
    "MultiGol 2-3 Casa",
    "MultiGol 1-2 Ospite",
    "MultiGol 1-3 Ospite",
    "MultiGol 1-3",
    "MultiGol 1-4",
    "MultiGol 1-5",
    "MultiGol 2-4",
    "MultiGol 2-5",
    "MultiGol 3-5",
    "1X + MultiGol 1-3",
    "1X + MultiGol 2-4",
    "1X + MultiGol 2-5",
    "X2 + MultiGol 1-3",
    "X2 + MultiGol 1-4",
    "X2 + MultiGol 2-4",
    "X2 + MultiGol 2-5",
    "1X + Under 2.5",
    "1X + Under 4.5",
    "X2 + Under 2.5",
    "X2 + Under 4.5",
    "1 + MultiGol 1-4",
    "2 + MultiGol 1-4",
    "1 + MultiGol 2-5",
    "2 + MultiGol 2-5",
    "Over 1.5",
    "Over 2.5",
    "Under 2.5",
    "Under 3.5",
)

_HOME_CAPPED = ("multigol 1-2 casa", "multigol 1-3 casa", "multigol 2-3 casa")
_AWAY_CAPPED = ("multigol 1-2 ospite", "multigol 1-3 ospite", "multigol 2-3 ospite")
_FIRST_HALF = ("1°", "1º", "1t", "primo tempo")


@dataclass(frozen=True)
class HiddenMarketFilter:
    """Quattro soglie dello sweet spot. Sotto o sopra la banda di quota il valore non entra."""

    min_probability: float = 0.70
    min_edge: float = 0.045
    min_odd: float = 1.35
    max_odd: float = 1.80


@dataclass(frozen=True)
class _PricePolicy:
    min_probability: float
    min_edge: float
    min_odd: float | None = None
    max_odd: float | None = None


@dataclass(frozen=True)
class PricedCombo:
    market: str
    probability: float
    fair_odd: float
    book_odd: float
    edge: float
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RejectedCombo:
    market: str
    reason: str


@dataclass(frozen=True)
class ComboSearch:
    xg_home: float
    xg_away: float
    notes: tuple[str, ...]
    ranked: tuple[PricedCombo, ...]
    rejected: tuple[RejectedCombo, ...]


def search_combo_edge(
    xg_home: float,
    xg_away: float,
    book_odds: dict[str, float] | None = None,
    context: MatchContext | None = None,
    min_edge: float = 0.04,
    min_probability: float = 0.55,
    catalog: tuple[str, ...] = COMBO_CATALOG,
) -> ComboSearch:
    return _classify(
        xg_home,
        xg_away,
        book_odds,
        context,
        _PricePolicy(min_probability, min_edge),
        catalog,
    )


def find_hidden_gems(
    xg_home: float,
    xg_away: float,
    book_odds: dict[str, float] | None = None,
    context: MatchContext | None = None,
    sweet: HiddenMarketFilter | None = None,
    corners_home: float | None = None,
    corners_away: float | None = None,
    catalog: tuple[str, ...] = COMBO_CATALOG,
) -> ComboSearch:
    """Pepite: sweet spot sul catalogo gol e, se le medie ci sono, sugli Over corner quotati."""
    band = sweet or HiddenMarketFilter()
    result = _classify(
        xg_home,
        xg_away,
        book_odds,
        context,
        _PricePolicy(band.min_probability, band.min_edge, band.min_odd, band.max_odd),
        catalog,
        corners_home=corners_home,
        corners_away=corners_away,
        price_corners=True,
    )
    return result


def _classify(
    xg_home: float,
    xg_away: float,
    book_odds: dict[str, float] | None,
    context: MatchContext | None,
    policy: _PricePolicy,
    catalog: tuple[str, ...],
    corners_home: float | None = None,
    corners_away: float | None = None,
    price_corners: bool = False,
) -> ComboSearch:
    match = context or MatchContext()
    projection = project_attack(xg_home, xg_away, match)
    engine = QuantitativeEngine()
    matrix, home, away, total = engine._score_axes(projection.xg_home, projection.xg_away)
    prices = book_odds or {}
    ranked: list[PricedCombo] = []
    rejected: list[RejectedCombo] = []
    seen: set[str] = set()
    for market in catalog:
        seen.add(market)
        mask = _goal_market_mask(market, home, away, total)
        if mask is None:
            rejected.append(RejectedCombo(market, "mercato non mappato sulla matrice gol"))
            continue
        veto = _veto(market, mask, projection)
        if veto:
            rejected.append(RejectedCombo(market, veto))
            continue
        _consider(
            market,
            float(np.sum(matrix[mask])),
            prices.get(market),
            policy,
            projection.notes,
            ranked,
            rejected,
        )
    if price_corners and (corners_home is not None or corners_away is not None or _quoted_corners(prices)):
        _consider_corners(
            engine,
            match,
            projection,
            prices,
            policy,
            ranked,
            rejected,
            corners_home,
            corners_away,
            seen,
        )
    ranked.sort(key=lambda combo: combo.edge, reverse=True)
    notes = projection.notes
    return ComboSearch(
        xg_home=projection.xg_home,
        xg_away=projection.xg_away,
        notes=notes,
        ranked=tuple(ranked),
        rejected=tuple(rejected),
    )


def _quoted_corners(prices: dict[str, float]) -> bool:
    return any("corner" in market.lower() for market in prices)


def _consider_corners(
    engine: QuantitativeEngine,
    match: MatchContext,
    projection: AttackProjection,
    prices: dict[str, float],
    policy: _PricePolicy,
    ranked: list[PricedCombo],
    rejected: list[RejectedCombo],
    corners_home: float | None,
    corners_away: float | None,
    seen: set[str],
) -> None:
    projected = project_corners(
        corners_home,
        corners_away,
        match,
        projection.xg_home,
        projection.xg_away,
    )
    notes = projection.notes + projected.notes
    for market, quoted in prices.items():
        if market in seen or "corner" not in market.lower():
            continue
        veto = market_context_veto(market, projection)
        if veto:
            rejected.append(RejectedCombo(market, veto))
            continue
        if corners_home is None or corners_away is None:
            rejected.append(RejectedCombo(market, "corner non forniti: proiezione base"))
            continue
        probability = engine.corner_over_probability(
            projected.corners_home,
            projected.corners_away,
            market,
        )
        if probability is None or probability <= 0.0:
            rejected.append(RejectedCombo(market, "mercato corner non mappato"))
            continue
        _consider(market, probability, quoted, policy, notes, ranked, rejected)


def _consider(
    market: str,
    probability: float,
    quoted: float | None,
    policy: _PricePolicy,
    notes: tuple[str, ...],
    ranked: list[PricedCombo],
    rejected: list[RejectedCombo],
) -> None:
    if quoted is None or quoted <= 1.0:
        rejected.append(RejectedCombo(market, "quota del banco assente"))
        return
    if policy.min_odd is not None and quoted < policy.min_odd:
        rejected.append(RejectedCombo(market, f"quota {quoted:.2f} sotto il minimo {policy.min_odd:.2f}"))
        return
    if probability < policy.min_probability:
        rejected.append(RejectedCombo(market, f"probabilità {probability:.1%} sotto la soglia"))
        return
    if policy.max_odd is not None and quoted > policy.max_odd:
        rejected.append(RejectedCombo(market, f"quota {quoted:.2f} sopra il massimo {policy.max_odd:.2f}"))
        return
    edge = probability * quoted - 1.0
    if edge < policy.min_edge:
        rejected.append(RejectedCombo(market, f"edge {edge:+.1%} sotto la soglia"))
        return
    ranked.append(
        PricedCombo(
            market=market,
            probability=probability,
            fair_odd=1.0 / probability,
            book_odd=quoted,
            edge=edge,
            notes=notes,
        )
    )


def _veto(market: str, mask: np.ndarray, projection) -> str | None:
    name = market.lower()
    contextual = market_context_veto(market, projection)
    if contextual:
        return contextual
    if projection.veto_first_half and any(token in name for token in _FIRST_HALF):
        return "sesto senso: mercato che può morire al 45'"
    if projection.veto_home_one_nil and not bool(mask[1, 0]):
        return "sesto senso: il corto muso casa perde questa combo sull'1-0"
    if projection.veto_away_one_nil and not bool(mask[0, 1]):
        return "sesto senso: il corto muso ospite perde questa combo sullo 0-1"
    if projection.veto_home_ceiling and any(token in name for token in _HOME_CAPPED):
        return "sesto senso: tetto di gol sulla favorita casa"
    if projection.veto_away_ceiling and any(token in name for token in _AWAY_CAPPED):
        return "sesto senso: tetto di gol sulla favorita ospite"
    if (projection.veto_home_ceiling or projection.veto_away_ceiling) and "under 2.5" in name:
        return "sesto senso: under stretto contro un attacco dominante"
    return None
