#!/usr/bin/env python3
"""
scripts/build_netwin_tactical_portfolio.py — Pipeline di Generazione Portafoglio Netwin.

Carica lo snapshot ufficiale fresco di Netwin (reports/tickets/netwin_nl_markets_20261006.json)
e applica il nuovo OmniStatisticalOptimizer con intelligenza causale e tattica per generare
un portafoglio di 5 ticket diversificati 100% giocabili su Netwin.
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.analysis.omni_statistical_optimizer import (
    MatchDossier,
    OmniStatisticalPricer,
    CombinatorialPortfolioOptimizer
)

# Dossier tattico per le 10 partite del 6 Ottobre 2026 su Netwin
TACTICAL_DOSSIERS_NETWIN = {
    "Croazia vs Spagna": MatchDossier(
        match_name="Croazia vs Spagna",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=0.95,
        xg_away=1.95,
        coach_profile_home="transizione_rapida",
        coach_profile_away="dominante_verticale",
        wing_play_intensity_home=0.45,
        wing_play_intensity_away=0.80,
        game_state_behavior="relentless",
        match_tension=4,
        rebound_00_risk=False,
        environmental_context="caldo_balcanico"
    ),
    "Inghilterra vs Repubblica Ceca": MatchDossier(
        match_name="Inghilterra vs Repubblica Ceca",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=2.20,
        xg_away=0.70,
        coach_profile_home="dominante_verticale",
        coach_profile_away="corto_muso",
        wing_play_intensity_home=0.85,
        wing_play_intensity_away=0.30,
        game_state_behavior="cruise_control",
        match_tension=3,
        rebound_00_risk=False,
        environmental_context="standard"
    ),
    "Svizzera vs Macedonia Del Nord": MatchDossier(
        match_name="Svizzera vs Macedonia Del Nord",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=1.70,
        xg_away=0.65,
        coach_profile_home="possesso_orizzontale",
        coach_profile_away="corto_muso",
        wing_play_intensity_home=0.55,
        wing_play_intensity_away=0.35,
        game_state_behavior="cruise_control",
        match_tension=3,
        rebound_00_risk=False,
        environmental_context="nordico_disciplinato"
    ),
    "Scozia vs Slovenia": MatchDossier(
        match_name="Scozia vs Slovenia",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=1.55,
        xg_away=0.90,
        coach_profile_home="dominante_verticale",
        coach_profile_away="corto_muso",
        wing_play_intensity_home=0.80,
        wing_play_intensity_away=0.35,
        game_state_behavior="relentless",
        match_tension=4,
        rebound_00_risk=False,
        environmental_context="standard"
    ),
    "Albania vs San Marino": MatchDossier(
        match_name="Albania vs San Marino",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=2.80,
        xg_away=0.20,
        coach_profile_home="dominante_verticale",
        coach_profile_away="corto_muso",
        wing_play_intensity_home=0.75,
        wing_play_intensity_away=0.10,
        game_state_behavior="relentless",
        match_tension=2,
        rebound_00_risk=False,
        environmental_context="caldo_balcanico"
    ),
    "Moldova vs Slovacchia": MatchDossier(
        match_name="Moldova vs Slovacchia",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=0.70,
        xg_away=1.75,
        coach_profile_home="corto_muso",
        coach_profile_away="dominante_verticale",
        wing_play_intensity_home=0.30,
        wing_play_intensity_away=0.70,
        game_state_behavior="cruise_control",
        match_tension=3,
        rebound_00_risk=False,
        environmental_context="standard"
    ),
    "Estonia vs Islanda": MatchDossier(
        match_name="Estonia vs Islanda",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=0.85,
        xg_away=1.65,
        coach_profile_home="corto_muso",
        coach_profile_away="dominante_verticale",
        wing_play_intensity_home=0.35,
        wing_play_intensity_away=0.75,
        game_state_behavior="cruise_control",
        match_tension=3,
        rebound_00_risk=False,
        environmental_context="nordico_disciplinato"
    ),
    "Bielorussia vs Finlandia": MatchDossier(
        match_name="Bielorussia vs Finlandia",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=0.90,
        xg_away=1.45,
        coach_profile_home="corto_muso",
        coach_profile_away="possesso_orizzontale",
        wing_play_intensity_home=0.40,
        wing_play_intensity_away=0.50,
        game_state_behavior="cruise_control",
        match_tension=3,
        rebound_00_risk=True,
        environmental_context="nordico_disciplinato"
    ),
    "Lussemburgo vs Bulgaria": MatchDossier(
        match_name="Lussemburgo vs Bulgaria",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=1.35,
        xg_away=1.05,
        coach_profile_home="possesso_orizzontale",
        coach_profile_away="transizione_rapida",
        wing_play_intensity_home=0.50,
        wing_play_intensity_away=0.45,
        game_state_behavior="cruise_control",
        match_tension=3,
        rebound_00_risk=False,
        environmental_context="standard"
    ),
    "Kazakistan vs Isole Far Oer": MatchDossier(
        match_name="Kazakistan vs Isole Far Oer",
        kickoff="2026-10-06 16:00 CEST",
        xg_home=1.40,
        xg_away=0.80,
        coach_profile_home="possesso_orizzontale",
        coach_profile_away="corto_muso",
        wing_play_intensity_home=0.45,
        wing_play_intensity_away=0.40,
        game_state_behavior="cruise_control",
        match_tension=3,
        rebound_00_risk=True,
        environmental_context="caucasico_ostile"
    )
}


def normalize_netwin_markets(netwin_m_dict: dict) -> list[dict]:
    """Converte il dizionario dei mercati di Netwin nella struttura standard catalog per l'ottimizzatore."""
    catalog_markets = []

    # 1. 1X2 e Doppia Chance
    if "DOPPIA_CHANCE" in netwin_m_dict:
        outcomes = []
        for sel, odd in netwin_m_dict["DOPPIA_CHANCE"].items():
            outcomes.append({"selection": sel, "odds": float(odd)})
        catalog_markets.append({"market": "DOPPIA CHANCE", "line": "", "outcomes": outcomes})

    # 2. Under / Over
    if "UNDER_OVER" in netwin_m_dict:
        for line, uo_dict in netwin_m_dict["UNDER_OVER"].items():
            outcomes = []
            for sel, odd in uo_dict.items():
                outcomes.append({"selection": sel.upper(), "odds": float(odd)})
            catalog_markets.append({"market": "UNDER / OVER", "line": f"U/O {line}", "outcomes": outcomes})

    # 3. Gol / NoGol
    if "GOL_NOGOL" in netwin_m_dict:
        outcomes = []
        for sel, odd in netwin_m_dict["GOL_NOGOL"].items():
            outcomes.append({"selection": sel.upper(), "odds": float(odd)})
        catalog_markets.append({"market": "GOAL / NOGOAL", "line": "", "outcomes": outcomes})

    # 4. MultiGol
    if "MULTIGOL" in netwin_m_dict:
        for mg_name, odd in netwin_m_dict["MULTIGOL"].items():
            catalog_markets.append({
                "market": mg_name,
                "line": "",
                "outcomes": [{"selection": "SI", "odds": float(odd)}]
            })

    # 5. Chance Mix
    if "CHANCE_MIX" in netwin_m_dict:
        for cm_name, odd in netwin_m_dict["CHANCE_MIX"].items():
            catalog_markets.append({
                "market": cm_name,
                "line": "",
                "outcomes": [{"selection": "SI", "odds": float(odd)}]
            })

    # 6. MultiGol Squadra
    if "MULTIGOL_SQUADRA" in netwin_m_dict:
        for mgs_name, odd in netwin_m_dict["MULTIGOL_SQUADRA"].items():
            catalog_markets.append({
                "market": mgs_name,
                "line": "",
                "outcomes": [{"selection": "SI", "odds": float(odd)}]
            })

    # 7. Primo Tempo
    if "PRIMO_TEMPO" in netwin_m_dict:
        outcomes = []
        for sel, odd in netwin_m_dict["PRIMO_TEMPO"].items():
            # Standardizza (es. '1X 1° Tempo' -> '1X')
            clean_sel = sel.replace(" 1° Tempo", "").strip()
            outcomes.append({"selection": clean_sel, "odds": float(odd)})
        catalog_markets.append({"market": "1 TEMPO: ESITO 1X2", "line": "1 TEMPO", "outcomes": outcomes})

    return catalog_markets


