"""
GoalModel — distribuzione di Poisson per mercati gol.

Stima λ_home e λ_away (gol attesi per squadra) e calcola:
  - Over/Under 1.5, 2.5, 3.5
  - BTTS (entrambe segnano)
  - Probabilità di ogni score esatto

Fonti per λ (in ordine di priorità):
  1. Statistiche di forma da football-data.co.uk
  2. Probabilità 1X2 da ClubElo (via calibrazione)
  3. Medie di campionato (default)

Utilizzo:
    model = GoalModel.from_form_stats(home_stats, away_stats)
    print(model.markets())

    # oppure da probabilità
    model = GoalModel.from_win_prob(home_win=0.55)
    print(model.markets())
"""

from __future__ import annotations

import math
from typing import Optional


class GoalModel:
    """
    Modello di Poisson per mercati gol.

    Parametri:
        lambda_home: gol attesi per la squadra di casa
        lambda_away: gol attesi per la squadra in trasferta
    """

    # Medie europee tipiche (aggiornabili per campionato)
    LEAGUE_AVG_HOME: float = 1.50
    LEAGUE_AVG_AWAY: float = 1.15

    def __init__(
        self,
        lambda_home: float = LEAGUE_AVG_HOME,
        lambda_away: float = LEAGUE_AVG_AWAY,
    ):
        self.lh = max(0.30, float(lambda_home))
        self.la = max(0.30, float(lambda_away))

    # ------------------------------------------------------------------
    # Costruttori alternativi
    # ------------------------------------------------------------------

    @classmethod
    def from_form_stats(
        cls,
        home_stats: dict,
        away_stats: dict,
        league_avg_home: float = LEAGUE_AVG_HOME,
        league_avg_away: float = LEAGUE_AVG_AWAY,
    ) -> "GoalModel":
        """
        Costruisce il modello da statistiche di forma (da football_data_uk).

        home_stats / away_stats: dict con keys matches, goals_for, goals_against
        Usa approccio Dixon-Coles semplificato:
          λ_home = home_attack_strength × away_defense_weakness × home_advantage
          λ_away = away_attack_strength × home_defense_weakness
        """
        hm = home_stats.get("matches", 0)
        am = away_stats.get("matches", 0)

        if hm < 3 or am < 3:
            return cls(lambda_home=league_avg_home, lambda_away=league_avg_away)

        # Forza attacco e difesa relativa alla media
        h_attack  = home_stats.get("goals_for", 0) / hm / league_avg_home
        h_defense = home_stats.get("goals_against", 0) / hm / league_avg_away
        a_attack  = away_stats.get("goals_for", 0) / am / league_avg_away
        a_defense = away_stats.get("goals_against", 0) / am / league_avg_home

        # λ = forza attacco × debolezza difesa avversaria × media campionato
        lh = h_attack * a_defense * league_avg_home * 1.05  # 5% home advantage
        la = a_attack * h_defense * league_avg_away

        # Clip a valori ragionevoli
        lh = max(0.40, min(4.0, lh))
        la = max(0.30, min(4.0, la))

        return cls(lambda_home=lh, lambda_away=la)

    @classmethod
    def from_win_prob(
        cls,
        home_win: float,
        draw: Optional[float] = None,
        away_win: Optional[float] = None,
    ) -> "GoalModel":
        """
        Stima λ dalla probabilità di vittoria casa (calibrazione empirica).

        Usato quando non abbiamo statistiche di forma ma abbiamo ClubElo.
        Calibrazione: home_win=0.33 → lh≈1.35, home_win=0.65 → lh≈1.90
        """
        # Spostamento rispetto alla neutralità (0.38 ≈ win% tipica casa)
        delta = home_win - 0.38

        lh = cls.LEAGUE_AVG_HOME + 0.90 * delta
        la = cls.LEAGUE_AVG_AWAY - 0.70 * delta

        lh = max(0.50, min(3.5, lh))
        la = max(0.35, min(3.5, la))

        return cls(lambda_home=lh, lambda_away=la)

    # ------------------------------------------------------------------
    # Calcoli
    # ------------------------------------------------------------------

    @staticmethod
    def _poisson(k: int, lam: float) -> float:
        """P(X = k) con distribuzione di Poisson."""
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    def score_matrix(self, max_goals: int = 8) -> list[list[float]]:
        """
        Matrice di probabilità P(home=h, away=a).
        Accesso: matrix[h][a]
        """
        return [
            [
                self._poisson(h, self.lh) * self._poisson(a, self.la)
                for a in range(max_goals + 1)
            ]
            for h in range(max_goals + 1)
        ]

    def markets(self, max_goals: int = 8) -> dict:
        """
        Calcola probabilità per tutti i principali mercati gol.

        Ritorna dict con:
          lambda_home, lambda_away, expected_total
          over_1_5, under_1_5
          over_2_5, under_2_5
          over_3_5, under_3_5
          btts_yes, btts_no
        """
        matrix = self.score_matrix(max_goals)

        over_1_5 = over_2_5 = over_3_5 = btts = 0.0

        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                p = matrix[h][a]
                total = h + a

                if total > 1.5:
                    over_1_5 += p
                if total > 2.5:
                    over_2_5 += p
                if total > 3.5:
                    over_3_5 += p
                if h > 0 and a > 0:
                    btts += p

        return {
            "lambda_home":    round(self.lh, 3),
            "lambda_away":    round(self.la, 3),
            "expected_total": round(self.lh + self.la, 2),
            "over_1_5":  round(over_1_5, 4),
            "under_1_5": round(1 - over_1_5, 4),
            "over_2_5":  round(over_2_5, 4),
            "under_2_5": round(1 - over_2_5, 4),
            "over_3_5":  round(over_3_5, 4),
            "under_3_5": round(1 - over_3_5, 4),
            "btts_yes":  round(btts, 4),
            "btts_no":   round(1 - btts, 4),
        }

    def value_signals(
        self,
        market_odds: dict,
        min_edge: float = 0.05,
    ) -> list[dict]:
        """
        Individua value bet nei mercati gol.

        market_odds: dict con chiavi come 'over_2_5', 'btts_yes', ecc.
        min_edge:    edge minimo per segnalare (default 5%)
        """
        m = self.markets()
        signals = []

        # Mappa: nome market → chiave in markets()
        checks = [
            ("over_1_5",  "over_1_5"),
            ("under_1_5", "under_1_5"),
            ("over_2_5",  "over_2_5"),
            ("under_2_5", "under_2_5"),
            ("over_3_5",  "over_3_5"),
            ("under_3_5", "under_3_5"),
            ("btts_yes",  "btts_yes"),
            ("btts_no",   "btts_no"),
        ]

        for market_key, prob_key in checks:
            odd = market_odds.get(market_key)
            if not odd or odd <= 1.0:
                continue

            our_prob    = m[prob_key]
            market_prob = 1.0 / odd
            edge        = our_prob - market_prob

            if edge >= min_edge:
                signals.append({
                    "market":           market_key,
                    "our_probability":  round(our_prob, 4),
                    "market_probability": round(market_prob, 4),
                    "edge":             round(edge, 4),
                    "market_odd":       odd,
                    "our_fair_odd":     round(1.0 / our_prob, 2) if our_prob > 0 else 999.0,
                    "recommendation":   "VALUE BET" if edge >= 0.08 else "WATCH",
                })

        return sorted(signals, key=lambda x: x["edge"], reverse=True)

    def __repr__(self) -> str:
        m = self.markets()
        return (
            f"GoalModel(λ_home={self.lh:.2f}, λ_away={self.la:.2f}) "
            f"| Over2.5={m['over_2_5']:.1%} BTTS={m['btts_yes']:.1%}"
        )
