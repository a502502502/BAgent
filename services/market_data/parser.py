from models.market_data.market_quote import MarketQuote


def parse_quotes(events):

    quotes = []

    for event in events:

        for bookmaker in event.get("bookmakers", []):

            bookmaker_name = bookmaker.get("title")

            for market in bookmaker.get("markets", []):

                market_key = market.get("key")

                if market_key not in {
                    "h2h",
                    "totals",
                }:
                    continue

                for outcome in market.get("outcomes", []):

                    quotes.append(
                        MarketQuote(
                            event_id=event["id"],
                            home_team=event["home_team"],
                            away_team=event["away_team"],
                            bookmaker=bookmaker_name,
                            market=market_key,
                            selection=outcome["name"],
                            odds=float(outcome["price"]),
                            point=(
                                float(outcome["point"])
                                if "point" in outcome
                                else None
                            ),
                        )
                    )

    return quotes
