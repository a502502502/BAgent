"""
Analisi tennis — BAgent.

Utilizzo:
    python scripts/analyze_tennis.py

Inserire i match nella lista MATCHES con:
  - player1/player2: nome del giocatore
  - player1_rank/player2_rank: ranking ATP/WTA corrente
  - surface: 'clay' | 'grass' | 'hard' | 'indoor'
  - best_of: 3 (default) o 5 (Slam, Davis)
  - h2h: (vittorie p1, vittorie p2) — opzionale
  - p1_surface_factor/p2_surface_factor: aggiustamento superficie manuale (1.0 = neutro)
    Esempi: Nadal su terra → 1.3, Federer su erba → 1.2
  - market_odds: quote bookmaker {player1, player2, over_2_5_sets, under_2_5_sets, ...}
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tennis.sixth_sense.engine import TennisEngine

# ─── CONFIGURA I MATCH QUI ───────────────────────────────────────────────────

MATCHES = [
    {
        "player1":      "Carlos Alcaraz",
        "player1_rank": 2,
        "player2":      "Jannik Sinner",
        "player2_rank": 1,
        "surface":      "hard",
        "best_of":      3,
        "h2h":          (3, 5),          # Alcaraz 3 vittorie, Sinner 5
        "p1_surface_factor": 1.0,
        "p2_surface_factor": 1.1,        # Sinner leggermente favorito su hard
        "market_odds":  {
            "player1":        1.90,
            "player2":        1.90,
            "over_2_5_sets":  1.75,
            "under_2_5_sets": 2.05,
        },
    },
    {
        "player1":      "Iga Swiatek",
        "player1_rank": 1,
        "player2":      "Aryna Sabalenka",
        "player2_rank": 2,
        "surface":      "clay",
        "best_of":      3,
        "h2h":          (11, 6),
        "p1_surface_factor": 1.25,       # Swiatek dominante su terra
        "p2_surface_factor": 1.0,
        "market_odds":  {
            "player1":        1.55,
            "player2":        2.50,
            "over_2_5_sets":  1.85,
            "under_2_5_sets": 1.90,
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────


def main():
    engine = TennisEngine(min_edge=0.05)

    for m in MATCHES:
        print(f"\n{'='*60}")
        print(f"  Analisi tennis: {m['player1']} vs {m['player2']}")
        print(f"{'='*60}")

        result = engine.analyze(
            player1=m["player1"],
            player1_rank=m["player1_rank"],
            player2=m["player2"],
            player2_rank=m["player2_rank"],
            surface=m.get("surface", "hard"),
            best_of=m.get("best_of", 3),
            h2h=m.get("h2h"),
            p1_surface_factor=m.get("p1_surface_factor", 1.0),
            p2_surface_factor=m.get("p2_surface_factor", 1.0),
            market_odds=m.get("market_odds"),
            verbose=True,
        )

        print(result.report())

    # Riepilogo multipla (solo vincitore match)
    print(f"\n{'='*60}")
    print("  RIEPILOGO — SEGNALI TENNIS")
    print(f"{'='*60}")

    engine2 = TennisEngine(min_edge=0.0)
    for m in MATCHES:
        r = engine2.analyze(
            player1=m["player1"], player1_rank=m["player1_rank"],
            player2=m["player2"], player2_rank=m["player2_rank"],
            surface=m.get("surface", "hard"), best_of=m.get("best_of", 3),
            h2h=m.get("h2h"),
            p1_surface_factor=m.get("p1_surface_factor", 1.0),
            p2_surface_factor=m.get("p2_surface_factor", 1.0),
            market_odds=m.get("market_odds"),
        )

        p1p = r.win_probs["player1"]
        p2p = r.win_probs["player2"]
        odds = m.get("market_odds", {})
        p1o  = odds.get("player1")
        p2o  = odds.get("player2")

        best = None
        if p1o:
            e1 = p1p - 1/p1o
            best = (m["player1"], p1p, p1o, e1)
        if p2o:
            e2 = p2p - 1/p2o
            if best is None or e2 > best[3]:
                best = (m["player2"], p2p, p2o, e2)

        if best:
            name, prob, odd, edge = best
            edge_str = f"+{edge:.1%}" if edge >= 0 else f"{edge:.1%}"
            print(f"  {m['player1']} vs {m['player2']}")
            print(f"    Selezione: {name:<25} quota {odd}  nostra {prob:.1%}  edge {edge_str}")


if __name__ == "__main__":
    main()
