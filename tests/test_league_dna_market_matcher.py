#!/usr/bin/env python3
"""
tests/test_league_dna_market_matcher.py
Unit tests for League & Team Tactical DNA Matching (Regola #71).
"""

import unittest
from services.analysis.league_dna_market_matcher import LeagueDNAMarketMatcher
from services.betting.strict_ticket_pipeline import StrictTicketPipeline, MarketCandidate


class TestLeagueDNAMarketMatcher(unittest.TestCase):

    def setUp(self):
        self.matcher = LeagueDNAMarketMatcher()
        self.pipeline = StrictTicketPipeline()

    def test_mls_corners_approved(self):
        """MLS: Over 6.5 Corner Totali deve essere APPROVATO con score massimo."""
        res = self.matcher.check_market_suitability(
            league="MLS Stati Uniti",
            home_team="San Jose Earthquakes",
            away_team="LAFC",
            market_name="Over 6.5 Corner Totali Incontro",
            bookmaker_odd=1.16
        )
        self.assertTrue(res.is_recommended)
        self.assertFalse(res.is_prohibited)
        self.assertEqual(res.status, "GREEN")
        self.assertGreaterEqual(res.suitability_score, 90.0)

    def test_mls_under_rejected(self):
        """MLS: Under 2.5 Gol deve essere VIETATO (Semaforo Rosso)."""
        res = self.matcher.check_market_suitability(
            league="MLS Stati Uniti",
            home_team="San Jose Earthquakes",
            away_team="LAFC",
            market_name="Under 2.5 Gol",
            bookmaker_odd=2.30
        )
        self.assertFalse(res.is_recommended)
        self.assertTrue(res.is_prohibited)
        self.assertEqual(res.status, "RED")
        self.assertIn("Under stretto incompatibile", res.rejection_reason)

    def test_argentina_over05_rejected(self):
        """Argentina: Over 0.5 Gol deve essere BLOCCATO (trappola dello 0-0)."""
        res = self.matcher.check_market_suitability(
            league="Argentina Liga Profesional",
            home_team="River Plate",
            away_team="Huracan",
            market_name="Over 0.5 Gol",
            bookmaker_odd=1.08
        )
        self.assertFalse(res.is_recommended)
        self.assertTrue(res.is_prohibited)
        self.assertEqual(res.status, "RED")
        self.assertIn("Trappola mortale dello 0-0", res.rejection_reason)

    def test_argentina_asian_under_approved(self):
        """Argentina: Under 3.0 Asiatico deve essere APPROVATO (Semaforo Verde)."""
        res = self.matcher.check_market_suitability(
            league="Argentina Liga Profesional",
            home_team="River Plate",
            away_team="Huracan",
            market_name="Under 3.0 Asiatico",
            bookmaker_odd=1.28
        )
        self.assertTrue(res.is_recommended)
        self.assertFalse(res.is_prohibited)
        self.assertEqual(res.status, "GREEN")

    def test_pipeline_gate_09_blocks_dna_incompatibility(self):
        """Verifica che Gate 0.90 in StrictTicketPipeline blocchi le giocate non idonee."""
        c = MarketCandidate(
            match_name="River Plate vs Huracan",
            tournament="Argentina Liga Profesional",
            market_name="Over 0.5 Gol",
            bookmaker_odd=1.08,
            estimated_p_90=0.88,
            sixth_sense_analysis="River cerca la vittoria",
            home_matches_played=3,
            away_matches_played=3,
        )
        report = self.pipeline.validate_candidate(c)
        self.assertFalse(report.passed)
        self.assertIn("REGOLA #71", report.rejection_reason)


if __name__ == "__main__":
    unittest.main()
