"""
Aggiunge il risultato reale a una previsione nel log.

Utilizzo:
    python scripts/add_result.py

Mostra le previsioni in sospeso e permette di inserire il risultato.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.football.prediction_logger import PredictionLogger


def main():
    logger = PredictionLogger()
    pending = logger.pending()

    if not pending:
        print("\nNessuna previsione in attesa di risultato.")
        return

    print("\n" + "=" * 60)
    print("  PREVISIONI IN ATTESA DI RISULTATO")
    print("=" * 60)

    for i, p in enumerate(pending):
        adj = p.get("adjusted_probs", {})
        ph = adj.get("home_win", 0)
        pd_ = adj.get("draw", 0)
        pa  = adj.get("away_win", 0)

        vs_count = len(p.get("value_signals", []))

        print(f"\n[{i+1}] ID: {p['id']}  |  {p['match_date']}")
        print(f"    {p['home']} vs {p['away']}")
        print(f"    Prob: H={ph:.1%}  D={pd_:.1%}  A={pa:.1%}")
        if vs_count:
            print(f"    Value bets: {vs_count}")

    print("\n" + "-" * 60)
    print("Inserisci il numero della previsione (o 0 per uscire): ", end="")
    try:
        choice = int(input().strip())
    except (ValueError, EOFError):
        return

    if choice == 0 or choice > len(pending):
        return

    rec = pending[choice - 1]
    print(f"\nPartita: {rec['home']} vs {rec['away']} ({rec['match_date']})")
    print("Risultato [H/D/A]: ", end="")
    try:
        result = input().strip().upper()
    except EOFError:
        return

    if result not in ("H", "D", "A"):
        print("Risultato non valido. Usa H, D o A.")
        return

    print("Gol casa (invio per saltare): ", end="")
    try:
        hg_input = input().strip()
        home_goals = int(hg_input) if hg_input else None
    except (ValueError, EOFError):
        home_goals = None

    print("Gol ospite (invio per saltare): ", end="")
    try:
        ag_input = input().strip()
        away_goals = int(ag_input) if ag_input else None
    except (ValueError, EOFError):
        away_goals = None

    ok = logger.add_result(rec["id"], result, home_goals, away_goals)
    if ok:
        print(f"\n✓ Risultato salvato: {rec['home']} vs {rec['away']} → {result}")
        if home_goals is not None:
            print(f"  Score: {home_goals} - {away_goals}")
    else:
        print("Errore: previsione non trovata.")


if __name__ == "__main__":
    main()
