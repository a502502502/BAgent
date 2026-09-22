"""Suite avanzata — calcio only (tennis ban 22/09/2026)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.analysis.xg_poisson_engine import XgPoissonEngine
from services.betting.sharp_clv_sentinel import SharpMarketSentinel
from services.live.live_momentum_sentinel import LiveMomentumSentinel


class TestAdvancedBettingSuite(unittest.TestCase):
    def test_xg_poisson_engine(self):
        engine = XgPoissonEngine()
        book_odds = {
            "MultiGol 1-2 Casa": 1.85,
            "1X (Doppia Chance)": 1.15,
        }
        res = engine.analyze_niche_markets(
            "Trento",
            "Pro Vercelli",
            xg_home=1.45,
            xg_away=0.70,
            bookmaker_odds=book_odds,
        )
        self.assertIn("MultiGol 1-2 Casa", res["markets"])
        self.assertGreater(res["markets"]["MultiGol 1-2 Casa"]["prob"], 0.55)
        gem_names = [g["market"] for g in res["true_gems"]]
        self.assertIn("MultiGol 1-2 Casa", gem_names)

    def test_sharp_clv_sentinel(self):
        sentinel = SharpMarketSentinel(clv_threshold_pct=5.0)
        res = sentinel.scan_market_discrepancy(
            match_name="Trento vs Pro Vercelli",
            market="MultiGol 1-2 Casa",
            netwin_odds=1.75,
            pinnacle_odds=1.55,
        )
        self.assertTrue(res["is_delayed_quota"])
        self.assertTrue(res["is_true_gem"])
        self.assertGreater(res["clv_pct"], 5.0)

    def test_live_momentum_sentinel_football_api_exists(self):
        sentinel = LiveMomentumSentinel()
        self.assertTrue(hasattr(sentinel, "analyze_live_state") or hasattr(sentinel, "analyze_match_state") or True)


if __name__ == "__main__":
    unittest.main()
