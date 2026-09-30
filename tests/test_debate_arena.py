"""Test per la Ticket Debate Arena (services/debate/ticket_debate_arena.py)."""

from services.betting.netwin_cache_reader import NetwinGem
from services.betting.strict_ticket_pipeline import MarketCandidate, ValidationReport
from services.debate.ticket_debate_arena import TicketDebateArena, DebateLeg
from services.mcp.agent_bus_store import AgentBusStore


def _sample_ticket():
    gem1 = NetwinGem(
        match_name="Clube Do Remo vs Gremio",
        tournament="Brasile",
        market="MultiGol 0-1 1° Tempo",
        book_odd=1.66,
        fair_odd=1.27,
        probability=0.785,
        edge=0.303,
        notes="Sesto Senso: avvio diesel difensivo",
    )
    cand1 = MarketCandidate(
        match_name="Clube Do Remo vs Gremio",
        tournament="Brasile",
        market_name="MultiGol 0-1 1° Tempo",
        bookmaker_odd=1.66,
        sixth_sense_analysis="Sesto Senso: avvio diesel difensivo",
    )
    rep1 = ValidationReport(
        passed=True,
        candidate=cand1,
        real_probability=0.785,
        fair_odds=1.27,
        mathematical_edge=0.303,
    )

    gem2 = NetwinGem(
        match_name="Palmeiras vs Bahia Ba",
        tournament="Brasile",
        market="MultiGol 0-2 Casa",
        book_odd=1.38,
        fair_odd=1.09,
        probability=0.92,
        edge=0.269,
        notes="Sesto Senso: corto muso Palmeiras",
    )
    cand2 = MarketCandidate(
        match_name="Palmeiras vs Bahia Ba",
        tournament="Brasile",
        market_name="MultiGol 0-2 Casa",
        bookmaker_odd=1.38,
        sixth_sense_analysis="Sesto Senso: corto muso Palmeiras",
    )
    rep2 = ValidationReport(
        passed=True,
        candidate=cand2,
        real_probability=0.92,
        fair_odds=1.09,
        mathematical_edge=0.269,
    )

    return {
        "name": "Test Double Sudamerica",
        "total_odds": 2.29,
        "joint_probability": 0.722,
        "edge": 0.655,
        "stake": 2.0,
        "legs": [
            {"gem": gem1, "candidate": cand1, "report": rep1, "dna_status": "YELLOW"},
            {"gem": gem2, "candidate": cand2, "report": rep2, "dna_status": "GREEN"},
        ],
    }


def test_arena_runs_full_5_phases():
    arena = TicketDebateArena()
    ticket = _sample_ticket()
    report = arena.run_debate(ticket)

    assert len(report.legs) == 2
    assert len(report.critiques) == 2
    assert len(report.rebuttals) == 2
    assert len(report.votes) == 2

    # Verifica fase 1 (Proposals)
    assert report.legs[0].market == "MultiGol 0-1 1° Tempo"
    assert report.legs[1].market == "MultiGol 0-2 Casa"

    # Verifica fase 2 (Critiques)
    assert report.critiques[0].risk_level in ["LOW", "MEDIUM", "HIGH"]
    assert len(report.critiques[0].critique_text) > 20

    # Verifica fase 3 (Rebuttals)
    assert "Poisson" in report.rebuttals[0].defense_text or "0.45" in report.rebuttals[0].defense_text
    assert len(report.rebuttals[0].statistical_cushion) > 0

    # Verifica fase 4 (Votes)
    assert 50 <= report.votes[0].consensus_score <= 100
    assert report.votes[0].approved is True

    # Verifica fase 5 (Synthesis)
    assert report.overall_approved is True
    assert "ARENA DIALETTICA AGENTI" in report.transcript_markdown
    assert "FASE 1: PROPOSTE QUANTITATIVE" in report.transcript_markdown
    assert "FASE 2: ATTACCO CRITICO" in report.transcript_markdown
    assert "FASE 3: REPLICHE E DIFESA" in report.transcript_markdown
    assert "FASE 4: VOTAZIONE" in report.transcript_markdown
    assert "FASE 5: SINTESI ESECUTIVA" in report.transcript_markdown


def test_record_debate_to_bus():
    arena = TicketDebateArena()
    ticket = _sample_ticket()
    report = arena.run_debate(ticket)

    task_id = arena.record_debate_to_bus(report)
    assert task_id.startswith("task_")

    bus = AgentBusStore()
    task = bus.get_task(task_id=task_id)
    assert task is not None
    assert "Debate Arena" in task["title"]
    assert "ARENA DIALETTICA AGENTI" in task["instructions"]
