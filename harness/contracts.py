"""Catalogo eseguibile delle regole che il funnel boccia o lascia passare.

Ogni voce ha una selezione che la regola deve fermare e una che deve arrivare in fondo.
Il marcatore è il testo del rejection_reason, così il test fallisce se a bocciare è un altro gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.betting.strict_ticket_pipeline import StrictTicketPipeline, ValidationReport

from harness.candidates import pipeline as offline_pipeline
from harness.candidates import selection


@dataclass(frozen=True)
class RuleContract:
    rule_id: str
    marker: str
    blocked: dict
    admitted: dict

    def check(self, pipe: StrictTicketPipeline | None = None) -> tuple[bool, str]:
        pipe = pipe or offline_pipeline()
        denied: ValidationReport = pipe.validate_candidate(selection(**self.blocked))
        allowed: ValidationReport = pipe.validate_candidate(selection(**self.admitted))
        problems: list[str] = []
        reason = denied.rejection_reason or ""
        if denied.passed or self.marker not in reason:
            problems.append(
                f"blocco {self.rule_id}: atteso '{self.marker}', "
                f"passed={denied.passed}, stage={denied.stage_failed}, reason={reason}"
            )
        if not allowed.passed:
            problems.append(
                f"ammissione {self.rule_id}: stage={allowed.stage_failed}, "
                f"reason={allowed.rejection_reason}"
            )
        if self.marker in (allowed.rejection_reason or ""):
            problems.append(f"ammissione {self.rule_id} fermata dallo stesso marcatore")
        return (not problems), " | ".join(problems)


def _corner(**overrides) -> dict:
    data = dict(
        market_name="Over 8.5 Corner Totali",
        market_type="CORNER",
        bookmaker_odd=1.55,
        team_avg_shots=20.0,
        avg_corners_home=6.0,
        avg_corners_away=5.5,
    )
    data.update(overrides)
    return data


CATALOG: tuple[RuleContract, ...] = (
    RuleContract(
        rule_id="R76-orario",
        marker="REGOLA #76",
        blocked={"kickoff_time": "2026-09-24"},
        admitted={},
    ),
    RuleContract(
        rule_id="R76-stagione",
        marker="GATE 0.05",
        blocked={"kickoff_time": "2025-09-24 20:45 CEST"},
        admitted={},
    ),
    RuleContract(
        rule_id="R-protezione-1",
        marker="DIVIETO 1/2 FISSO",
        blocked={"market_name": "1", "market_type": "1X2", "bookmaker_odd": 1.40},
        admitted={"market_name": "1X", "market_type": "COMBO", "bookmaker_odd": 1.40},
    ),
    RuleContract(
        rule_id="R80",
        marker="REGOLA #80",
        blocked={
            "match_name": "Bayern Munchen vs Bochum",
            "tournament": "Bundesliga",
            "market_name": "Under 2.5",
            "pre_match_odd_favorite": 1.25,
        },
        admitted={
            "match_name": "Bayern Munchen vs Bochum",
            "tournament": "Bundesliga",
            "market_name": "Over 1.5",
            "pre_match_odd_favorite": 1.25,
        },
    ),
    RuleContract(
        rule_id="R56",
        marker="REGOLA #56",
        blocked={"tournament": "Serie B", "match_name": "Como vs Pisa"},
        admitted={"tournament": "Serie A", "match_name": "Como vs Pisa"},
    ),
    RuleContract(
        rule_id="R67",
        marker="REGOLA #67",
        blocked={
            "match_name": "Besiktas vs Marsiglia",
            "tournament": "UEFA Champions League",
            "market_name": "X2",
            "bookmaker_odd": 1.80,
        },
        admitted={
            "match_name": "Besiktas vs Marsiglia",
            "tournament": "UEFA Champions League",
            "market_name": "Over 1.5",
            "bookmaker_odd": 1.40,
        },
    ),
    RuleContract(
        rule_id="R45",
        marker="REGOLA #45",
        blocked=_corner(team_avg_shots=12.0),
        admitted=_corner(),
    ),
    RuleContract(
        rule_id="R66-corner",
        marker="REGOLA #66",
        blocked=_corner(
            market_name="Over 6.5 Corner Casa",
            bookmaker_odd=1.28,
            pre_match_odd_favorite=1.28,
        ),
        admitted=_corner(),
    ),
    RuleContract(
        rule_id="R48",
        marker="ANTI-CEILING",
        blocked={
            "match_name": "Barcelona vs Elche",
            "tournament": "La Liga",
            "market_name": "MultiGol 1-3 Barcelona",
        },
        admitted={
            "match_name": "Barcelona vs Elche",
            "tournament": "La Liga",
            "market_name": "Over 1.5",
        },
    ),
    RuleContract(
        rule_id="R51",
        marker="REGOLA #51",
        blocked={"match_name": "Napoli vs Roma", "market_name": "1X + Over 1.5"},
        admitted={"match_name": "Napoli vs Roma", "market_name": "1X + Under 3.5"},
    ),
    RuleContract(
        rule_id="R71",
        marker="REGOLA #71",
        blocked={
            "match_name": "Ajax vs Twente",
            "tournament": "Eredivisie",
            "market_name": "Under 2.5",
        },
        admitted={
            "match_name": "Ajax vs Twente",
            "tournament": "Eredivisie",
            "market_name": "Over 1.5",
        },
    ),
    RuleContract(
        rule_id="R55",
        marker="REGOLA #55",
        blocked={
            "verified_sources_checked": False,
            "xg_home": None,
            "xg_away": None,
            "home_matches_played": 1,
            "away_matches_played": 1,
        },
        admitted={},
    ),
)
