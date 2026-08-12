import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_backtester import FootballBacktester
from services.football_backtest_summary import FootballBacktestSummaryBuilder
from services.football_baseline_comparison import FootballBaselineComparison

matches = FootballDataLoader().load("data/football/raw/E0_2025_2026.csv")
dataset = FootballHistoricalDataset(matches)

results = FootballBacktester().run(dataset)

summary = FootballBacktestSummaryBuilder().build(results)

print("PREDICTIONS:", summary.total_predictions)
print("ACCURACY:", summary.accuracy)
print("LOG LOSS:", summary.average_log_loss)
print("BRIER:", summary.average_brier_score)
print()
print("DRAW PREDICTED:", summary.draw_predictions)
print("DRAW CORRECT:", summary.draw_correct)
print("DRAW ACCURACY:", summary.draw_accuracy)
print()

comparison = FootballBaselineComparison().compare(results)
print("BASELINE COMPARISON:", comparison)
