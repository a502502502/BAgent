import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_backtester import FootballBacktester

m = FootballDataLoader().load(
    "data/football/raw/E0_2025_2026.csv"
)

d = FootballHistoricalDataset(m)
r = FootballBacktester().run(d)

print("PREDICTIONS:", len(r))
print(
    "ACCURACY:",
    sum(x.correct for x in r) / len(r)
)
print(
    "LOG LOSS:",
    sum(x.log_loss for x in r) / len(r)
)
print(
    "BRIER:",
    sum(x.brier_score for x in r) / len(r)
)
