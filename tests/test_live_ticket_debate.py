"""Il voto live non si muove con la prosa: solo CONCEDE o una rimisurazione."""

from services.debate.live_exchange import (
    LiveTicketDebate,
    apply_rebuttal,
    blocking_objections,
    parse_rebuttal,
)
from services.mcp.agent_bus_store import AgentBusStore


def _blocked_leg(**overrides):
    leg = {
        "index": 1,
        "match_name": "Clube Do Remo vs Gremio",
        "tournament": "Brasile",
        "market": "MultiGol 0-1 1° Tempo",
        "book_odd": 1.66,
        "claimed_probability": 0.785,
        "engine_probability": None,
        "is_period": True,
        "dna_status": "YELLOW",
        "dna_archetype": "PRAGMATIC_MANAGEMENT",
        "dna_prohibited": False,
        "sixth_sense": "Sesto Senso: avvio diesel difensivo",
        "validator_passed": False,
        "validator_reason": "mercato non prezzato",
        "straight_result_odd": None,
    }
    leg.update(overrides)
    leg["objections"] = blocking_objections(leg)
    return leg


def test_period_market_and_drift_stay_blocking():
    first_half = _blocked_leg()
    codes = {item["code"] for item in first_half["objections"]}
    assert "DIES_AT_45" in codes
    assert "ENGINE_UNMAPPED" in codes
    assert "STOCK_SIXTH_SENSE" in codes
    assert "VALIDATOR_BLOCK" in codes

    palmeiras = _blocked_leg(
        index=2,
        match_name="Palmeiras vs Bahia Ba",
        market="MultiGol 0-2 Casa",
        book_odd=1.38,
        claimed_probability=0.92,
        engine_probability=0.764,
        is_period=False,
        dna_archetype="ASYMMETRIC_DOMINANCE",
        sixth_sense="nota di stampa sufficientemente lunga sulla partita",
        validator_passed=True,
        validator_reason="",
    )
    codes = {item["code"] for item in palmeiras["objections"]}
    assert "PROBABILITY_DRIFT" in codes
    assert "CEILING_ON_DOMINANT" in codes
    assert "DIES_AT_45" not in codes


def test_double_chance_next_to_the_straight_price_is_blocked():
    leg = _blocked_leg(
        market="X2",
        book_odd=1.76,
        claimed_probability=0.798,
        engine_probability=0.798,
        is_period=False,
        dna_archetype="ASYMMETRIC_DOMINANCE",
        sixth_sense="nota di stampa sufficientemente lunga sulla partita",
        validator_passed=True,
        validator_reason="",
        straight_result_odd=1.80,
    )
    codes = {item["code"] for item in leg["objections"]}
    assert "INCOHERENT_DOUBLE_CHANCE" in codes


def test_prose_rebuttal_does_not_clear_a_block():
    leg = _blocked_leg()
    actions = parse_rebuttal(
        "La Poisson con xG per 0.45 copre l'81.4% dei primi tempi. Selezione idonea."
    )
    judged = apply_rebuttal([leg], actions, remeasure=lambda proposal: proposal)
    assert actions == {}
    assert judged[0]["status"] == "BLOCKED"
    assert judged[0]["objections"]


def test_concede_withdraws_and_replace_is_remeasured():
    legs = [_blocked_leg(), _blocked_leg(index=2, match_name="Palmeiras vs Bahia Ba")]

    def remeasure(proposal):
        return {
            **proposal,
            "engine_probability": 0.80,
            "is_period": False,
            "dna_archetype": "DEFENSIVE_ATTRITION",
            "dna_prohibited": False,
            "dna_status": "GREEN",
            "sixth_sense": "Rassegna Gazzetta e BBC sulla formazione e sul ritmo della gara.",
            "validator_passed": True,
            "validator_reason": "",
            "claimed_probability": None,
            "straight_result_odd": None,
            "book_odd": proposal.get("book_odd"),
            "market": proposal.get("market"),
        }

    text = '\n'.join([
        "LEG 1: CONCEDE",
        'LEG 2: REPLACE market="1X + Under 3.5" odd=1.83',
    ])
    judged = apply_rebuttal(legs, parse_rebuttal(text), remeasure)
    assert judged[0]["status"] == "WITHDRAWN"
    assert judged[1]["status"] == "PASSED_VALIDATOR"
    assert judged[1]["market"] == "1X + Under 3.5"
    assert judged[1]["objections"] == []


def test_bus_round_trip_waits_for_the_other_side(tmp_path):
    store = AgentBusStore(bus_file=tmp_path / "bus.json")
    debate = LiveTicketDebate(store=store, measurer=lambda proposal: {
        **proposal,
        "engine_probability": None,
        "is_period": True,
        "dna_status": "YELLOW",
        "dna_archetype": "PRAGMATIC_MANAGEMENT",
        "dna_prohibited": False,
        "validator_passed": False,
        "validator_reason": "non prezzato",
        "straight_result_odd": None,
        "sixth_sense": proposal.get("sixth_sense") or "",
    })
    opened = debate.open("Test Double", [{
        "match_name": "Clube Do Remo vs Gremio",
        "tournament": "Brasile",
        "market": "MultiGol 0-1 1° Tempo",
        "book_odd": 1.66,
        "claimed_probability": 0.785,
        "sixth_sense": "Sesto Senso: avvio diesel difensivo",
    }])
    assert opened["status"] == "AWAITING_REBUTTAL"
    messages = store.list_messages(limit=5)
    assert messages[-1]["message_type"] == "DEBATE_CRITIQUE"

    other = LiveTicketDebate(store=store, measurer=debate.measurer)
    other.rebut(opened["debate_id"], "LEG 1: CONCEDE")
    judged = debate.wait_rebuttal(opened["debate_id"], timeout=2, interval=0.1)
    assert judged is not None
    assert judged["approved"] is False
    assert judged["legs"][0]["status"] == "WITHDRAWN"
    assert judged["status"] == "REJECTED"
