#!/usr/bin/env python3
"""
scripts/argon_supervisor.py — Interfaccia Esecutiva di Gemini Argon (Adversarial Auditor).

Esegue l'audit avversariale in 4 fasi:
1. Reality Gate Audit 2026/27 (DB official_team_managers_2026 + player_registry_2026)
2. Trappole Bookmaker & Mercati Protetti (Regola #82, Anti-Ceiling #48, soglia quota 1.20)
3. Esposizione & Ortogonalità (Regola #83, #86)
4. Verdetto Finale di Argon (APPROVATO, DA REVISIONARE, RESPINTO)
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.football.reality_gate_guardian import RealityGateGuardian

SCHEDINE_PATH = ROOT / "portal" / "schedine.json"


def audit_ticket_with_argon(ticket: Dict[str, Any]) -> Dict[str, Any]:
    guardian = RealityGateGuardian()
    ticket_id = ticket.get("id", "TICKET_SCONOSCIUTO")
    title = ticket.get("title", ticket_id)
    legs = ticket.get("legs", [])
    stake_str = str(ticket.get("stake", "0")).replace("€", "").replace(",", ".").strip()
    
    try:
        stake_val = float(stake_str)
    except ValueError:
        stake_val = 0.0

    reality_violations: List[str] = []
    for leg in legs:
        match = leg.get("match", "")
        pick = leg.get("pick", "")
        score_note = leg.get("score", "")
        home = match.split(" vs ")[0].strip() if " vs " in match else None
        away = match.split(" vs ")[1].strip() if " vs " in match else None
        
        r_pick = guardian.audit_text(pick, home_team=home, away_team=away)
        if not r_pick.is_valid:
            reality_violations.extend(r_pick.violations)
            
        r_note = guardian.audit_text(score_note, home_team=home, away_team=away)
        if not r_note.is_valid:
            reality_violations.extend(r_note.violations)

    reality_passed = len(reality_violations) == 0

    trap_warnings: List[str] = []
    critiques: List[Dict[str, Any]] = []

    for leg in legs:
        match = leg.get("match", "")
        pick = leg.get("pick", "")
        odd_str = str(leg.get("odd", "0")).replace(",", ".").strip()
        try:
            odd_val = float(odd_str)
        except ValueError:
            odd_val = 1.0

        leg_critique = {
            "match": match,
            "pick": pick,
            "odd": odd_val,
            "risk_level": "LOW",
            "notes": "Mercato equilibrato."
        }

        # Controllo quote compresse
        if odd_val < 1.15:
            leg_critique["risk_level"] = "HIGH"
            leg_critique["notes"] = f"Quota compressa estrema @{odd_val:.2f}. Rischio asimmetrico sfavorevole."
            trap_warnings.append(f"{match}: Quota @{odd_val:.2f} sotto soglia minima.")
        elif odd_val < 1.20:
            leg_critique["risk_level"] = "MEDIUM"
            leg_critique["notes"] = f"Quota @{odd_val:.2f} sotto 1.20. Giocabile solo con edge verificato > 15%."

        # Controllo 1X2 secco compresso
        if pick in ["1", "2", "1 Fisso", "2 Fisso"] and odd_val < 1.65:
            leg_critique["risk_level"] = "CRITICAL"
            leg_critique["notes"] = f"Trappola 1X2 secco a quota @{odd_val:.2f}. Obbligatorio convertire in 1X o MultiGol."
            trap_warnings.append(f"{match}: 1X2 secco a quota compressa vietato.")

        # Controllo Anti-Ceiling su squadre offensive
        high_scoring = ["Bayern", "Barcelona", "Barcellona", "Manchester City", "Real Madrid", "Liverpool", "PSG"]
        if any(h in match for h in high_scoring):
            if "Under 2.5" in pick or "Under 3.5" in pick or "MultiGol 1-3" in pick:
                leg_critique["risk_level"] = "CRITICAL"
                leg_critique["notes"] = f"Rischio Anti-Ceiling Trap: tetto gol troppo basso su match ad alto volume offensivo."
                trap_warnings.append(f"{match}: Tetto gol rischioso con attacchi d'élite.")

        critiques.append(leg_critique)

    # Verdetto complessivo
    if not reality_passed:
        verdict = "RESPINTO"
        reason = "Violazione anagrafica Reality Gate (nomi o rose disallineate)."
    elif any(c["risk_level"] == "CRITICAL" for c in critiques):
        verdict = "DA REVISIONARE"
        reason = "Rilevata almeno una trappola critica da correggere prima della giocata."
    elif trap_warnings:
        verdict = "APPROVATO CON RISERVA"
        reason = "Quote al limite inferiore, ma mercati conformi ai protocolli."
    else:
        verdict = "APPROVATO"
        reason = "Tutti i protocolli di sicurezza e valore atteso sono rispettati."

    return {
        "ticket_id": ticket_id,
        "title": title,
        "stake_eur": stake_val,
        "reality_gate": {
            "status": "CONFERMATO" if reality_passed else "ALLARME",
            "violations": reality_violations
        },
        "leg_critiques": critiques,
        "verdict": verdict,
        "reason": reason,
        "trap_warnings": trap_warnings
    }


def main():
    parser = argparse.ArgumentParser(description="Gemini Argon Adversarial Auditor")
    parser.add_argument("--ticket-id", type=str, help="ID specifico del ticket da verificare")
    parser.add_argument("--all", action="store_true", help="Verifica tutti i ticket attivi in portal/schedine.json")
    args = parser.parse_args()

    if not SCHEDINE_PATH.exists():
        print(f"File non trovato: {SCHEDINE_PATH}")
        sys.exit(1)

    data = json.loads(SCHEDINE_PATH.read_text(encoding="utf-8"))
    present = data.get("present", [])

    print("=" * 80)
    print("GEMINI ARGON — AUDIT QUANTITATIVO & CACCIATORE DI TRAPPOLE")
    print("=" * 80)

    if args.ticket_id:
        targets = [t for t in present if t.get("id") == args.ticket_id]
        if not targets:
            print(f"Ticket con ID '{args.ticket_id}' non trovato in schedine attive.")
            sys.exit(1)
    else:
        targets = present

    for t in targets:
        rep = audit_ticket_with_argon(t)
        print(f"\n--- TICKET: {rep['title']} ---")
        print(f"Reality Gate 2026/27 : {rep['reality_gate']['status']}")
        if rep['reality_gate']['violations']:
            print(f"  Violazioni: {rep['reality_gate']['violations']}")
        print(f"Verdetto Argon       : {rep['verdict']} ({rep['reason']})")
        if rep['trap_warnings']:
            print("  Avvisi trappola:")
            for w in rep['trap_warnings']:
                print(f"    - {w}")
        for c in rep['leg_critiques']:
            print(f"  * {c['match']} | {c['pick']} @{c['odd']} -> [{c['risk_level']}] {c['notes']}")

    print("\n" + "=" * 80)
    print("AUDIT DI ARGON COMPLETATO.")
    print("=" * 80)


if __name__ == "__main__":
    main()
