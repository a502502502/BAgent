"""
Bridge: StrictTicketPipeline (candidati approvati) → Telegram 1-Click PRENOTA.

Converte MarketCandidate / ValidationReport in selezioni NetwinAutomator
e pubblica il Master Ticket su TelegramSentinel.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from services.betting.strict_ticket_pipeline import (
    MarketCandidate,
    StrictTicketPipeline,
    ValidationReport,
)
from services.telegram.telegram_sentinel import TelegramSentinel

logger = logging.getLogger("CertifiedTicketPublisher")

_VS = re.compile(r"\s+vs\.?\s+|\s+-\s+", re.IGNORECASE)


def candidate_to_netwin_selection(
    candidate: MarketCandidate,
    report: Optional[ValidationReport] = None,
) -> Dict[str, Any]:
    """Map a certified candidate to NetwinAutomator selection dict."""
    home, away = _split_match(candidate.match_name)
    odd = float(candidate.netwin_actual_odd or candidate.bookmaker_odd)
    edge_pct = 0.0
    if report is not None:
        edge_pct = float(report.mathematical_edge) * 100.0
    return {
        "match": candidate.match_name,
        "home": home,
        "away": away,
        "tournament": candidate.tournament,
        "market": candidate.market_name,
        "pick": candidate.market_name,
        "netwin_odds": odd,
        "odd": odd,
        "edge_pct": edge_pct,
        "fixture_id": candidate.fixture_id,
        "sixth_sense": candidate.sixth_sense_analysis,
    }


def _split_match(match_name: str) -> Tuple[str, str]:
    parts = _VS.split(str(match_name or "").strip(), maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return str(match_name or "").strip(), ""


def audit_and_publish(
    candidates: Sequence[MarketCandidate],
    *,
    bankroll: float,
    ticket_name: str = "Master Ticket Certificato",
    notes: str = "",
    send_telegram: bool = True,
    sentinel: Optional[TelegramSentinel] = None,
) -> Dict[str, Any]:
    """
    Validate candidates via StrictTicketPipeline and optionally push to Telegram.

    Returns dict with approved selections, stake, odds, and telegram_sent flag.
    """
    pipeline = StrictTicketPipeline()
    approved: List[MarketCandidate] = []
    reports: List[ValidationReport] = []
    total_odds = 1.0

    for cand in candidates:
        rep = pipeline.validate_candidate(cand)
        if rep.passed:
            approved.append(cand)
            reports.append(rep)
            total_odds *= float(cand.netwin_actual_odd or cand.bookmaker_odd)

    if not approved:
        return {
            "success": False,
            "error": "Nessuna selezione ha superato StrictTicketPipeline.",
            "approved": [],
            "selections": [],
            "telegram_sent": False,
        }

    stake = pipeline.calculate_recommended_stake(
        current_bankroll=bankroll,
        total_odds=total_odds,
        num_selections=len(approved),
    )
    selections = [
        candidate_to_netwin_selection(c, r) for c, r in zip(approved, reports)
    ]
    pot = stake * total_odds

    telegram_sent = False
    if send_telegram:
        bot = sentinel or TelegramSentinel()
        telegram_sent = bot.send_master_ticket(
            ticket_name=ticket_name,
            selections=selections,
            total_odds=total_odds,
            stake_eur=stake,
            potential_win_eur=pot,
            bankroll_current=bankroll,
            notes=notes
            or "Tocca PRENOTA SU NETWIN per il codice a 6 cifre (nessuna puntata automatica).",
        )
        if telegram_sent:
            logger.info("Master ticket inviato su Telegram (%s selezioni)", len(selections))

    return {
        "success": True,
        "approved": approved,
        "reports": reports,
        "selections": selections,
        "total_odds": total_odds,
        "stake": stake,
        "potential_win": pot,
        "telegram_sent": telegram_sent,
    }
