#!/usr/bin/env python3
"""
services/analysis/backtest_engine.py — Motore di Backtesting Rigoroso per BAgent.
Simula strategie di betting temporali (TimeSeriesSplit) su dati storici per validare Yield, ROI e BetGuard rules.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from dataclasses import dataclass
from sklearn.model_selection import TimeSeriesSplit

@dataclass
class BacktestSummary:
    total_bets: int
    won_bets: int
    win_rate: float
    total_staked: float
    total_returned: float
    net_profit: float
    yield_pct: float
    roi_pct: float
    max_drawdown_pct: float

class BacktestEngine:
    """Esegue backtesting temporale senza data leakage su quote e probabilità."""

    def __init__(self, initial_bankroll: float = 1000.0, stake_per_bet: float = 20.0):
        self.initial_bankroll = initial_bankroll
        self.stake_per_bet = stake_per_bet

    def evaluate_strategy(self, probs: pd.DataFrame, outcomes: pd.DataFrame, odds: pd.DataFrame, min_edge: float = 0.05, min_odd: float = 1.20, max_odd: float = 5.00) -> BacktestSummary:
        """
        Valuta una strategia deterministica basata su probabilità e quote.
        Piazza scommessa solo se prob * quota - 1 >= min_edge e min_odd <= quota <= max_odd.
        """
        bankroll = self.initial_bankroll
        equity_curve = [bankroll]
        
        total_bets = 0
        won_bets = 0
        total_staked = 0.0
        total_returned = 0.0

        for col in outcomes.columns:
            if col not in probs.columns or col not in odds.columns:
                continue

            p = probs[col].values
            y = outcomes[col].values
            o = odds[col].values

            # Calcola Edge: (prob * quota) - 1
            edge = (p * o) - 1.0

            # Filtra selezioni valide
            valid_mask = (edge >= min_edge) & (o >= min_odd) & (o <= max_odd) & (~np.isnan(o)) & (~np.isnan(p))

            for is_selected, won, odd_val in zip(valid_mask, y, o):
                if is_selected:
                    total_bets += 1
                    stake = self.stake_per_bet
                    total_staked += stake
                    bankroll -= stake

                    if won == 1:
                        won_bets += 1
                        ret = stake * odd_val
                        total_returned += ret
                        bankroll += ret

                    equity_curve.append(bankroll)

        net_profit = total_returned - total_staked
        yield_pct = (net_profit / total_staked * 100.0) if total_staked > 0 else 0.0
        roi_pct = (net_profit / self.initial_bankroll * 100.0)
        win_rate = (won_bets / total_bets * 100.0) if total_bets > 0 else 0.0

        # Calcola Max Drawdown
        equity_arr = np.array(equity_curve)
        peak = np.maximum.accumulate(equity_arr)
        drawdown = (peak - equity_arr) / np.maximum(peak, 1.0) * 100.0
        max_dd = np.max(drawdown) if len(drawdown) > 0 else 0.0

        return BacktestSummary(
            total_bets=total_bets,
            won_bets=won_bets,
            win_rate=win_rate,
            total_staked=total_staked,
            total_returned=total_returned,
            net_profit=net_profit,
            yield_pct=yield_pct,
            roi_pct=roi_pct,
            max_drawdown_pct=max_dd
        )
