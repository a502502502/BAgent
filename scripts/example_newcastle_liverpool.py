import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_historical_profile import FootballHistoricalProfile
from services.football_prediction_engine import FootballPredictionEngine
from models.football import FootballMatch, FootballTeam
from models.football_odds import FootballMatchOdds

raw_dir = Path("data/football/raw")
files = sorted(raw_dir.glob("E0_*.csv"))

loader = FootballDataLoader()
all_matches = []
for f in files:
    all_matches.extend(loader.load(f))

dataset = FootballHistoricalDataset(all_matches)
profile = FootballHistoricalProfile(dataset)
engine = FootballPredictionEngine()

HOME_TEAM = "Newcastle"
AWAY_TEAM = "Liverpool"
MATCH_DATE = "2026-08-23T16:30:00"

HOME_ODDS = 2.95
DRAW_ODDS = 4.00
AWAY_ODDS = 2.25

match = FootballMatch(
    id="NEW-LIV-2026",
    competition="Premier League",
    season="2026/27",
    home=FootballTeam(id=HOME_TEAM, name=HOME_TEAM),
    away=FootballTeam(id=AWAY_TEAM, name=AWAY_TEAM),
    start_time=MATCH_DATE,
    status="Scheduled",
)

odds = FootballMatchOdds(
    home=HOME_ODDS,
    draw=DRAW_ODDS,
    away=AWAY_ODDS,
)

prediction = engine.predict(
    match=match,
    historical_profile=profile,
    date=datetime.fromisoformat(MATCH_DATE),
    odds=odds,
)

if prediction is None:
    print("Nessuna predizione possibile.")
else:
    print(f"=== {HOME_TEAM} vs {AWAY_TEAM} ===")
    print(f"Data: {MATCH_DATE}")
    print()

    if prediction.is_market_fallback:
        print("*** MODALITA' FALLBACK: nessuno storico sufficiente. ***")
        print()
    else:
        print("*** MODELLO COMPLETO: storico + mercato ***")
        print()

    print("PROBABILITÀ:")
    print(f"  HOME ({HOME_TEAM}):  {prediction.probability.home:.1%}")
    print(f"  DRAW:                {prediction.probability.draw:.1%}")
    print(f"  AWAY ({AWAY_TEAM}):  {prediction.probability.away:.1%}")
    print()
    print(f"ESITO PIÙ PROBABILE: {prediction.predicted_result}")
    print(f"Rating: {prediction.rating:+.4f}  |  Confidence: {prediction.confidence:.2f}  |  Balance: {prediction.match_balance:.2f}")
    print()
    print("QUOTE DI MERCATO:")
    print(f"  HOME {HOME_ODDS}  -> {1/HOME_ODDS:.1%}")
    print(f"  DRAW {DRAW_ODDS}  -> {1/DRAW_ODDS:.1%}")
    print(f"  AWAY {AWAY_ODDS}  -> {1/AWAY_ODDS:.1%}")
    print()
    print("CONTRIBUTI:")
    for c in prediction.contributions:
        home_wr = c.details.get('home_smoothed_win_rate', 0)
        away_wr = c.details.get('away_smoothed_win_rate', 0)
        home_gs = c.details.get('home_goal_strength', 0)
        away_gs = c.details.get('away_goal_strength', 0)
        print(f"  - {c.factor}: value={c.value:+.4f}  confidence={c.confidence:.2f}")
        print(f"    home_smoothed_win_rate={home_wr:.3f}")
        print(f"    away_smoothed_win_rate={away_wr:.3f}")
        print(f"    home_goal_strength={home_gs:+.3f}")
        print(f"    away_goal_strength={away_gs:+.3f}")
