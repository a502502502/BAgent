#!/usr/bin/env python3
"""
scripts/ingest_tipster_ticket.py — CLI per Ingestion & Report di Tipster Intelligence.

Uso:
    # Mostra lo stato attuale dell'apprendimento su tutte le famiglie di mercato:
    python scripts/ingest_tipster_ticket.py --summary

    # Ingestione delle due schedine storiche vincenti del 01/10/2026:
    python scripts/ingest_tipster_ticket.py --bootstrap-october-01
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.tipster_intelligence import (
    TipsterIntelligenceEngine,
    TipsterTicketInput,
    TipsterLegInput,
    CANONICAL_FAMILIES
)

def bootstrap_tonight_tickets():
    engine = TipsterIntelligenceEngine()

    print("🚀 Ingestion Schedine Vincenti del 01/10/2026...")

    # Ticket 1 (Quella da @2.78 del primo tipster)
    ticket_1 = TipsterTicketInput(
        tipster_name="Tipster 1 - Flussi & Tempi",
        ticket_date="2026-10-01",
        total_odds=2.78,
        status="WON",
        source="CHAT_INPUT_01_10_2026",
        legs=[
            TipsterLegInput(
                match_name="Grecia vs Olanda",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="MultiGol 0-2 1°T + 1-3 2°T",
                odds=1.47,
                outcome="WON"
            ),
            TipsterLegInput(
                match_name="Danimarca vs Portogallo",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="X o GG",
                odds=1.43,
                outcome="WON"
            ),
            TipsterLegInput(
                match_name="Germania vs Serbia",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="OV 1°T + OV 2°T 0.5 0.5",
                odds=1.32,
                outcome="WON"
            ),
        ]
    )
    t1_id = engine.ingest_ticket(ticket_1)
    print(f"✅ Inserito Ticket #1 (ID: {t1_id}) con 3 selezioni vincenti (@2.78).")

    # Ticket 2 (Quella dello screenshot con 6 selezioni @9.10)
    ticket_2 = TipsterTicketInput(
        tipster_name="Tipster 2 - Multipla Volume & Tempi",
        ticket_date="2026-10-01",
        total_odds=9.10,
        status="WON",
        source="SCREENSHOT_MEDIA_1790889022566",
        legs=[
            TipsterLegInput(
                match_name="Irlanda vs Austria",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="U/O 1.5 Cartellini Squadra 1 : OVER",
                odds=1.43,
                outcome="WON"
            ),
            TipsterLegInput(
                match_name="Grecia vs Olanda",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="X2 + U/O 1.5 : X2 + OV",
                odds=1.58,
                outcome="WON"
            ),
            TipsterLegInput(
                match_name="Israele vs Kosovo",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="Doppia Chance: X2",
                odds=1.37,
                outcome="WON"
            ),
            TipsterLegInput(
                match_name="Germania vs Serbia",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="U/O 5.5 Corner Squadra 1(esc.TS) : OVER",
                odds=1.41,
                outcome="WON"
            ),
            TipsterLegInput(
                match_name="Danimarca vs Portogallo",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="U/O 7.5 Tiri in Porta : OVER",
                odds=1.38,
                outcome="WON"
            ),
            TipsterLegInput(
                match_name="Galles vs Norvegia",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="MultiGol 0-2 1°Tempo + 1-3 2°Tempo : SI",
                odds=1.51,
                outcome="WON"
            ),
        ]
    )
    t2_id = engine.ingest_ticket(ticket_2)
    print(f"✅ Inserito Ticket #2 (ID: {t2_id}) con 6 selezioni vincenti (@9.10).")

    # Ingestione delle nostre selezioni perse per confronto statistico
    ticket_lost = TipsterTicketInput(
        tipster_name="BAgent Legacy (Sessione Drawdown)",
        ticket_date="2026-10-01",
        total_odds=11.33,
        status="LOST",
        source="USER_SESSION_01_10_2026",
        legs=[
            TipsterLegInput(
                match_name="Galles vs Norvegia",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="X2 + MultiGol 2-5",
                odds=1.38,
                outcome="LOST" # Vinto dal Galles 2-1 (X2 perso!)
            ),
            TipsterLegInput(
                match_name="Germania vs Serbia",
                tournament="Nations League",
                kickoff_time="2026-10-01 20:45 CEST",
                market_name="1X + MultiGol 2-4",
                odds=1.60,
                outcome="WON" # Finita 2-0
            ),
            TipsterLegInput(
                match_name="Azerbaigian vs Liechtenstein",
                tournament="Nations League",
                kickoff_time="2026-10-01 18:00 CEST",
                market_name="1X2 Corner Tempo 1 : 1",
                odds=1.19,
                outcome="LOST" # 0-0 HT
            ),
        ]
    )
    t3_id = engine.ingest_ticket(ticket_lost)
    print(f"✅ Inserite selezioni perse di confronto (ID: {t3_id}) per calibrare i pesi penalizzanti.")


def print_summary():
    engine = TipsterIntelligenceEngine()
    summary = engine.get_intelligence_summary()

    print("\n" + "=" * 90)
    print("🧠 BAGENT TIPSTER INTELLIGENCE — QUADRO EMPIRICO FAMIGLIE DI MERCATO")
    print("=" * 90)
    print(f"{'Famiglia Mercato':<26} {'Giocate':<9} {'Vinte':<7} {'Perse':<7} {'Win Rate':<10} {'Quota Media':<12} {'Moltiplicatore Efficacia'}")
    print("-" * 90)

    for row in summary:
        fam = row["market_family"]
        tot = row["total_bets"]
        won = row["won_bets"]
        lost = row["lost_bets"]
        wr = row["win_rate"] * 100.0
        avg_odd = row["avg_odds"]
        eff = row["efficacy_weight"]

        star = "🔥" if eff >= 1.25 else ("⭐" if eff >= 1.15 else ("⚠️" if eff < 0.90 else "•"))
        print(f"{fam:<26} {tot:<9} {won:<7} {lost:<7} {wr:>5.1f}%     @{avg_odd:<10.2f} {eff:>5.3f} {star}")

    print("=" * 90)
    print("💡 Nota: I moltiplicatori di efficacia modificano dinamicamente il Balanced Safety Score (BSS)")
    print("   premiando i mercati resilienti al flusso ed escludendo le trappole rigide.\n")


def main():
    parser = argparse.ArgumentParser(description="Tipster Intelligence CLI")
    parser.add_argument("--summary", action="store_true", help="Mostra riepilogo pesi ed efficacia mercati")
    parser.add_argument("--bootstrap-october-01", action="store_true", help="Ingerisci le schedine del 01/10/2026")
    args = parser.parse_args()

    if args.bootstrap_october_01:
        bootstrap_tonight_tickets()
        print_summary()
    elif args.summary:
        print_summary()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