def main():
    print("==================================================================")
    print("PIPELINE OTTIMIZZAZIONE TATTICA NETWIN — NATIONS LEAGUE (06 OTT)")
    print("==================================================================\n")

    netwin_file = ROOT / "reports/tickets/netwin_nl_markets_20261006.json"
    if not netwin_file.exists():
        print(f"Errore: {netwin_file} non trovato!")
        return

    with open(netwin_file, "r", encoding="utf-8") as f:
        netwin_data = json.load(f)

    pricer = OmniStatisticalPricer()
    optimizer = CombinatorialPortfolioOptimizer(pricer=pricer)

    candidate_picks_by_match = {}
    dossiers_list = []

    print("[1/3] Parsing mercati ufficiali Netwin ed esecuzione Pricing Causale/Tattico...")
    for match_obj in netwin_data.get("matches", []):
        m_name = match_obj.get("match_name")
        dossier = TACTICAL_DOSSIERS_NETWIN.get(m_name)
        if not dossier:
            continue

        raw_markets = match_obj.get("markets", {})
        catalog_markets = normalize_netwin_markets(raw_markets)
        picks = optimizer.generate_candidate_picks(dossier, catalog_markets)
        
        # Filtra solo mercati con segnale stella o occhio e probabilità solida
        valid_picks = [p for p in picks if p[0].score >= 0.70 and not p[0].blocked]
        candidate_picks_by_match[dossier.match_name] = valid_picks
        dossiers_list.append(dossier)
        print(f"  - {dossier.match_name}: {len(valid_picks)} mercati ottimali prezzati nello Sweet-Spot")

    print(f"\n[2/3] Generazione portafoglio diversificato Netwin (max 4 leg per ticket)...")
    portfolio = optimizer.build_diversified_portfolio(
        dossiers_list,
        candidate_picks_by_match,
        num_tickets=5,
        ticket_size=4,
        stake_per_ticket=2.50,
        bankroll_reference=100.0
    )

    out_path = ROOT / "reports/tickets/ticket_netwin_nl_06ott_portfolio.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)
    print(f"\n[3/3] Portafoglio Netwin salvato con successo in {out_path}!")

    print("\n================== RIEPILOGO PORTAFOGLIO NETWIN 06 OTT ==================")
    for i, t in enumerate(portfolio["tickets"], 1):
        print(f"\n--- {t['name']} ---")
        print(f"Quota Totale: {t['total_odds']} | Prob: {t['probability']*100:.1f}% | Edge: {t['edge']*100:+.1f}% | Ritorno: {t['potential_payout']} EUR")
        for leg in t["legs"]:
            print(f"  * [{leg['market_family']}] {leg['match']} -> {leg['market']} @ {leg['odds']} (P: {leg['probability']*100:.1f}%, Score: {leg['score']}, Segnale: {leg['verdict']})")


if __name__ == "__main__":
    main()
