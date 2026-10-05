import pytest
import numpy as np
from services.analysis.ml_features_engine import MLFeaturesEngine

def test_ml_features_engine_feature_extraction():
    engine = MLFeaturesEngine()
    h2h = {
        "games_played": 6,
        "team1_wins": 3,
        "team2_wins": 1,
        "draws": 2,
        "team1_goals": 8,
        "team2_goals": 4
    }
    form_t1 = {"points_avg": 2.0, "goals_avg": 1.6}
    form_t2 = {"points_avg": 0.8, "goals_avg": 0.6}
    odds = {"home_win": 1.70, "draw": 3.40, "away_win": 5.00}

    features = engine.extract_match_features(
        team1_rank=3,
        team2_rank=14,
        h2h_history=h2h,
        recent_form_t1=form_t1,
        recent_form_t2=form_t2,
        odds=odds
    )

    assert features["rank_diff"] == 11.0 # 14 - 3
    assert round(features["h2h_team1_win_rate"], 2) == 0.50
    assert features["team1_form_points"] == 2.0
    assert features["odds_ratio_home_away"] == 1.70 / 5.00
    assert features["implied_prob_home"] > features["implied_prob_away"]

def test_ml_features_engine_predictions():
    engine = MLFeaturesEngine()
    features = {
        "rank_diff": 8.0,
        "h2h_team1_win_rate": 0.60,
        "h2h_team2_win_rate": 0.20,
        "h2h_draw_rate": 0.20,
        "h2h_goals_per_game": 2.1,
        "team1_form_points": 1.8,
        "team2_form_points": 1.0,
        "team1_form_goals": 1.5,
        "team2_form_goals": 0.9,
        "odds_ratio_home_away": 0.45,
        "odds_min": 1.60,
        "implied_prob_home": 0.55,
        "implied_prob_away": 0.20
    }

    preds = engine.predict_match_probabilities(features)
    assert 0.0 <= preds["p_home"] <= 1.0
    assert 0.0 <= preds["p_draw"] <= 1.0
    assert 0.0 <= preds["p_away"] <= 1.0
    assert round(preds["p_home"] + preds["p_draw"] + preds["p_away"], 2) == 1.00
    assert preds["p_1X"] >= preds["p_home"]
    assert 0.0 <= preds["p_over_25"] <= 1.0
    assert 0.0 <= preds["p_under_25"] <= 1.0
    assert round(preds["p_over_25"] + preds["p_under_25"], 2) == 1.00

def test_ml_features_engine_training():
    engine = MLFeaturesEngine()
    # Mock dataset
    X = np.random.randn(50, len(engine.feature_columns))
    y_winner = np.random.choice([0, 1, 2], size=50)
    y_over25 = np.random.choice([0, 1], size=50)
    y_dict = {"winner": y_winner, "over25": y_over25}

    engine.train_baseline_models(X, y_dict)
    assert "winner" in engine.models
    assert "over25" in engine.models

    dummy_feats = {col: 0.5 for col in engine.feature_columns}
    preds = engine.predict_match_probabilities(dummy_feats)
    assert "p_home" in preds
    assert "p_over_25" in preds
