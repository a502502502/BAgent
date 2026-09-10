#!/usr/bin/env python3
"""
verify_squad_control.py — Tool Ufficiale Controllo Rose, Trasferimenti, Assenze e Distinte (Regole #37, #38, #40).

Utilizzo:
    # 1. Verifica rosa e trasferimenti
    python scripts/verify_squad_control.py --player "Muriqi" --team "Fenerbahce"
    python scripts/verify_squad_control.py --player "Lewandowski" --team "Barcelona"

    # 2. Audit completo match (formazioni ufficiali + lista infortunati/indisponibili per entrambe le squadre)
    python scripts/verify_squad_control.py --fixture 1635659

    # 3. Audit singolo giocatore per un match specifico
    python scripts/verify_squad_control.py --player "Pellegrini" --team "Roma" --fixture 1635659
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.football.squad_absence_checker import SquadAbsenceChecker, normalize

def inspect_fixture(checker: SquadAbsenceChecker, fixture_id: int):
    print(f"\n=======================================================")
    print(f"🏟️ AUDIT UFFICIALE MATCH & ASSENZE — Fixture #{fixture_id}")
    print(f"=======================================================")

    # 1. Infortuni & Assenze
    injuries = checker.check_fixture_injuries(fixture_id)
    print(f"\n🏥 LISTA INFORTUNI & INDISPONIBILI ({len(injuries)} riscontrati):")
    if not injuries:
        print("   ✅ Nessun infortunato segnalato a referto.")
    else:
        by_team = {}
        for inj in injuries:
            t = inj.get("team", {}).get("name", "Generale")
            p = inj.get("player", {})
            p_name = p.get("name", "Sconosciuto")
            reason = p.get("reason") or p.get("type", "Indisponibile")
            by_team.setdefault(t, []).append(f"• {p_name} ({reason})")

        for t_name, player_list in by_team.items():
            print(f"   🔴 {t_name}:")
            for line in player_list:
                print(f"      {line}")

    # 2. Formazioni Ufficiali
    res = checker._fetch_api("fixtures", {"id": fixture_id})
    if not res:
        print("\n❌ Dati partita non disponibili.")
        return

    f = res[0]
    lineups = f.get("lineups", [])
    if not lineups:
        print("\n⏳ Distinte ufficiali NON ancora depositate (Regola #37: Zero Player Props finché non sono ufficiali).")
        print("=======================================================\n")
        return

    print("\n📋 FORMAZIONI UFFICIALI DEPOSITATE:")
    for team_lineup in lineups:
        t_name = team_lineup.get("team", {}).get("name")
        formation = team_lineup.get("formation")
        coach = team_lineup.get("coach", {}).get("name")
        starters = team_lineup.get("startXI", [])
        subs = team_lineup.get("substitutes", [])
        print(f"\n   ⚽ {t_name} (Modulo: {formation} | Coach: {coach}):")
        print(f"      ⭐ TITOLARI ({len(starters)}):")
        for item in starters:
            p = item.get("player", {})
            print(f"         • #{p.get('number', '-')} {p.get('name')} ({p.get('pos')})")
        print(f"      🪑 PANCHINA ({len(subs)}):")
        for item in subs[:5]:
            p = item.get("player", {})
            print(f"         • #{p.get('number', '-')} {p.get('name')} ({p.get('pos')})")
        if len(subs) > 5:
            print(f"         ... altri {len(subs)-5} in panchina")

    print("\n=======================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Tool Ufficiale Verifica Rose, Assenze e Distinte (BAgent)")
    parser.add_argument("--player", default="", help="Nome del giocatore")
    parser.add_argument("--team", default="", help="Nome della squadra")
    parser.add_argument("--fixture", type=int, help="ID Fixture per formazioni e infortuni")
    args = parser.parse_args()

    checker = SquadAbsenceChecker()

    if args.player and args.team:
        print(f"\n🛡️ AVVIO AUDIT GIOCATORE: '{args.player}' @ '{args.team}' (Fixture: {args.fixture or 'Non specificata'})...")
        report = checker.full_player_audit(args.player, args.team, args.fixture)
        print("-------------------------------------------------------")
        print(f"• Giocatore:         {report.player_name}")
        print(f"• Squadra Verificata: {report.team_name}")
        print(f"• Tesserato 2026/27:  {'SÌ ✅' if report.in_squad else 'NO ❌ (Attuale: ' + report.current_actual_team + ')'}")
        print(f"• Infortuni/Assenze:  {'SÌ 🚨 (' + report.injury_reason + ')' if report.is_injured_or_suspended else 'NESSUNA ✅'}")
        print(f"• Stato Distinta:     {report.lineup_status}")
        print(f"• Giocabile Player:   {'AUTORIZZATO ⭐' if report.can_bet_player_prop else 'VIETATO / BLOCCATO 🛑'}")
        if report.rejection_reason:
            print(f"• Motivo Blocco:      {report.rejection_reason}")
        print("-------------------------------------------------------\n")
        sys.exit(0 if report.can_bet_player_prop else 1)

    elif args.fixture:
        inspect_fixture(checker, args.fixture)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
