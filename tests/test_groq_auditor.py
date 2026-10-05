from unittest.mock import MagicMock, patch
from services.debate.groq_auditor import GroqAuditor, resolve_audit_verdict


def test_groq_auditor_not_configured():
    auditor = GroqAuditor(api_key="")
    res = auditor.audit_ticket("Test Ticket", [])
    assert res["success"] is False
    assert "GROQ_API_KEY non configurata" in res["error"]


def test_groq_auditor_mock_audit():
    auditor = GroqAuditor(api_key="gsk_dummy_test_key")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Analisi: EV positivo. Verdetto: APPROVATA. Stake consigliata 3%."
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_response):
        res = auditor.audit_ticket(
            title="Ticket Mock",
            legs=[
                {
                    "match_name": "Squadra A vs Squadra B",
                    "market": "1X",
                    "book_odd": 1.40,
                    "fair_odd": 1.25,
                    "probability": 0.80,
                    "edge": 0.12,
                }
            ]
        )

    assert res["success"] is True
    assert res["approved"] is True
    assert "APPROVATA" in res["critique"]


def test_negative_ev_is_warning_not_a_block():
    approved, warning = resolve_audit_verdict(
        "EV complessivo -17%. Verdetto: BOCCIATA. Stake 0%."
    )
    assert approved is True
    assert warning is not None


def test_structural_risk_still_blocks():
    approved, warning = resolve_audit_verdict(
        "Under 2.5 sulla corazzata. RISCHIO_STRUTTURALE. Verdetto: BOCCIATA."
    )
    assert approved is False
    assert warning is None
