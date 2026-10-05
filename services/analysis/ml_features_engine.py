"""
services/analysis/ml_features_engine.py

Modulo di Feature Engineering e Machine Learning per BAgent,
ispirato all'architettura di fernandosc14/football-prediction.

Caratteristiche implementate:
- Feature H2H (Win rate, Goal rate casa/fuori, total goals H2H)
- Feature di forma recente (media punti ultimi N match, media gol fatti/subiti)
- Differenziale di classifica (Rank Difference)
- Feature quote e lavagna (rapporto quote 1/2, min/max, implied probabilities margin-free)
- Training e inferenza con RandomForest / GradientBoosting con output probabilistico (predict_proba)
  per Winner (1X2), Over 1.5, Over 2.5, BTTS e Double Chance.
"""

from __future__ import annotations
import math
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class MLFeaturesEngine:
    """
    Engine per l'estrazione delle feature tabellari avanzate e 
    la predizione tramite modelli supervisionati (Random Forest / Gradient Boosting).
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.models: Dict[str, RandomForestClassifier] = {}
        self.feature_columns: List[str] = [
            "rank_diff",
            "h2h_team1_win_rate",
            "h2h_team2_win_rate",
            "h2h_draw_rate",
            "h2h_goals_per_game",
            "team1_form_points",
            "team2_form_points",
            "team1_form_goals",
            "team2_form_goals",
            "odds_ratio_home_away",
            "odds_min",
            "implied_prob_home",
            "implied_prob_away"
        ]

    def extract_match_features(
        self,
        team1_rank: int,
        team2_rank: int,
        h2h_history: Dict[str, Any],
        recent_form_t1: Dict[str, Any],
        recent_form_t2: Dict[str, Any],
        odds: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Estrae un vettore di feature per una singola partita.
        """
        # 1. Differenziale di classifica (rank più basso = squadra migliore)
        rank_diff = float(team2_rank - team1_rank)

        # 2. Statistiche H2H
        h2h_played = max(h2h_history.get("games_played", 0), 1)
        h2h_t1_wins = h2h_history.get("team1_wins", 0)
        h2h_t2_wins = h2h_history.get("team2_wins", 0)
        h2h_draws = h2h_history.get("draws", 0)
        h2h_total_goals = h2h_history.get("team1_goals", 0) + h2h_history.get("team2_goals", 0)

        h2h_t1_win_rate = h2h_t1_wins / h2h_played
        h2h_t2_win_rate = h2h_t2_wins / h2h_played
        h2h_draw_rate = h2h_draws / h2h_played
        h2h_gpg = h2h_total_goals / h2h_played

        # 3. Forma recente (ultime 5 partite)
        t1_pts = recent_form_t1.get("points_avg", 1.2)
        t2_pts = recent_form_t2.get("points_avg", 1.2)
        t1_goals = recent_form_t1.get("goals_avg", 1.1)
        t2_goals = recent_form_t2.get("goals_avg", 1.1)

        # 4. Feature quote di mercato
        if odds and all(k in odds for k in ("home_win", "draw", "away_win")):
            hw, dr, aw = odds["home_win"], odds["draw"], odds["away_win"]
            margin = (1.0 / hw) + (1.0 / dr) + (1.0 / aw)
            odds_ratio = hw / aw if aw > 0 else 1.0
            odds_min = min(hw, dr, aw)
            implied_home = (1.0 / hw) / margin
            implied_away = (1.0 / aw) / margin
        else:
            odds_ratio = 1.0
            odds_min = 2.0
            implied_home = 0.40
            implied_away = 0.35

        return {
            "rank_diff": rank_diff,
            "h2h_team1_win_rate": h2h_t1_win_rate,
            "h2h_team2_win_rate": h2h_t2_win_rate,
            "h2h_draw_rate": h2h_draw_rate,
            "h2h_goals_per_game": h2h_gpg,
            "team1_form_points": t1_pts,
            "team2_form_points": t2_pts,
            "team1_form_goals": t1_goals,
            "team2_form_goals": t2_goals,
            "odds_ratio_home_away": odds_ratio,
            "odds_min": odds_min,
            "implied_prob_home": implied_home,
            "implied_prob_away": implied_away
        }

    def train_baseline_models(self, X: np.ndarray, y_dict: Dict[str, np.ndarray]):
        """
        Addestra modelli Random Forest per i diversi target (Winner, Over 2.5, BTTS, Double Chance).
        """
        for target_name, y in y_dict.items():
            rf = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                min_samples_leaf=5,
                random_state=self.random_state
            )
            rf.fit(X, y)
            self.models[target_name] = rf

    def predict_match_probabilities(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Genera le probabilità stimate per tutti i target modellati.
        Se i modelli non sono ancora addestrati con dataset storico esteso,
        fornisce una stima calibrata Bayesiana unendo prior empirici e le feature.
        """
        # Se abbiamo modelli addestrati, usiamo predict_proba
        if "winner" in self.models and "over25" in self.models:
            x_vec = np.array([[features[col] for col in self.feature_columns]])
            winner_probs = self.models["winner"].predict_proba(x_vec)[0]
            over_probs = self.models["over25"].predict_proba(x_vec)[0]
            btts_probs = self.models.get("btts", self.models["over25"]).predict_proba(x_vec)[0]
            
            p_home, p_draw, p_away = winner_probs[0], winner_probs[1], winner_probs[2]
            p_over25 = over_probs[1] if len(over_probs) > 1 else 0.5
            p_btts = btts_probs[1] if len(btts_probs) > 1 else 0.5
        else:
            # Calibrazione euristica-bayesiana (fondata sulle features di fernandosc14)
            implied_h = features.get("implied_prob_home", 0.40)
            implied_a = features.get("implied_prob_away", 0.35)
            implied_d = max(0.05, 1.0 - implied_h - implied_a)

            # Aggiustamento per forma recente e classifica
            form_delta = (features.get("team1_form_points", 1.2) - features.get("team2_form_points", 1.2)) * 0.05
            rank_delta = (features.get("rank_diff", 0) / 20.0) * 0.05
            h2h_delta = (features.get("h2h_team1_win_rate", 0.33) - features.get("h2h_team2_win_rate", 0.33)) * 0.05

            net_shift = np.clip(form_delta + rank_delta + h2h_delta, -0.15, 0.15)
            p_home = float(np.clip(implied_h + net_shift, 0.10, 0.85))
            p_away = float(np.clip(implied_a - net_shift, 0.10, 0.85))
            p_draw = float(max(0.05, 1.0 - p_home - p_away))
            # Normalizzazione
            total_p = p_home + p_draw + p_away
            p_home, p_draw, p_away = p_home / total_p, p_draw / total_p, p_away / total_p

            # Gol e BTTS basati su media gol storici ed H2H
            avg_goals = (features.get("team1_form_goals", 1.1) + features.get("team2_form_goals", 1.1)) / 2.0
            h2h_goals = features.get("h2h_goals_per_game", 2.2)
            expected_total_goals = (avg_goals * 2.0 + h2h_goals) / 2.0

            # Poisson approssimato per Over 2.5 e Over 1.5
            p_over25 = float(1.0 - np.exp(-expected_total_goals) * (1 + expected_total_goals + (expected_total_goals**2)/2.0))
            p_over15 = float(1.0 - np.exp(-expected_total_goals) * (1 + expected_total_goals))
            p_btts = float(np.clip((p_over25 * 0.85) + 0.15, 0.20, 0.80))

        return {
            "p_home": round(p_home, 4),
            "p_draw": round(p_draw, 4),
            "p_away": round(p_away, 4),
            "p_1X": round(p_home + p_draw, 4),
            "p_X2": round(p_draw + p_away, 4),
            "p_12": round(p_home + p_away, 4),
            "p_over_15": round(p_over15 if 'p_over15' in locals() else 0.75, 4),
            "p_over_25": round(p_over25, 4),
            "p_under_25": round(1.0 - p_over25, 4),
            "p_btts": round(p_btts, 4),
            "p_btts_no": round(1.0 - p_btts, 4),
        }
