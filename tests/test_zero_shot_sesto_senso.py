import unittest
from services.ml.zero_shot_sesto_senso import ZeroShotSestoSenso


class TestZeroShotSestoSenso(unittest.TestCase):
    def setUp(self):
        self.classifier = ZeroShotSestoSenso()

    def test_classify_injury(self):
        snippet = "Alcaraz avverte un forte risentimento muscolare alla coscia destra in rifinitura, forfait probabile."
        res = self.classifier.classify_snippet(snippet)
        self.assertEqual(res["top_category"], "INJURY_OR_ABSENCE")
        self.assertTrue(res["is_risk"])
        self.assertLess(res["impact_factor"], 0.0)

    def test_classify_turnover(self):
        snippet = "Il mister annuncia ampio turnover in vista della sfida decisiva di Champions League: riposo per i titolari."
        res = self.classifier.classify_snippet(snippet)
        self.assertEqual(res["top_category"], "ROTATION_OR_TURNOVER")
        self.assertTrue(res["is_risk"])

    def test_classify_positive(self):
        snippet = "Rientro fondamentale tra i titolari del capitano, squadra carica e reduce da tre vittorie consecutive."
        res = self.classifier.classify_snippet(snippet)
        self.assertEqual(res["top_category"], "POSITIVE_MOMENTUM")
        self.assertFalse(res["is_risk"])
        self.assertGreater(res["impact_factor"], 0.0)

    def test_audit_news(self):
        snippets = [
            "Terreno di gioco pesante e fango a causa del forte maltempo delle ultime ore.",
            "Liti nello spogliatoio e stipendi non pagati negli ultimi tre mesi."
        ]
        results = self.classifier.audit_news(snippets)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["top_category"], "TACTICAL_OR_SURFACE")
        self.assertEqual(results[1]["top_category"], "LOCKER_ROOM_OR_DISCIPLINE")


if __name__ == "__main__":
    unittest.main()
