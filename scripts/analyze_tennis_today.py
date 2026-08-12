"""
Analisi semifinali Montreal National Bank Open 2026
Hard Court (outdoor) — Best of 3
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tennis.sixth_sense.engine import TennisEngine

MATCHES = [
    {
        "title": "SF1 — Learner Tien (12) vs Ben Shelton (5)",
        "p1": "Learner Tien",
        "p2": "Ben Shelton",
        "p1_rank": 13,   # seed 12
        "p2_rank": 8,    # seed 5, defending champion
        "surface": "hard",
        "best_of": 3,
        "h2h": (0, 1),   # Tien 0 vinte, 1 giocate (Shelton domina H2H)
        # Shelton: grande servizio su hard, difende il titolo
        # Tien: solidissimo, primo Masters 1000 SF, ha perso 0 set nel torneo
        "p1_surface_factor": 0.95,   # Tien solido su hard ma non dominante
        "p2_surface_factor": 1.10,   # Shelton eccellente su hard americano
        "market_odds": {
            "player1": 2.80,   # Tien
            "player2": 1.45,   # Shelton favorito
        },
    },
    {
        "title": "SF2 — Rafael Jódar (20) vs Brandon Nakashima (28)",
        "p1": "Rafael Jódar",
        "p2": "Brandon Nakashima",
        "p1_rank": 21,   # seed 20, 19 anni, in grande forma
        "p2_rank": 29,   # seed 28
        "surface": "hard",
        "best_of": 3,
        "h2h": (0, 0),   # Mai giocato
        # Jódar: 19 anni, ha battuto Fils 7-6 6-3, tatticalmente maturo
        # Nakashima: ha battuto Darderi 6-2 6-3, ottima settimana
        "p1_surface_factor": 1.05,   # Jódar buono su hard, ha dimostrato solidità
        "p2_surface_factor": 1.05,   # Nakashima hard court specialist
        "market_odds": {
            "player1": 1.65,   # Jódar leggero favorito
            "player2": 2.25,   # Nakashima outsider
        },
    },
]

def main():
    for m in MATCHES:
        print(f"\n{'='*60}")
        print(f"  {m['title']}")
        print(f"  Superficie: {m['surface'].upper()}  |  BO{m['best_of']}")
        print(f"{'='*60}")

        engine = TennisEngine()
        result = engine.analyze(
            player1=m["p1"],
            player2=m["p2"],
            player1_rank=m["p1_rank"],
            player2_rank=m["p2_rank"],
            surface=m["surface"],
            best_of=m["best_of"],
            h2h=m["h2h"],
            p1_surface_factor=m.get("p1_surface_factor", 1.0),
            p2_surface_factor=m.get("p2_surface_factor", 1.0),
            market_odds=m.get("market_odds"),
        )
        print(result.report())

if __name__ == "__main__":
    main()
