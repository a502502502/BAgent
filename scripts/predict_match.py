import sys
from pathlib import Path
from datetime import datetime
from statistics import median

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile
from services.football_prediction_engine import FootballPredictionEngine

from models.football import (
    FootballMatch,
    FootballTeam,
)

from models.football_odds import (
    FootballMatchOdds,
)

from services.market_data.the_odds_api import TheOddsApi


ROOT = Path(__file__).resolve().parents[1]

HISTORICAL_FILES = [
    ROOT / "data/football/raw/E0_2021.csv",
    ROOT / "data/football/raw/E0_2122.csv",
    ROOT / "data/football/raw/E0_2223.csv",
    ROOT / "data/football/raw/E0_2324.csv",
    ROOT / "data/football/raw/E0_2425.csv",
    ROOT / "data/football/raw/E0_2025_2026.csv",
]


def load_history():

    loader = FootballDataLoader()

    matches = []

    for path in HISTORICAL_FILES:

        if path.exists():
            matches.extend(
                loader.load(path)
            )

    return FootballHistoricalDataset(
        matches
    )


def find_event(
    events,
    home,
    away,
):

    home = home.lower().strip()
    away = away.lower().strip()

    for event in events:

        event_home = (
            event["home_team"]
            .lower()
            .strip()
        )

        event_away = (
            event["away_team"]
            .lower()
            .strip()
        )

        if (
            event_home == home
            and event_away == away
        ):
            return event

    return None


def event_date(event):

    value = event["commence_time"]

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is not None:
        parsed = parsed.replace(
            tzinfo=None
        )

    return parsed


def extract_1x2_odds(event):

    home_name = event["home_team"]
    away_name = event["away_team"]

    home_odds = []
    draw_odds = []
    away_odds = []

    for bookmaker in event.get(
        "bookmakers",
        []
    ):

        for market in bookmaker.get(
            "markets",
            []
        ):

            if market.get("key") != "h2h":
                continue

            for outcome in market.get(
                "outcomes",
                []
            ):

                name = outcome["name"]

                price = float(
                    outcome["price"]
                )

                if name == home_name:
                    home_odds.append(price)

                elif name == away_name:
                    away_odds.append(price)

                elif name.lower() == "draw":
                    draw_odds.append(price)

    return (
        home_odds,
        draw_odds,
        away_odds,
    )


def devig_probabilities(
    home_odds,
    draw_odds,
    away_odds,
):

    home_median = median(
        home_odds
    )

    draw_median = median(
        draw_odds
    )

    away_median = median(
        away_odds
    )

    inverse_home = (
        1.0 / home_median
    )

    inverse_draw = (
        1.0 / draw_median
    )

    inverse_away = (
        1.0 / away_median
    )

    total = (
        inverse_home
        + inverse_draw
        + inverse_away
    )

    return (
        inverse_home / total,
        inverse_draw / total,
        inverse_away / total,
        home_median,
        draw_median,
        away_median,
    )


def print_value(
    name,
    probability,
    odds,
):

    fair_odds = (
        1.0 / probability
    )

    expected_value = (
        probability * odds
    ) - 1.0

    value = (
        expected_value > 0.0
    )

    print(
        f"{name:5s} "
        f"FAIR={fair_odds:.2f} "
        f"ODDS={odds:.2f} "
        f"EV={expected_value:+.4f} "
        f"{'VALUE' if value else '-'}"
    )


