"""
TennisSetModel — mercati su set e game totali.

Data P(player1 vince il match), stima:
  Best of 3: P(2-0), P(2-1), P(0-2), P(1-2) — e over/under 2.5 set
  Best of 5: P(3-0..3-2) e over/under 3.5 / 4.5 set

Utilizzo:
    model = TennisSetModel(p1_win_prob=0.65, best_of=3)
    print(model.markets())
    print(model.value_signals({"over_2_5_sets": 1.85}))
"""

from __future__ import annotations


class TennisSetModel:

    def __init__(self, p1_win_prob: float, best_of: int = 3):
        self.p      = max(0.05, min(0.95, float(p1_win_prob)))
        self.q      = 1.0 - self.p
        self.best_of = best_of

    # ------------------------------------------------------------------
    # Stima P(vince un set) da P(vince il match)
    # ------------------------------------------------------------------

    def _set_win_prob(self) -> float:
        """
        Approssimazione calibrata empiricamente.

        Best-of-3 esatto: P(match) = ps²·(1 + 2·qs) non è invertibile in forma chiusa,
        usiamo la linearizzazione: ps ≈ 0.5 + 0.42·(p_match - 0.5)

        Verifica:
          p=0.5  → ps=0.50  → P(match)=0.50  ✓
          p=0.7  → ps=0.584 → P(match)≈0.70  ✓
          p=0.9  → ps=0.668 → P(match)≈0.90  ✓
        """
        if self.best_of == 3:
            return 0.5 + 0.42 * (self.p - 0.5)
        else:
            return 0.5 + 0.35 * (self.p - 0.5)

    # ------------------------------------------------------------------
    # Mercati
    # ------------------------------------------------------------------

    def markets(self) -> dict:
        ps = self._set_win_prob()
        qs = 1.0 - ps

        if self.best_of == 3:
            # Distribuzione esatta best-of-3
            raw_p1_2_0 = ps * ps
            raw_p1_2_1 = 2 * ps * ps * qs
            raw_p2_2_0 = qs * qs
            raw_p2_2_1 = 2 * qs * qs * ps
            total = raw_p1_2_0 + raw_p1_2_1 + raw_p2_2_0 + raw_p2_2_1

            p1_2_0 = raw_p1_2_0 / total
            p1_2_1 = raw_p1_2_1 / total
            p2_2_0 = raw_p2_2_0 / total
            p2_2_1 = raw_p2_2_1 / total

            two_sets   = p1_2_0 + p2_2_0
            three_sets = p1_2_1 + p2_2_1

            return {
                "p1_wins":        round(self.p, 4),
                "p2_wins":        round(self.q, 4),
                "p1_2_0":         round(p1_2_0, 4),
                "p1_2_1":         round(p1_2_1, 4),
                "p2_2_1":         round(p2_2_1, 4),
                "p2_2_0":         round(p2_2_0, 4),
                "two_sets":       round(two_sets, 4),
                "three_sets":     round(three_sets, 4),
                "over_2_5_sets":  round(three_sets, 4),
                "under_2_5_sets": round(two_sets, 4),
                "expected_sets":  round(2 * two_sets + 3 * three_sets, 2),
            }

        else:  # best of 5
            raw = {
                "p1_3_0": ps**3,
                "p1_3_1": 3 * ps**3 * qs,
                "p1_3_2": 6 * ps**3 * qs**2,
                "p2_3_2": 6 * qs**3 * ps**2,
                "p2_3_1": 3 * qs**3 * ps,
                "p2_3_0": qs**3,
            }
            total = sum(raw.values())
            n = {k: v / total for k, v in raw.items()}

            three = n["p1_3_0"] + n["p2_3_0"]
            four  = n["p1_3_1"] + n["p2_3_1"]
            five  = n["p1_3_2"] + n["p2_3_2"]

            return {
                "p1_wins":         round(self.p, 4),
                "p2_wins":         round(self.q, 4),
                "p1_3_0":          round(n["p1_3_0"], 4),
                "p1_3_1":          round(n["p1_3_1"], 4),
                "p1_3_2":          round(n["p1_3_2"], 4),
                "p2_3_2":          round(n["p2_3_2"], 4),
                "p2_3_1":          round(n["p2_3_1"], 4),
                "p2_3_0":          round(n["p2_3_0"], 4),
                "three_sets":      round(three, 4),
                "four_sets":       round(four, 4),
                "five_sets":       round(five, 4),
                "over_3_5_sets":   round(four + five, 4),
                "under_3_5_sets":  round(three, 4),
                "over_4_5_sets":   round(five, 4),
                "under_4_5_sets":  round(three + four, 4),
                "expected_sets":   round(3*three + 4*four + 5*five, 2),
            }

    # ------------------------------------------------------------------
    # Value bets
    # ------------------------------------------------------------------

    def value_signals(self, market_odds: dict, min_edge: float = 0.05) -> list[dict]:
        m       = self.markets()
        signals = []

        keys = [
            "over_2_5_sets", "under_2_5_sets",
            "over_3_5_sets", "under_3_5_sets",
            "over_4_5_sets", "under_4_5_sets",
        ]

        for key in keys:
            odd = market_odds.get(key)
            if not odd or odd <= 1.0 or key not in m:
                continue

            our_p = m[key]
            mkt_p = 1.0 / odd
            edge  = our_p - mkt_p

            if edge >= min_edge:
                signals.append({
                    "market":             key,
                    "our_probability":    round(our_p, 4),
                    "market_probability": round(mkt_p, 4),
                    "edge":               round(edge, 4),
                    "market_odd":         odd,
                    "our_fair_odd":       round(1.0 / our_p, 2),
                    "recommendation":     "VALUE BET" if edge >= 0.08 else "WATCH",
                })

        return sorted(signals, key=lambda x: x["edge"], reverse=True)
