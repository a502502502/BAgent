import unittest
from services.ml.tabpfn_sports_predictor import TabPFNSportsPredictor


class TestTabPFNSportsPredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = TabPFNSportsPredictor()

    def test_predict_football_favorite(self):
        # Match con netta favorita in casa (es. +300 ELO)
        res = self.predictor.predict_football(
            home_team="Pari FC",
            away_team="Underdog United",
            home_elo=1750,
            away_elo=1450,
            home_form_5=12.0,
            away_form_5=4.0,
            market_odds={"1": 1.45, "X": 4.20, "2": 6.50, "1X": 1.12}
        )

        self.assertIn("prob_1", res)
        self.assertIn("prob_x", res)
        self.assertIn("prob_2", res)
        self.assertGreater(res["prob_1"], res["prob_2"])
        self.assertAlmostEqual(res["prob_1"] + res["prob_x"] + res["prob_2"], 1.0, places=2)
        self.assertIn("fair_odds", res)
        self.assertIn("1X", res["fair_odds"])

    def test_predict_football_balanced(self):
        # Match equilibrato (0 diff ELO)
        res = self.predictor.predict_football(
            home_team="Team A",
            away_team="Team B",
            home_elo=1500,
            away_elo=1500,
            home_form_5=7.0,
            away_form_5=7.0,
        )
        self.assertGreater(res["prob_1x"], 0.50)
        self.assertGreater(res["prob_x2"], 0.40)


if __name__ == "__main__":
    unittest.main()