def main():

    home_name = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Arsenal"
    )

    away_name = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "Coventry City"
    )

    api = TheOddsApi()

    try:

        # ==================================================
        # LIVE MARKET
        # ==================================================

        events = api.get_soccer_odds()

        event = find_event(
            events,
            home_name,
            away_name,
        )

        if event is None:

            print(
                f"PARTITA NON TROVATA: "
                f"{home_name} - {away_name}"
            )

            return

        match_date = event_date(
            event
        )

        (
            home_odds,
            draw_odds,
            away_odds,
        ) = extract_1x2_odds(event)

        if not (
            home_odds
            and draw_odds
            and away_odds
        ):

            print(
                "Quote 1X2 insufficienti."
            )

            return

        (
            market_home,
            market_draw,
            market_away,
            median_home,
            median_draw,
            median_away,
        ) = devig_probabilities(
            home_odds,
            draw_odds,
            away_odds,
        )

        best_home = max(
            home_odds
        )

        best_draw = max(
            draw_odds
        )

        best_away = max(
            away_odds
        )

        # ==================================================
        # MARKET ODDS OBJECT
        #
        # IMPORTANT:
        # We pass the median 1X2 odds into the prediction
        # engine. The engine itself de-vigs them before using
        # them as market features.
        # ==================================================

        market_odds = FootballMatchOdds(
            home=median_home,
            draw=median_draw,
            away=median_away,
        )

        # ==================================================
        # HISTORICAL DATA
        # ==================================================

        dataset = load_history()

        profile = FootballHistoricalProfile(
            dataset
        )

        # ==================================================
        # UPCOMING MATCH
        # ==================================================

        match = FootballMatch(
            id=event["id"],
            competition="Premier League",
            season=None,
            home=FootballTeam(
                id=home_name,
                name=home_name,
            ),
            away=FootballTeam(
                id=away_name,
                name=away_name,
            ),
            start_time=match_date.isoformat(),
            status="Scheduled",
        )

        # ==================================================
        # V3 CANDIDATE
        #
        # HISTORY + LIVE MARKET
        #
        # Recency is NOT yet injected into the historical
        # profile here. This is deliberately the safe first
        # step: activate the already-tested market branch
        # without fabricating a recency implementation.
        # ==================================================

        engine = FootballPredictionEngine()

        prediction = engine.predict(
            match=match,
            historical_profile=profile,
            date=match_date,
            odds=market_odds,
            recency_decay=2.0,
        )

        # ==================================================
        # OUTPUT
        # ==================================================

        print()
        print("=" * 64)
        print(
            f"{home_name} - {away_name}"
        )
        print("=" * 64)

        print()
        print("MODEL V3 HISTORY + RECENCY(2.0) + MARKET")

        if prediction is None:

            print(
                "MODEL: nessuna previsione"
            )

            print()
            print(
                "Il modello non dispone di "
                "storico sufficiente per una "
                "previsione."
            )

            return

        p_home = (
            prediction.probability.home
        )

        p_draw = (
            prediction.probability.draw
        )

        p_away = (
            prediction.probability.away
        )

        print(
            f"HOME   {p_home:.4f} "
            f"FAIR={1.0 / p_home:.2f}"
        )

        print(
            f"DRAW   {p_draw:.4f} "
            f"FAIR={1.0 / p_draw:.2f}"
        )

        print(
            f"AWAY   {p_away:.4f} "
            f"FAIR={1.0 / p_away:.2f}"
        )

        print()
        print("MARKET CONSENSUS")

        print(
            f"HOME   {market_home:.4f} "
            f"MEDIAN={median_home:.2f}"
        )

        print(
            f"DRAW   {market_draw:.4f} "
            f"MEDIAN={median_draw:.2f}"
        )

        print(
            f"AWAY   {market_away:.4f} "
            f"MEDIAN={median_away:.2f}"
        )

        print()
        print("BOOKMAKER COVERAGE")

        print(
            f"HOME   {len(home_odds)} bookmakers"
        )

        print(
            f"DRAW   {len(draw_odds)} bookmakers"
        )

        print(
            f"AWAY   {len(away_odds)} bookmakers"
        )

        print()
        print("BEST AVAILABLE ODDS")

        print(
            f"HOME   {best_home:.2f}"
        )

        print(
            f"DRAW   {best_draw:.2f}"
        )

        print(
            f"AWAY   {best_away:.2f}"
        )

        print()
        print("VALUE")

        print_value(
            "HOME",
            p_home,
            best_home,
        )

        print_value(
            "DRAW",
            p_draw,
            best_draw,
        )

        print_value(
            "AWAY",
            p_away,
            best_away,
        )

        print()
        print("MODEL VS MARKET")

        print(
            f"HOME   DELTA="
            f"{p_home - market_home:+.4f}"
        )

        print(
            f"DRAW   DELTA="
            f"{p_draw - market_draw:+.4f}"
        )

        print(
            f"AWAY   DELTA="
            f"{p_away - market_away:+.4f}"
        )

        print()
        print("MODEL METADATA")

        print(
            f"CONFIDENCE="
            f"{prediction.confidence:.4f}"
        )

        print(
            f"RATING="
            f"{prediction.rating:.4f}"
        )

        print(
            f"HISTORY MATCHES="
            f"{len(dataset.completed_before(match_date))}"
        )

        print(
            "MARKET INPUT=MEDIAN 1X2"
        )

        print(
            "RECENCY=2.0"
        )

        print(
            "SIXTH SENSE=OFF"
        )

    finally:

        api.close()


if __name__ == "__main__":
    main()


