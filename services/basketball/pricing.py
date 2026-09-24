"""Probabilità su due esiti e edge sulla quota decimale."""

from __future__ import annotations

from dataclasses import dataclass

from scipy.stats import norm


def edge(probability: float, decimal_odds: float) -> float:
    """Edge = (P × quota) − 1. Stessa definizione del Kelly del calcio."""
    return probability * decimal_odds - 1.0


def home_cover_probability(margin_mean: float, margin_sigma: float, home_spread: float) -> float:
    """P(margine casa + spread casa > 0).

    Lo spread casa è negativo quando la casa è favorita: −6.5 significa che
    la casa deve vincere di 7 o più.
    """
    if margin_sigma <= 0:
        raise ValueError("sigma del margine deve essere positiva")
    return float(norm.cdf((margin_mean + home_spread) / margin_sigma))


def over_probability(total_mean: float, total_sigma: float, total_line: float) -> float:
    """P(punti totali > linea)."""
    if total_sigma <= 0:
        raise ValueError("sigma del totale deve essere positiva")
    return float(norm.sf((total_line - total_mean) / total_sigma))


@dataclass(frozen=True)
class SideChoice:
    side: str
    probability: float
    decimal_odds: float
    edge: float


def choose_side(
    sides: dict[str, tuple[float, float]],
    min_edge: float,
) -> SideChoice | None:
    """Sceglie l'esito con edge più alto, solo se supera la soglia.

    `sides` mappa il nome dell'esito su (probabilità, quota decimale).
    """
    best: SideChoice | None = None
    for side, (probability, decimal_odds) in sides.items():
        if decimal_odds <= 1.0:
            raise ValueError("la quota deve essere maggiore di 1")
        value = edge(probability, decimal_odds)
        if best is None or value > best.edge:
            best = SideChoice(side, probability, decimal_odds, value)
    if best is None or best.edge < min_edge:
        return None
    return best
