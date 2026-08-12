"""
TennisWinModel — probabilità di vittoria nel tennis da ranking ATP/WTA.

Utilizza Bradley-Terry: P(P1 vince) = rating1 / (rating1 + rating2)
dove rating = 1/rank (con aggiustamenti superficie e H2H).

Utilizzo:
    model = TennisWinModel(player1_rank=15, player2_rank=42, surface="clay")
    print(model.win_probs())   # {"player1": 0.71, "player2": 0.29}
    print(model.value_signals({"player1": 1.60, "player2": 2.40}))
"""

from __future__ import annotations
from typing import Optional, Tuple


class TennisWinModel:
    """
    Parametri:
        player1_rank:       ranking ATP/WTA (1 = numero 1 al mondo)
        player2_rank:       ranking ATP/WTA del secondo giocatore
        surface:            'clay' | 'grass' | 'hard' | 'indoor'
        h2h:                (vittorie P1, vittorie P2) - opzionale
        p1_surface_factor:  moltiplicatore manuale forza P1 su questa superficie
                            (1.0 = neutro, 1.2 = P1 molto favorito su superficie)
        p2_surface_factor:  idem per P2
    """

    def __init__(
        self,
        player1_rank: int,
        player2_rank: int,
        surface: str = "hard",
        h2h: Optional[Tuple[int, int]] = None,
        p1_surface_factor: float = 1.0,
        p2_surface_factor: float = 1.0,
    ):
        self.r1  = max(1, int(player1_rank))
        self.r2  = max(1, int(player2_rank))
        self.surface = surface.lower()
        self.h2h = h2h
        self.sf1 = float(p1_surface_factor)
        self.sf2 = float(p2_surface_factor)

    # ------------------------------------------------------------------
    # Calcolo probabilità
    # ------------------------------------------------------------------

    def _ranking_win_prob(self) -> float:
        """
        Bradley-Terry: rating = (1/rank) * surface_factor
        P(P1) = rating1 / (rating1 + rating2)

        Con ranking inversamente proporzionale: rank 1 >> rank 100.
        Questo riflette la differenza reale di qualità tra top e metà classifica.
        """
        rating1 = (1.0 / self.r1) * self.sf1
        rating2 = (1.0 / self.r2) * self.sf2
        return rating1 / (rating1 + rating2)

    def _apply_h2h(self, base_prob: float) -> float:
        """
        Aggiusta con record H2H.

        Peso proporzionale alle partite disputate, cap 30%.
        Poche partite H2H contano poco (credibilità statistica bassa).
        """
        if not self.h2h:
            return base_prob

        p1_w, p2_w = self.h2h
        total = p1_w + p2_w
        if total == 0:
            return base_prob

        h2h_prob = p1_w / total
        weight   = min(0.30, total * 0.04)  # 4% per partita, max 30%
        return base_prob * (1 - weight) + h2h_prob * weight

    def win_probs(self) -> dict:
        """
        Ritorna {"player1": float, "player2": float} — somma a 1.0.
        """
        p1 = self._ranking_win_prob()
        p1 = self._apply_h2h(p1)
        p1 = round(max(0.05, min(0.95, p1)), 4)
        return {"player1": p1, "player2": round(1.0 - p1, 4)}

    # ------------------------------------------------------------------
    # Value bets
    # ------------------------------------------------------------------

    def value_signals(
        self,
        market_odds: dict,
        min_edge: float = 0.05,
    ) -> list[dict]:
        """
        Confronta le nostre probabilità con le quote di mercato.
        market_odds: {"player1": 1.75, "player2": 2.20}
        """
        probs   = self.win_probs()
        signals = []

        for player in ("player1", "player2"):
            odd = market_odds.get(player)
            if not odd or odd <= 1.0:
                continue

            our_p    = probs[player]
            mkt_p    = 1.0 / odd
            edge     = our_p - mkt_p

            if edge >= min_edge:
                signals.append({
                    "market":             player,
                    "our_probability":    round(our_p, 4),
                    "market_probability": round(mkt_p, 4),
                    "edge":               round(edge, 4),
                    "market_odd":         odd,
                    "our_fair_odd":       round(1.0 / our_p, 2),
                    "recommendation":     "VALUE BET" if edge >= 0.08 else "WATCH",
                })

        return sorted(signals, key=lambda x: x["edge"], reverse=True)

    def __repr__(self) -> str:
        p = self.win_probs()
        return (
            f"TennisWinModel(R{self.r1} vs R{self.r2} | {self.surface}) "
            f"P1={p['player1']:.1%}  P2={p['player2']:.1%}"
        )
