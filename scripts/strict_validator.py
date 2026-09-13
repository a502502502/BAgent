#!/usr/bin/env python3
"""
scripts/strict_validator.py — Hard-Gate Automated Validator (Regole #37-#45).

Questo script è l'autorità suprema di controllo pre-schedina di BAgent.
Nessun mercato, pronostico o schedina può essere proposto all'utente senza aver
prima ottenuto lo stato 'PASSED' (CERTIFICATO ED APPROVATO) da questo motore.

Hard Gates Implementati:
- Gate 0: Divieto 1 o 2 fisso a quota compressa (< 1.65) -> Obbligo mercati protetti (1X, 1X+OV1.5, DNB, MultiGol)
- Gate 0.5 (Regola #45): Filtro Volume Offensivo Corner (>= 18-20 tiri totali squadra a partita)
- Gate 0.75 (Regola #48): Anti-Ceiling Trap (Divieto tetto 3 gol su attacchi devastanti Barça/Bayern/City/Real)
- Gate 0.8 (Regola #49): Anti-Allucinazione Nominale & Formazioni (Divieto memoria parametrica 2024, audit entità DB 2026/27)
- Gate 1-3: Controllo anagrafico 2026/27, indisponibili e formazioni ufficiali
- Gate 4 (Regola #43): Sesto Senso Obbligatorio & Rischio Coppe Europee Infrasettimanali
- Gate 5-6: Calcolo Probabilità Reale & Edge Matematico Reale (>= +4.0%)
- Gate 7: Filtro Anti-Scadenza 45' a quota compressa (< 1.55)
- Gate 8: Money Management (Max 3-4 selezioni per ticket, Max 8% bankroll per ticket)

Uso:
    python scripts/strict_validator.py --demo
    python scripts/strict_validator.py --ticket-json '<json>'
    python scripts/strict_validator.py --match "Lecce vs Monza" --market "1X + MultiGol 1-5" --odd 1.35 --p-real 0.82 --sixth-sense "Lecce solido in casa, Monza difensivo"
"""

from __future__ import annotations
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.strict_ticket_pipeline import (
    StrictTicketPipeline,
    MarketCandidate,
    ValidationReport,
    TicketValidationReport
)

def print_banner(title: str, char: str = "="):
    line = char * 85
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")

def validate_selection_cli(candidate: MarketCandidate) -> ValidationReport:
    pipeline = StrictTicketPipeline()
    return pipeline.validate_candidate(candidate)

def format_report(report: ValidationReport) -> str:
    c = report.candidate
    out = []
    out.append(f"• Evento: {c.match_name} ({c.tournament or 'Lega'})")
    out.append(f"• Mercato Proposto: '{c.market_name}' @ {c.bookmaker_odd:.2f}")
    if c.market_type:
        out.append(f"  Tipologia Mercato: {c.market_type}")
    if c.team_avg_shots is not None:
        out.append(f"  Volume Balistico Registrato: {c.team_avg_shots:.1f} tiri/partita")
    if c.has_upcoming_midweek_cup:
        out.append(f"  ⚠️  Impegno Europeo Infrasettimanale Segnalato (Champions/Europa League)")

    if report.passed:
        out.append(f"  ESITO: 🟢 CERTIFICATO ED APPROVATO")
        out.append(f"  Probabilità Reale: {report.real_probability*100:.1f}% | Fair Odd: @{report.fair_odds:.2f}")
        out.append(f"  Edge Matematico:    {report.mathematical_edge*100:+.1f}%")
        out.append(f"  Sesto Senso:        {c.sixth_sense_analysis}")
    else:
        out.append(f"  ESITO: 🔴 BOCCIATO TASSATIVAMENTE (Gate {report.stage_failed})")
        out.append(f"  Motivo Blocco:     {report.rejection_reason}")
        if report.mathematical_edge != 0.0:
            out.append(f"  Edge Calcolato:    {report.mathematical_edge*100:+.1f}% (Fair: @{report.fair_odds:.2f})")
    return "\n".join(out)

def validate_full_ticket(candidates: List[MarketCandidate], bankroll: float, proposed_stake: Optional[float] = None) -> TicketValidationReport:
    pipeline = StrictTicketPipeline()
    return pipeline.validate_ticket(candidates, current_bankroll=bankroll, proposed_stake=proposed_stake)

