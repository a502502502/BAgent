#!/usr/bin/env python3
"""
scripts/run_historical_backtest.py — Esegue Backtest Storico Avanzato su Serie A, Premier League, LaLiga, Bundesliga, Ligue 1.
Calcola rendimento reale, Yield %, ROI % e validazione temporale anti-leakage.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import make_column_transformer
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.database.historical_loader import HistoricalDataLoader
from services.analysis.backtest_engine import BacktestEngine

def run_backtest():
    print("=" * 70)
    print("🔬 BAGENT HISTORICAL BACKTEST ENGINE — TOP 5 CAMPIONATI EUROPEI")
    print("=" * 70)

    loader = HistoricalDataLoader()
    leagues = ["Serie A", "Premier League", "La Liga", "Bundesliga", "Ligue 1"]
    years = [2021, 2022, 2023, 2024]
    
    print(f"📥 Download e preparazione dati per: {', '.join(leagues)} ({years[0]}-{years[-1]})...")
    X, Y, O = loader.load_dataset(leagues=leagues, years=years)
    print(f"✅ Totale partite caricate: {len(X)} partite storiche con quote reali!\n")

    # TimeSeriesSplit su 5 fold temporali
    n_splits = 5
    tscv = TimeSeriesSplit(n_splits=n_splits)

    engine = BacktestEngine(initial_bankroll=1000.0, stake_per_bet=20.0)

    markets = ["home_win", "away_win", "over_2.5", "under_2.5"]
    
    fold_results = []
    
    print(f"⚙️ Avvio simulazione temporale su {n_splits} fold...")
    print("-" * 70)

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        Y_train, Y_test = Y.iloc[train_idx], Y.iloc[test_idx]
        O_test = O.iloc[test_idx]

        train_start = X_train["DateClean"].min().strftime("%d/%m/%Y")
        train_end = X_train["DateClean"].max().strftime("%d/%m/%Y")
        test_start = X_test["DateClean"].min().strftime("%d/%m/%Y")
        test_end = X_test["DateClean"].max().strftime("%d/%m/%Y")

        # Addestra modello per stimare probabilità
        prob_preds = pd.DataFrame(index=X_test.index)

        # Preprocessing: OneHotEncoder su squadre e leghe
        preprocessor = make_column_transformer(
            (OneHotEncoder(handle_unknown="ignore"), ["LeagueName", "HomeTeam", "AwayTeam"]),
            remainder="drop"
        )

        for m in markets:
            clf = make_pipeline(
                preprocessor,
                SimpleImputer(),
                LogisticRegression(max_iter=500, solver="lbfgs")
            )
            # Addestra solo sul passato
            clf.fit(X_train[["LeagueName", "HomeTeam", "AwayTeam"]], Y_train[m])
            # Predici probabilità sul futuro
            proba = clf.predict_proba(X_test[["LeagueName", "HomeTeam", "AwayTeam"]])[:, 1]
            prob_preds[m] = proba

        # Valuta strategia Value Bet (Edge >= 5%, Quota >= 1.20)
        summary = engine.evaluate_strategy(
            probs=prob_preds,
            outcomes=Y_test[markets],
            odds=O_test[markets],
            min_edge=0.05,
            min_odd=1.20,
            max_odd=4.50
        )

        fold_results.append({
            "Fold": fold,
            "Train Period": f"{train_start} -> {train_end}",
            "Test Period": f"{test_start} -> {test_end}",
            "Bets": summary.total_bets,
            "Win Rate %": f"{summary.win_rate:.1f}%",
            "Yield %": f"{summary.yield_pct:+.2f}%",
            "ROI %": f"{summary.roi_pct:+.2f}%",
            "Net Profit": f"{summary.net_profit:+.2f} €",
            "Max DD %": f"{summary.max_drawdown_pct:.1f}%"
        })

    df_res = pd.DataFrame(fold_results)
    print(df_res.to_string(index=False))
    print("-" * 70)
    print("🏆 SIMULAZIONE COMPLETATA CON SUCCESSO!")

if __name__ == "__main__":
    run_backtest()
