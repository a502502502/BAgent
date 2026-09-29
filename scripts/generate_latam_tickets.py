#!/usr/bin/env python3
"""
scripts/generate_latam_tickets.py — Generatore di Schedine Certificate Sudamerica (Argentina & Brasile).

Risolve il problema dei "mercati poveri 1X2":
- Invece di limitarsi a 1X2 o Under 2.5 a quota compressa (@1.15-1.25),
  attinge all'intero spettro delle oltre 70 Hidden Gems Netwin:
  • Combo Protette: 1X + Under 3.5, X2 + Under 4.5, Under 2.5 + NoGol;
  • 1° Tempo: MultiGol 0-1 1°T, Under 1.5 1°T, 1X 1°T;
  • Chance Mix: 1 o Under 2.5, 1X o Gol, NoGol o Under 2.5;
  • Draw No Bet: DNB 1, DNB 2;
  • MultiGol Squadra: MultiGol 0-1 Casa / Ospite.
- Garantisce l'indipendenza degli eventi (max 1 selezione per partita).
- Calcola la probabilità congiunta e lo stake Kelly sul bankroll reale.
- Opzione --publish-to-bus per notificare istantaneamente Cursor tramite il Bus MCP.

Uso:
    python scripts/generate_latam_tickets.py
    python scripts/generate_latam_tickets.py --publish-to-bus
    python scripts/generate_latam_tickets.py --min-prob 0.72 --min-edge 0.08
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

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

from services.betting.netwin_cache_reader import (
    NetwinGem,
    load_cached_matches,
    scan_netwin_matches,
)
from services.betting.strict_ticket_pipeline import (
    StrictTicketPipeline,
    MarketCandidate,
    TicketValidationReport,
)
from services.database.performance_tracker import PerformanceTracker
from services.mcp.agent_bus_store import AgentBusStore


def pick_best_gem_per_match(gems: List[NetwinGem]) -> List[NetwinGem]:
    """Seleziona al massimo una gemma per partita, privilegiando mercati protetti con miglior score."""
    by_match: Dict[str, List[NetwinGem]] = {}
    for g in gems:
        by_match.setdefault(g.match_name.lower().strip(), []).append(g)

    best_gems: List[NetwinGem] = []
    for match_key, match_gems in by_match.items():
        # Score ponderato: preferenza a mercati protetti (combo, chance mix, multigol) con buona probabilità ed edge
        def _score(gem: NetwinGem) -> float:
            m_low = gem.market.lower()
            bonus = 1.0
            if "+" in m_low or "chance mix" in m_low or " o " in m_low:
                bonus = 1.25  # Favorisci combo protette e chance mix
            elif "1° tempo" in m_low or "dnb" in m_low:
                bonus = 1.15
            elif "multigol" in m_low:
                bonus = 1.10
            return (gem.edge * 1.5 + gem.probability) * bonus

        sorted_gems = sorted(match_gems, key=_score, reverse=True)
        best_gems.append(sorted_gems[0])

    # Ordina per edge decrescente
    best_gems.sort(key=lambda g: g.edge, reverse=True)
    return best_gems


def build_tickets(
    best_gems: List[NetwinGem],
    bankroll: float,
) -> List[Dict[str, Any]]:
    """Costruisce 3 tipologie di ticket indipendenti e complementari."""
    tickets = []

    # 1. RADDOPPIO PROTETTO LATAM (2 Selezioni ad altissima probabilità: P > 73%, quota ~2.20 - 2.80)
    high_p_gems = [g for g in best_gems if g.probability >= 0.72 and g.book_odd >= 1.35]
    if len(high_p_gems) >= 2:
        leg1 = high_p_gems[0]
        # Trova seconda selezione su un match diverso
        leg2 = next((g for g in high_p_gems[1:] if g.match_name != leg1.match_name), None)
        if leg2:
            odds_tot = round(leg1.book_odd * leg2.book_odd, 2)
            p_joint = round(leg1.probability * leg2.probability, 3)
            # Kelly 25% su raddoppio protetto
            b = odds_tot - 1.0
            q = 1.0 - p_joint
            raw_kelly = max(0.0, (b * p_joint - q) / b) if b > 0 else 0.0
            stake_pct = min(0.06, raw_kelly * 0.25)
            stake_eur = round(max(2.0, bankroll * stake_pct), 2) if bankroll >= 20.0 else 2.0

            tickets.append({
                "type": "RADDOPPIO_PROTETTO_LATAM",
                "title": "🛡️ Raddoppio Protetto Sudamerica (2 Selezioni)",
                "legs": [leg1, leg2],
                "total_odds": odds_tot,
                "joint_probability": p_joint,
                "expected_edge": round((p_joint * odds_tot - 1.0) * 100.0, 1),
                "recommended_stake_eur": stake_eur,
                "stake_pct_bankroll": round(stake_pct * 100.0, 1),
            })

    # 2. TRIPLA BLINDATA LATAM (3 Selezioni: mix Argentina + Brasile, quota ~3.00 - 4.50)
    # Cerchiamo di bilanciare almeno una brasiliana e almeno un'argentina
    arg_gems = [g for g in best_gems if "argentina" in g.tournament.lower()]
    bra_gems = [g for g in best_gems if "brasile" in g.tournament.lower()]

    tripla_legs = []
    used_matches = set()
    # Includi se possibile almeno una brasiliana e una argentina
    if bra_gems:
        tripla_legs.append(bra_gems[0])
        used_matches.add(bra_gems[0].match_name)
    if arg_gems and arg_gems[0].match_name not in used_matches:
        tripla_legs.append(arg_gems[0])
        used_matches.add(arg_gems[0].match_name)

    # Completa fino a 3 selezioni con le migliori gemme rimanenti
    for g in best_gems:
        if g.match_name not in used_matches and len(tripla_legs) < 3:
            tripla_legs.append(g)
            used_matches.add(g.match_name)

    if len(tripla_legs) == 3:
        odds_tot = round(tripla_legs[0].book_odd * tripla_legs[1].book_odd * tripla_legs[2].book_odd, 2)
        p_joint = round(tripla_legs[0].probability * tripla_legs[1].probability * tripla_legs[2].probability, 3)
        b = odds_tot - 1.0
        q = 1.0 - p_joint
        raw_kelly = max(0.0, (b * p_joint - q) / b) if b > 0 else 0.0
        stake_pct = min(0.05, raw_kelly * 0.20)
        stake_eur = round(max(2.0, bankroll * stake_pct), 2) if bankroll >= 20.0 else 2.0

        tickets.append({
            "type": "TRIPLA_BLINDATA_LATAM",
            "title": "⭐ Tripla Blindata Sudamerica (Argentina & Brasile)",
            "legs": tripla_legs,
            "total_odds": odds_tot,
            "joint_probability": p_joint,
            "expected_edge": round((p_joint * odds_tot - 1.0) * 100.0, 1),
            "recommended_stake_eur": stake_eur,
            "stake_pct_bankroll": round(stake_pct * 100.0, 1),
        })

    # 3. QUATERNA OMNI-MARKET COMBO & 1°T (4 Selezioni a quote 1.40-1.75, quota ~5.00 - 8.00)
    quaterna_legs = []
    used_matches = set()
    for g in best_gems:
        if g.match_name not in used_matches:
            quaterna_legs.append(g)
            used_matches.add(g.match_name)
            if len(quaterna_legs) == 4:
                break

    if len(quaterna_legs) == 4:
        odds_tot = 1.0
        p_joint = 1.0
        for l in quaterna_legs:
            odds_tot *= l.book_odd
            p_joint *= l.probability
        odds_tot = round(odds_tot, 2)
        p_joint = round(p_joint, 3)
        b = odds_tot - 1.0
        q = 1.0 - p_joint
        raw_kelly = max(0.0, (b * p_joint - q) / b) if b > 0 else 0.0
        stake_pct = min(0.035, raw_kelly * 0.15)
        stake_eur = round(max(1.5, bankroll * stake_pct), 2) if bankroll >= 20.0 else 1.50

        tickets.append({
            "type": "MASTER_LATAM_COMBO",
            "title": "💎 Master Ticket Combo & 1° Tempo Sudamerica (4 Selezioni)",
            "legs": quaterna_legs,
            "total_odds": odds_tot,
            "joint_probability": p_joint,
            "expected_edge": round((p_joint * odds_tot - 1.0) * 100.0, 1),
            "recommended_stake_eur": stake_eur,
            "stake_pct_bankroll": round(stake_pct * 100.0, 1),
        })

    return tickets


def format_ticket(ticket: Dict[str, Any]) -> str:
    lines = [
        "=" * 80,
        f"{ticket['title']}",
        "=" * 80,
        f"• Quota Complessiva:  @{ticket['total_odds']:.2f}",
        f"• Probabilità Congiunta: {ticket['joint_probability']*100:.1f}%",
        f"• Edge Matematico Reale: {ticket['expected_edge']:+.1f}%",
        f"• Stake Consigliato:     €{ticket['recommended_stake_eur']:.2f} ({ticket['stake_pct_bankroll']:.1f}% del bankroll)",
        "-" * 80,
        "SELEZIONI RIGOROSAMENTE INDIPENDENTI:"
    ]
    for idx, leg in enumerate(ticket["legs"], 1):
        lines.append(
            f"  {idx}. ⚽ {leg.match_name} ({leg.tournament})\n"
            f"     Mercato: '{leg.market}' @ {leg.book_odd:.2f} (Fair @{leg.fair_odd:.2f}, P={leg.probability*100:.1f}%, Edge {leg.edge:+.1%})\n"
            f"     Note: {leg.notes or 'Dixon-Coles calibrato su xG reali'}"
        )
    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generatore Schedine Certificate Sudamerica")
    parser.add_argument("--min-prob", type=float, default=0.70, help="Probabilità minima di ciascuna selezione (default 0.70)")
    parser.add_argument("--min-edge", type=float, default=0.045, help="Edge minimo di ciascuna selezione (default 0.045)")
    parser.add_argument("--publish-to-bus", action="store_true", help="Pubblica i ticket certificati sul Bus MCP per Cursor")
    args = parser.parse_args()

    # 1. Carica le partite in cache
    matches_arg = load_cached_matches("Argentina")
    matches_bra = load_cached_matches("Brasile")
    total_matches = len(matches_arg) + len(matches_bra)

    if total_matches == 0:
        print("❌ Nessuna partita trovata in cache per Argentina e Brasile.")
        print("Esegui prima: python scripts/download_netwin_odds.py --tournament Argentina")
        print("              python scripts/download_netwin_odds.py --tournament Brasile")
        sys.exit(1)

    # 2. Scansione quote con modello Poisson/Dixon-Coles
    gems_arg = scan_netwin_matches(matches_arg, min_edge=args.min_edge, min_probability=args.min_prob)
    gems_bra = scan_netwin_matches(matches_bra, min_edge=args.min_edge, min_probability=args.min_prob)
    all_gems = gems_arg + gems_bra

    print("\n" + "=" * 80)
    print(f"🌎 GENERATORE SCHEDINE SUDAMERICA (ARGENTINA & BRASILE)")
    print(f"   Partite analizzate: {total_matches} (Argentina: {len(matches_arg)}, Brasile: {len(matches_bra)})")
    print(f"   Hidden Gems trovate sopra soglia: {len(all_gems)} (Arg: {len(gems_arg)}, Bra: {len(gems_bra)})")
    print("=" * 80)

    # 3. Bankroll attuale
    tracker = PerformanceTracker()
    bankroll = tracker.get_current_bankroll()
    print(f"💰 Bankroll reale attuale: €{bankroll:.2f}")

    # 4. Selezione non correlata (max 1 gemma per partita)
    best_gems = pick_best_gem_per_match(all_gems)
    print(f"🎯 Partite distinte con valore matematico accertato: {len(best_gems)}")

    # 5. Costruzione ticket
    tickets = build_tickets(best_gems, bankroll)

    print("\n" + "#" * 80)
    print(f"📋 SCHEDINE CERTIFICATE GENERATE: {len(tickets)}")
    print("#" * 80 + "\n")

    for t in tickets:
        formatted = format_ticket(t)
        print(formatted)
        print()

    # 6. Pubblicazione opzionale su Bus MCP
    if args.publish_to_bus and tickets:
        bus = AgentBusStore()
        summary_text = "\n\n".join([format_ticket(t) for t in tickets])
        task = bus.post_task(
            title="Schedine Certificate Sudamerica (Argentina & Brasile)",
            instructions=(
                "Sono state generate le schedine certificate con i nuovi mercati integrati "
                "(Combo protette, 1° Tempo, Chance Mix, DNB):\n\n"
                f"{summary_text}\n\n"
                "Verifica la conformità con strict_validator e prepara la prenotazione su Netwin se approvato."
            ),
            target_files=["scripts/generate_latam_tickets.py", "data/netwin_live_odds.json"],
            sender="Antigravity",
        )
        print(f"🚀 Schedine pubblicate con successo sul Bus MCP! [Task ID: {task['task_id']}]")


if __name__ == "__main__":
    main()
