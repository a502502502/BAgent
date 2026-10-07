"""
tests/test_dual_portfolio_orchestrator.py — Test per l'orchestratore a doppio binario (Core-Satellite).
"""

import json
from pathlib import Path

from services.analysis.dual_portfolio_orchestrator import (
    DualPortfolioOrchestrator,
    TicketLeg,
)


def test_dual_portfolio_assembly_and_budget_split():
    orchestrator = DualPortfolioOrchestrator(total_budget_eur=10.0, core_ratio=0.70)

    core_legs = [
        TicketLeg(
            match="Catolica - LDU Quito",
            competition="ECU Coppa",
            kickoff_time="2026-10-07 17:00 CEST",
            market="Under/Over",
            selection="UNDER 3.5",
            odds=1.15,
            bookmaker="SNAI",
            rationale="Protezione linea 3.5",
        ),
        TicketLeg(
            match="Gnistan - Inter Turku",
            competition="FIN Veikkausliiga",
            kickoff_time="2026-10-07 18:00 CEST",
            market="COMBO: DC + U/O 1.5",
            selection="X2 + OVER 1.5",
            odds=1.48,
            bookmaker="SNAI",
            rationale="Inter Turku superiore e difese aperte",
        ),
        TicketLeg(
            match="CS Cerrito - Wanderers",
            competition="URU Coppa Auf",
            kickoff_time="2026-10-07 20:30 CEST",
            market="Doppia Chance",
            selection="1X",
            odds=1.25,
            bookmaker="SNAI",
            rationale="Fattore campo coppa",
        ),
    ]

    gem_legs = [
        TicketLeg(
            match="Jedinstvo U19 - Stella Rossa U19",
            competition="SER U19",
            kickoff_time="2026-10-07 18:00 CEST",
            market="Entrambe Segnano",
            selection="SI (GG)",
            odds=1.44,
            bookmaker="SNAI/Oddspedia",
            rationale="Hot Bet: 7 su 7 partite con esito GG (100% win rate)",
        ),
        TicketLeg(
            match="Gnistan - Inter Turku",
            competition="FIN Veikkausliiga",
            kickoff_time="2026-10-07 18:00 CEST",
            market="COMBO: DC + GOAL",
            selection="X2 + GOAL",
            odds=1.95,
            bookmaker="SNAI",
            rationale="Asimmetria: entrambe segnano da 6+ gare e Turku non perde",
        ),
    ]

    session = orchestrator.assemble_session(
        core_legs=core_legs, gem_legs=gem_legs, session_name="Sessione 07 Ottobre"
    )

    # Verifica split budget 70% Core / 30% Gemme
    assert session.total_budget_eur == 10.0
    assert session.core_ticket.stake_eur == 7.00
    assert session.gem_ticket.stake_eur == 3.00

    # Verifica moltiplicatori
    # Core: 1.15 * 1.48 * 1.25 = 2.13
    assert session.core_ticket.total_odds == 2.13
    assert session.core_ticket.potential_payout_eur == round(7.00 * 2.13, 2)

    # Gem: 1.44 * 1.95 = 2.81
    assert session.gem_ticket.total_odds == 2.81
    assert session.gem_ticket.potential_payout_eur == round(3.00 * 2.81, 2)


def test_save_dual_portfolio_session(tmp_path):
    orchestrator = DualPortfolioOrchestrator(total_budget_eur=10.0)
    leg = TicketLeg(
        match="Test Match",
        competition="Test",
        kickoff_time="2026-10-07 18:00",
        market="1X",
        selection="1X",
        odds=1.30,
        bookmaker="SNAI",
        rationale="Test",
    )
    session = orchestrator.assemble_session([leg], [leg])
    out_file = tmp_path / "test_dual_session.json"
    result = orchestrator.save_session_to_json(session, output_path=out_file)

    assert result.exists()
    data = json.loads(result.read_text(encoding="utf-8"))
    assert "core_ticket" in data
    assert "gem_ticket" in data
    assert data["total_budget_eur"] == 10.0
