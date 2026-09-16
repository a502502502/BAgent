#!/usr/bin/env python3
"""
scripts/run_post_mortem.py — Post-Mortem Audit & Tactical Lessons CLI (Pilastro 4).

Consente l'analisi analitica post-partita di eventi conclusi e la consultazione
delle lezioni tattiche memorizzate in bagent.db.

Uso:
    python scripts/run_post_mortem.py --list-lessons
    python scripts/run_post_mortem.py --diagnose "Arsenal vs Brighton" --market "1 + Over 2.5" --odd 1.60 --outcome LOST --goals-ft 1 --goals-ht 0 --red-card 34
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.post_mortem_engine import PostMortemEngine

def print_banner(title: str):
    line = "=" * 75
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")

def main():
    parser = argparse.ArgumentParser(description="BAgent Post-Mortem Audit CLI")
    parser.add_argument("--list-lessons", action="store_true", help="Mostra le lezioni tattiche recenti memorizzate")
    parser.add_argument("--diagnose", type=str, help="Nome match da diagnosticare (es. 'Arsenal vs Brighton')")
    parser.add_argument("--market", type=str, default="Mercato", help="Mercato selezionato")
    parser.add_argument("--odd", type=float, default=1.50, help="Quota scommessa")
    parser.add_argument("--outcome", type=str, choices=["WON", "LOST"], default="LOST", help="Esito finale")
    parser.add_argument("--goals-ft", type=int, default=1, help="Gol totali al 90'")
    parser.add_argument("--goals-ht", type=int, default=0, help="Gol totali al 45'")
    parser.add_argument("--corners", type=int, help="Corner totali")
    parser.add_argument("--shots", type=int, help="Tiri totali")
    parser.add_argument("--red-card", type=int, help="Minuto eventuale cartellino rosso")
    parser.add_argument("--missed-penalty", action="store_true", help="Presenza di rigore fallito")

    args = parser.parse_args()
    engine = PostMortemEngine()

    if args.list_lessons:
        print_banner("🧠 REGISTRO LEZIONI TATTICHE POST-MORTEM")
        lessons = engine.get_recent_tactical_lessons(limit=10)
        if not lessons:
            print("Nessuna lezione tattica memorizzata al momento.")
        else:
            for l in lessons:
                icon = "🟢" if l["outcome"] == "WON" else "🔴"
                print(f"[{l['timestamp'][:19]}] {icon} {l['match_name']} | {l['market_name']} @ {l['odds']:.2f}")
                print(f"  • Causa:  {l['failure_category']} ({l['actual_stats']})")
                print(f"  • Regola: {l['applied_rule']}")
                print(f"  • Lezione: {l['tactical_lesson']}\n")
        return

    if args.diagnose:
        print_banner(f"🔬 DIAGNOSI POST-MORTEM: {args.diagnose}")
        lesson_id = engine.record_post_mortem(
            match_name=args.diagnose,
            market_name=args.market,
            odds=args.odd,
            outcome=args.outcome,
            actual_goals_ft=args.goals_ft,
            actual_goals_ht=args.goals_ht,
            actual_corners=args.corners,
            red_card_minute=args.red_card,
            total_shots=args.shots,
            missed_penalty=args.missed_penalty
        )
        lessons = engine.get_recent_tactical_lessons(limit=1)
        if lessons:
            l = lessons[0]
            print(f"ID Lezione: #{lesson_id}")
            print(f"Esito:       {l['outcome']}")
            print(f"Categoria:   {l['failure_category']}")
            print(f"Statistiche: {l['actual_stats']}")
            print(f"Regola:      {l['applied_rule']}")
            print(f"Lezione:     {l['tactical_lesson']}")
        return

    # Default: mostra lezioni
    print_banner("🧠 REGISTRO LEZIONI TATTICHE POST-MORTEM")
    lessons = engine.get_recent_tactical_lessons(limit=10)
    if not lessons:
        print("Nessuna lezione tattica memorizzata al momento.")
    else:
        for l in lessons:
            icon = "🟢" if l["outcome"] == "WON" else "🔴"
            print(f"[{l['timestamp'][:19]}] {icon} {l['match_name']} | {l['market_name']} @ {l['odds']:.2f}")
            print(f"  • Causa:  {l['failure_category']} ({l['actual_stats']})")
            print(f"  • Regola: {l['applied_rule']}")
            print(f"  • Lezione: {l['tactical_lesson']}\n")

if __name__ == "__main__":
    main()