def format_ticket_report(ticket_report: TicketValidationReport) -> str:
    lines = []
    lines.append("=" * 85)
    lines.append("🛡️  BAGENT STRICT VALIDATOR — AUDIT CERTIFICAZIONE TICKET PRE-SCHEDINA")
    lines.append("=" * 85)

    if ticket_report.passed:
        lines.append(f"STATUS GLOBALE: 🟢 CERTIFICATO ED APPROVATO (PRONTO PER LA GIOCATA)")
    else:
        lines.append(f"STATUS GLOBALE: 🔴 BOCCIATO TASSATIVAMENTE (VIOLAZIONE PROTOCOLLI)")

    lines.append(f"• Numero Selezioni: {ticket_report.num_selections} (Limite max: 4)")
    lines.append(f"• Quota Complessiva Valida: @{ticket_report.total_odds:.2f}")
    lines.append(f"• Stake Consigliato: €{ticket_report.recommended_stake:.2f} ({ticket_report.stake_percentage:.1f}% del bankroll)")

    lines.append("\n" + "-" * 85)
    lines.append("DETTAGLIO SELEZIONI:")
    lines.append("-" * 85)
    for idx, rep in enumerate(ticket_report.legs_reports, 1):
        lines.append(f"\n[SELEZIONE #{idx}]")
        lines.append(format_report(rep))

    if not ticket_report.passed:
        lines.append("\n" + "!" * 85)
        lines.append("🛑 MOTIVI BLOCCANTI RILEVATI DAL VALIDATORE:")
        lines.append("!" * 85)
        for r in ticket_report.rejection_reasons:
            lines.append(f"❌ {r}")
        lines.append("\nQUESTO TICKET È BLOCCATO. È VIETATO PROPORLO ALL'UTENTE SENZA CORREZIONI.")
    else:
        lines.append("\n" + "=" * 85)
        lines.append("✅ TUTTI I CONTROLLI SUPERATI CON SUCCESSO. IL TICKET È MATEMATICAMENTE E TATTICAMENTE BLINDATO.")
        lines.append("=" * 85)

    return "\n".join(lines)

def run_demo():
    print_banner("ESECUZIONE AUDIT DI PROVA SUI CASI LIMITE DI OGGI E DOMENICA", "=")
    
    # Test 1: Athletic Bilbao 1 Fisso @ 1.38 (Quello saltato oggi!)
    c1 = MarketCandidate(
        match_name="Athletic Bilbao vs Elche",
        tournament="La Liga",
        market_name="1 Fisso",
        bookmaker_odd=1.38,
        market_type="1X2",
        sixth_sense_analysis="Athletic favoritissimo al San Mames contro neopromossa.",
        estimated_p_90=0.74
    )

    # Test 2: Liverpool Corner (Quello saltato oggi!)
    c2 = MarketCandidate(
        match_name="Liverpool vs Fulham",
        tournament="Premier League",
        market_name="1 Corner",
        bookmaker_odd=1.40,
        market_type="CORNER",
        team_avg_shots=11.2, # Sotto 18!
        sixth_sense_analysis="Liverpool attacca ad Anfield ma Fulham si difende ordinato.",
        estimated_p_90=0.75
    )

    # Test 3: Arsenal MultiGol 1° Tempo prima della Champions (Quello saltato stasera!)
    c3 = MarketCandidate(
        match_name="Sunderland vs Arsenal",
        tournament="Premier League",
        market_name="MultiGol 1-3 1°Tempo",
        bookmaker_odd=1.43,
        market_type="FIRST_HALF",
        has_upcoming_midweek_cup=True,
        is_first_half_only=True,
        is_intermediate_deadline=True,
        sixth_sense_analysis="Arsenal gioca col Sunderland prima della Champions League.",
        sixth_sense_risk_flags=["MIDWEEK_CUP", "SLOW_START"],
        estimated_p_1h=0.68
    )

    # Test 4: Selezione Protetta Valida per Domenica (Lecce vs Monza 1X + MultiGol 1-5)
    c4 = MarketCandidate(
        match_name="Lecce vs Monza",
        tournament="Serie A",
        market_name="1X + MultiGol 1-5",
        bookmaker_odd=1.35,
        market_type="COMBO",
        team_avg_shots=14.0,
        has_upcoming_midweek_cup=False,
        sixth_sense_analysis="Lecce al Via del Mare concede pochissimo a squadre di pari livello; Monza gioca blocco basso.",
        estimated_p_90=0.83
    )

    candidates = [c1, c2, c3, c4]
    ticket_rep = validate_full_ticket(candidates, bankroll=100.0, proposed_stake=10.0)
    print(format_ticket_report(ticket_rep))

