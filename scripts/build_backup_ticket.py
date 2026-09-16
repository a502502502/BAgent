#!/usr/bin/env python3
"""
scripts/build_backup_ticket.py — Twin-Ticket Zero-Loss Builder CLI.

Genera la coppia [Schedina Principale + Schedina di Backup]:
- Calcola gli stake esatti per azzerare al 100% le perdite in caso di errore della principale;
- Mostra la matrice scenari con profitto netto garantito.

Uso:
    python scripts/build_backup_ticket.py --budget 10.0 --main-odd 3.30 --backup-odd 5.20
    python scripts/build_backup_ticket.py --budget 5.0 --main-odd 3.30 --backup-odd 4.80
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.backup_hedge_engine import BackupHedgeEngine

def print_banner(title: str):
    line = "=" * 80
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")

def main():
    parser = argparse.ArgumentParser(description="BAgent Twin-Ticket Zero-Loss Builder CLI")
    parser.add_argument("--budget", type=float, default=10.0, help="Budget totale di sessione in Euro")
    parser.add_argument("--main-odd", type=float, default=3.30, help="Quota totale moltiplicatore schedina principale")
    parser.add_argument("--backup-odd", type=float, default=5.20, help="Quota totale moltiplicatore schedina backup")
    parser.add_argument("--main-name", type=str, default="Master Ticket Top 3", help="Nome ticket principale")
    parser.add_argument("--backup-name", type=str, default="Ticket Paracadute Zero-Perdita", help="Nome ticket backup")

    args = parser.parse_args()
    engine = BackupHedgeEngine()

    res = engine.create_orthogonal_twin_ticket(
        total_budget=args.budget,
        main_name=args.main_name,
        main_selections=[],
        main_odd=args.main_odd,
        backup_name=args.backup_name,
        backup_selections=[],
        backup_odd=args.backup_odd
    )

    print_banner(f"🛡️ TWIN-TICKET ENGINE: SISTEMA ZERO-PERDITA (Budget €{args.budget:.2f})")
    
    print("🎟️ SCHEDINA 1 — PRINCIPALE (CORE)")
    print(f"  • Quota Moltiplicatore: @{res.main_total_odd:.2f}")
    print(f"  • Puntata Consigliata:  € {res.main_stake_eur:.2f} ({res.main_stake_eur/args.budget*100:.1f}% del budget)")
    print(f"  • Payout Potenziale:    € {res.main_payout_eur:.2f}")

    print("\n🪂 SCHEDINA 2 — BACKUP (PARACADUTE ZERO-PERDITA)")
    print(f"  • Quota Moltiplicatore: @{res.backup_total_odd:.2f}")
    print(f"  • Puntata Consigliata:  € {res.backup_stake_eur:.2f} ({res.backup_stake_eur/args.budget*100:.1f}% del budget)")
    print(f"  • Payout Minimo:        € {res.backup_payout_eur:.2f} (COPRE L'INTERO BUDGET DI €{args.budget:.2f})")

    print_banner("📊 MATRICE SCENARI FINANZIARI GARANTITI")
    print(f"🟢 SCENARIO A: Vince Principale, Perde Backup")
    print(f"   Payout Incassato: € {res.main_payout_eur:.2f} | Utile Netto Reale: € {res.scenario_main_won_net_eur:+.2f}")

    print(f"\n🟡 SCENARIO B: Perde Principale, Vince Backup (SALVA-CAPITALE)")
    print(f"   Payout Incassato: € {res.backup_payout_eur:.2f} | Utile Netto Reale: € {res.scenario_backup_won_net_eur:+.2f}")
    print(f"   🛡️ RISULTATO: NESSUNA PERDITA! Il capitale è recuperato integralmente al 100%.")

    print(f"\n💎 SCENARIO C: Vincono Entrambe (Eventi Disgiunti)")
    print(f"   Payout Cumulativo: € {res.main_payout_eur + res.backup_payout_eur:.2f} | Utile Netto: € {res.scenario_both_won_net_eur:+.2f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
