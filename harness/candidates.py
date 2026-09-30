"""Selezioni di partenza per contratti e slate. Lo storico di stagione è spento."""

from __future__ import annotations

from dataclasses import fields

from services.betting.strict_ticket_pipeline import MarketCandidate, StrictTicketPipeline

SENSE = "Volume offensivo reale della stagione in corso, ritmo aperto su entrambi i fronti."

_FIELDS = {item.name for item in fields(MarketCandidate)}


def selection(**overrides) -> MarketCandidate:
    """Over 1.5 in Serie A che supera il funnel, salvo gli override del contratto."""
    unknown = set(overrides) - _FIELDS
    if unknown:
        raise TypeError(f"Campi sconosciuti per MarketCandidate: {sorted(unknown)}")
    data = dict(
        match_name="Home FC vs Away FC",
        tournament="Serie A",
        market_name="Over 1.5",
        bookmaker_odd=1.40,
        xg_home=1.7,
        xg_away=1.2,
        sixth_sense_analysis=SENSE,
        kickoff_time="2026-09-24 20:45 CEST",
        home_matches_played=10,
        away_matches_played=10,
        verified_sources_checked=True,
    )
    data.update(overrides)
    return MarketCandidate(**data)


def pipeline() -> StrictTicketPipeline:
    """Pipeline senza lettura dello storico in bagent.db."""
    return StrictTicketPipeline(season_matches=[])
