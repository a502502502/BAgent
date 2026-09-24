"""Classifica le combo gol solo contro una quota vera del banco.

Senza quota non c'è edge: la fair odd non viene travestita da prezzo.
Il sesto senso, se c'è, modifica i gol attesi e toglie le combo fragili
prima della classifica.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from services.analysis.xg_poisson_engine import QuantitativeEngine, _goal_market_mask
from services.football.sixth_sense.lambda_context import (
    MatchContext,
    market_context_veto,
    project_attack,
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
    "MultiGol 1-3 Casa",
    "MultiGol 1-3 Ospite",
    "MultiGol 1-4",
    "MultiGol 1-5",
    "MultiGol 2-5",
    "Over 1.5",
    "Over 2.5",
    "Under 2.5",
    "Under 3.5",
)

_HOME_CAPPED = ("multigol 1-2 casa", "multigol 1-3 casa")
_AWAY_CAPPED = ("multigol 1-2 ospite", "multigol 1-3 ospite")
_FIRST_HALF = ("1°", "1º", "1t", "primo tempo")


@dataclass(frozen=True)
class PricedCombo:
    market: str
    probability: float
    fair_odd: float
    book_odd: float
    edge: float


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
    projection = project_attack(xg_home, xg_away, context or MatchContext())
    engine = QuantitativeEngine()
    matrix, home, away, total = engine._score_axes(projection.xg_home, projection.xg_away)
    prices = book_odds or {}
    ranked: list[PricedCombo] = []
    rejected: list[RejectedCombo] = []
    for market in catalog:
        mask = _goal_market_mask(market, home, away, total)
        if mask is None:
            rejected.append(RejectedCombo(market, "mercato non mappato sulla matrice gol"))
            continue
        veto = _veto(market, mask, projection)
        if veto:
            rejected.append(RejectedCombo(market, veto))
            continue
        quoted = prices.get(market)
        if quoted is None or quoted <= 1.0:
            rejected.append(RejectedCombo(market, "quota del banco assente"))
            continue
        probability = float(np.sum(matrix[mask]))
        if probability < min_probability:
            rejected.append(RejectedCombo(market, f"probabilità {probability:.1%} sotto la soglia"))
            continue
        edge = probability * quoted - 1.0
        if edge < min_edge:
            rejected.append(RejectedCombo(market, f"edge {edge:+.1%} sotto la soglia"))
            continue
        ranked.append(
            PricedCombo(
                market=market,
                probability=probability,
                fair_odd=1.0 / probability,
                book_odd=quoted,
                edge=edge,
            )
        )
    ranked.sort(key=lambda combo: combo.edge, reverse=True)
    return ComboSearch(
        xg_home=projection.xg_home,
        xg_away=projection.xg_away,
        notes=projection.notes,
        ranked=tuple(ranked),
        rejected=tuple(rejected),
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
