"""Analyzer che prezza un evento con il motore Dixon-Coles quando ha gli xG."""

from domain.interfaces.analyzer import Analyzer
from services.analysis.xg_poisson_engine import QuantitativeEngine


class PoissonAnalyzer(Analyzer):

    def __init__(self, engine=None):
        self.engine = engine or QuantitativeEngine()

    def analyze(self, event):
        xg_home = getattr(event, "xg_home", None)
        xg_away = getattr(event, "xg_away", None)
        home = event.competitors[0].name
        away = event.competitors[1].name
        if xg_home is None or xg_away is None:
            return {
                "event_id": event.id,
                "priced": False,
                "reason": "xg_home e xg_away sono obbligatori",
            }
        priced = self.engine.analyze_football_markets(home, away, xg_home, xg_away)
        return {
            "event_id": event.id,
            "priced": True,
            "home": home,
            "away": away,
            "markets": priced.get("markets", priced),
        }
