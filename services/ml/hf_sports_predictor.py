"""
HFSportsPredictor — Integrazione modelli predittivi calibrati da Hugging Face.
Repository sorgente: ruslanmv/sports-trends-models

Fornisce il modello calcio CalibratedClassifierCV (HistGradientBoosting)
addestrato su match di campionato: probabilità 1X2, quota equa ed edge.
"""

import os
import urllib.request
import logging
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

HF_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "hf_cache")
FOOTBALL_URL = "https://huggingface.co/ruslanmv/sports-trends-models/resolve/main/football/latest/model.pkl"


class HFSportsPredictor:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or HF_MODELS_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.fb_model = None
        self._load_models()

    def _ensure_file(self, filename: str, url: str) -> str:
        filepath = os.path.join(self.cache_dir, filename)
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            logger.info(f"Scaricamento modello da {url} in {filepath}...")
            urllib.request.urlretrieve(url, filepath)
            logger.info(f"Modello salvato con successo: {filepath}")
        return filepath

    def _load_models(self):
        try:
            fb_path = self._ensure_file("football_model.pkl", FOOTBALL_URL)
            self.fb_model = joblib.load(fb_path)
        except Exception as e:
            logger.error(f"Impossibile caricare il modello Football HF: {e}")

    def predict_football(
        self,
        home_team: str,
        away_team: str,
        home_elo: float = 1500.0,
        away_elo: float = 1500.0,
        home_form_5: float = 7.0,  # punti su 15 (W=3, D=1, L=0)
        away_form_5: float = 7.0,
        home_form_10: float = 14.0,
        away_form_10: float = 14.0,
        home_gf_5: float = 7.0,
        away_gf_5: float = 6.0,
        home_ga_5: float = 6.0,
        away_ga_5: float = 7.0,
        home_rest_days: float = 6.0,
        away_rest_days: float = 6.0,
        h2h_home_wins: int = 1,
        h2h_draws: int = 1,
        h2h_away_wins: int = 1,
        league_importance: float = 1.0,
        market_odds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Predizione calibrata per match di Calcio (Home vs Away).
        Utilizza HistGradientBoosting calibrato con CalibratedClassifierCV.
        Classi [0, 2]: 0 = X2 (Away/Pareggio), 2 = 1 (Vittoria Casa).
        """
        if self.fb_model is None:
            raise RuntimeError("Modello Football HF non inizializzato.")

        elo_diff = home_elo - away_elo
        cols = list(self.fb_model.feature_names_in_)
        row = {c: 0.0 for c in cols}
        row["home_elo"] = home_elo
        row["away_elo"] = away_elo
        row["elo_diff"] = elo_diff
        row["home_form_last_5"] = home_form_5
        row["away_form_last_5"] = away_form_5
        row["home_form_last_10"] = home_form_10
        row["away_form_last_10"] = away_form_10
        row["home_goals_for_last_5"] = home_gf_5
        row["away_goals_for_last_5"] = away_gf_5
        row["home_goals_against_last_5"] = home_ga_5
        row["away_goals_against_last_5"] = away_ga_5
        row["home_rest_days"] = home_rest_days
        row["away_rest_days"] = away_rest_days
        row["home_advantage"] = 1.0
        row["h2h_home_wins"] = float(h2h_home_wins)
        row["h2h_draws"] = float(h2h_draws)
        row["h2h_away_wins"] = float(h2h_away_wins)
        row["league_importance_score"] = league_importance
        row["social_interest_score"] = 1.0

        df = pd.DataFrame([row])
        probs = self.fb_model.predict_proba(df)[0]
        # Classi [0, 2]: 0 = Away/Draw (X2), 2 = Home Win (1)
        prob_x2 = float(probs[0])
        prob_home = float(probs[1])

        # Derivazione stima 1X2 completa:
        # La frazione di prob_x2 divisa tra Draw e Away tipicamente segue il rapporto base 45% D / 55% A
        # quando le squadre sono equilibrate, o modulata dalla differenza ELO.
        draw_ratio = 0.44 - 0.0001 * elo_diff
        draw_ratio = max(0.25, min(0.55, draw_ratio))
        prob_draw = round(prob_x2 * draw_ratio, 4)
        prob_away = round(prob_x2 * (1.0 - draw_ratio), 4)

        fair_odds_1 = round(1.0 / prob_home, 2) if prob_home > 0 else 99.0
        fair_odds_x = round(1.0 / prob_draw, 2) if prob_draw > 0 else 99.0
        fair_odds_2 = round(1.0 / prob_away, 2) if prob_away > 0 else 99.0
        fair_odds_1x = round(1.0 / (prob_home + prob_draw), 2) if (prob_home + prob_draw) > 0 else 99.0
        fair_odds_x2 = round(1.0 / prob_x2, 2) if prob_x2 > 0 else 99.0

        result = {
            "home_team": home_team,
            "away_team": away_team,
            "prob_1": round(prob_home, 4),
            "prob_x": prob_draw,
            "prob_2": prob_away,
            "prob_1x": round(prob_home + prob_draw, 4),
            "prob_x2": round(prob_x2, 4),
            "fair_odds": {
                "1": fair_odds_1,
                "X": fair_odds_x,
                "2": fair_odds_2,
                "1X": fair_odds_1x,
                "X2": fair_odds_x2,
            },
            "value_bets": []
        }

        if market_odds:
            for market_key, fair_val in result["fair_odds"].items():
                if market_key in market_odds:
                    mkt_odd = market_odds[market_key]
                    prob = 1.0 / fair_val
                    edge = round((prob * mkt_odd - 1.0) * 100, 2)
                    if edge > 3.0:
                        result["value_bets"].append({
                            "selection": market_key,
                            "odds": mkt_odd,
                            "fair_odds": fair_val,
                            "edge_pct": edge
                        })

        return result
