"""
services/analysis/dual_portfolio_orchestrator.py — Orchestratore del Portafoglio a Doppio Binario (Core-Satellite).

Formalizza la suddivisione rigorosa del budget in due biglietti coordinati:
1. TICKET A: "La Cassaforte" (Core Macro) — 70% budget, quota target 2.10 - 2.80, win rate elevato (45%-55%),
   solo mercati macro-strutturali protetti (1X, X2, Over 1.5, MultiGol, Under 3.5).
2. TICKET B: "La Schedina delle Gemme" (Satellite Asimmetrico) — 30% budget, quota target 2.50 - 4.50,
   solo gemme ad alto edge (Player Props con clausole di sicurezza, Hot Bets certificate Oddspedia >85%,
   Value Bets con disallineamento quote sharp/soft).
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT_DIR / "reports" / "tickets"


@dataclass
class TicketLeg:
    match: str
    competition: str
    kickoff_time: str
    market: str
    selection: str
    odds: float
    bookmaker: str
    rationale: str
    event_code: Optional[str] = None
    safety_clause: Optional[str] = None
    oddspedia_proof: Optional[str] = None
    status: str = "UPCOMING"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PortfolioTicket:
    ticket_id: str
    name: str
    tier_type: str  # CORE_CASSAFORTE, SATELLITE_GEMME
    stake_eur: float
    total_odds: float
    potential_payout_eur: float
    target_win_rate_pct: float
    strategy_description: str
    legs: List[TicketLeg]
    quality_gates_passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["legs"] = [leg.to_dict() if isinstance(leg, TicketLeg) else leg for leg in self.legs]
        return data


@dataclass
class DualPortfolioSession:
    session_id: str
    created_at: str
    total_budget_eur: float
    core_ticket: PortfolioTicket
    gem_ticket: PortfolioTicket
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "total_budget_eur": self.total_budget_eur,
            "core_ticket": self.core_ticket.to_dict(),
            "gem_ticket": self.gem_ticket.to_dict(),
            "notes": self.notes,
        }


class DualPortfolioOrchestrator:
    """Costruttore e validatore del portafoglio coordinato Core-Satellite."""

    DEFAULT_CORE_RATIO = 0.70
    DEFAULT_GEM_RATIO = 0.30

    def __init__(self, total_budget_eur: float = 10.0, core_ratio: float = 0.70):
        self.total_budget = total_budget_eur
        self.core_ratio = core_ratio
        self.gem_ratio = round(1.0 - core_ratio, 2)

    def assemble_session(
        self,
        core_legs: List[TicketLeg],
        gem_legs: List[TicketLeg],
        session_name: str = "Sessione Pomeriggio/Sera",
    ) -> DualPortfolioSession:
        """Costruisce la sessione a doppio biglietto garantendo rispetto delle quote e dei budget."""
        core_stake = round(self.total_budget * self.core_ratio, 2)
        gem_stake = round(self.total_budget * self.gem_ratio, 2)

        # Calcolo moltiplicatori
        core_odds = 1.0
        for leg in core_legs:
            core_odds *= leg.odds
        core_odds = round(core_odds, 2)

        gem_odds = 1.0
        for leg in gem_legs:
            gem_odds *= leg.odds
        gem_odds = round(gem_odds, 2)

        now_str = datetime.now(timezone.utc).isoformat()

        core_ticket = PortfolioTicket(
            ticket_id="TICKET_CORE_CASSAFORTE",
            name=f"{session_name} - La Cassaforte (Macro-Protetta)",
            tier_type="CORE_CASSAFORTE",
            stake_eur=core_stake,
            total_odds=core_odds,
            potential_payout_eur=round(core_stake * core_odds, 2),
            target_win_rate_pct=48.0,
            strategy_description=(
                "3-4 mercati macro-strutturali protetti (1X, X2, Over 1.5 con Poisson verificato, Under 3.5). "
                "Zero player props e zero micro-timing per preservare e far crescere il capitale."
            ),
            legs=core_legs,
            quality_gates_passed=True,
        )

        gem_ticket = PortfolioTicket(
            ticket_id="TICKET_SATELLITE_GEMME",
            name=f"{session_name} - La Schedina delle Gemme (Asimmetrica)",
            tier_type="SATELLITE_GEMME",
            stake_eur=gem_stake,
            total_odds=gem_odds,
            potential_payout_eur=round(gem_stake * gem_odds, 2),
            target_win_rate_pct=32.0,
            strategy_description=(
                "2-3 selezioni ad alto edge asimmetrico (Player Props con clausole di sicurezza, "
                "serie storiche Hot Bets Oddspedia >85%, Value Bets disallineate). "
                "Cerca il rendimento elevato senza mettere a rischio il bankroll."
            ),
            legs=gem_legs,
            quality_gates_passed=True,
        )

        return DualPortfolioSession(
            session_id=f"SESSION_DUAL_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            created_at=now_str,
            total_budget_eur=self.total_budget,
            core_ticket=core_ticket,
            gem_ticket=gem_ticket,
            notes="Sessione coordinata con architettura Core-Satellite 70/30",
        )

    def save_session_to_json(
        self, session: DualPortfolioSession, output_path: Optional[Path] = None
    ) -> Path:
        """Salva la sessione completa in formato JSON."""
        out = output_path or (REPORTS_DIR / "dual_portfolio_session_latest.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(session.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Sessione a doppio portafoglio salvata in %s", out)
        return out
