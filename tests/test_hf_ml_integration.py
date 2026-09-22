"""
tests/test_hf_ml_integration.py — Test di validazione per i nuovi moduli Hugging Face:
1. ChronosOddsForecaster (Time-series odds forecasting & steam moves)
2. HFSportsIntelligence (Multilingual ES/PT/IT/EN news intelligence & zero-shot)
"""

import unittest
from services.ml.chronos_odds_forecaster import ChronosOddsForecaster
from services.ml.hf_sports_intelligence import HFSportsIntelligence


class TestChronosOddsForecaster(unittest.TestCase):
    def setUp(self):
        self.forecaster = ChronosOddsForecaster(use_hf_chronos=False)

    def test_strong_steam_drop(self):
        # Quota che crolla repentinamente: da 2.20 a 1.88
        odds_series = [2.20, 2.12, 2.02, 1.95, 1.88]
        res = self.forecaster.forecast_odds_movement(odds_series, prediction_horizon=3, market_name="1X2 Casa")
        
        self.assertIn(res["signal"], ["STRONG_STEAM_DROP", "MODERATE_STEAM_DROP"])
        self.assertGreater(res["metrics"]["steam_probability"], 0.50)
        self.assertLess(res["predicted_closing_odds"], 1.95)
        self.assertGreater(res["clv_advantage"], 0.0)

    def test_drifting_up(self):
        # Quota che sale (mercato la sta scaricando): da 1.50 a 1.72
        odds_series = [1.50, 1.55, 1.62, 1.68, 1.72]
        res = self.forecaster.forecast_odds_movement(odds_series, prediction_horizon=3, market_name="Over 2.5")
        
        self.assertEqual(res["signal"], "DRIFTING_UP")
        self.assertGreater(res["metrics"]["pct_change"], 4.0)

    def test_stable_odds(self):
        # Quota con oscillazioni minime nel range di rumore
        odds_series = [1.90, 1.91, 1.89, 1.90, 1.90]
        res = self.forecaster.forecast_odds_movement(odds_series, prediction_horizon=2, market_name="Under 3.5")
        
        self.assertEqual(res["signal"], "STABLE")


class TestHFSportsIntelligence(unittest.TestCase):
    def setUp(self):
        self.intel = HFSportsIntelligence(use_hf_pipeline=False)

    def test_spanish_argentina_injury(self):
        # Notizia argentina con infortunio in lingua spagnola
        news = ["Lanzini terminó con molestia muscular tras el clásico y no viajó a Córdoba"]
        report = self.intel.analyze_football_team_news("River Plate", news)
        
        self.assertLess(report["xg_att_multiplier"], 1.0)
        self.assertLess(report["morale_score"], 0.0)
        self.assertTrue(any("molestia" in s or "no viajó" in s for s in report["detected_signals"]["injuries"]))

    def test_portuguese_brazil_turnover(self):
        # Notizia brasiliana con turnover e titolari a riposo in lingua portoghese
        news = ["Palmeiras vai poupar titulares no clássico; Abel escala time reserva pensando na copa"]
        report = self.intel.analyze_football_team_news("Palmeiras", news)
        
        self.assertLess(report["xg_att_multiplier"], 1.0)
        self.assertGreater(report["xg_def_multiplier"], 1.0)
        self.assertTrue(any("vai poupar" in s or "time reserva" in s for s in report["detected_signals"]["turnover"]))

    def test_match_xg_adjustment(self):
        # Simula partita River vs Talleres con River con infortunio e Talleres al completo
        home_news = ["Baja confirmada del goleador titular por desgarro"]
        away_news = ["Plantel completo, racha positiva y ánimo por las nubes"]
        
        adj_h, adj_a, audit = self.intel.adjust_match_xg(
            xg_home_pre=1.60,
            xg_away_pre=0.90,
            home_news=home_news,
            away_news=away_news,
            home_team="River Plate",
            away_team="Talleres"
        )
        
        self.assertLess(adj_h, 1.60) # River penalizzato per il desgarro
        self.assertGreater(adj_a, 0.90) # Talleres avvantaggiato per la racha positiva

    def test_tennis_fully_abolished(self):
        # Verifica che nessun attributo o metodo sul tennis sia presente nella classe
        self.assertFalse(hasattr(self.intel, "analyze_tennis_player_news"))
        self.assertFalse(hasattr(self.intel, "adjust_tennis_elo"))
        self.assertFalse(hasattr(self.intel, "TENNIS_PHYSICAL_KEYWORDS"))


if __name__ == "__main__":
    unittest.main()
