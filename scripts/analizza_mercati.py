#!/usr/bin/env python3
"""
BAgent — Analisi multi-mercato
Uso:
    python scripts/analizza_mercati.py

Inserisci interattivamente le probabilità 1X2, gli xG stimati
e le quote del bookmaker. Il sistema calcola edge su tutti i mercati.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analysis.multi_market import (
    MultiMarketAnalyzer,
    BookmakerOdds,
    estimate_xg,
)


def ask_float(prompt: str, required: bool = True) -> float | None:
    while True:
        val = input(prompt).strip()
        if val == "" and not required:
            return None
        try:
            return float(val)
        except ValueError:
            print("  ⚠️  Inserisci un numero (es. 1.75) o premi Invio per saltare.")


def ask_odds_section(label: str, fields: list[tuple[str, str]]) -> dict:
    print(f"\n  [{label}] — premi Invio per saltare un mercato")
    result = {}
    for key, prompt in fields:
        val = ask_float(f"    {prompt}: ", required=False)
        result[key] = val
    return result


def main():
    print("\n" + "=" * 60)
    print("  BAGENT — Analisi Multi-Mercato")
    print("=" * 60)

    # ---- Dati partita ----
    match_label = input("\nPartita (es. Monza vs Avellino): ").strip() or "Partita"

    print("\n--- Le tue probabilità 1X2 (Sesto Senso già incluso) ---")
    p1 = ask_float("  Prob Casa 1 (es. 0.78): ")
    pX = ask_float("  Prob Pareggio X (es. 0.14): ")
    p2 = ask_float("  Prob Ospite 2 (es. 0.08): ")

    print("\n--- xG attesi (gol attesi per squadra) ---")
    print("  Se non li conosci, inserisci le medie stagionali e calcolo automatico.")
    mode = input("  Inserisci xG direttamente? (s/n): ").strip().lower()

    if mode == "s":
        xg_home = ask_float("  xG Casa (es. 1.80): ")
        xg_away = ask_float("  xG Ospite (es. 0.85): ")
    else:
        print("  Medie stagionali squadra CASA:")
        h_scored   = ask_float("    Gol segnati/partita (es. 1.60): ")
        h_conceded = ask_float("    Gol subiti/partita (es. 1.10): ")
        print("  Medie stagionali squadra OSPITE:")
        a_scored   = ask_float("    Gol segnati/partita (es. 0.95): ")
        a_conceded = ask_float("    Gol subiti/partita (es. 1.40): ")
        xg_home, xg_away = estimate_xg(h_scored, h_conceded, a_scored, a_conceded)
        print(f"\n  ✅ xG stimati → Casa: {xg_home}  Ospite: {xg_away}")

    # ---- Quote bookmaker ----
    print("\n--- Quote Bookmaker ---")

    q_1x2 = ask_odds_section("1X2", [
        ("home_1", "Casa 1"),
        ("draw_x", "Pareggio X"),
        ("away_2", "Ospite 2"),
    ])

    q_dc = ask_odds_section("Doppia Chance", [
        ("dc_1x", "1X"),
        ("dc_12", "12"),
        ("dc_x2", "X2"),
    ])

    q_ou = ask_odds_section("Over/Under", [
        ("over_05",  "Over 0.5"),
        ("under_05", "Under 0.5"),
        ("over_15",  "Over 1.5"),
        ("under_15", "Under 1.5"),
        ("over_25",  "Over 2.5"),
        ("under_25", "Under 2.5"),
        ("over_35",  "Over 3.5"),
        ("under_35", "Under 3.5"),
        ("over_45",  "Over 4.5"),
        ("under_45", "Under 4.5"),
    ])

    q_ggng = ask_odds_section("GG / NG", [
        ("gg", "GG (entrambe segnano)"),
        ("ng", "NG (almeno una non segna)"),
    ])

    q_corners = ask_odds_section("Corner Over/Under", [
        ("corner_over_75",  "Over 7.5"),
        ("corner_under_75", "Under 7.5"),
        ("corner_over_85",  "Over 8.5"),
        ("corner_under_85", "Under 8.5"),
        ("corner_over_95",  "Over 9.5"),
        ("corner_under_95", "Under 9.5"),
        ("corner_over_105", "Over 10.5"),
        ("corner_under_105","Under 10.5"),
        ("corner_over_115", "Over 11.5"),
        ("corner_under_115","Under 11.5"),
        ("corner_over_125", "Over 12.5"),
        ("corner_under_125","Under 12.5"),
    ])

    q_cards = ask_odds_section("Cartellini Over/Under", [
        ("card_over_15",  "Over 1.5"),
        ("card_under_15", "Under 1.5"),
        ("card_over_25",  "Over 2.5"),
        ("card_under_25", "Under 2.5"),
        ("card_over_35",  "Over 3.5"),
        ("card_under_35", "Under 3.5"),
        ("card_over_45",  "Over 4.5"),
        ("card_under_45", "Under 4.5"),
        ("card_over_55",  "Over 5.5"),
        ("card_under_55", "Under 5.5"),
    ])

    odds = BookmakerOdds(
        **q_1x2, **q_dc, **q_ou, **q_ggng, **q_corners, **q_cards
    )

    # ---- xCorner e xCard (opzionali) ----
    xc_home = xc_away = None
    xk_home = xk_away = None

    has_corner_odds = any(v is not None for v in q_corners.values())
    has_card_odds   = any(v is not None for v in q_cards.values())

    if has_corner_odds:
        print("\n--- Corner attesi (per stimare le probabilità) ---")
        print("  Usa la media corner per partita (casa: in casa, ospite: in trasferta).")
        xc_home = ask_float("  Corner attesi Casa (es. 5.5): ", required=False)
        xc_away = ask_float("  Corner attesi Ospite (es. 4.2): ", required=False)

    if has_card_odds:
        print("\n--- Cartellini attesi ---")
        print("  Usa la media cartellini per partita (gialli, non rossi).")
        xk_home = ask_float("  Cartellini attesi Casa (es. 2.1): ", required=False)
        xk_away = ask_float("  Cartellini attesi Ospite (es. 1.8): ", required=False)

    # ---- Analisi ----
    analyzer = MultiMarketAnalyzer(
        prob_home=p1,
        prob_draw=pX,
        prob_away=p2,
        xg_home=xg_home,
        xg_away=xg_away,
        odds=odds,
        xc_home=xc_home,
        xc_away=xc_away,
        xk_home=xk_home,
        xk_away=xk_away,
        match_label=match_label,
    )

    print("\n--- RISULTATI (ordinati per probabilità) ---")
    analyzer.print_table(show_all=True)

    # Riepilogo value bets
    results = analyzer.analyze()
    value = [r for r in results if r.edge >= 0.05]
    if value:
        print("✅ VALUE BETS (edge ≥ 5%):")
        for r in value:
            print(f"   {r.market} — {r.selection} @{r.quota:.2f} | Prob {r.prob_pct} | Edge {r.edge_pct}")
    else:
        print("ℹ️  Nessun value bet sopra soglia 5% trovato.")

    print()


if __name__ == "__main__":
    main()
