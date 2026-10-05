"""Sceglie la combinazione dalla matrice dei gol, non dall'EV.

Lo sweet spot del progetto è probabilità 80% e quota 1.45. Ogni mercato
quotato almeno 1.20 riceve un punteggio a campana intorno a quel centro:

    S(p, q) = exp(-1/2 * (((p - 0.80) / 0.12)^2 + ((ln q - ln 1.45) / 0.20)^2))

p esce da Dixon-Coles. q è la quota del banco. L'EV, p*q - 1, si allega
e non entra in S: un valore atteso negativo non toglie la riga.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from services.analysis.xg_poisson_engine import QuantitativeEngine

SWEET_PROBABILITY = 0.80
SWEET_ODD = 1.45
PROBABILITY_WIDTH = 0.12
ODD_WIDTH = 0.20
MIN_ODD = 1.20

_RIGID_RESULT = re.compile(r"^(?:1|2)(?:\s*\+|$)")
_CRUSHED_HOME = re.compile(
    r"^(?:2|x2)\b|chance mix:\s*(?:2|x2)\b|nogol|no gol|under 2\.5|under 3\.5|multigol 0-2 casa",
    re.IGNORECASE,
)
_CRUSHED_AWAY = re.compile(
    r"^(?:1|1x)\b|chance mix:\s*(?:1|1x)\b|nogol|no gol|under 2\.5|under 3\.5|multigol 0-2 ospite",
    re.IGNORECASE,
)
_TIGHT_TOTAL = re.compile(r"\b1-2\b|\b1-3\b|under 2\.5", re.IGNORECASE)


@dataclass(frozen=True)
class StatPick:
    market: str
    probability: float
    book_odd: float
    fair_odd: float
    edge: float
    score: float
    blocked: str | None = None

    @property
    def verdict(self) -> str:
        if self.edge >= 0.05:
            return "stella"
        if self.edge > 0:
            return "occhio"
        return "croce"


def statistical_score(probability: float, book_odd: float) -> float:
    """Distanza dallo sweet spot. 1 sul centro, vicino a 0 lontano."""
    if probability <= 0.0 or book_odd < MIN_ODD:
        return 0.0
    z_prob = (probability - SWEET_PROBABILITY) / PROBABILITY_WIDTH
    z_odd = (math.log(book_odd) - math.log(SWEET_ODD)) / ODD_WIDTH
    return math.exp(-0.5 * (z_prob * z_prob + z_odd * z_odd))


def structural_block(
    market: str,
    *,
    home_odd: float | None = None,
    away_odd: float | None = None,
    over_25: float | None = None,
    xg_home: float = 0.0,
    xg_away: float = 0.0,
) -> str | None:
    """Vincoli di mercato. L'EV non è tra questi."""
    name = market.strip().lower()
    if _RIGID_RESULT.match(name):
        return "1X2 secco"
    home_crushed = _crushed(home_odd, away_odd, over_25, favorite="home")
    away_crushed = _crushed(away_odd, home_odd, over_25, favorite="away")
    if home_crushed and _CRUSHED_HOME.search(name):
        return "corazzata in casa"
    if away_crushed and _CRUSHED_AWAY.search(name):
        return "corazzata in trasferta"
    if _dominant(xg_home, xg_away) and _TIGHT_TOTAL.search(name):
        return "tetto su attacco dominante"
    return None


def rank_statistical_combos(
    xg_home: float,
    xg_away: float,
    book_odds: dict[str, float],
    *,
    engine: QuantitativeEngine | None = None,
) -> tuple[StatPick, ...]:
    """Classifica i mercati quotati. I bloccati restano in coda, con il motivo."""
    pricer = engine or QuantitativeEngine()
    home_odd = book_odds.get("1")
    away_odd = book_odds.get("2")
    over_25 = book_odds.get("Over 2.5")
    picked: list[StatPick] = []
    for market, odd in book_odds.items():
        if market in {"1", "X", "2"} or odd is None or odd < MIN_ODD:
            continue
        probability = pricer.goal_market_probability(xg_home, xg_away, market)
        if probability is None or probability <= 0.0:
            continue
        block = structural_block(
            market,
            home_odd=home_odd,
            away_odd=away_odd,
            over_25=over_25,
            xg_home=xg_home,
            xg_away=xg_away,
        )
        edge = probability * odd - 1.0
        picked.append(
            StatPick(
                market=market,
                probability=probability,
                book_odd=odd,
                fair_odd=1.0 / probability,
                edge=edge,
                score=0.0 if block else statistical_score(probability, odd),
                blocked=block,
            )
        )
    picked.sort(key=lambda row: (row.blocked is not None, -row.score, -row.probability))
    return tuple(picked)


def best_combination(ranked: tuple[StatPick, ...] | list[StatPick]) -> StatPick | None:
    """La prima riga non bloccata. None se il banco non ha un mercato legale."""
    for row in ranked:
        if row.blocked is None and row.score > 0.0:
            return row
    return None


def best_ticket(picks: list[StatPick], size: int = 4) -> list[StatPick]:
    """Le migliori selezioni indipendenti, una già scelta per partita. Massimo 4."""
    legal = [row for row in picks if row.blocked is None and row.score > 0.0]
    legal.sort(key=lambda row: row.score, reverse=True)
    return legal[: max(1, min(size, 4))]


def _crushed(
    favorite_odd: float | None,
    other_odd: float | None,
    over_25: float | None,
    *,
    favorite: str,
) -> bool:
    del favorite
    if favorite_odd is None:
        return False
    is_favorite = other_odd is None or favorite_odd <= other_odd
    if not is_favorite:
        return False
    return favorite_odd <= 1.35 or (over_25 is not None and over_25 <= 1.45)


def _dominant(xg_home: float, xg_away: float) -> bool:
    high, low = max(xg_home, xg_away), min(xg_home, xg_away)
    return high >= 2.0 and low > 0 and high >= low * 1.6
