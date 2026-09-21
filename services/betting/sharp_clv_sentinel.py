"""
Sharp Market Sentinel & Closing Line Value (CLV) Detector
Confronta le quote commerciali (Netwin) con i benchmark sharp internazionali
(Pinnacle, Betfair Exchange) per rilevare quote ritardate (Steam Moves)
e garantire valore matematico positivo (CLV > +5%).
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional

class SharpMarketSentinel:
    """
    Rilevatore di Closing Line Value (CLV) e ritardi di quota tra Sharp e Netwin.
    """

    def __init__(self, clv_threshold_pct: float = 5.0):
        self.clv_threshold_pct = clv_threshold_pct

    @staticmethod
    def calculate_clv(netwin_odds: float, sharp_fair_odds: float) -> float:
        """
        Calcola il Closing Line Value (CLV) percentuale.
        CLV = ((Netwin Odds / Sharp Fair Odds) - 1) * 100
        """
        if sharp_fair_odds <= 1.0 or netwin_odds <= 1.0:
            return 0.0
        return round(((netwin_odds / sharp_fair_odds) - 1.0) * 100.0, 2)

    def scan_market_discrepancy(
        self,
        match_name: str,
        market: str,
        netwin_odds: float,
        pinnacle_odds: float,
        pinnacle_margin_pct: float = 2.0
    ) -> Dict[str, Any]:
        """
        Analizza se la quota Netwin offre valore rispetto al benchmark sharp Pinnacle.
        """
        # Rimozione margine Pinnacle per trovare la quota equa reale (Fair Sharp Odds)
        fair_sharp_odds = pinnacle_odds * (1.0 + (pinnacle_margin_pct / 100.0))
        clv = self.calculate_clv(netwin_odds, fair_sharp_odds)

        is_steam_move = netwin_odds > (pinnacle_odds * 1.08) # Netwin è in ritardo di oltre l'8%
        is_value_gem = clv >= self.clv_threshold_pct and netwin_odds >= 1.60

        return {
            "match": match_name,
            "market": market,
            "netwin_odds": netwin_odds,
            "pinnacle_odds": pinnacle_odds,
            "fair_sharp_odds": round(fair_sharp_odds, 2),
            "clv_pct": clv,
            "is_delayed_quota": is_steam_move,
            "is_true_gem": is_value_gem,
            "verdict": "VALORE ACCERTATO (GIOCARE SUBITO)" if is_value_gem else (
                "RITARDO NETWIN (STEAM MOVE)" if is_steam_move else "NEUTRA / ALLINEATA"
            )
        }
