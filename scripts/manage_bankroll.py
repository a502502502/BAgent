#!/usr/bin/env python3
"""
scripts/manage_bankroll.py — Bankroll Ledger & P&L Tracker CLI (Pilastro 2).

Consente la gestione scientifica e integrata del conto scommesse di BAgent:
- Visualizzazione saldo corrente, storico transazioni e metriche di resa (Yield%, Win Rate%, ROI);
- Aggiornamento manuale del capitale o registrazione vincite/rimborsi;
- Report delle performance disaggregate per mercato.

Uso:
    python scripts/manage_bankroll.py --status
    python scripts/manage_bankroll.py --set-bankroll 37.32 --reason "Allineamento conto Netwin"
    python scripts/manage_bankroll.py --adjust +12.50 --reason "Vincita Ticket Europa League"
    python scripts/manage_bankroll.py --history
    python scripts/manage_bankroll.py --markets
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.database.performance_tracker import PerformanceTracker

def print_banner(title: str):
    line = "=" * 70
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")

def main():
    parser = argparse.ArgumentParser(description="BAgent Bankroll Ledger CLI")
    parser.add_argument("--status", action="store_true", help="Mostra il saldo corrente e riassunto conto")
    parser.add_argument("--set-bankroll", type=float, help="Imposta un nuovo valore assoluto per il saldo del conto")
    parser.add_argument("--adjust", type=float, help="Aggiunge (+) o sottrae (-) un importo dal conto")
    parser.add_argument("--reason", type=str, default="MANUAL_ADJUSTMENT", help="Motivazione della modifica del saldo")
    parser.add_argument("--history", action="store_true", help="Mostra le ultime transazioni del bankroll")
    parser.add_argument("--markets", action="store_true", help="Mostra le performance per categoria di mercato")
    
    args = parser.parse_args()
    tracker = PerformanceTracker()

    if args.set_bankroll is not None:
        new_b = tracker.set_bankroll(args.set_bankroll, reason=args.reason)
        print_banner("💰 AGGIORNAMENTO BANKROLL ESEGUITO")
        print(f"Nuovo Saldo Registrato: € {new_b:.2f}")
        print(f"Motivazione:            {args.reason}")
        return

    if args.adjust is not None:
        new_b = tracker.adjust_bankroll(args.adjust, reason=args.reason)
        print_banner("💸 VARIAZIONE BANKROLL REGISTRATA")
        print(f"Variazione Applicata:   € {args.adjust:+.2f}")
        print(f"Nuovo Saldo Totale:     € {new_b:.2f}")
        print(f"Motivazione:            {args.reason}")
        return

    if args.history:
        print_banner("📜 STORICO TRANSAZIONI BANKROLL")
        with tracker._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bankroll_history ORDER BY id DESC LIMIT 15")
            rows = cursor.fetchall()
            if not rows:
                print("Nessuna transazione registrata.")
            else:
                for r in rows:
                    print(f"[{r['timestamp'][:19]}] Saldo: €{r['balance_eur']:6.2f} | Δ: {r['change_eur']:+6.2f} | {r['reason']}")
        return

    if args.markets:
        print_banner("📊 PERFORMANCE PER CATEGORIA DI MERCATO")
        metrics = tracker.get_market_analytics()
        if not metrics:
            print("Nessun dato storico archiviato nelle selezioni.")
        else:
            print(f"{'Categoria':<18} | {'Bets':<5} | {'W-L':<6} | {'Win%':<7} | {'Yield%':<8} | {'Verdetto'}")
            print("-" * 70)
            for m in metrics:
                wl = f"{m.won_bets}-{m.lost_bets}"
                print(f"{m.category:<18} | {m.total_bets:<5} | {wl:<6} | {m.win_rate_pct:5.1f}% | {m.yield_roi_pct:+6.1f}% | {m.verdict}")
        return

    # Default: mostra status
    curr = tracker.get_current_bankroll()
    summary = tracker.get_global_ledger_summary()

    print_banner("💼 BAGENT BANKROLL & P&L DASHBOARD")
    print(f"  • Saldo Corrente Disponibile:  € {curr:.2f}")
    print(f"  • Ticket Totali Registrati:    {summary['total_tickets']}")
    print(f"  • Ticket Vinti / Persi:        {summary['won_tickets']} Vinti / {summary['lost_tickets']} Persi (Win Rate: {summary['win_rate_pct']}%)")
    print(f"  • Volume Totale Giocato:       € {summary['total_staked_eur']:.2f}")
    print(f"  • Payout Incassato:            € {summary['total_payout_eur']:.2f}")
    print(f"  • Profitto Netto Complessivo:  € {summary['net_profit_eur']:+.2f}")
    print(f"  • Resa Storica (Yield%):       {summary['yield_pct']:+.2f}%")
    print("=" * 70)

if __name__ == "__main__":
    main()
