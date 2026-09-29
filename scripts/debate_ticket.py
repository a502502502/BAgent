#!/usr/bin/env python3
"""
scripts/debate_ticket.py — CLI per lanciare il Dibattito in Tempo Reale tra Agenti sulle Schedine.

Esegue il protocollo dialettico a 5 fasi tra Antigravity (The Quant) e Cursor (The Auditor).
Stampa la trascrizione formattata e registra l'esito sul bus MCP per Cursor.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# UTF-8 su Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.generate_latam_tickets import (
    build_disjoint_tickets,
    filter_and_certify_gems,
    load_cached_matches,
    scan_netwin_matches,
)
from services.analysis.league_dna_market_matcher import LeagueDNAMarketMatcher
from services.betting.strict_ticket_pipeline import StrictTicketPipeline
from services.database.performance_tracker import PerformanceTracker
from services.debate.ticket_debate_arena import TicketDebateArena


def main():
    parser = argparse.ArgumentParser(description="Live Debate Arena sulle Schedine (Antigravity vs Cursor)")
    parser.add_argument("--ticket-index", type=int, default=0, help="Indice della schedina da dibattere (0 per la prima, 1 per la seconda, -1 per tutte)")
    parser.add_argument("--no-bus", action="store_true", help="Non salvare l'esito sul Bus MCP")
    args = parser.parse_args()

    # 1. Carica le partite e genera le schedine certificate
    matches_arg = load_cached_matches("Argentina")
    matches_bra = load_cached_matches("Brasile")
    match_kickoffs = {m.match_name.strip().lower(): m.kickoff for m in (matches_arg + matches_bra)}

    gems_arg = scan_netwin_matches(matches_arg)
    gems_bra = scan_netwin_matches(matches_bra)
    all_gems = gems_arg + gems_bra

    pipeline = StrictTicketPipeline()
    dna_matcher = LeagueDNAMarketMatcher()
    certified = filter_and_certify_gems(all_gems, match_kickoffs, pipeline, dna_matcher)

    tracker = PerformanceTracker()
    bankroll = tracker.get_current_bankroll()
    tickets = build_disjoint_tickets(certified, bankroll)

    if not tickets:
        print("🛑 Nessuna schedina disponibile per il dibattito (NO BET).")
        sys.exit(0)

    arena = TicketDebateArena()

    target_tickets = tickets if args.ticket_index == -1 else [tickets[min(args.ticket_index, len(tickets) - 1)]]

    for t in target_tickets:
        title = t.get("title") or t.get("name") or "Schedina Candidata"
        print("\n" + "=" * 80)
        print(f"🥊 AVVIO DIBATTITO LIVE SU: {title}")
        print("=" * 80 + "\n")

        def progress_cb(msg: str, pct: int):
            print(f"[{pct:3d}%] {msg}")

        report = arena.run_debate(t, on_progress=progress_cb)

        print("\n" + report.transcript_markdown)
        print("\n" + "=" * 80)

        if not args.no_bus:
            task_id = arena.record_debate_to_bus(report)
            print(f"📢 Trascrizione del dibattito registrata sul Bus MCP! [Task ID: {task_id}]")
            print("=" * 80)


if __name__ == "__main__":
    main()
