"""
tests/test_telegram_notifications_and_gates.py — Verifica gate temporali, assenza emoji e deduplicazione Telegram.
"""

from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

from services.telegram.telegram_sentinel import TelegramSentinel, clean_telegram_text
from scripts.live_user_tickets_watcher import (
    load_active_user_tickets,
    is_leg_eligible,
    parse_kickoff,
    ROME
)

ROOT = Path(__file__).resolve().parent.parent


def test_clean_telegram_text_removes_emojis_and_decorative_symbols():
    sample = "⚽ AGGIORNAMENTO LIVE 🚀 Risultato: 1-0 💎 🎯 Quota @2.00 ━━━"
    cleaned = clean_telegram_text(sample)
    assert "⚽" not in cleaned
    assert "🚀" not in cleaned
    assert "💎" not in cleaned
    assert "🎯" not in cleaned
    assert "━" not in cleaned
    assert "AGGIORNAMENTO LIVE" in cleaned
    assert "Risultato: 1-0" in cleaned
    assert "Quota @2.00" in cleaned


def test_telegram_sentinel_deduplication():
    sentinel = TelegramSentinel()
    # Mock session
    sentinel.token = "DUMMY_TOKEN"
    sentinel.chat_id = "DUMMY_CHAT"
    
    calls = []
    class DummyResp:
        status_code = 200
        text = "ok"

    def dummy_post(url, json=None, timeout=None):
        calls.append(json)
        return DummyResp()

    sentinel.session.post = dummy_post

    # First send should succeed
    res1 = sentinel.send_message("Messaggio di test live 1")
    assert res1 is True
    assert len(calls) == 1

    # Immediate duplicate send should be blocked by anti-flood
    res2 = sentinel.send_message("Messaggio di test live 1")
    assert res2 is False
    assert len(calls) == 1

    # Different message should succeed
    res3 = sentinel.send_message("Altro messaggio live differente")
    assert res3 is True
    assert len(calls) == 2


def test_active_user_tickets_filter_excludes_past_tickets():
    active = load_active_user_tickets()
    past_ids = ["01OCT", "02OCT", "04OCT", "05OCT", "06OCT", "06OTT"]
    for t in active:
        tid = t.get("ticket_id", "")
        for p in past_ids:
            assert p not in tid, f"Ticket passato non escluso: {tid}"
        assert t.get("status") in ["OPEN", "PENDING", "WAITING_LINEUPS"]
        assert not t.get("settled", False)


def test_is_leg_eligible_kickoff_gates():
    now = datetime(2026, 10, 7, 16, 0, tzinfo=ROME)

    # Leg in the past (yesterday)
    past_leg = {"kickoff": "2026-10-06 20:45 CEST", "status": "PENDING"}
    assert is_leg_eligible(past_leg, now) is False

    # Leg earlier today > 4 hours ago (11:00 CEST)
    concluded_today_leg = {"kickoff": "2026-10-07 11:00 CEST", "status": "PENDING"}
    assert is_leg_eligible(concluded_today_leg, now) is False

    # Leg today upcoming or recent (17:00 CEST)
    eligible_today_leg = {"kickoff": "2026-10-07 17:00 CEST", "status": "PENDING"}
    assert is_leg_eligible(eligible_today_leg, now) is True

    # Leg in the future (09 Oct)
    future_leg = {"kickoff": "2026-10-09 20:30 CEST", "status": "PENDING"}
    assert is_leg_eligible(future_leg, now) is True

    # Already settled leg
    settled_leg = {"kickoff": "2026-10-07 17:00 CEST", "status": "LOST"}
    assert is_leg_eligible(settled_leg, now) is False
