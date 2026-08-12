"""
ProbabilityAdjuster — converte gli eventi del Sesto Senso
in aggiustamenti sulle probabilità base.

Logica:
  - Ogni evento ha un impatto (-3...+3) e una confidenza (0...1)
  - L'impatto effettivo = impact * confidence * impact_per_point
  - Gli aggiustamenti vengono applicati alle probabilità base
    e ri-normalizzati in modo che sommino sempre a 1.0

Calibrazione:
  impact_per_point = 0.04 (4% per punto di impatto)
  → impatto -2 con confidenza 0.8 = -6.4% sulla probabilità di quella squadra
  Questo valore è conservativo e modificabile con dati storici.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from services.football.sixth_sense.analyzer import (
    SixthSenseAnalysis,
    SixthSenseEvent,
)


# ------------------------------------------------------------------
# Config di calibrazione
# ------------------------------------------------------------------

# Percentuale di probabilità spostata per ogni punto di impatto
# con confidenza 1.0. Calibrabile con dati storici.
IMPACT_PER_POINT: float = 0.04  # 4% per punto

# Limiti: nessuna probabilità va sotto/sopra questi valori
MIN_PROB: float = 0.03
MAX_PROB: float = 0.92

# Peso dell'impatto sul pareggio (eventi forti aumentano l'incertezza)
DRAW_UNCERTAINTY_WEIGHT: float = 0.3


# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------

@dataclass
class AdjustedProbabilities:
    home_win: float
    draw: float
    away_win: float

    # Probabilità base prima dell'aggiustamento
    base_home_win: float = 0.0
    base_draw: float = 0.0
    base_away_win: float = 0.0

    # Delta applicati
    home_delta: float = 0.0
    draw_delta: float = 0.0
    away_delta: float = 0.0

    # Confidenza complessiva del Sesto Senso
    sixth_sense_confidence: float = 0.0

    # Numero di eventi considerati
    n_events: int = 0

    def to_dict(self) -> dict:
        return {
            "home_win": round(self.home_win, 4),
            "draw": round(self.draw, 4),
            "away_win": round(self.away_win, 4),
            "base": {
                "home_win": round(self.base_home_win, 4),
                "draw": round(self.base_draw, 4),
                "away_win": round(self.base_away_win, 4),
            },
            "delta": {
                "home": round(self.home_delta, 4),
                "draw": round(self.draw_delta, 4),
                "away": round(self.away_delta, 4),
            },
            "sixth_sense_confidence": round(self.sixth_sense_confidence, 3),
            "n_events": self.n_events,
        }

    @property
    def has_significant_adjustment(self) -> bool:
        """True se almeno un delta supera 3%."""
        return max(
            abs(self.home_delta),
            abs(self.draw_delta),
            abs(self.away_delta),
        ) >= 0.03

    @property
    def signal(self) -> str:
        """
        Segnale sintetico: HOME | DRAW | AWAY | CONFLICT | NEUTRAL
        Conflict = il Sesto Senso punta in direzione opposta al modello base.
        """
        if not self.has_significant_adjustment:
            return "NEUTRAL"

        base_winner = max(
            ("home", self.base_home_win),
            ("draw", self.base_draw),
            ("away", self.base_away_win),
            key=lambda x: x[1],
        )[0]

        adj_winner = max(
            ("home", self.home_win),
            ("draw", self.draw),
            ("away", self.away_win),
            key=lambda x: x[1],
        )[0]

        if base_winner != adj_winner:
            return "CONFLICT"

        return adj_winner.upper()


# ------------------------------------------------------------------
# Adjuster
# ------------------------------------------------------------------

class ProbabilityAdjuster:
    """
    Applica gli eventi del Sesto Senso alle probabilità base.

    Utilizzo:
        adjuster = ProbabilityAdjuster()
        adjusted = adjuster.adjust(base_probs, analysis)
        print(adjusted.to_dict())
        print(adjusted.signal)  # HOME | DRAW | AWAY | CONFLICT | NEUTRAL
    """

    def __init__(
        self,
        impact_per_point: float = IMPACT_PER_POINT,
        draw_uncertainty_weight: float = DRAW_UNCERTAINTY_WEIGHT,
    ):
        self.impact_per_point = impact_per_point
        self.draw_uncertainty_weight = draw_uncertainty_weight

    def adjust(
        self,
        base_probs: dict,
        analysis: SixthSenseAnalysis,
    ) -> AdjustedProbabilities:
        """
        Applica gli eventi dell'analisi alle probabilità base.

        base_probs: dict con home_win, draw, away_win (devono sommare ~1.0)
        analysis:   SixthSenseAnalysis dall'analyzer LLM
        """
        h = float(base_probs.get("home_win", 0.33))
        d = float(base_probs.get("draw", 0.33))
        a = float(base_probs.get("away_win", 0.34))

        # Normalizza base
        total = h + d + a
        h, d, a = h / total, d / total, a / total

        if not analysis.events:
            return AdjustedProbabilities(
                home_win=h, draw=d, away_win=a,
                base_home_win=h, base_draw=d, base_away_win=a,
                sixth_sense_confidence=0.0,
                n_events=0,
            )

        # Calcola delta grezzi per ogni evento
        home_delta = 0.0
        away_delta = 0.0

        for event in analysis.events:
            effective = event.impact * event.confidence * self.impact_per_point

            if event.team == "home":
                home_delta += effective
            elif event.team == "away":
                away_delta += effective
            elif event.team == "both":
                # Impatto simmetrico — aumenta incertezza (draw)
                home_delta += effective * 0.5
                away_delta += effective * 0.5

        # Il draw assorbe parte dell'incertezza quando ci sono eventi forti
        total_movement = abs(home_delta) + abs(away_delta)
        draw_delta = total_movement * self.draw_uncertainty_weight * (
            1 if home_delta < 0 or away_delta < 0 else -1
        )

        # Applica e clippa
        new_h = max(MIN_PROB, min(MAX_PROB, h + home_delta))
        new_a = max(MIN_PROB, min(MAX_PROB, a + away_delta))
        new_d = max(MIN_PROB, min(MAX_PROB, d + draw_delta))

        # Ri-normalizza
        total_new = new_h + new_d + new_a
        new_h /= total_new
        new_d /= total_new
        new_a /= total_new

        # Confidenza complessiva = media pesata per |impatto|
        total_abs_impact = sum(abs(e.impact) for e in analysis.events)
        if total_abs_impact > 0:
            overall_conf = sum(
                e.confidence * abs(e.impact)
                for e in analysis.events
            ) / total_abs_impact
        else:
            overall_conf = 0.0

        return AdjustedProbabilities(
            home_win=new_h,
            draw=new_d,
            away_win=new_a,
            base_home_win=h,
            base_draw=d,
            base_away_win=a,
            home_delta=new_h - h,
            draw_delta=new_d - d,
            away_delta=new_a - a,
            sixth_sense_confidence=overall_conf,
            n_events=len(analysis.events),
        )

    def implied_odds(self, probs: AdjustedProbabilities) -> dict:
        """Converte probabilità in quote fair (senza margine bookmaker)."""
        def to_odd(p: float) -> float:
            return round(1.0 / p, 2) if p > 0 else 999.0

        return {
            "home_win": to_odd(probs.home_win),
            "draw": to_odd(probs.draw),
            "away_win": to_odd(probs.away_win),
        }

    def value_signals(
        self,
        probs: AdjustedProbabilities,
        market_odds: dict,
        min_edge: float = 0.05,
    ) -> list[dict]:
        """
        Identifica scommesse con valore positivo.

        market_odds: quote offerte dal bookmaker {home_win, draw, away_win}
        min_edge:    edge minimo per considerare una scommessa (default 5%)

        Ritorna lista di {market, our_prob, market_prob, edge, value_odd}
        """
        signals = []

        checks = [
            ("home_win", probs.home_win),
            ("draw", probs.draw),
            ("away_win", probs.away_win),
        ]

        for market, our_prob in checks:
            market_odd = market_odds.get(market)
            if not market_odd or market_odd <= 1.0:
                continue

            market_prob = 1.0 / market_odd
            edge = our_prob - market_prob

            if edge >= min_edge:
                signals.append({
                    "market": market,
                    "our_probability": round(our_prob, 4),
                    "market_probability": round(market_prob, 4),
                    "edge": round(edge, 4),
                    "market_odd": market_odd,
                    "our_fair_odd": round(1.0 / our_prob, 2),
                    "recommendation": "VALUE BET" if edge >= 0.08 else "WATCH",
                })

        return sorted(signals, key=lambda x: x["edge"], reverse=True)
