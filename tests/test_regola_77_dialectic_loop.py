"""
tests/test_regola_77_dialectic_loop.py — Verifica Regola #77: Ciclo Dialettico Obbligatorio Pre-Costruzione.
"""

from unittest.mock import MagicMock
import pytest
from services.debate.groq_auditor import GroqAuditor


def test_regola_77_immediate_approval():
    auditor = GroqAuditor(api_key="gsk_dummy_test_key")
    # Simula risposta immediata positiva di Groq al Turno 1
    auditor.audit_ticket = MagicMock(return_value={
        "success": True,
        "approved": True,
        "critique": "Verdetto Finale: APPROVATA con +30% EV.",
        "total_odd": 2.50,
    })

    legs = [{"match_name": "Team A vs Team B", "market": "1X", "book_odd": 1.30}]
    res = auditor.dialectic_debate_loop("Test Ticket", legs)

    assert res["consensus_reached"] is True
    assert res["final_status"] == "APPROVATA"
    assert res["turns_needed"] == 1
    assert len(res["debate_history"]) == 1


def test_regola_77_rectification_convergence():
    auditor = GroqAuditor(api_key="gsk_dummy_test_key")

    # Turno 1: Bocciata per rischio Under secco
    # Turno 2: Approvata dopo rettifica con MultiGol 1° Tempo
    auditor.audit_ticket = MagicMock(side_effect=[
        {
            "success": True,
            "approved": False,
            "critique": "Verdetto Finale: BOCCIATA. L'Under 2.5 è troppo esposto a espulsioni.",
            "total_odd": 1.95,
        },
        {
            "success": True,
            "approved": True,
            "critique": "Verdetto Finale: APPROVATA. MultiGol 0-1 1° Tempo neutralizza il rischio ripresa.",
            "total_odd": 1.86,
        },
    ])

    def mock_rectify(audit_res, current_legs):
        # Il modellista quantitativo accoglie la critica e sostituisce l'Under con MultiGol 1°T
        return [{
            "match_name": "Defensa vs San Lorenzo",
            "market": "MultiGol 0-1 1° Tempo",
            "book_odd": 1.38,
        }]

    initial_legs = [{
        "match_name": "Defensa vs San Lorenzo",
        "market": "Under 2.5",
        "book_odd": 1.43,
    }]

    res = auditor.dialectic_debate_loop("Catenaccio Argentina", initial_legs, rectification_callback=mock_rectify)

    assert res["consensus_reached"] is True
    assert res["final_status"] == "APPROVATA"
    assert res["turns_needed"] == 2
    assert res["final_legs"][0]["market"] == "MultiGol 0-1 1° Tempo"
    assert len(res["debate_history"]) == 2


def test_regola_77_blocks_unresolved_ticket():
    auditor = GroqAuditor(api_key="gsk_dummy_test_key")
    # Rifiuta ripetutamente senza convergenza
    auditor.audit_ticket = MagicMock(return_value={
        "success": True,
        "approved": False,
        "critique": "Verdetto Finale: BOCCIATA. Quota compressa non negoziabile.",
        "total_odd": 1.40,
    })

    initial_legs = [{"match_name": "Derby Trap", "market": "1X", "book_odd": 1.20}]
    res = auditor.dialectic_debate_loop("Trap Derby", initial_legs, max_turns=2)

    assert res["consensus_reached"] is False
    assert res["final_status"] == "BOCCIATA_SENZA_CONSENSO"
    assert res["turns_needed"] == 2
