import sys
from pathlib import Path

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

# ---- MODIFICA QUI: scegli le due squadre e la data della partita ----
HOME_TEAM = "Liverpool"
AWAY_TEAM = "Arsenal"
MATCH_DATE = "2026-08-20T20:00:00"

# Quote di mercato ipotetiche (sostituisci con quelle reali se le hai)
HOME_ODDS = 2.10
DRAW_ODDS = 3.60
AWAY_ODDS = 3.40
# -----------------------------------------------------------------

match = FootballMatch(
    id="EXAMPLE-001",
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

from datetime import datetime

prediction = engine.predict(
    match=match,
    historical_profile=profile,
    date=datetime.fromisoformat(MATCH_DATE),
    odds=odds,
)

if prediction is None:
    print("Nessuna predizione possibile: storico insufficiente per una delle due squadre.")
else:
    print(f"=== {HOME_TEAM} vs {AWAY_TEAM} ===")
    print(f"Data: {MATCH_DATE}")
    print()
    print("PROBABILITÀ DEL MODELLO:")
    print(f"  HOME ({HOME_TEAM}):  {prediction.probability.home:.1%}")
    print(f"  DRAW:                {prediction.probability.draw:.1%}")
    print(f"  AWAY ({AWAY_TEAM}):  {prediction.probability.away:.1%}")
    print()
    print(f"ESITO PIÙ PROBABILE: {prediction.predicted_result}")
    print()
    print(f"Rating (forza relativa, tanh-compresso): {prediction.rating:+.4f}")
    print(f"Confidence (basata su partite storiche disponibili): {prediction.confidence:.2f}")
    print(f"Match balance (equilibrio stimato 0-1): {prediction.match_balance:.2f}")
    print()
    print("QUOTE DI MERCATO INSERITE:")
    print(f"  HOME {HOME_ODDS}  ->  probabilità implicita {1/HOME_ODDS:.1%}")
    print(f"  DRAW {DRAW_ODDS}  ->  probabilità implicita {1/DRAW_ODDS:.1%}")
    print(f"  AWAY {AWAY_ODDS}  ->  probabilità implicita {1/AWAY_ODDS:.1%}")
    print()
    print("CONTRIBUTI (segnali che hanno formato il rating):")
    for c in prediction.contributions:
        print(f"  - {c.factor}: value={c.value:+.4f}  confidence={c.confidence:.2f}")
        print(f"    {c.explanation}")
