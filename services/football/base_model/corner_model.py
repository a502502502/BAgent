"""
CornerModel — distribuzione di Poisson per mercati corner.

Stima λ_home e λ_away (corner attesi per squadra) e calcola:
  - Over/Under 8.5, 9.5, 10.5, 11.5
  - Corner handicap (home -1.5, -2.5, -3.5)
  - Corner asiatici (home -4.5)

Medie europee tipiche:
  Home: 5.5 corner/partita   Away: 4.5 corner/partita   Totale: ~10

Corner e gol sono correlati positivamente — squadre che attaccano
di più tendono ad avere più corner. Usiamo lo stesso approccio
di GoalModel: calibrazione da statistiche di forma o da win prob.

Utilizzo:
    model = CornerModel.from_win_prob(home_win=0.55)
    print(model.markets())
    print(model.value_signals({"over_9_5": 1.90, "under_9_5": 1.90}))
"""

from __future__ import annotations

import math
from typing import Optional


class CornerModel:

    # Medie europee (aggiornabili per campionato)
    LEAGUE_AVG_HOME: float = 5.50
    LEAGUE_AVG_AWAY: float = 4.50

    def __init__(
        self,
        lambda_home: float = LEAGUE_AVG_HOME,
        lambda_away: float = LEAGUE_AVG_AWAY,
    ):
        self.lh = max(1.0, float(lambda_home))
        self.la = max(1.0, float(lambda_away))

    # ------------------------------------------------------------------
    # Costruttori alternativi
    # ------------------------------------------------------------------

    @classmethod
    def from_form_stats(
        cls,
        home_stats: dict,
        away_stats: dict,
    ) -> "CornerModel":
        """
        Costruisce il modello da statistiche di forma.

        home_stats / away_stats devono avere:
          matches, corners_for, corners_against
        """
        hm = home_stats.get("matches", 0)
        am = away_stats.get("matches", 0)

        if hm < 3 or am < 3:
            return cls()

        h_corners_for  = home_stats.get("corners_for", 0) / hm
        h_corners_aga  = home_stats.get("corners_against", 0) / hm
        a_corners_for  = away_stats.get("corners_for", 0) / am
        a_corners_aga  = away_stats.get("corners_against", 0) / am

        # Approccio Dixon-Coles semplificato per corner
        h_attack  = h_corners_for  / cls.LEAGUE_AVG_HOME
        h_defense = h_corners_aga  / cls.LEAGUE_AVG_AWAY
        a_attack  = a_corners_for  / cls.LEAGUE_AVG_AWAY
        a_defense = a_corners_aga  / cls.LEAGUE_AVG_HOME

        lh = h_attack * a_defense * cls.LEAGUE_AVG_HOME * 1.05
        la = a_attack * h_defense * cls.LEAGUE_AVG_AWAY

        lh = max(2.0, min(10.0, lh))
        la = max(1.5, min(9.0, la))

        return cls(lambda_home=lh, lambda_away=la)

    @classmethod
    def from_api_stats(
        cls,
        home_stats: dict,
        away_stats: dict,
    ) -> "CornerModel":
        """
        Costruisce il modello da statistiche API-Football (/teams/statistics).

        home_stats / away_stats: output di FootballExternalCollector.parse_corner_stats()
        Devono avere: avg_corners_for, matches_home/away/total

        Logica:
          λ_home = media corner fatti dalla squadra casa nelle partite in casa
          λ_away = media corner fatti dalla squadra ospite nelle partite in trasferta
          Se dati insufficienti (<5 partite), fallback su from_win_prob.
        """
        hm = home_stats.get("matches_home", 0)
        am = away_stats.get("matches_away", 0)

        if hm < 5 or am < 5:
            return cls()   # fallback medie europee

        # Media corner fatti in casa vs. media fatti in trasferta
        # Normalizzata sulla media di lega
        h_avg = home_stats.get("avg_corners_for", cls.LEAGUE_AVG_HOME)
        a_avg = away_stats.get("avg_corners_for", cls.LEAGUE_AVG_AWAY)

        # Scala: se una squadra fa 6.5 corner in casa (vs media 5.5) → fattore 1.18
        h_factor = h_avg / cls.LEAGUE_AVG_HOME
        a_factor = a_avg / cls.LEAGUE_AVG_AWAY

        lh = cls.LEAGUE_AVG_HOME * h_factor
        la = cls.LEAGUE_AVG_AWAY * a_factor

        lh = max(2.0, min(10.0, lh))
        la = max(1.5, min(9.0, la))

        return cls(lambda_home=lh, lambda_away=la)

    @classmethod
    def from_win_prob(
        cls,
        home_win: float,
    ) -> "CornerModel":
        """
        Stima λ corner dalla probabilità di vittoria casa.

        Le squadre più forti tendono ad attaccare di più → più corner.
        Calibrazione: home_win=0.33 → lh≈5.0, home_win=0.65 → lh≈6.2
        """
        delta = home_win - 0.38   # scostamento dalla neutralità

        lh = cls.LEAGUE_AVG_HOME + 1.50 * delta   # più sensibile dei gol
        la = cls.LEAGUE_AVG_AWAY - 1.20 * delta

        lh = max(2.0, min(10.0, lh))
        la = max(1.5, min(9.0, la))

        return cls(lambda_home=lh, lambda_away=la)

    # ------------------------------------------------------------------
    # Calcoli
    # ------------------------------------------------------------------

    @staticmethod
    def _poisson(k: int, lam: float) -> float:
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    def _over_prob(self, threshold: float, max_corners: int = 25) -> float:
        """P(totale corner > threshold)."""
        lam = self.lh + self.la
        total = 0.0
        for k in range(max_corners + 1):
            if k > threshold:
                total += self._poisson(k, lam)
        return total

    def _home_over_prob(self, threshold: float, max_corners: int = 20) -> float:
        """P(corner casa > threshold)."""
        total = 0.0
        for k in range(max_corners + 1):
            if k > threshold:
                total += self._poisson(k, self.lh)
        return total

    def markets(self) -> dict:
        """
        Calcola probabilità per i principali mercati corner.

        Ritorna dict con:
          lambda_home, lambda_away, expected_total
          over_8_5, under_8_5
          over_9_5, under_9_5
          over_10_5, under_10_5
          over_11_5, under_11_5
          home_over_4_5, home_under_4_5  (corner solo casa)
          home_over_5_5, home_under_5_5
        """
        expected = self.lh + self.la

        o85  = self._over_prob(8.5)
        o95  = self._over_prob(9.5)
        o105 = self._over_prob(10.5)
        o115 = self._over_prob(11.5)

        h_o45 = self._home_over_prob(4.5)
        h_o55 = self._home_over_prob(5.5)

        return {
            "lambda_home":    round(self.lh, 2),
            "lambda_away":    round(self.la, 2),
            "expected_total": round(expected, 2),
            "over_8_5":       round(o85, 4),
            "under_8_5":      round(1 - o85, 4),
            "over_9_5":       round(o95, 4),
            "under_9_5":      round(1 - o95, 4),
            "over_10_5":      round(o105, 4),
            "under_10_5":     round(1 - o105, 4),
            "over_11_5":      round(o115, 4),
            "under_11_5":     round(1 - o115, 4),
            "home_over_4_5":  round(h_o45, 4),
            "home_under_4_5": round(1 - h_o45, 4),
            "home_over_5_5":  round(h_o55, 4),
            "home_under_5_5": round(1 - h_o55, 4),
        }

    def value_signals(
        self,
        market_odds: dict,
        min_edge: float = 0.05,
    ) -> list[dict]:
        """
        Individua value bet nei mercati corner.

        market_odds: dict con chiavi come 'over_9_5', 'under_10_5', ecc.
        """
        m = self.markets()
        signals = []

        checks = [
            ("over_8_5",       "over_8_5"),
            ("under_8_5",      "under_8_5"),
            ("over_9_5",       "over_9_5"),
            ("under_9_5",      "under_9_5"),
            ("over_10_5",      "over_10_5"),
            ("under_10_5",     "under_10_5"),
            ("over_11_5",      "over_11_5"),
            ("under_11_5",     "under_11_5"),
            ("home_over_4_5",  "home_over_4_5"),
            ("home_under_4_5", "home_under_4_5"),
            ("home_over_5_5",  "home_over_5_5"),
            ("home_under_5_5", "home_under_5_5"),
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
                    "market":             market_key,
                    "our_probability":    round(our_prob, 4),
                    "market_probability": round(market_prob, 4),
                    "edge":               round(edge, 4),
                    "market_odd":         odd,
                    "our_fair_odd":       round(1.0 / our_prob, 2),
                    "recommendation":     "VALUE BET" if edge >= 0.08 else "WATCH",
                })

        return sorted(signals, key=lambda x: x["edge"], reverse=True)

    def __repr__(self) -> str:
        m = self.markets()
        return (
            f"CornerModel(λ_home={self.lh:.2f}, λ_away={self.la:.2f}) "
            f"| Expected={m['expected_total']} Over9.5={m['over_9_5']:.1%}"
        )
