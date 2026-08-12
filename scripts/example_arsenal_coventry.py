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

HOME_TEAM = "Arsenal"
AWAY_TEAM = "Coventry"
MATCH_DATE = "2026-08-21T21:00:00"

HOME_ODDS = 1.19
DRAW_ODDS = 8.10
AWAY_ODDS = 19.50

match = FootballMatch(
    id="ARS-COV-2026",
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
    print("Nessuna predizione possibile: nessuno storico e nessuna quota disponibile.")
else:
    print(f"=== {HOME_TEAM} vs {AWAY_TEAM} ===")
    print(f"Data: {MATCH_DATE}")
    print()

    if prediction.is_market_fallback:
        print("*** MODALITA' FALLBACK: nessuno storico Premier League sufficiente. ***")
        print("*** Previsione basata SOLO sulle quote di mercato. ***")
        print()

    print("PROBABILITÀ:")
    print(f"  HOME ({HOME_TEAM}):  {prediction.probability.home:.1%}")
    print(f"  DRAW:                {prediction.probability.draw:.1%}")
    print(f"  AWAY ({AWAY_TEAM}):  {prediction.probability.away:.1%}")
    print()
    print(f"ESITO PIÙ PROBABILE: {prediction.predicted_result}")
    print(f"Rating: {prediction.rating:+.4f}  |  Confidence: {prediction.confidence:.2f}  |  Balance: {prediction.match_balance:.2f}")
    print(f"Fallback di mercato: {prediction.is_market_fallback}")
    print()
    print("CONTRIBUTI:")
    if not prediction.contributions:
        print("  (nessuno - fallback puro sul mercato)")
    for c in prediction.contributions:
        print(f"  - {c.factor}: value={c.value:+.4f}  confidence={c.confidence:.2f}")
