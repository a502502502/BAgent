"""
Sharp Market Sentinel & Closing Line Value (CLV) Detector
Metodi avanzati per rimozione margine (Shin 1992, Power Method),
Kelly Criterion frazionario per stake sizing, e rilevamento Steam Moves.
"""

from __future__ import annotations
import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

class SharpMarketSentinel:
    """
    Rilevatore di CLV e ritardi di quota con metodi quantitativi avanzati.
    Supporta il Metodo Shin (1992) per isolare scommettitori informati
    e il Fractional Kelly Criterion per il dimensionamento del rischio.
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

    def _remove_margin_shin(
        self, 
        odds_list: List[float], 
        max_iterations: int = 100, 
        tolerance: float = 1e-6
    ) -> List[float]:
        """
        Rimuove il margine usando la formula esatta di Shin (1992, 1993).
        Modella la quota come combinazione di scommettitori informati (z) e non informati (1-z).
        Risolve per bisezione/Newton la condizione sum(p_i(z)) = 1:
        p_i = (sqrt(z^2 + 4*(1-z)*pi_i^2 / sum(pi)) - z) / (2*(1-z))
        """
        n = len(odds_list)
        if n == 0:
            return []
        
        pi = np.array([1.0 / o for o in odds_list], dtype=float)
        sum_pi = np.sum(pi)
        
        # Se non c'è margine o è già <= 1.0
        if sum_pi <= 1.0:
            p_norm = pi / sum_pi
            return [float(round(1.0 / p, 4)) for p in p_norm]

        # Bisezione robusta per z in [0.0, 0.40]
        z_low = 0.0
        z_high = 0.40
        z = 0.02

        for _ in range(max_iterations):
            z_mid = (z_low + z_high) / 2.0
            terms = np.sqrt(z_mid**2 + 4.0 * (1.0 - z_mid) * (pi**2) / sum_pi)
            p_i = (terms - z_mid) / (2.0 * (1.0 - z_mid))
            f_z = np.sum(p_i) - 1.0

            if abs(f_z) < tolerance:
                z = z_mid
                break
            if f_z > 0:
                z_low = z_mid
            else:
                z_high = z_mid
            z = z_mid

        # Calcola probabilità vere normalizzate
        terms = np.sqrt(z**2 + 4.0 * (1.0 - z) * (pi**2) / sum_pi)
        p_i = (terms - z) / (2.0 * (1.0 - z))
        p_i = p_i / np.sum(p_i)

        fair_odds = [float(round(1.0 / p, 4)) for p in p_i]
        return fair_odds

    def _remove_margin_power(
        self, 
        odds_list: List[float],
        tolerance: float = 1e-6
    ) -> List[float]:
        """
        Rimuove il margine usando il Power Method (decomposizione moltiplicativa logaritmica).
        Trova l'esponente k tale che sum(pi_i^k) = 1.
        """
        n = len(odds_list)
        if n == 0:
            return []
        
        pi = np.array([1.0 / o for o in odds_list], dtype=float)
        sum_pi = np.sum(pi)
        
        if sum_pi <= 1.0:
            p_norm = pi / sum_pi
            return [float(round(1.0 / p, 4)) for p in p_norm]
        
        # Bisezione per trovare il power k
        power_low = 1.0
        power_high = 3.0
        power = 1.0

        for _ in range(50):
            power_mid = (power_low + power_high) / 2.0
            powered_probs = pi ** power_mid
            total_powered = np.sum(powered_probs)

            if abs(total_powered - 1.0) < tolerance:
                power = power_mid
                break
            if total_powered > 1.0:
                power_low = power_mid
            else:
                power_high = power_mid
            power = power_mid
        
        powered_probs = pi ** power
        fair_probs = powered_probs / np.sum(powered_probs)
        return [float(round(1.0 / p, 4)) for p in fair_probs]

    def remove_margin(
        self, 
        odds_list: List[float], 
        method: str = "shin"
    ) -> List[float]:
        """
        Rimuove il margine dalle quote usando il metodo specificato ('shin' o 'power').
        """
        if method.lower() == "shin":
            return self._remove_margin_shin(odds_list)
        elif method.lower() == "power":
            return self._remove_margin_power(odds_list)
        else:
            raise ValueError(f"Metodo non riconosciuto: {method}. Usa 'shin' o 'power'.")

    def calculate_kelly_stake(
        self,
        netwin_odds: float,
        fair_sharp_odds: float,
        bankroll: float = 1000.0,
        kelly_fraction: float = 0.5,
        max_stake_pct: float = 5.0
    ) -> Dict[str, float]:
        """
        Calcola la stake ottimale usando il Fractional Kelly Criterion:
        f* = ((b * p - q) / b) * fraction
        
        Args:
            netwin_odds: Quota Netwin disponibile
            fair_sharp_odds: Quota equa sharp (dopo rimozione vig)
            bankroll: Bankroll totale disponibile
            kelly_fraction: Frazione di Kelly (0.5 = Half Kelly, 0.25 = Quarter Kelly)
            max_stake_pct: Percentuale massima del bankroll allocabile
        """
        if netwin_odds <= 1.0 or fair_sharp_odds <= 1.0:
            return {
                "stake_amount": 0.0,
                "stake_pct": 0.0,
                "expected_value": 0.0,
                "kelly_criterion": "NO_VALUE"
            }
        
        p_win = 1.0 / fair_sharp_odds
        p_lose = 1.0 - p_win
        b = netwin_odds - 1.0
        
        # Formula Kelly completa
        kelly_full = (b * p_win - p_lose) / b
        
        if kelly_full <= 0:
            return {
                "stake_amount": 0.0,
                "stake_pct": 0.0,
                "expected_value": 0.0,
                "kelly_full_pct": 0.0,
                "kelly_adjusted_pct": 0.0,
                "kelly_criterion": "NO_VALUE"
            }
        
        kelly_adjusted = kelly_full * kelly_fraction
        max_stake_decimal = max_stake_pct / 100.0
        kelly_capped = min(kelly_adjusted, max_stake_decimal)
        
        stake_amount = bankroll * kelly_capped
        ev = (p_win * b - p_lose) * stake_amount
        
        return {
            "stake_amount": round(stake_amount, 2),
            "stake_pct": round(kelly_capped * 100.0, 2),
            "expected_value": round(ev, 2),
            "kelly_full_pct": round(kelly_full * 100.0, 2),
            "kelly_adjusted_pct": round(kelly_adjusted * 100.0, 2),
            "kelly_criterion": "VALUE_BET"
        }

    def detect_steam_move(
        self,
        current_odds: float,
        previous_odds: float,
        time_delta_minutes: float
    ) -> Dict[str, Any]:
        """
        Rileva e classifica Steam Moves e drop rapidi di quota su mercati sharp.
        """
        if previous_odds <= 1.0 or current_odds <= 1.0:
            return {
                "is_steam_move": False,
                "steam_type": "NO_DATA",
                "drop_pct": 0.0,
                "velocity_pct_per_min": 0.0
            }
        
        drop_pct = ((previous_odds - current_odds) / previous_odds) * 100.0
        velocity = drop_pct / max(0.1, time_delta_minutes)
        
        is_steam_move = False
        steam_type = "STABLE"
        
        if drop_pct >= 5.0 and time_delta_minutes <= 15:
            is_steam_move = True
            steam_type = "SHARP_INFLUX"
        elif drop_pct >= 3.0 and time_delta_minutes <= 30:
            is_steam_move = True
            steam_type = "MODERATE_STEAM"
        elif drop_pct >= 2.0 and time_delta_minutes <= 60:
            is_steam_move = True
            steam_type = "SLOW_DRIFT"
        
        return {
            "is_steam_move": is_steam_move,
            "steam_type": steam_type,
            "drop_pct": round(drop_pct, 2),
            "velocity_pct_per_min": round(velocity, 3)
        }

    def scan_market_discrepancy(
        self,
        match_name: str,
        market: str,
        netwin_odds: float,
        pinnacle_odds: float,
        pinnacle_all_odds: Optional[List[float]] = None,
        margin_removal_method: str = "shin",
        bankroll: float = 1000.0,
        kelly_fraction: float = 0.5,
        max_stake_pct: float = 5.0,
        previous_pinnacle_odds: Optional[float] = None,
        time_delta_minutes: Optional[float] = None,
        pinnacle_margin_pct: float = 2.0
    ) -> Dict[str, Any]:
        """
        Analizza se la quota Netwin offre valore rispetto al benchmark sharp Pinnacle.
        Supporta quote multiple con Shin/Power Method e calcolo Kelly.
        """
        if pinnacle_all_odds and len(pinnacle_all_odds) > 1:
            fair_sharp_odds_list = self.remove_margin(pinnacle_all_odds, method=margin_removal_method)
            try:
                # Trova la quota più vicina per tolleranza float
                idx = min(range(len(pinnacle_all_odds)), key=lambda i: abs(pinnacle_all_odds[i] - pinnacle_odds))
                fair_sharp_odds = fair_sharp_odds_list[idx]
            except Exception:
                fair_sharp_odds = pinnacle_odds * (1.0 + (pinnacle_margin_pct / 100.0))
        else:
            fair_sharp_odds = pinnacle_odds * (1.0 + (pinnacle_margin_pct / 100.0))
        
        clv = self.calculate_clv(netwin_odds, fair_sharp_odds)
        
        steam_analysis = {"is_steam_move": False, "steam_type": "STABLE"}
        if previous_pinnacle_odds and time_delta_minutes:
            steam_analysis = self.detect_steam_move(
                current_odds=pinnacle_odds,
                previous_odds=previous_pinnacle_odds,
                time_delta_minutes=time_delta_minutes
            )
        
        kelly_analysis = self.calculate_kelly_stake(
            netwin_odds=netwin_odds,
            fair_sharp_odds=fair_sharp_odds,
            bankroll=bankroll,
            kelly_fraction=kelly_fraction,
            max_stake_pct=max_stake_pct
        )
        
        is_value_gem = clv >= self.clv_threshold_pct and netwin_odds >= 1.60
        is_steam_move = steam_analysis["is_steam_move"] or (netwin_odds > pinnacle_odds * 1.08)
        
        if is_value_gem and kelly_analysis.get("kelly_criterion") == "VALUE_BET":
            verdict = "VALORE ACCERTATO (GIOCARE SUBITO)"
        elif is_steam_move:
            verdict = "RITARDO NETWIN (STEAM MOVE)"
        elif clv > 0:
            verdict = "LEGGERO VALORE (MONITORARE)"
        else:
            verdict = "NEUTRA / ALLINEATA"
        
        return {
            "match": match_name,
            "market": market,
            "netwin_odds": netwin_odds,
            "pinnacle_odds": pinnacle_odds,
            "fair_sharp_odds": round(fair_sharp_odds, 3),
            "margin_removal_method": margin_removal_method,
            "clv_pct": clv,
            "steam_analysis": steam_analysis,
            "kelly_stake": kelly_analysis,
            "is_delayed_quota": is_steam_move,
            "is_true_gem": is_value_gem,
            "verdict": verdict
        }
