"""
tennis_schedina.py — Genera tabella scommesse tennis con edge e Sesto Senso.

Usa le stesse regole del calcio:
  - Edge = (probabilità × quota) - 1
  - Rimuove pick con edge negativo
  - Rimuove pick con quota < 1.20
  - Sesto Senso automatico per ogni partita

Utilizzo:
    python scripts/tennis_schedina.py

Aggiungere partite nella lista MATCHES qui sotto.

Mercati disponibili:
    P1     = vittoria player1/team1
    P2     = vittoria player2/team2
    O2.5S  = over 2.5 set
    U2.5S  = under 2.5 set
    O3.5S  = over 3.5 set (best of 5)
    U3.5S  = under 3.5 set (best of 5)
    O4.5S  = over 4.5 set (best of 5)
    U4.5S  = under 4.5 set (best of 5)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

def _load_env():
    env = ROOT / ".env"
    if not env.exists(): return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        import os
        k, _, v = line.partition("=")
        if k.strip() and k.strip() not in __import__("os").environ:
            __import__("os").environ[k.strip()] = v.strip()
_load_env()

from services.tennis.engine import TennisEngine

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURA LE PARTITE DI OGGI
# ══════════════════════════════════════════════════════════════════════════════

MATCHES = [
    # Esempio singolare ATP
    {
        "type":        "singles",
        "player1":     "Carlos Alcaraz",
        "player1_rank": 2,
        "player2":     "Jannik Sinner",
        "player2_rank": 1,
        "surface":     "hard",
        "best_of":     3,
        "tournament":  "Cincinnati Masters",
        "market_odds": {
            "player1":      1.85,
            "player2":      2.00,
            "over_2_5_sets":  1.90,
            "under_2_5_sets": 1.85,
        },
    },
    # Esempio doppio
    # {
    #     "type":           "doubles",
    #     "team1":          ("M. Arevalo", "M. Pavić"),
    #     "team1_avg_rank": 12,
    #     "team2":          ("O. Luz", "R. Matos"),
    #     "team2_avg_rank": 35,
    #     "surface":        "hard",
    #     "best_of":        3,
    #     "tournament":     "Cincinnati Masters",
    #     "market_odds": {
    #         "player1": 1.60,
    #         "player2": 2.30,
    #         "over_2_5_sets": 1.75,
    #     },
    # },
]

# Soglia minima quota (pick sotto questa soglia vengono rimossi)
MIN_QUOTA = 1.20
MIN_EDGE  = 0.0   # edge minimo (0 = mostra tutto, usa valori negativi per mostrare anche watch)

# ══════════════════════════════════════════════════════════════════════════════

def edge(prob: float, quota: float) -> float:
    return prob * quota - 1

def run():
    engine = TennisEngine(min_edge=0.01)
    all_picks = []

    for m in MATCHES:
        print(f"\n{'='*62}")

        if m["type"] == "singles":
            result = engine.analyze(
                player1=m["player1"],
                player1_rank=m["player1_rank"],
                player2=m["player2"],
                player2_rank=m["player2_rank"],
                surface=m.get("surface", "hard"),
                best_of=m.get("best_of", 3),
                tournament=m.get("tournament", ""),
                market_odds=m.get("market_odds"),
                include_sixth_sense=True,
                verbose=True,
            )
            p1_label = m["player1"]
            p2_label = m["player2"]
        else:
            result = engine.analyze_doubles(
                team1=m["team1"],
                team2=m["team2"],
                team1_avg_rank=m["team1_avg_rank"],
                team2_avg_rank=m["team2_avg_rank"],
                surface=m.get("surface", "hard"),
                best_of=m.get("best_of", 3),
                tournament=m.get("tournament", ""),
                market_odds=m.get("market_odds"),
                include_sixth_sense=True,
                verbose=True,
            )
            p1_label = result.player1
            p2_label = result.player2

        print(result.report())

        # Raccolta pick per la tabella finale
        odds = m.get("market_odds", {})
        probs = result.win_probs
        sm    = result.set_markets

        candidates = [
            ("P1",    probs.get("player1", 0), odds.get("player1")),
            ("P2",    probs.get("player2", 0), odds.get("player2")),
            ("O2.5S", sm.get("over_2_5_sets", 0),  odds.get("over_2_5_sets")),
            ("U2.5S", sm.get("under_2_5_sets", 0), odds.get("under_2_5_sets")),
            ("O3.5S", sm.get("over_3_5_sets", 0),  odds.get("over_3_5_sets")),
            ("U3.5S", sm.get("under_3_5_sets", 0), odds.get("under_3_5_sets")),
            ("O4.5S", sm.get("over_4_5_sets", 0),  odds.get("over_4_5_sets")),
            ("U4.5S", sm.get("under_4_5_sets", 0), odds.get("under_4_5_sets")),
        ]

        for market, prob, quota in candidates:
            if not quota or quota < MIN_QUOTA or prob <= 0:
                continue
            e = edge(prob, quota)
            if e < MIN_EDGE:
                continue

            all_picks.append({
                "match":   f"{p1_label} vs {p2_label}",
                "surface": m.get("surface", "?").upper(),
                "bo":      m.get("best_of", 3),
                "market":  market,
                "prob":    prob,
                "quota":   quota,
                "edge":    e,
                "ss":      result.sixth_sense.summary[:60] if result.sixth_sense and result.sixth_sense.status == "OK" else "",
            })

    # ── Tabella finale ────────────────────────────────────────────────────────
    if not all_picks:
        print("\n⚠️  Nessun pick sopra la soglia.")
        return

    all_picks.sort(key=lambda x: x["edge"], reverse=True)

    print(f"\n{'='*90}")
    print(f"  SCHEDINA TENNIS — {len(all_picks)} pick")
    print(f"{'='*90}")
    print(f"  {'Partita':<32} {'Surf':<5} {'Bo':<3} {'Mkt':<7} {'Prob':>6} {'Quota':>6} {'Edge':>7}  Sesto Senso")
    print(f"  {'-'*88}")

    for p in all_picks:
        edge_str = f"{p['edge']:+.1%}"
        flag = "⭐" if p["edge"] >= 0.08 else "  "
        print(
            f"  {flag}{p['match']:<30} {p['surface']:<5} {p['bo']:<3} "
            f"{p['market']:<7} {p['prob']:>5.1%} {p['quota']:>6.2f} {edge_str:>7}  {p['ss']}"
        )

    print(f"{'='*90}\n")

    best = [p for p in all_picks if p["edge"] >= 0.08]
    if best:
        print(f"⭐ VALUE BETS ({len(best)}):")
        for p in best:
            print(f"   {p['match']} → {p['market']} @ {p['quota']} (edge {p['edge']:+.1%})")


if __name__ == "__main__":
    run()
