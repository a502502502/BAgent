"""
Mostra le statistiche di performance del modello BAgent.

Utilizzo:
    python scripts/show_stats.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.football.prediction_logger import PredictionLogger


def main():
    logger = PredictionLogger()
    pending = logger.pending()
    settled = logger.settled()

    print("\n" + "=" * 60)
    print("  STATISTICHE BAGENT")
    print("=" * 60)
    print(f"  Previsioni totali     : {len(logger.all())}")
    print(f"  Con risultato         : {len(settled)}")
    print(f"  In attesa di risultato: {len(pending)}")

    if not settled:
        print("\n  Nessuna previsione con risultato. Aggiungi i risultati con:")
        print("  python scripts/add_result.py")
        return

    stats = logger.stats()

    print("\n── PERFORMANCE MODELLO ─────────────────────────────────")
    print(f"  Accuracy (esito più prob.) : {stats['accuracy']:.1%}")
    print(f"  Brier Score                : {stats['brier_score']:.4f}  "
          f"({'ottimo' if stats['brier_score'] < 0.20 else 'buono' if stats['brier_score'] < 0.24 else 'da migliorare'})")

    if stats.get("value_bets_placed", 0) > 0:
        print("\n── VALUE BETS ──────────────────────────────────────────")
        print(f"  Scommesse piazzate : {stats['value_bets_placed']}")
        print(f"  Vinte              : {stats['value_bets_won']}")
        acc = stats.get("value_bet_accuracy")
        roi = stats.get("roi_value_bets")
        if acc is not None:
            print(f"  Accuracy           : {acc:.1%}")
        if roi is not None:
            roi_pct = roi * 100
            print(f"  ROI simulato       : {roi_pct:+.1f}%  "
                  f"({'profitto' if roi > 0 else 'perdita'})")
    else:
        print("\n  Nessuna value bet tracciata.")

    print("\n── ULTIME PREVISIONI VALUTATE ──────────────────────────")
    for rec in sorted(settled, key=lambda x: x["match_date"], reverse=True)[:10]:
        adj = rec.get("adjusted_probs", {})
        ph = adj.get("home_win", 0)
        pd_ = adj.get("draw", 0)
        pa  = adj.get("away_win", 0)
        pred = max(("H", ph), ("D", pd_), ("A", pa), key=lambda x: x[1])[0]
        actual = rec["result"]
        ok = "✓" if pred == actual else "✗"
        score_str = ""
        if rec.get("home_goals") is not None:
            score_str = f"  {rec['home_goals']}-{rec['away_goals']}"

        print(f"  {ok} {rec['match_date']}  {rec['home'][:12]:12} vs {rec['away'][:12]:12}"
              f"  pred={pred} actual={actual}{score_str}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
