import pytest

from harness.calibration import brier_binary, load_settled, reliability, report_settled, simulate_bankroll


def test_perfect_predictions_have_zero_brier_and_zero_ece():
    pairs = [(0.8, 1)] * 8 + [(0.8, 0)] * 2
    report = reliability(pairs)
    assert report.n == 10
    assert report.brier == brier_binary(pairs)
    assert abs(report.brier - 0.16) < 1e-9
    assert report.ece == pytest.approx(0.0, abs=1e-12)
    assert len(report.bins) == 1
    assert report.bins[0].lower == 0.8
    assert report.bins[0].observed_frequency == 0.8


def test_a_loss_opens_a_drawdown_inside_the_stake_cap():
    curve = simulate_bankroll(
        [{"probability": 0.9, "odds": 1.5, "outcome": 0}],
        start=200,
    )
    assert curve.steps[0].stake > 0
    assert curve.steps[0].stake <= 200 * 0.08 + 1e-6
    assert curve.end < curve.start
    assert curve.max_drawdown > 0


def test_settled_smoke_file_reports_brier_and_bankroll():
    calibration, curve = report_settled(load_settled())
    assert calibration.n == 4
    assert 0.0 <= calibration.brier <= 1.0
    assert 0.0 <= calibration.ece <= 1.0
    assert curve.start == 200
    assert curve.end != curve.start
