"""Brier, affidabilità e curva di cassa sulle selezioni già chiuse.

Lo stake di ogni passo è quello di KellyStakingEngine, con il tetto dell'8%.
Il report non chiama Groq e non entra nel ciclo di emissione.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from services.betting.kelly_staking_engine import KellyStakingEngine

SLATES = Path(__file__).resolve().parent / "slates"


@dataclass(frozen=True)
class ReliabilityBin:
    lower: float
    upper: float
    count: int
    mean_predicted: float
    observed_frequency: float


@dataclass(frozen=True)
class CalibrationReport:
    n: int
    brier: float
    ece: float
    bins: tuple[ReliabilityBin, ...]


@dataclass(frozen=True)
class BankrollStep:
    index: int
    stake: float
    bankroll: float
    won: bool


@dataclass(frozen=True)
class BankrollReport:
    start: float
    end: float
    max_drawdown: float
    steps: tuple[BankrollStep, ...]


def brier_binary(pairs: list[tuple[float, int]]) -> float:
    if not pairs:
        raise ValueError("Servono coppie probabilità-esito")
    total = 0.0
    for probability, outcome in pairs:
        total += (probability - outcome) ** 2
    return total / len(pairs)


def reliability(
    pairs: list[tuple[float, int]],
    bin_width: float = 0.05,
) -> CalibrationReport:
    """Bin da 0 a 1. L'ultimo include la probabilità 1."""
    if not pairs:
        raise ValueError("Servono coppie probabilità-esito")
    if bin_width <= 0 or bin_width > 1:
        raise ValueError("bin_width deve stare tra 0 e 1")
    n_bins = int(round(1.0 / bin_width))
    counts = [0] * n_bins
    predicted = [0.0] * n_bins
    outcomes = [0.0] * n_bins
    for probability, outcome in pairs:
        if not 0.0 <= probability <= 1.0:
            raise ValueError(f"Probabilità fuori da [0, 1]: {probability}")
        if outcome not in (0, 1):
            raise ValueError(f"Esito binario atteso, ricevuto {outcome}")
        index = min(n_bins - 1, int(probability / bin_width))
        counts[index] += 1
        predicted[index] += probability
        outcomes[index] += outcome
    bins: list[ReliabilityBin] = []
    ece = 0.0
    n = len(pairs)
    for index, count in enumerate(counts):
        if count == 0:
            continue
        mean_predicted = predicted[index] / count
        observed = outcomes[index] / count
        ece += (count / n) * abs(observed - mean_predicted)
        bins.append(
            ReliabilityBin(
                lower=round(index * bin_width, 2),
                upper=round(min(1.0, (index + 1) * bin_width), 2),
                count=count,
                mean_predicted=mean_predicted,
                observed_frequency=observed,
            )
        )
    return CalibrationReport(n=n, brier=brier_binary(pairs), ece=ece, bins=tuple(bins))


def simulate_bankroll(
    bets: list[dict],
    start: float,
) -> BankrollReport:
    """bets: probability, odds, outcome (1 vinta, 0 persa), in ordine cronologico."""
    if start <= 0:
        raise ValueError("Il bankroll iniziale deve essere positivo")
    bankroll = float(start)
    peak = bankroll
    max_drawdown = 0.0
    steps: list[BankrollStep] = []
    engine = KellyStakingEngine(bankroll)
    for index, bet in enumerate(bets):
        engine.set_bankroll(bankroll)
        stake = engine.calculate_stake(
            odds=float(bet["odds"]),
            estimated_prob=float(bet["probability"]),
        ).recommended_stake
        cap = bankroll * KellyStakingEngine.HARD_CAP_SINGLE_TICKET_PCT
        if stake > cap + 1e-6:
            raise RuntimeError(f"Stake {stake} sopra il tetto {cap}")
        won = int(bet["outcome"]) == 1
        if won:
            bankroll += stake * (float(bet["odds"]) - 1.0)
        else:
            bankroll -= stake
        peak = max(peak, bankroll)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - bankroll) / peak)
        steps.append(BankrollStep(index=index, stake=stake, bankroll=bankroll, won=won))
    return BankrollReport(
        start=float(start),
        end=bankroll,
        max_drawdown=max_drawdown,
        steps=tuple(steps),
    )


def load_settled(path: Path | None = None) -> dict:
    slate = path or (SLATES / "settled_smoke.json")
    return json.loads(slate.read_text(encoding="utf-8"))


def report_settled(payload: dict) -> tuple[CalibrationReport, BankrollReport]:
    pairs = [(float(bet["probability"]), int(bet["outcome"])) for bet in payload["bets"]]
    curve = simulate_bankroll(payload["bets"], float(payload["bankroll"]))
    return reliability(pairs), curve
