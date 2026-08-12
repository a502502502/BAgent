from dataclasses import dataclass
from statistics import mean, median

from models.market_data.market_quote import MarketQuote


@dataclass(frozen=True)
class MarketConsensus:

    event_id: str
    market: str
    selection: str
    point: float | None

    best_odds: float
    average_odds: float
    median_odds: float
    bookmakers: int
    best_bookmaker: str


def aggregate_quotes(quotes):

    groups = {}

    for quote in quotes:

        key = (
            quote.event_id,
            quote.market,
            quote.selection,
            quote.point,
        )

        groups.setdefault(key, []).append(quote)

    results = []

    for key, group in groups.items():

        best = max(
            group,
            key=lambda q: q.odds,
        )

        odds = [
            q.odds
            for q in group
        ]

        results.append(
            MarketConsensus(
                event_id=key[0],
                market=key[1],
                selection=key[2],
                point=key[3],
                best_odds=best.odds,
                average_odds=mean(odds),
                median_odds=median(odds),
                bookmakers=len(group),
                best_bookmaker=best.bookmaker,
            )
        )

    return results
