from dataclasses import dataclass

from models.football_prediction import FootballPrediction


@dataclass(frozen=True)
class FootballBacktestResult:

    match_id: str

    actual_result: str

    prediction: FootballPrediction

    correct: bool

    log_loss: float

    brier_score: float
