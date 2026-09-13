#!/usr/bin/env python3
"""
scripts/test_siege_engine.py
Test di verifica per LiveSiegeEngine (Regola #50: Protocollo Assedio Live & Trigger Asimmetrico).

Simula scenari realistici in cui una sfavorita passa in vantaggio contro una favorita:
1. Gil Vicente in vantaggio 0-1 al 15' a Lisbona contro il Benfica
2. Monza in vantaggio 0-1 a San Siro contro il Milan
3. Celta Vigo sotto 0-1 al 35' contro l'Espanyol
4. Test di rifiuto quando non c'è asimmetria o non c'è svantaggio
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.live.siege_engine import LiveSiegeEngine, SiegeOpportunity


def test_siege_engine():
    print("=" * 65)
    print("🔬 TEST PROTOCOLLO ASSEDIO LIVE & TRIGGER ASIMMETRICO (REGOLA #50)")
    print("=" * 65)

    engine = LiveSiegeEngine()

    # Scenario 1: Benfica (favorita casa @ 1.25) sotto 0-1 al 18' contro Gil Vicente
    print("\n--- SCENARIO 1: Benfica vs Gil Vicente (0-1 al 18') ---")
    opp1 = engine.evaluate_in_play(
        match_name="Benfica vs Gil Vicente",
        minute=18,
        home_team="Benfica",
        away_team="Gil Vicente",
        home_score=0,
        away_score=1,
        pre_match_odd_home=1.25,
        pre_match_odd_away=10.50,
        current_corners_home=2,
        current_corners_away=0,
        current_cards_home=0,
        current_cards_away=1,
        current_shots_home=4,
        current_shots_away=1,
    )
    assert opp1 is not None, "Scenario 1 fallito: doveva generare una SiegeOpportunity"
    print(f"✅ Trigger Attivato per: {opp1.favorite_name} (Svantaggio {opp1.current_score} al {opp1.minute}')")
    print(f"   • Corner consigliati: {opp1.recommended_corner_line} (+{opp1.projected_additional_corners_fav} attesi)")
    print(f"   • Cartellini sfavorita: {opp1.recommended_card_line} (+{opp1.projected_additional_cards_underdog} attesi)")
    print(f"   • Tiri favorita: {opp1.recommended_shot_line} (+{opp1.projected_additional_shots_fav} attesi)")
    print(f"   • Rimonta DC Live: {opp1.recommended_comeback_market} @ ~{opp1.estimated_comeback_odd} (Edge: {opp1.estimated_comeback_edge*100:+.1f}%)")
    print("\n[ANTEPRIMA TELEGRAM ALERT]:\n" + opp1.telegram_alert_html)

    # Scenario 2: Barcellona (favorita trasferta @ 1.35) sotto 1-0 al 52' sul campo del Levante
    print("\n--- SCENARIO 2: Levante vs Barcelona (1-0 al 52') ---")
    opp2 = engine.evaluate_in_play(
        match_name="Levante vs Barcelona",
        minute=52,
        home_team="Levante",
        away_team="Barcelona",
        home_score=1,
        away_score=0,
        pre_match_odd_home=7.50,
        pre_match_odd_away=1.35,
        current_corners_home=1,
        current_corners_away=4,
        current_cards_home=2,
        current_cards_away=0,
        current_shots_home=3,
        current_shots_away=9,
    )
    assert opp2 is not None, "Scenario 2 fallito"
    print(f"✅ Trigger Attivato per: {opp2.favorite_name} (Svantaggio {opp2.current_score} al {opp2.minute}')")
    print(f"   • Corner consigliati: {opp2.recommended_corner_line}")
    print(f"   • Cartellini sfavorita: {opp2.recommended_card_line}")
    print(f"   • Rimonta DC Live: {opp2.recommended_comeback_market} @ ~{opp2.estimated_comeback_odd} (Edge: {opp2.estimated_comeback_edge*100:+.1f}%)")

    # Scenario 3: Partita equilibrata (Atletico @ 2.40 vs Real Sociedad @ 2.90, 1-0 al 30') -> NON deve scattare
    print("\n--- SCENARIO 3 (NEGATIVO): Real Sociedad vs Atletico (1-0 al 30', quote equilibrate) ---")
    opp3 = engine.evaluate_in_play(
        match_name="Real Sociedad vs Atletico Madrid",
        minute=30,
        home_team="Real Sociedad",
        away_team="Atletico Madrid",
        home_score=1,
        away_score=0,
        pre_match_odd_home=2.90,
        pre_match_odd_away=2.40,
    )
    assert opp3 is None, "Scenario 3 fallito: non doveva scattare per quote equilibrate"
    print("✅ Correttamente RIFIUTATO: nessuna big dominante asimmetrica (quote > 1.60)")

    # Scenario 4: Favorita già in vantaggio (Napoli 1-0 al 70') -> NON deve scattare
    print("\n--- SCENARIO 4 (NEGATIVO): Napoli vs Bologna (1-0 al 70', favorita in vantaggio) ---")
    opp4 = engine.evaluate_in_play(
        match_name="Napoli vs Bologna",
        minute=70,
        home_team="Napoli",
        away_team="Bologna",
        home_score=1,
        away_score=0,
        pre_match_odd_home=1.55,
        pre_match_odd_away=6.00,
    )
    assert opp4 is None, "Scenario 4 fallito: non doveva scattare se la favorita è in vantaggio"
    print("✅ Correttamente RIFIUTATO: la favorita è già in vantaggio (nessun assedio disperato)")

    print("\n" + "=" * 65)
    print("🎉 TUTTI I TEST LIVE SIEGE ENGINE SONO STATI SUPERATI CON SUCCESSO!")
    print("=" * 65)


if __name__ == "__main__":
    test_siege_engine()