def main():
    parser = argparse.ArgumentParser(description="Strict Validator di BAgent — Filtro Rigoroso Pre-Schedina")
    parser.add_argument("--demo", action="store_true", help="Esegui audit di prova sui casi storici ed evoluti")
    parser.add_argument("--bankroll", type=float, default=100.0, help="Bankroll liquido attuale in euro")
    parser.add_argument("--stake", type=float, default=None, help="Stake proposto in euro")
    parser.add_argument("--match", type=str, help="Nome della partita")
    parser.add_argument("--market", type=str, help="Nome del mercato proposto")
    parser.add_argument("--odd", type=float, help="Quota bookmaker")
    parser.add_argument("--type", type=str, default="", help="Tipologia mercato (1X2, CORNER, FIRST_HALF, COMBO, GOALS)")
    parser.add_argument("--shots", type=float, default=None, help="Media tiri registrata della squadra (per corner)")
    parser.add_argument("--midweek-cup", action="store_true", help="Squadra impegnata in coppe europee a breve")
    parser.add_argument("--p-real", type=float, default=None, help="Probabilità reale stimata Poisson/modello (0.0-1.0)")
    parser.add_argument("--first-half", action="store_true", help="Mercato limitato al 1° tempo")
    parser.add_argument("--sixth-sense", type=str, default="", help="Analisi Sesto Senso obbligatoria")
    parser.add_argument("--ticket-json", type=str, help="JSON array con candidati del ticket completo")

    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    if args.ticket_json:
        try:
            data = json.loads(args.ticket_json)
            candidates = []
            for item in data:
                c = MarketCandidate(
                    match_name=item["match_name"],
                    tournament=item.get("tournament", ""),
                    market_name=item["market_name"],
                    bookmaker_odd=float(item["bookmaker_odd"]),
                    market_type=item.get("market_type", ""),
                    team_avg_shots=float(item["team_avg_shots"]) if "team_avg_shots" in item else None,
                    has_upcoming_midweek_cup=bool(item.get("has_upcoming_midweek_cup", False)),
                    is_first_half_only=bool(item.get("is_first_half_only", False)),
                    is_intermediate_deadline=bool(item.get("is_intermediate_deadline", False)),
                    is_compound_time_market=bool(item.get("is_compound_time_market", False)),
                    sixth_sense_analysis=item.get("sixth_sense_analysis", ""),
                    sixth_sense_risk_flags=item.get("sixth_sense_risk_flags", []),
                    estimated_p_90=float(item["estimated_p_90"]) if "estimated_p_90" in item else None,
                    estimated_p_1h=float(item.get("estimated_p_1h", 0.50)),
                    estimated_p_2h=float(item.get("estimated_p_2h", 0.60)),
                    player_name=item.get("player_name"),
                    team_name=item.get("team_name"),
                    fixture_id=item.get("fixture_id")
                )
                candidates.append(c)

            res = validate_full_ticket(candidates, bankroll=args.bankroll, proposed_stake=args.stake)
            print(format_ticket_report(res))
            sys.exit(0 if res.passed else 1)
        except Exception as e:
            print(f"Errore parsing ticket JSON: {e}", file=sys.stderr)
            sys.exit(2)

    if args.match and args.market and args.odd:
        c = MarketCandidate(
            match_name=args.match,
            tournament="",
            market_name=args.market,
            bookmaker_odd=args.odd,
            market_type=args.type,
            team_avg_shots=args.shots,
            has_upcoming_midweek_cup=args.midweek_cup,
            is_first_half_only=args.first_half,
            is_intermediate_deadline=args.first_half,
            sixth_sense_analysis=args.sixth_sense,
            estimated_p_90=args.p_real
        )
        rep = validate_selection_cli(c)
        print(format_report(rep))
        sys.exit(0 if rep.passed else 1)

    parser.print_help()

if __name__ == "__main__":
    main()
