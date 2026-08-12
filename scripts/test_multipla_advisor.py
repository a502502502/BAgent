"""
Test MultiplaAdvisor — replica ticket 12/08/2026 per mostrare i filtri.

Esegui:
    python scripts/test_multipla_advisor.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.betting.multipla_advisor import MultiplaAdvisor, Selection

def main():
    advisor = MultiplaAdvisor()

    print("\n" + "="*65)
    print("  SIMULAZIONE TICKET 12/08/2026")
    print("  (quello che avrebbe detto il modello PRIMA di giocare)")
    print("="*65 + "\n")

    selezioni = [
        Selection(
            home="FC Copenhagen", away="Debrecen",
            market="over_0_5_ht",
            our_prob=0.88,
            market_odd=1.21,
            cup_leg=2,
            label="Copenhagen-Debrecen Over 0.5 HT",
        ),
        Selection(
            home="Rapid Vienna", away="Paide",
            market="btts_yes",
            our_prob=0.55,
            market_odd=1.92,
            cup_leg=2,
            label="Rapid-Paide BTTS Sì",
        ),
        Selection(
            home="GKS Katowice", away="Hapoel Tel Aviv",
            market="away_win",
            our_prob=0.65,
            market_odd=3.15,
            cup_leg=2,
            label="Hapoel Tel Aviv Vince (1X2)",
        ),
        Selection(
            home="Austria Vienna", away="Beitar Jerusalem",
            market="qualify_home",
            our_prob=0.78,
            market_odd=1.23,
            cup_leg=2,
            label="Austria Vienna Passa il Turno",
        ),
    ]

    report = advisor.analyze(selezioni)
    print(report)

    print("\n" + "="*65)
    print("  COSA SAREBBE SUCCESSO: il ticket aveva 2 errori")
    print("  1. Copenhagen @1.21 → quota troppo bassa (< 1.40)")
    print("  2. BTTS Rapid-Paide @55% → sotto soglia 62%")
    print("  3. Hapoel 1X2 in coppa 2° turno → doveva essere 'qualify'")
    print("  → Il modello avrebbe giocato solo Austria Vienna")
    print("    oppure consigliato di non giocare oggi.")
    print("="*65 + "\n")

if __name__ == "__main__":
    main()
