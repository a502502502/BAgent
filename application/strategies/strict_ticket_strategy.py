"""Strategy che tiene solo i candidati certificati da StrictTicketPipeline."""

from domain.interfaces.strategy import Strategy
from services.betting.strict_ticket_pipeline import StrictTicketPipeline


class StrictTicketStrategy(Strategy):

    def __init__(self, pipeline=None):
        self.pipeline = pipeline or StrictTicketPipeline()

    def select(self, predictions):
        kept = []
        for candidate in predictions:
            report = self.pipeline.validate_candidate(candidate)
            if report.passed:
                kept.append(candidate)
        return kept
