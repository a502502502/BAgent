"""Prenotazione Netwin: salva il codice a 6 cifre e lo mostra sul portale."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.book_portal_tickets import book_ticket, collect_codes, format_chat, select_tickets, stake_of
from services.portal.slip_archive import load_slips, render_slip_page

ROME = ZoneInfo("Europe/Rome")


class _Booked:
    def __init__(self, code: str):
        self.code = code
        self.calls = []

    def build_ticket_and_book(self, selections, stake, receipt_id=None):
        self.calls.append({"selections": selections, "stake": stake, "receipt_id": receipt_id})
        return {
            "success": True,
            "booking_code": self.code,
            "screenshot": f"reports/receipts/prenotazione_{receipt_id}_{self.code}.png",
        }


def _feed() -> dict:
    return {
        "future": [
            {
                "id": "TICKET_ONE",
                "title": "Una",
                "stake": "2.50 €",
                "legs": [{"match": "Germania vs Serbia", "pick": "Under 4.5", "odd": "1.32"}],
            },
            {
                "id": "TICKET_TWO",
                "stake": None,
                "legs": [{"match": "Grecia vs Olanda", "pick": "Under 3.5", "odd": "1.45"}],
            },
        ]
    }


def test_ticket_id_selects_one_future_slip():
    chosen = select_tickets(_feed(), all_future=False, ticket_id="TICKET_TWO")
    assert [row["id"] for row in chosen] == ["TICKET_TWO"]
    assert len(select_tickets(_feed(), all_future=True, ticket_id="")) == 2


def test_booking_code_is_written_to_the_ticket_and_the_feed(tmp_path):
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    source = tickets / "ticket_one.json"
    source.write_text(
        json.dumps({
            "ticket_id": "TICKET_ONE",
            "stake": 3.0,
            "legs": [{
                "match": "Germania vs Serbia",
                "market": "Under / Over",
                "pick": "Under 4.5",
                "netwin_odds": 1.32,
            }],
        }),
        encoding="utf-8",
    )
    feed = tmp_path / "schedine.json"
    feed.write_text(json.dumps(_feed()), encoding="utf-8")
    automator = _Booked("663801")
    result = book_ticket(
        _feed()["future"][0],
        stake=None,
        tickets_dir=tickets,
        feed_path=feed,
        automator_factory=lambda: automator,
    )
    assert result["ok"] is True
    assert result["code"] == "663801"
    assert automator.calls[0]["stake"] == 3.0
    assert automator.calls[0]["selections"][0]["pick"] == "Under 4.5"
    assert automator.calls[0]["selections"][0]["market"] == "Under / Over"
    saved = json.loads(source.read_text(encoding="utf-8"))
    portal = json.loads(feed.read_text(encoding="utf-8"))
    assert saved["booking_code"] == "663801"
    assert portal["future"][0]["booking_code"] == "663801"
    assert stake_of({}) == 2.50


def test_chat_lists_the_saved_code_and_marks_a_missing_one(tmp_path):
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    (tickets / "one.json").write_text(
        json.dumps({"ticket_id": "TICKET_ONE", "booking_code": "663801", "legs": []}),
        encoding="utf-8",
    )
    rows = collect_codes(_feed(), tickets)
    text = format_chat(rows)
    assert "663801  Una" in text
    assert "manca  " in text
    assert "Germania vs Serbia — Under 4.5" in text
    assert "1 codici su 2 schedine" in text


def test_portal_card_renders_the_booking_badge(tmp_path):
    path = tmp_path / "coded.json"
    path.write_text(
        json.dumps({
            "ticket_id": "CODED",
            "name": "Tripla",
            "stake": 2.5,
            "total_odds": 2.1,
            "status": "PENDING",
            "booking_code": "663801",
            "legs": [{"match": "A vs B", "pick": "1X", "date_time": "2026-10-04 18:00"}],
        }),
        encoding="utf-8",
    )
    slips = load_slips(tmp_path, tmp_path / "missing.db")
    assert slips[0].booking_code == "663801"
    page = render_slip_page(slips, datetime(2026, 10, 1, 12, 0, tzinfo=ROME))
    assert "663801" in page
    assert "booking-badge" in page
    assert "Prenotazione Netwin" in page
