"""Rigioca uno slate JSON dentro la pipeline, senza FootyStats e senza bagent.db."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from services.betting.strict_ticket_pipeline import ValidationReport

from harness.candidates import pipeline as offline_pipeline
from harness.candidates import selection

SLATES = Path(__file__).resolve().parent / "slates"


@dataclass(frozen=True)
class SlateRow:
    match_name: str
    market_name: str
    passed: bool
    stage_failed: int | None
    reason: str
    expected_ok: bool
    detail: str


def run_slate(path: Path | None = None) -> list[SlateRow]:
    slate_path = path or (SLATES / "2026-09-24_rules.json")
    payload = json.loads(slate_path.read_text(encoding="utf-8"))
    pipe = offline_pipeline()
    rows: list[SlateRow] = []
    for item in payload["selections"]:
        expect = item.get("expect") or {}
        overrides = {key: value for key, value in item.items() if key != "expect"}
        report: ValidationReport = pipe.validate_candidate(selection(**overrides))
        reason = report.rejection_reason or ""
        problems: list[str] = []
        if report.passed != bool(expect.get("passed")):
            problems.append(f"passed={report.passed}, atteso {expect.get('passed')}")
        if "stage_failed" in expect and report.stage_failed != expect["stage_failed"]:
            problems.append(f"stage={report.stage_failed}, atteso {expect['stage_failed']}")
        marker = expect.get("rule")
        if marker and marker not in reason:
            problems.append(f"manca '{marker}' in {reason}")
        rows.append(
            SlateRow(
                match_name=overrides.get("match_name", "Home FC vs Away FC"),
                market_name=overrides.get("market_name", "Over 1.5"),
                passed=report.passed,
                stage_failed=report.stage_failed,
                reason=reason,
                expected_ok=not problems,
                detail=" | ".join(problems),
            )
        )
    return rows
