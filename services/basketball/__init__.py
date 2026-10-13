"""Ricerca Basket separata dal calcio.

Handicap e totale partita, proiettati da pace e rating offensivo/difensivo.
Include l'estensione OFP Basket (Oddspedia / Forebet / Quantitative).
"""

from services.basketball.backtest import WalkForwardBacktest, summarize
from services.basketball.pricing import edge, home_cover_probability, over_probability
from services.basketball.projection import project_score
from services.basketball.ofp_basket import (
    OFPBasketEngine,
    OFPBasketMatch,
    build_today_euroleague_ofp,
)

__all__ = [
    "WalkForwardBacktest",
    "edge",
    "home_cover_probability",
    "over_probability",
    "project_score",
    "summarize",
    "OFPBasketEngine",
    "OFPBasketMatch",
    "build_today_euroleague_ofp",
]
