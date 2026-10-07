"""
scripts/publish_dual_tickets_to_site.py — Genera i file JSON e aggiorna il sito HTML git.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TICKETS_DIR = ROOT / "reports" / "tickets"
PUBLIC_SITE = ROOT.parent / "bagent-schedine"

t1 = {
    "ticket_id": "TICKET_07OTT_CASSAFORTE_CORE",
    "title": "Schedina A: La Cassaforte Core-Protetta (7 Ottobre)",
    "name": "Schedina A: La Cassaforte Core-Protetta (7 Ottobre)",
    "created_at": "2026-10-07T12:30:00+00:00",
    "status": "PENDING",
    "strategy": "CORE_CASSAFORTE_MACRO",
    "stake_eur": 7.0,
    "total_odds": 2.13,
    "potential_payout_eur": 14.91,
    "booking_code": "36411",
    "notes": "Portafoglio Core 70% budget. Mercati macro protetti senza player props.",
    "legs": [
        {
            "match": "CD Universidad Catolica vs LDU Quito",
            "tournament": "Ecuador Serie A",
            "competition": "Ecuador Serie A",
            "market": "Under 3.5",
            "selection": "Under 3.5",
            "odds": 1.15,
            "date_time": "2026-10-07 17:00 CEST",
            "kickoff": "2026-10-07 17:00 CEST",
            "status": "PENDING",
            "rationale": "LDU Quito 5 gare consecutive Under 2.5; match tattico di alta classifica."
        },
        {
            "match": "IF Gnistan vs Inter Turku",
            "tournament": "Finlandia Veikkausliiga",
            "competition": "Finlandia Veikkausliiga",
            "market": "X2 + Over 1.5",
            "selection": "X2 + Over 1.5",
            "odds": 1.48,
            "date_time": "2026-10-07 18:00 CEST",
            "kickoff": "2026-10-07 18:00 CEST",
            "status": "PENDING",
            "rationale": "Inter Turku imbattuta in 6 H2H recenti; Gnistan subisce da 11 gare consecutive."
        },
        {
            "match": "CS Cerrito vs Montevideo Wanderers",
            "tournament": "Uruguay Copa Auf",
            "competition": "Uruguay Copa Auf",
            "market": "1X",
            "selection": "1X",
            "odds": 1.25,
            "date_time": "2026-10-07 20:30 CEST",
            "kickoff": "2026-10-07 20:30 CEST",
            "status": "PENDING",
            "rationale": "Fattore campo coppa nazionale, Cerrito imbattuto in casa nelle ultime 5 uscite."
        }
    ]
}

t2 = {
    "ticket_id": "TICKET_07OTT_GEMME_SATELLITE",
    "title": "Schedina B: La Schedina delle Gemme (7 Ottobre)",
    "name": "Schedina B: La Schedina delle Gemme (7 Ottobre)",
    "created_at": "2026-10-07T12:30:00+00:00",
    "status": "PENDING",
    "strategy": "SATELLITE_GEMME_ASYMMETRIC",
    "stake_eur": 3.0,
    "total_odds": 2.81,
    "potential_payout_eur": 8.43,
    "notes": "Portafoglio Satellite 30% budget. Hot Bet Oddspedia 100% streak e H2H asimmetrico.",
    "legs": [
        {
            "match": "Jedinstvo UB U19 vs Stella Rossa Belgrado U19",
            "tournament": "Serbia U19 League",
            "competition": "Serbia U19 League",
            "market": "Goal (Entrambe segnano)",
            "selection": "Goal (Entrambe segnano)",
            "odds": 1.44,
            "date_time": "2026-10-07 18:00 CEST",
            "kickoff": "2026-10-07 18:00 CEST",
            "status": "PENDING",
            "rationale": "Oddspedia Hot Bet certificata al 100%: 7 su 7 recenti terminate con entrambe a segno."
        },
        {
            "match": "IF Gnistan vs Inter Turku",
            "tournament": "Finlandia Veikkausliiga",
            "competition": "Finlandia Veikkausliiga",
            "market": "X2 + Goal",
            "selection": "X2 + Goal",
            "odds": 1.95,
            "date_time": "2026-10-07 18:00 CEST",
            "kickoff": "2026-10-07 18:00 CEST",
            "status": "PENDING",
            "rationale": "Inter Turku imbattuta nei precedenti; Gnistan segna in casa ma concede da 11 partite di fila."
        }
    ]
}

t3 = {
    "ticket_id": "TICKET_10OTT_SABATO_GEMME",
    "title": "Schedina Gemme Sabato Campionati Maggiori (10 Ottobre)",
    "name": "Schedina Gemme Sabato Campionati Maggiori (10 Ottobre)",
    "created_at": "2026-10-07T12:30:00+00:00",
    "status": "PENDING",
    "strategy": "SATELLITE_GEMME_BIG_LEAGUES",
    "stake_eur": 3.0,
    "total_odds": 3.27,
    "potential_payout_eur": 9.81,
    "notes": "Player Prop con paracadute sostituto/legni e Hot Bet Bernabeu 100% H2H streak.",
    "legs": [
        {
            "match": "Manchester United vs Tottenham",
            "tournament": "Premier League",
            "competition": "Premier League",
            "market": "Bruno Fernandes: Almeno 1 tiro in porta",
            "selection": "Bruno Fernandes O0.5 Tiri in Porta (Clausola Pali e Sostituto)",
            "odds": 1.72,
            "date_time": "2026-10-10 18:30 CEST",
            "kickoff": "2026-10-10 18:30 CEST",
            "status": "PENDING",
            "rationale": "Fernandes tira punizioni e rigori, media 3.3 tiri p90, 84% presenze con tiro in porta a Old Trafford. Clausola salvaguardia attiva."
        },
        {
            "match": "Real Madrid vs Villarreal",
            "tournament": "La Liga",
            "competition": "La Liga",
            "market": "Goal (Entrambe le squadre a segno)",
            "selection": "Goal (Entrambe segnano)",
            "odds": 1.90,
            "date_time": "2026-10-10 21:00 CEST",
            "kickoff": "2026-10-10 21:00 CEST",
            "status": "PENDING",
            "rationale": "Hot Bet Oddspedia: ultimi 7 precedenti consecutivi al Bernabeu tutti chiusi con entrambe a segno (100% streak)."
        }
    ]
}

def main() -> None:
    TICKETS_DIR.mkdir(parents=True, exist_ok=True)
    for t in (t1, t2, t3):
        fname = f"{t['ticket_id'].lower()}.json"
        path = TICKETS_DIR / fname
        path.write_text(json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Salvato ticket JSON in {path}")

    # Aggiorna anche active_user_tickets.json
    active_path = ROOT / "data" / "active_user_tickets.json"
    if active_path.exists():
        active = json.loads(active_path.read_text(encoding="utf-8"))
        existing_ids = {item.get("ticket_id") for item in active}
        for t in (t1, t2, t3):
            if t["ticket_id"] not in existing_ids:
                active.append(t)
        active_path.write_text(json.dumps(active, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Aggiornato {active_path}")

if __name__ == "__main__":
    main()
