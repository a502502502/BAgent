import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_backtester import FootballBacktester


EV_THRESHOLDS = [
    0.00,
    0.02,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
]


def evaluate_value(results, odds_by_match_id, threshold):

    bets = 0
    wins = 0
    profit = 0.0
    odds_sum = 0.0

    for result in results:

        prediction = result.prediction

        historical_odds = odds_by_match_id.get(
            result.match_id
        )

        if historical_odds is None:
            continue

        selections = [
            (
                "HOME",
                prediction.probability.home,
                historical_odds.home,
            ),
            (
                "DRAW",
                prediction.probability.draw,
                historical_odds.draw,
            ),
            (
                "AWAY",
                prediction.probability.away,
                historical_odds.away,
            ),
        ]

        for selection, model_probability, market_odds in selections:

            if market_odds is None:
                continue

            if market_odds <= 1.0:
                continue

            ev = (
                model_probability
                * market_odds
            ) - 1.0

            if ev < threshold:
                continue

            bets += 1
            odds_sum += market_odds

            if result.actual_result == selection:

                wins += 1
                profit += market_odds - 1.0

            else:

                profit -= 1.0

    if bets == 0:

        return {
            "bets": 0,
            "wins": 0,
            "win_rate": 0.0,
            "profit": 0.0,
            "roi": 0.0,
            "average_odds": 0.0,
        }

    return {
        "bets": bets,
        "wins": wins,
        "win_rate": wins / bets,
        "profit": profit,
        "roi": profit / bets,
        "average_odds": odds_sum / bets,
    }


def main():

    raw_dir = Path(
        "data/football/raw"
    )

    files = sorted(
        raw_dir.glob("E0_*.csv")
    )

    print("FILES FOUND:")

    for file in files:
        print(" -", file.name)

    loader = FootballDataLoader()

    all_matches = []

    for file in files:

        matches = loader.load(file)

        print(
            f"{file.name}: "
            f"{len(matches)} matches"
        )

        all_matches.extend(matches)

    print()
    print(
        "TOTAL MATCHES:",
        len(all_matches),
    )

    dataset = FootballHistoricalDataset(
        all_matches
    )

    odds_by_match_id = {}

    for historical_match in dataset.all():

        odds = historical_match.odds

        if odds is None:
            continue

        odds_by_match_id[
            historical_match.match_id
        ] = odds

    print(
        "MATCHES WITH ODDS:",
        len(odds_by_match_id),
    )

    results = FootballBacktester().run(
        dataset
    )

    print()
    print(
        "=== VALUE BACKTEST ==="
    )

    print(
        "PREDICTIONS:",
        len(results),
    )

    print()

    print(
        "ACTUAL RESULTS:",
        Counter(
            r.actual_result
            for r in results
        ),
    )

    print()

    print(
        "THRESHOLD        BETS    WINS    "
        "WIN_RATE    AVG_ODDS    PROFIT       ROI"
    )

    print(
        "-" * 95
    )

    all_metrics = []

    for threshold in EV_THRESHOLDS:

        metrics = evaluate_value(
            results,
            odds_by_match_id,
            threshold,
        )

        all_metrics.append(
            (
                threshold,
                metrics,
            )
        )

        print(
            f"{threshold:>8.0%}"
            f"{metrics['bets']:>12}"
            f"{metrics['wins']:>9}"
            f"{metrics['win_rate']:>12.4f}"
            f"{metrics['average_odds']:>12.3f}"
            f"{metrics['profit']:>12.2f}"
            f"{metrics['roi']:>12.4f}"
        )

    print()
    print(
        "=== POSITIVE ROI THRESHOLDS ==="
    )

    positive = [
        (
            threshold,
            metrics,
        )
        for threshold, metrics
        in all_metrics
        if metrics["bets"] > 0
        and metrics["roi"] > 0.0
    ]

    if not positive:

        print("NONE")

    else:

        for threshold, metrics in positive:

            print(
                f"EV >= {threshold:.0%} "
                f"| BETS={metrics['bets']} "
                f"| WIN_RATE={metrics['win_rate']:.4f} "
                f"| ROI={metrics['roi']:.4f} "
                f"| PROFIT={metrics['profit']:.2f}"
            )

    print()
    print(
        "=== BEST ROI ==="
    )

    valid = [
        x
        for x in all_metrics
        if x[1]["bets"] > 0
    ]

    if not valid:

        print(
            "NO VALID BETS"
        )

    else:

        best = max(
            valid,
            key=lambda x: x[1]["roi"],
        )

        threshold, metrics = best

        print(
            f"THRESHOLD={threshold:.0%}"
        )

        print(
            "BETS=",
            metrics["bets"],
        )

        print(
            "WINS=",
            metrics["wins"],
        )

        print(
            "WIN_RATE=",
            metrics["win_rate"],
        )

        print(
            "AVERAGE_ODDS=",
            metrics["average_odds"],
        )

        print(
            "PROFIT=",
            metrics["profit"],
        )

        print(
            "ROI=",
            metrics["roi"],
        )


if __name__ == "__main__":
    main()
