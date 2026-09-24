"""Ricerca NBA separata dal calcio.

Handicap e totale partita, proiettati da pace e rating offensivo/difensivo.
Non entra in StrictTicketPipeline e non emette ticket.
"""

from services.basketball.backtest import WalkForwardBacktest, summarize
from services.basketball.pricing import edge, home_cover_probability, over_probability
from services.basketball.projection import project_score

__all__ = [
    "WalkForwardBacktest",
    "edge",
    "home_cover_probability",
    "over_probability",
    "project_score",
    "summarize",
]
