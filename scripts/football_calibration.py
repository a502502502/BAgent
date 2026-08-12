import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from collections import Counter

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_backtester import FootballBacktester


m = FootballDataLoader().load(
    "data/football/raw/E0_2025_2026.csv"
)

d = FootballHistoricalDataset(m)
r = FootballBacktester().run(d)

print("PREDICTIONS:", len(r))

for result in ["HOME", "DRAW", "AWAY"]:

    rows = [
        x for x in r
        if x.actual_result == result
    ]

    print()
    print("ACTUAL", result, ":", len(rows))

    for predicted_class in ["HOME", "DRAW", "AWAY"]:

        values = [
            getattr(
                x.prediction.probability,
                predicted_class.lower(),
            )
            for x in rows
        ]

        print(
            predicted_class,
            "AVG=",
            sum(values) / len(values),
            "MIN=",
            min(values),
            "MAX=",
            max(values),
        )

print()
print(
    "PREDICTED:",
    Counter(
        x.prediction.predicted_result
        for x in r
    ),
)

print()
print("PROBABILITY BUCKETS:")

for result in ["HOME", "DRAW", "AWAY"]:

    print()
    print(result)

    for low, high in [
        (0.00, 0.20),
        (0.20, 0.30),
        (0.30, 0.40),
        (0.40, 0.50),
        (0.50, 0.60),
        (0.60, 1.01),
    ]:

        rows = [
            x for x in r
            if low
            <= getattr(
                x.prediction.probability,
                result.lower(),
            )
            < high
        ]

        if rows:

            correct = sum(
                x.actual_result == result
                for x in rows
            )

            print(
                f"{low:.2f}-{high:.2f}:",
                len(rows),
                "actual=",
                correct,
                "rate=",
                correct / len(rows),
            )
