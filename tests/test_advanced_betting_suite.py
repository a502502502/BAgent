import unittest
import sys
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
sys.path.insert(0, str(root))

from services.tennis.surface_elo_engine import SurfaceEloEngine
from services.analysis.xg_poisson_engine import XgPoissonEngine
from services.betting.sharp_clv_sentinel import SharpMarketSentinel
from services.live.live_momentum_sentinel import LiveMomentumSentinel

class TestAdvancedBettingSuite(unittest.TestCase):

    def test_surface_elo_tennis(self):
        engine = SurfaceEloEngine()
        # Test Shinikova on hard
        res = engine.calculate_match_odds("Isabella Shinikova", "Aysegul Mert", surface="hard")
        self.assertGreater(res["p1_prob"], 0.65)
        self.assertIn("Isabella Shinikova Handicap -2.5 Game", [r["market"] for r in res["recommendations"]])

        # Test Arantxa Rus fatigue risk
        rus_res = engine.calculate_match_odds("Arantxa Rus", "Mia Ristic", surface="clay")
        self.assertTrue(rus_res["fatigue_risk"]["Arantxa Rus"])

    def test_xg_poisson_engine(self):
        engine = XgPoissonEngine()
        # Test Trento vs Pro Vercelli (xG ~ 1.45 vs 0.70)
        book_odds = {
            "MultiGol 1-2 Casa": 1.85,
            "1X (Doppia Chance)": 1.15
        }
        res = engine.analyze_niche_markets("Trento", "Pro Vercelli", xg_home=1.45, xg_away=0.70, bookmaker_odds=book_odds)
        self.assertIn("MultiGol 1-2 Casa", res["markets"])
        self.assertGreater(res["markets"]["MultiGol 1-2 Casa"]["prob"], 0.55)
        # Should identify MultiGol 1-2 Casa as true gem
        gem_names = [g["market"] for g in res["true_gems"]]
        self.assertIn("MultiGol 1-2 Casa", gem_names)

    def test_sharp_clv_sentinel(self):
        sentinel = SharpMarketSentinel(clv_threshold_pct=5.0)
        # Scenario: Pinnacle odds is 1.55 (fair 1.58), but Netwin still pays 1.75
        res = sentinel.scan_market_discrepancy(
            match_name="Trento vs Pro Vercelli",
            market="MultiGol 1-2 Casa",
            netwin_odds=1.75,
            pinnacle_odds=1.55
        )
        self.assertTrue(res["is_delayed_quota"])
        self.assertTrue(res["is_true_gem"])
        self.assertGreater(res["clv_pct"], 5.0)

    def test_live_momentum_sentinel(self):
        sentinel = LiveMomentumSentinel()
        # Test Bagel detection on Rus
        t_res = sentinel.analyze_tennis_live_state(
            player1="Mia Ristic",
            player2="Arantxa Rus",
            sets_score="1-1",
            games_score="4-6 6-0 1-0",
            active_bet="2 (Arantxa Rus)"
        )
        self.assertTrue(t_res["has_bagel"])
        self.assertEqual(t_res["status_verdict"], "HIGH_VOLATILITY")

        # Test Over 18.5 lock on Hercog
        h_res = sentinel.analyze_tennis_live_state(
            player1="Polona Hercog",
            player2="Leyre Romero Gormaz",
            sets_score="1-0",
            games_score="7-6 0-0",
            active_bet="Over 18.5 Game Totali"
        )
        self.assertTrue(h_res["over_locked"])

if __name__ == "__main__":
    unittest.main()
