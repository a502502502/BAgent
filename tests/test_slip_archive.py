"""L'archivio divide le schedine registrate tra quelle ancora davanti e quelle chiuse."""

import json
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from services.portal.slip_archive import load_slips, render_slip_page, split_slips

ROME = ZoneInfo("Europe/Rome")
NOW = datetime(2026, 9, 25, 12, 0, tzinfo=ROME)


def test_a_later_kickoff_stays_future_and_a_past_one_does_not(tmp_path):
    _write(tmp_path, "ahead.json", "AHEAD", "2026-09-26 20:45", "Casa vs Ospite", "Over 1.5")
    _write(tmp_path, "behind.json", "BEHIND", "2026-09-22 21:00", "Vecchia vs Gara", "1X")
    groups = split_slips(load_slips(tmp_path, tmp_path / "missing.db"), NOW)
    assert [slip.slip_id for slip in groups["future"]] == ["AHEAD"]
    assert [slip.slip_id for slip in groups["past"]] == ["BEHIND"]
    assert groups["present"] == []


def test_a_match_already_started_stays_present_for_two_hours(tmp_path):
    _write(tmp_path, "live.json", "LIVE", "2026-09-25 11:20", "Casa vs Ospite", "Over 1.5")
    _write(tmp_path, "later.json", "LATER", "2026-09-25 18:00", "Sera vs Notte", "1X")
    groups = split_slips(load_slips(tmp_path, tmp_path / "missing.db"), NOW)
    assert [slip.slip_id for slip in groups["present"]] == ["LIVE"]
    assert [slip.slip_id for slip in groups["future"]] == ["LATER"]


def test_a_settled_ledger_row_overrides_the_json_and_counts_as_past(tmp_path):
    _write(tmp_path, "same.json", "SAME", "2026-09-26 20:45", "Casa vs Ospite", "Over 1.5")
    db = tmp_path / "bagent.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """CREATE TABLE ticket_ledger (
            ticket_id TEXT, date_created TEXT, description TEXT, num_legs INTEGER,
            total_odds REAL, stake_eur REAL, payout_eur REAL, profit_loss_eur REAL,
            status TEXT, strategy_type TEXT, notes TEXT
        )"""
    )
    conn.execute(
        "INSERT INTO ticket_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("SAME", "2026-09-20", "Schedina chiusa", 1, 1.5, 10, 15, 5, "WON", "", ""),
    )
    conn.commit()
    conn.close()
    groups = split_slips(load_slips(tmp_path, db), NOW)
    assert groups["future"] == []
    assert groups["present"] == []
    assert groups["past"][0].status == "WON"
    assert groups["past"][0].profit == 5
    page = render_slip_page(load_slips(tmp_path, db), NOW)
    assert "Vinta" in page
    assert "Schedina chiusa" in page
    assert "Presenti" in page and "Future" in page and "Passate" in page
    assert '"check_seconds": 30' in page


def test_a_title_with_markup_is_escaped(tmp_path):
    path = tmp_path / "raw.json"
    path.write_text(
        json.dumps(
            {
                "ticket_id": "RAW",
                "name": "<script>alert(1)</script>",
                "status": "PENDING",
                "legs": [{"match": "A vs B", "pick": "1X", "date_time": "2026-09-26 18:00"}],
            }
        ),
        encoding="utf-8",
    )
    page = render_slip_page(load_slips(tmp_path, tmp_path / "missing.db"), NOW)
    assert "<script>alert" not in page
    assert "\\u003cscript>" in page


def _write(folder, filename, slip_id, kickoff, match, pick):
    (folder / filename).write_text(
        json.dumps(
            {
                "ticket_id": slip_id,
                "name": slip_id,
                "stake": 10,
                "total_odds": 1.8,
                "legs": [{"match": match, "pick": pick, "netwin_odds": 1.8, "date_time": kickoff}],
            }
        ),
        encoding="utf-8",
    )
