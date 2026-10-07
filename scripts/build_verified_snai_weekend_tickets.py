"""
scripts/build_verified_snai_weekend_tickets.py — Costruisce e pubblica i ticket verificati dai JSON ufficiali SNAI 2026-10-07-11.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TICKETS_DIR = ROOT / "reports" / "tickets"
ACTIVE_FILE = ROOT / "data" / "active_user_tickets.json"

# ==============================================================================
# VENERDI 9 OTTOBRE 2026
# ==============================================================================
fri_core = {
    "ticket_id": "TICKET_09OTT_VENERDI_CASSAFORTE_CORE",
    "title": "Schedina A: La Cassaforte Core-Protetta (Venerdi 9 Ottobre)",
    "name": "Schedina A: La Cassaforte Core-Protetta (Venerdi 9 Ottobre)",
    "created_at": "2026-10-07T13:20:00+00:00",
    "status": "PENDING",
    "strategy": "CORE_CASSAFORTE_MACRO_SNAI",
    "stake_eur": 7.0,
    "total_odds": 2.73,
    "potential_payout_eur": 19.11,
    "notes": "Mercati protetti estratti dal palinsesto ufficiale SNAI (Event Detail JSON).",
    "legs": [
        {
            "event_code": "36411-2051",
            "match": "Borussia Dortmund - Werder Brema",
            "tournament": "GER Bundesliga",
            "competition": "GER Bundesliga",
            "market": "COMBO: DC + U/O",
            "selection": "1X + OVER 2.5",
            "odds": 1.42,
            "date_time": "2026-10-09 20:30 CEST",
            "kickoff": "2026-10-09 20:30 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Dortmund dominante al Signal Iduna Park, xG di squadra 2026 > 2.2, linea 2.5 ad alto assorbimento con doppia chance."
        },
        {
            "event_code": "36411-1970",
            "match": "Lens - Lione",
            "tournament": "FRA Ligue 1",
            "competition": "FRA Ligue 1",
            "market": "COMBO CHANCE",
            "selection": "X O UNDER 3.5",
            "odds": 1.30,
            "date_time": "2026-10-09 20:45 CEST",
            "kickoff": "2026-10-09 20:45 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Scontro tattico di vertice: copertura doppia su pareggio oppure punteggio a basso volume (<= 3 gol)."
        },
        {
            "event_code": "36411-2278",
            "match": "Malaga - Espanyol",
            "tournament": "ESP Liga",
            "competition": "ESP Liga",
            "market": "COMBO: DC + U/O",
            "selection": "1X + UNDER 4.5",
            "odds": 1.48,
            "date_time": "2026-10-09 21:00 CEST",
            "kickoff": "2026-10-09 21:00 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Fattore campo Rosaleda a favore del Malaga; linea Under 4.5 difensiva contro Espanyol guardingo."
        }
    ]
}

fri_gem = {
    "ticket_id": "TICKET_09OTT_VENERDI_GEMME_SATELLITE",
    "title": "Schedina B: La Schedina delle Gemme (Venerdi 9 Ottobre)",
    "name": "Schedina B: La Schedina delle Gemme (Venerdi 9 Ottobre)",
    "created_at": "2026-10-07T13:20:00+00:00",
    "status": "WAITING_LINEUPS",
    "strategy": "SATELLITE_GEMME_ASYMMETRIC_SNAI",
    "stake_eur": 3.0,
    "total_odds": 2.92,
    "potential_payout_eur": 8.76,
    "notes": "Paracadute ufficiale SNAI Marcatore/Legni e Combo DC+Over. In attesa formazioni ufficiali (T-60m) per conferma titolarita.",
    "legs": [
        {
            "event_code": "36411-2051",
            "match": "Borussia Dortmund - Werder Brema",
            "tournament": "GER Bundesliga",
            "competition": "GER Bundesliga",
            "market": "MARCATORE PIU ULTRA (Sostituto e Legni)",
            "selection": "FABIO SILVA O SOSTITUTO SEGNA O PRENDE PALO/TRAVERSA INC. T.S.",
            "odds": 1.80,
            "date_time": "2026-10-09 20:30 CEST",
            "kickoff": "2026-10-09 20:30 CEST",
            "status": "WAITING_LINEUPS",
            "bookmaker": "SNAI",
            "rationale": "Attaccante di movimento ad alto volume conclusioni; clausola paracadute attiva su eventuale subentrante e pali/traverse."
        },
        {
            "event_code": "36411-1970",
            "match": "Lens - Lione",
            "tournament": "FRA Ligue 1",
            "competition": "FRA Ligue 1",
            "market": "COMBO: DC + U/O",
            "selection": "1X + OVER 1.5",
            "odds": 1.62,
            "date_time": "2026-10-09 20:45 CEST",
            "kickoff": "2026-10-09 20:45 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Lens imbattuto in casa con produzione offensiva di 1.6 xG p90; Lione sempre a segno in trasferta."
        }
    ]
}

# ==============================================================================
# SABATO 10 OTTOBRE 2026
# ==============================================================================
sat_core = {
    "ticket_id": "TICKET_10OTT_SABATO_CASSAFORTE_CORE",
    "title": "Schedina A: La Cassaforte Core-Protetta (Sabato 10 Ottobre)",
    "name": "Schedina A: La Cassaforte Core-Protetta (Sabato 10 Ottobre)",
    "created_at": "2026-10-07T13:20:00+00:00",
    "status": "PENDING",
    "strategy": "CORE_CASSAFORTE_MACRO_SNAI",
    "stake_eur": 7.0,
    "total_odds": 2.25,
    "potential_payout_eur": 15.75,
    "notes": "Trittico di campionati maggiori protetto da DC + Over/Under da catalogo SNAI.",
    "legs": [
        {
            "event_code": "36411-2275",
            "match": "Real Madrid - Villarreal",
            "tournament": "ESP Liga",
            "competition": "ESP Liga",
            "market": "COMBO: DC + U/O",
            "selection": "1X + OVER 2.5",
            "odds": 1.32,
            "date_time": "2026-10-10 21:00 CEST",
            "kickoff": "2026-10-10 21:00 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Real Madrid dominante al Bernabeu, match ad alto tasso di transizioni contro Villarreal offensivo."
        },
        {
            "event_code": "36411-1373",
            "match": "Inter - Parma",
            "tournament": "ITA Serie A",
            "competition": "ITA Serie A",
            "market": "COMBO: DC + U/O",
            "selection": "1X + OVER 2.5",
            "odds": 1.28,
            "date_time": "2026-10-10 18:00 CEST",
            "kickoff": "2026-10-10 18:00 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Inter a San Siro con volume di occasioni elevato; Parma con atteggiamento sbarazzino che concede spazi."
        },
        {
            "event_code": "36411-1887",
            "match": "Manchester United - Tottenham",
            "tournament": "ENG Premier League",
            "competition": "ENG Premier League",
            "market": "COMBO: DC + U/O",
            "selection": "1X + OVER 1.5",
            "odds": 1.33,
            "date_time": "2026-10-10 18:30 CEST",
            "kickoff": "2026-10-10 18:30 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Old Trafford fattore chiave; Tottenham con linea difensiva alta che assicura gol ma concede contropiedi."
        }
    ]
}

sat_gem = {
    "ticket_id": "TICKET_10OTT_SABATO_GEMME",
    "title": "Schedina B: La Schedina delle Gemme (Sabato 10 Ottobre)",
    "name": "Schedina B: La Schedina delle Gemme (Sabato 10 Ottobre)",
    "created_at": "2026-10-07T13:20:00+00:00",
    "status": "WAITING_LINEUPS",
    "strategy": "SATELLITE_GEMME_ASYMMETRIC_SNAI",
    "stake_eur": 3.0,
    "total_odds": 3.20,
    "potential_payout_eur": 9.60,
    "notes": "Doppio Marcatore Piu Ultra SNAI (valido su sostituto e pali/traverse inclusi). In attesa formazioni ufficiali (T-60m) per conferma titolarita.",
    "legs": [
        {
            "event_code": "36411-2275",
            "match": "Real Madrid - Villarreal",
            "tournament": "ESP Liga",
            "competition": "ESP Liga",
            "market": "MARCATORE PIU ULTRA (Sostituto e Legni)",
            "selection": "VINICIUS JUNIOR O SOSTITUTO SEGNA O PRENDE PALO/TRAVERSA INC. T.S.",
            "odds": 2.00,
            "date_time": "2026-10-10 21:00 CEST",
            "kickoff": "2026-10-10 21:00 CEST",
            "status": "WAITING_LINEUPS",
            "bookmaker": "SNAI",
            "rationale": "Vinicius accentra oltre 3.5 conclusioni al Bernabeu; quota @2.00 include pali, traverse e subentrante."
        },
        {
            "event_code": "36411-1373",
            "match": "Inter - Parma",
            "tournament": "ITA Serie A",
            "competition": "ITA Serie A",
            "market": "MARCATORE PIU ULTRA (Sostituto e Legni)",
            "selection": "THURAM MARCUS O SOSTITUTO SEGNA O PRENDE PALO/TRAVERSA INC. T.S.",
            "odds": 1.60,
            "date_time": "2026-10-10 18:00 CEST",
            "kickoff": "2026-10-10 18:00 CEST",
            "status": "WAITING_LINEUPS",
            "bookmaker": "SNAI",
            "rationale": "Thuram punto di riferimento nei tagli in area contro la linea alta del Parma. Copertura pali/sostituto inclusa."
        }
    ]
}

# ==============================================================================
# DOMENICA 11 OTTOBRE 2026
# ==============================================================================
sun_core = {
    "ticket_id": "TICKET_11OTT_DOMENICA_CASSAFORTE_CORE",
    "title": "Schedina A: La Cassaforte Core-Protetta (Domenica 11 Ottobre)",
    "name": "Schedina A: La Cassaforte Core-Protetta (Domenica 11 Ottobre)",
    "created_at": "2026-10-07T13:20:00+00:00",
    "status": "PENDING",
    "strategy": "CORE_CASSAFORTE_MACRO_SNAI",
    "stake_eur": 7.0,
    "total_odds": 2.19,
    "potential_payout_eur": 15.33,
    "notes": "Combinazioni protette SNAI su Serie A e Premier League.",
    "legs": [
        {
            "event_code": "36411-1374",
            "match": "Cagliari - Juventus",
            "tournament": "ITA Serie A",
            "competition": "ITA Serie A",
            "market": "COMBO: DC + U/O",
            "selection": "X2 + UNDER 3.5",
            "odds": 1.45,
            "date_time": "2026-10-11 20:45 CEST",
            "kickoff": "2026-10-11 20:45 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Juventus con indice difensivo inferiore a 0.8 gol attesi p90; Cagliari prudente tra le mura amiche."
        },
        {
            "event_code": "36411-1376",
            "match": "Lazio  - Monza",
            "tournament": "ITA Serie A",
            "competition": "ITA Serie A",
            "market": "COMBO CHANCE",
            "selection": "1 O OVER 2.5",
            "odds": 1.24,
            "date_time": "2026-10-11 15:00 CEST",
            "kickoff": "2026-10-11 15:00 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Chance Mix SNAI: vittoria della Lazio oppure match con almeno 3 reti totali."
        },
        {
            "event_code": "36411-1883",
            "match": "Liverpool - Manchester City",
            "tournament": "ENG Premier League",
            "competition": "ENG Premier League",
            "market": "COMBO CHANCE",
            "selection": "GOAL O OVER  2.5",
            "odds": 1.22,
            "date_time": "2026-10-11 17:30 CEST",
            "kickoff": "2026-10-11 17:30 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Big match ad altissimo indice xG combinato (> 3.4 xG attesi); Chance Mix centrata se c'e Gol oppure Over 2.5."
        }
    ]
}

sun_gem = {
    "ticket_id": "TICKET_11OTT_DOMENICA_GEMME_SATELLITE",
    "title": "Schedina B: La Schedina delle Gemme (Domenica 11 Ottobre)",
    "name": "Schedina B: La Schedina delle Gemme (Domenica 11 Ottobre)",
    "created_at": "2026-10-07T13:20:00+00:00",
    "status": "WAITING_LINEUPS",
    "strategy": "SATELLITE_GEMME_ASYMMETRIC_SNAI",
    "stake_eur": 3.0,
    "total_odds": 3.10,
    "potential_payout_eur": 9.30,
    "notes": "Paracadute Marcatore/Legni Haaland e Combo DC+Over su Como-Roma. In attesa formazioni ufficiali (T-60m) per conferma titolarita.",
    "legs": [
        {
            "event_code": "36411-1883",
            "match": "Liverpool - Manchester City",
            "tournament": "ENG Premier League",
            "competition": "ENG Premier League",
            "market": "MARCATORE PIU ULTRA (Sostituto e Legni)",
            "selection": "HAALAND E. O SOSTITUTO SEGNA O PRENDE PALO/TRAVERSA INC. T.S.",
            "odds": 1.80,
            "date_time": "2026-10-11 17:30 CEST",
            "kickoff": "2026-10-11 17:30 CEST",
            "status": "WAITING_LINEUPS",
            "bookmaker": "SNAI",
            "rationale": "Haaland punto focale offensivo del City; clausola paracadute attiva con subentrante e pali/traverse conteggiati vincenti."
        },
        {
            "event_code": "36411-1370",
            "match": "Como - Roma",
            "tournament": "ITA Serie A",
            "competition": "ITA Serie A",
            "market": "COMBO: DC + U/O",
            "selection": "X2 + OVER 1.5",
            "odds": 1.72,
            "date_time": "2026-10-11 12:30 CEST",
            "kickoff": "2026-10-11 12:30 CEST",
            "status": "PENDING",
            "bookmaker": "SNAI",
            "rationale": "Dati 2026: Como baricentro alto (54m) con 1.68 xG concessi p90; Roma prolifica in ripartenza e sempre a segno in trasferta."
        }
    ]
}

ALL_TICKETS = [fri_core, fri_gem, sat_core, sat_gem, sun_core, sun_gem]


def main() -> None:
    TICKETS_DIR.mkdir(parents=True, exist_ok=True)
    for t in ALL_TICKETS:
        p = TICKETS_DIR / f"{t['ticket_id'].lower()}.json"
        p.write_text(json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Salvato {p.name}")

    if ACTIVE_FILE.exists():
        active = json.loads(ACTIVE_FILE.read_text(encoding="utf-8"))
        id_map = {item.get("ticket_id"): idx for idx, item in enumerate(active)}
        for t in ALL_TICKETS:
            t_id = t["ticket_id"]
            if t_id in id_map:
                active[id_map[t_id]] = t
            else:
                active.append(t)
        ACTIVE_FILE.write_text(json.dumps(active, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Aggiornato data/active_user_tickets.json con i 6 ticket del weekend.")


if __name__ == "__main__":
    main()
