#!/usr/bin/env python3
"""
scripts/build_verified_ticket.py — Certificatore Rigoroso Schedine BAgent (Regole #40, #41, #42, #43).

Esegue l'audit sequenziale obbligatorio prima di piazzare o proporre qualsiasi ticket:
1. Controllo Roster & Trasferimenti 2026/2027 (DB + API Transfers)
2. Controllo Lista Infortunati / Indisponibili (/injuries)
3. Controllo Formazioni Ufficiali Titolari (/fixtures/lineups)
4. Sesto Senso & Intelligence Tattica (OBBLIGATORIO: rassegna, spogliatoio, trappole)
5. Calcolo Probabilità Reale Coniugata (Poisson & Modelli Tempi)
6. Filtro Edge Matematico Reale (Minimo +4.0%)
7. Filtro Anti-Scadenza 45' (< 1.55)
8. Money Management (Kelly Frazionario calcolato sul Bankroll attuale)

Uso CLI:
    python scripts/build_verified_ticket.py --bankroll 100.0 --demo
"""

from __future__ import annotations
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.strict_ticket_pipeline import StrictTicketPipeline, MarketCandidate
from services.betting.certified_ticket_publisher import audit_and_publish


def run_ticket_audit(
    candidates: list[MarketCandidate],
    current_bankroll: float,
    *,
    send_telegram: bool = False,
    ticket_name: str = "Master Ticket Certificato",
):
    pipeline = StrictTicketPipeline()

    print("\n" + "=" * 85)
    print("🛡️  BAGENT PROTOCOLLO DEI COMANDAMENTI PRE-SCHEDINA CON SESTO SENSO (Regola #41 & #43)")
    print(f"💰  Bankroll Attuale di Riferimento: €{current_bankroll:.2f}")
    print("=" * 85)

    approved_candidates = []
    total_approved_odds = 1.0
    joint_probability = 1.0

    for idx, c in enumerate(candidates, 1):
        print(f"\n[SELEZIONE #{idx}] {c.match_name} ({c.tournament})")
        print(f"   Mercato Proposto: '{c.market_name}' @ quota {c.bookmaker_odd:.2f}")
        if c.player_name:
            print(
                f"   Target Giocatore: {c.player_name} "
                f"(Squadra: {c.team_name or 'N/D'}) | Fixture ID: {c.fixture_id or 'N/D'}"
            )

        rep = pipeline.validate_candidate(c)

        if rep.passed:
            print("   🟢 ESITO: APPROVATO (Tutte le Fasi Superate)")
            print(f"   🧠 Sesto Senso:       {c.sixth_sense_analysis}")
            print(
                f"   📊 Probabilità Reale: {rep.real_probability*100:.1f}% | "
                f"Fair Odd: @{rep.fair_odds:.2f}"
            )
            print(f"   ⭐ Edge Matematico:    {rep.mathematical_edge*100:+.1f}%")
            print(f"   🔬 Dettagli:          {rep.details}")
            approved_candidates.append(c)
            total_approved_odds *= c.bookmaker_odd
            joint_probability *= rep.real_probability
        else:
            print(f"   🔴 ESITO: BLOCCATO ALLA FONTE (Fase {rep.stage_failed})")
            print(f"   ⚠️  Motivo Blocco:    {rep.rejection_reason}")
            if c.sixth_sense_analysis:
                print(f"   🧠 Sesto Senso:       {c.sixth_sense_analysis}")
            if rep.mathematical_edge != 0.0:
                print(
                    f"   📉 Edge Calcolato:    {rep.mathematical_edge*100:+.1f}% "
                    f"(Fair Odd: @{rep.fair_odds:.2f})"
                )

    print("\n" + "=" * 85)
    print("📋 RIEPILOGO FINALE TICKET CERTIFICATO")
    print("=" * 85)
    print(f"• Selezioni Validate / Proposte: {len(approved_candidates)} / {len(candidates)}")

    if len(approved_candidates) < len(candidates):
        print(
            f"🚨 ATTENZIONE: {len(candidates) - len(approved_candidates)} "
            "selezioni sono state SCARTATE perché non conformi alle regole."
        )

    if approved_candidates:
        recommended_stake = pipeline.calculate_recommended_stake(
            current_bankroll=current_bankroll,
            total_odds=total_approved_odds,
            num_selections=len(approved_candidates),
            estimated_prob=joint_probability,
        )
        pot_payout = recommended_stake * total_approved_odds

        print(f"• Quota Totale Valida:           @{total_approved_odds:.2f}")
        print(
            f"• Stake Consigliato (Kelly Frax): €{recommended_stake:.2f} "
            f"({recommended_stake/max(1, current_bankroll)*100:.1f}% del bankroll)"
        )
        print(f"• Vincita Potenziale Stimata:     €{pot_payout:.2f}")
        print("\n✅ TICKET CERTIFICATO, PONDERATO CON SESTO SENSO E PRONTO ALL'USO!")

        if send_telegram:
            pub = audit_and_publish(
                approved_candidates,
                bankroll=current_bankroll,
                ticket_name=ticket_name,
                send_telegram=True,
            )
            if pub.get("telegram_sent"):
                print("📲 Inviato su Telegram con pulsante PRENOTA SU NETWIN (1-Click).")
            else:
                print(f"⚠️  Invio Telegram fallito: {pub.get('error', 'token/chat mancanti?')}")
    else:
        print("\n❌ NESSUNA SELEZIONE HA SUPERATO TUTTI I GATE. TICKET NON GIOCABILE!")
    print("=" * 85 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Audit Pre-Schedina con Protocollo Matematico & Sesto Senso"
    )
    parser.add_argument("--bankroll", type=float, default=100.0, help="Bankroll liquido disponibile")
    parser.add_argument("--file", type=str, help="File JSON con candidati")
    parser.add_argument("--demo", action="store_true", help="Esegui demo con match reali Champions League")
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Dopo certificazione, invia Master Ticket 1-Click su Telegram",
    )
    parser.add_argument("--ticket-name", type=str, default="Master Ticket Certificato")
    args = parser.parse_args()

    if args.demo:
        demo_candidates = [
            MarketCandidate(
                match_name="PSV Eindhoven vs Shakhtar Donetsk",
                tournament="Champions League",
                market_name="1X + Over 1.5",
                bookmaker_odd=1.31,
                xg_home=1.9,
                xg_away=0.8,
                sixth_sense_analysis=(
                    "PSV con forte spinta interna al Philips Stadion ma Shakhtar esperto e "
                    "resiliente. Il mercato 1X+Over 1.5 protegge dall'1-1 e sfrutta le "
                    "transizioni olandesi."
                ),
            ),
            MarketCandidate(
                match_name="Fenerbahce vs AS Roma",
                tournament="Champions League",
                market_name="MultiGol 1-3 Ospite",
                bookmaker_odd=1.30,
                xg_home=1.1,
                xg_away=1.4,
                sixth_sense_analysis=(
                    "Roma di Gasperini con assetto propositivo, produce sempre occasioni "
                    "ma in trasferta a Istanbul non dilaga oltre i 3 gol."
                ),
            ),
            MarketCandidate(
                match_name="Como vs RB Leipzig",
                tournament="Champions League",
                market_name="MultiGol 1-3 Casa",
                bookmaker_odd=1.32,
                xg_home=1.3,
                xg_away=1.5,
                sixth_sense_analysis=(
                    "Entusiasmo storico al Sinigaglia per l'esordio europeo del Como. "
                    "Il Lipsia concede spazi in contropiede ma il Como segna solitamente 1-2 reti."
                ),
            ),
            MarketCandidate(
                match_name="Bayern Monaco vs Bodo Glimt",
                tournament="Champions League",
                market_name="Casa Segna in Entrambi i Tempi",
                bookmaker_odd=1.20,
                estimated_p_1h=0.75,
                estimated_p_2h=0.85,
                is_compound_time_market=True,
                is_intermediate_deadline=True,
                sixth_sense_analysis=(
                    "Bayern con tendenza ad avvio diesel contro blocchi bassi scandinavi. "
                    "Rischio 0-0 al 45' altissimo."
                ),
                sixth_sense_risk_flags=["SLOW_START"],
            ),
            MarketCandidate(
                match_name="Manchester United vs Sabah Masazir",
                tournament="Champions League",
                market_name="Casa Segna in Entrambi i Tempi",
                bookmaker_odd=1.30,
                estimated_p_1h=0.78,
                estimated_p_2h=0.85,
                is_compound_time_market=True,
                is_intermediate_deadline=True,
                sixth_sense_analysis="",
            ),
        ]
        run_ticket_audit(
            demo_candidates,
            args.bankroll,
            send_telegram=args.telegram,
            ticket_name=args.ticket_name,
        )
    elif args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"File {args.file} non trovato.")
            return
        data = json.loads(p.read_text(encoding="utf-8"))
        candidates = [MarketCandidate(**item) for item in data]
        run_ticket_audit(
            candidates,
            args.bankroll,
            send_telegram=args.telegram,
            ticket_name=args.ticket_name,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
