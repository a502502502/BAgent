from pathlib import Path

from harness.replay import SLATES, run_slate


def test_frozen_slate_matches_the_recorded_verdicts():
    rows = run_slate(SLATES / "2026-09-24_rules.json")
    assert rows
    failed = [row for row in rows if not row.expected_ok]
    assert not failed, [(row.match_name, row.market_name, row.detail) for row in failed]


def test_slate_file_is_the_one_shipped_with_the_harness():
    assert Path(SLATES / "2026-09-24_rules.json").is_file()
