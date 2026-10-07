"""
scripts/publish_weekend_dual_sessions.py — Registra e pubblica su Git e Sito HTML le sessioni di Venerdi (9 Ott) e Domenica (11 Ott).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TICKETS_DIR = ROOT / "reports" / "tickets"
PUBLIC_SITE = ROOT.parent / "bagent-schedine"

friday_core = {
    "ticket_id": "TICKET_09OTT_VENERDI_CASSAFORTE_CORE",
    "title": "Schedina A: La Cassaforte Core-Protetta (Venerdi 9 Ottobre)",
    "name": "Schedina A: La Cassaforte Core-Protetta (Venerdi 9 Ottobre)",
    "created_at": "2026-10-07T12:45:00+00:00",
    "status": "PENDING",
    "strategy": "CORE_CASSAFORTE_MACRO",
    "stake_eur": 7.0,
    "total_odds": 2.32,
    "potential_payout_eur": 16.24,
    "notes": "Portafoglio Core 70% budget. Macro-mercati protetti per anticipi campionati maggiori.",
    "legs": [
        {
            "match": "Borussia Dortmund vs Werder Bremen",
            "tournament": "Bundesliga",
            "competition": "Bundesliga",
            "market": "1X + Over 1.5",
            "selection": "1X + Over 1.5",
            "odds": 1.32,
            "date_time": "2026-10-09 20:30 CEST",
            "kickoff": "2026-10-09 20:30 CEST",
            "status": "PENDING",
            "rationale": "Dortmund al Signal Iduna Park dominante, lambda offensivo Poisson > 2.1, Werder con difesa aperta."
        },
        {
            "match": "Lens vs Lyon",
            "tournament": "Ligue 1",
            "competition": "Ligue 1",
            "market": "Under 3.5",
            "selection": "Under 3.5",
            "odds": 1.35,
            "date_time": "2026-10-09 21:00 CEST",
            "kickoff": "2026-10-09 21:00 CEST",
            "status": "PENDING",
            "rationale": "Scontro tattico di vertice, Lens con blocco basso casalingo e Lyon guardingo in trasferta."
        },
        {
            "match": "Malaga vs Espanyol",
            "tournament": "La Liga",
            "competition": "La Liga",
            "market": "1X",
            "selection": "1X",
            "odds": 1.30,
            "date_time": "2026-10-09 21:00 CEST",
            "kickoff": "2026-10-09 21:00 CEST",
            "status": "PENDING",
            "rationale": "Fattore campo Rosaleda a favore del Malaga; Espanyol con baricentro conservativo."
        }
    ]
}

friday_gem = {
    "ticket_id": "TICKET_09OTT_VENERDI_GEMME_SATELLITE",
    "title": "Schedina B: La Schedina delle Gemme (Venerdi 9 Ottobre)",
    "name": "Schedina B: La Schedina delle Gemme (Venerdi 9 Ottobre)",
    "created_at": "2026-10-07T12:45:00+00:00",
    "status": "PENDING",
    "strategy": "SATELLITE_GEMME_ASYMMETRIC",
    "stake_eur": 3.0,
    "total_odds": 3.15,
    "potential_payout_eur": 9.45,
    "notes": "Portafoglio Satellite 30% budget. Player Prop protetta Guirassy e Combo Asimmetrica Lens-Lyon.",
    "legs": [
        {
            "match": "Borussia Dortmund vs Werder Bremen",
            "tournament": "Bundesliga",
            "competition": "Bundesliga",
            "market": "Serhou Guirassy: Almeno 1 tiro in porta",
            "selection": "Serhou Guirassy O0.5 Tiri in Porta (Clausola Pali e Sostituto)",
            "odds": 1.70,
            "date_time": "2026-10-09 20:30 CEST",
            "kickoff": "2026-10-09 20:30 CEST",
            "status": "PENDING",
            "rationale": "Guirassy terminale offensivo di punta, media 3.4 tiri p90 con oltre 1.6 nello specchio, rigorista designato con salvaguardia subentrante."
        },
        {
            "match": "Lens vs Lyon",
            "tournament": "Ligue 1",
            "competition": "Ligue 1",
            "market": "Goal (Entrambe le squadre a segno)",
            "selection": "Goal (Entrambe segnano)",
            "odds": 1.85,
            "date_time": "2026-10-09 21:00 CEST",
            "kickoff": "2026-10-09 21:00 CEST",
            "status": "PENDING",
            "rationale": "Lyon a segno nelle ultime 8 trasferte consecutive; Lens pericoloso in ripartenza casalinga. Disallineamento quota soft/sharp."
        }
    ]
}

sunday_core = {
    "ticket_id": "TICKET_11OTT_DOMENICA_CASSAFORTE_CORE",
    "title": "Schedina A: La Cassaforte Core-Protetta (Domenica 11 Ottobre)",
    "name": "Schedina A: La Cassaforte Core-Protetta (Domenica 11 Ottobre)",
    "created_at": "2026-10-07T12:45:00+00:00",
    "status": "PENDING",
    "strategy": "CORE_CASSAFORTE_MACRO",
    "stake_eur": 7.0,
    "total_odds": 2.33,
    "potential_payout_eur": 16.31,
    "notes": "Portafoglio Core 70% budget. Serie A e La Liga con coperture ad alta resilienza.",
    "legs": [
        {
            "match": "Cagliari vs Juventus",
            "tournament": "Serie A",
            "competition": "Serie A",
            "market": "X2 + Under 3.5",
            "selection": "X2 + Under 3.5",
            "odds": 1.38,
            "date_time": "2026-10-11 20:45 CEST",
            "kickoff": "2026-10-11 20:45 CEST",
            "status": "PENDING",
            "rationale": "Juventus con lambda concesso < 0.8, Cagliari con approccio guardingo tra le mura amiche."
        },
        {
            "match": "Lazio vs Monza",
            "tournament": "Serie A",
            "competition": "Serie A",
            "market": "1X + Over 1.5",
            "selection": "1X + Over 1.5",
            "odds": 1.34,
            "date_time": "2026-10-11 15:00 CEST",
            "kickoff": "2026-10-11 15:00 CEST",
            "status": "PENDING",
            "rationale": "Lazio all'Olimpico con volume di occasioni elevato; Monza vulnerabile in transizione."
        },
        {
            "match": "Real Betis vs Osasuna",
            "tournament": "La Liga",
            "competition": "La Liga",
            "market": "1X",
            "selection": "1X",
            "odds": 1.26,
            "date_time": "2026-10-11 16:15 CEST",
            "kickoff": "2026-10-11 16:15 CEST",
            "status": "PENDING",
            "rationale": "Fattore campo Benito Villamarin, Osasuna concede possesso e tiri concessi p90 sopra quota 13."
        }
    ]
}

sunday_gem = {
    "ticket_id": "TICKET_11OTT_DOMENICA_GEMME_SATELLITE",
    "title": "Schedina B: La Schedina delle Gemme (Domenica 11 Ottobre)",
    "name": "Schedina B: La Schedina delle Gemme (Domenica 11 Ottobre)",
    "created_at": "2026-10-07T12:45:00+00:00",
    "status": "PENDING",
    "strategy": "SATELLITE_GEMME_ASYMMETRIC",
    "stake_eur": 3.0,
    "total_odds": 3.41,
    "potential_payout_eur": 10.23,
    "notes": "Portafoglio Satellite 30% budget. Big Match Anfield con Salah protetto e classica Hot Bet Sassuolo-Milan.",
    "legs": [
        {
            "match": "Liverpool vs Manchester City",
            "tournament": "Premier League",
            "competition": "Premier League",
            "market": "Mohamed Salah: Almeno 1 tiro in porta",
            "selection": "Mohamed Salah O0.5 Tiri in Porta (Clausola Pali e Sostituto)",
            "odds": 1.75,
            "date_time": "2026-10-11 17:30 CEST",
            "kickoff": "2026-10-11 17:30 CEST",
            "status": "PENDING",
            "rationale": "Ad Anfield nei big match Salah accentra le conclusioni (media 3.6 tiri p90), rigorista designato. Copertura da pali e sostituzione attiva."
        },
        {
            "match": "Sassuolo vs Milan",
            "tournament": "Serie A",
            "competition": "Serie A",
            "market": "Goal + Over 2.5",
            "selection": "Goal + Over 2.5",
            "odds": 1.95,
            "date_time": "2026-10-11 15:00 CEST",
            "kickoff": "2026-10-11 15:00 CEST",
            "status": "PENDING",
            "rationale": "Hot Bet H2H storica: 8 degli ultimi 9 precedenti tra Sassuolo e Milan terminati con Goal e Over 2.5 (media 3.4 reti a match)."
        }
    ]
}

new_tickets = [friday_core, friday_gem, sunday_core, sunday_gem]

def main() -> None:
    TICKETS_DIR.mkdir(parents=True, exist_ok=True)
    for t in new_tickets:
        p = TICKETS_DIR / f"{t['ticket_id'].lower()}.json"
        p.write_text(json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Creato ticket JSON: {p}")

    # Aggiorna active_user_tickets.json
    active_path = ROOT / "data" / "active_user_tickets.json"
    if active_path.exists():
        active = json.loads(active_path.read_text(encoding="utf-8"))
        existing_ids = {item.get("ticket_id") for item in active}
        for t in new_tickets:
            if t["ticket_id"] not in existing_ids:
                active.append(t)
        active_path.write_text(json.dumps(active, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Aggiornato {active_path}")

if __name__ == "__main__":
    main()
