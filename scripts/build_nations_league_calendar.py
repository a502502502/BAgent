#!/usr/bin/env python3
"""
scripts/build_nations_league_calendar.py
Popola e struttura il calendario ufficiale UEFA Nations League 2026/27 (League A & Key Fixtures)
con analisi tattica preventiva, cluster di rischio e mercati consigliati secondo le regole di BAgent.
"""

from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "storage" / "database" / "bagent.db"

FIXTURES_2026 = [
    # GIORNATA 1: GIOVEDÌ 24 SETTEMBRE 2026
    {
        "date": "2026-09-24 20:45:00",
        "home": "Olanda",
        "away": "Germania",
        "group": "League A - Gruppo 2",
        "dna_cluster": "OPEN_BALLISTIC_TRANSITION",
        "recommended_market": "Over 1.5 Gol Totali / Gol-Gol",
        "target_odd": 1.25,
        "est_prob": 0.88,
        "tactical_notes": "Scontro aperto ad altissimo xG. Difese con poca chimica e transizioni verticali rapide. Evitare 1X2."
    },
    {
        "date": "2026-09-24 20:45:00",
        "home": "Portogallo",
        "away": "Galles",
        "group": "League A - Gruppo 4",
        "dna_cluster": "ASYMMETRIC_DOMINANCE",
        "recommended_market": "1X + MultiGol 1-5",
        "target_odd": 1.28,
        "est_prob": 0.90,
        "tactical_notes": "Portogallo padrone del campo all'Alvalade. Galles blocco basso ma vulnerabile. 1X protegge da qualsiasi intoppo."
    },
    {
        "date": "2026-09-24 20:45:00",
        "home": "Norvegia",
        "away": "Danimarca",
        "group": "League A - Gruppo 4",
        "dna_cluster": "BALANCED_COMPETITIVE",
        "recommended_market": "1X o Over 1.5 (Chance Mix)",
        "target_odd": 1.35,
        "est_prob": 0.84,
        "tactical_notes": "Derby scandinavo a Oslo. Haaland punto di riferimento, Danimarca esperta. Match da almeno 2 gol o spinta casalinga."
    },
    {
        "date": "2026-09-24 20:45:00",
        "home": "Serbia",
        "away": "Grecia",
        "group": "League A - Gruppo 2",
        "dna_cluster": "DEFENSIVE_ATTRITION",
        "recommended_market": "Under 3.0 Asiatico / 1X",
        "target_odd": 1.25,
        "est_prob": 0.87,
        "tactical_notes": "Gara balcanica fisica a Belgrado. Ritmi spezzettati, molti falli e poche occasioni limpide."
    },

    # GIORNATA 1: VENERDÌ 25 SETTEMBRE 2026
    {
        "date": "2026-09-25 20:45:00",
        "home": "Italia",
        "away": "Belgio",
        "group": "League A - Gruppo 1",
        "dna_cluster": "BALANCED_COMPETITIVE",
        "recommended_market": "1X + MultiGol 1-5",
        "target_odd": 1.34,
        "est_prob": 0.86,
        "tactical_notes": "All'Olimpico di Roma esordio di fuoco. L'Italia protegge l'imbattibilità casalinga contro un Belgio in ricambio generazionale."
    },
    {
        "date": "2026-09-25 20:45:00",
        "home": "Turchia",
        "away": "Francia",
        "group": "League A - Gruppo 1",
        "dna_cluster": "HIGH_HOSTILITY_CUP",
        "recommended_market": "MultiGol 1-4 Partita / Over 1.5",
        "target_odd": 1.27,
        "est_prob": 0.88,
        "tactical_notes": "Regola #67: Attenzione all'ambiente infernale di Istanbul. VIETATO il 2 secco della Francia. Meglio linee gol protette."
    },
    {
        "date": "2026-09-25 20:45:00",
        "home": "Spagna",
        "away": "Croazia",
        "group": "League A - Gruppo 3",
        "dna_cluster": "ASYMMETRIC_DOMINANCE",
        "recommended_market": "1X + Under 4.5 / 1X + MG 1-5",
        "target_odd": 1.30,
        "est_prob": 0.89,
        "tactical_notes": "Spagna campione in carica col controllo del possesso. Croazia esperta ma lenta a centrocampo. 1X blindata."
    },
    {
        "date": "2026-09-25 20:45:00",
        "home": "Inghilterra",
        "away": "Repubblica Ceca",
        "group": "League A - Gruppo 3",
        "dna_cluster": "ASYMMETRIC_DOMINANCE",
        "recommended_market": "1X + Over 1.5",
        "target_odd": 1.28,
        "est_prob": 0.88,
        "tactical_notes": "A Wembley l'Inghilterra spinge per chiudere la gara. Cechi solidi sui piazzati ma inferiori negli ultimi 30 metri."
    },

    # GIORNATA 2: DOMENICA 27 SETTEMBRE 2026
    {
        "date": "2026-09-27 20:45:00",
        "home": "Germania",
        "away": "Grecia",
        "group": "League A - Gruppo 2",
        "dna_cluster": "ASYMMETRIC_DOMINANCE",
        "recommended_market": "1X + MultiGol 1-5",
        "target_odd": 1.24,
        "est_prob": 0.91,
        "tactical_notes": "Tedeschi dominanti in casa. La Grecia difenderà con blocco basso a 5."
    },
    {
        "date": "2026-09-27 20:45:00",
        "home": "Norvegia",
        "away": "Portogallo",
        "group": "League A - Gruppo 4",
        "dna_cluster": "OPEN_BALLISTIC_TRANSITION",
        "recommended_market": "Over 1.5 Gol Totali / Gol-Gol",
        "target_odd": 1.26,
        "est_prob": 0.87,
        "tactical_notes": "Duello balistico tra attaccanti di livello mondiale (Haaland vs Portogallo). Altissimo rischio gol da ambo i lati."
    },

    # GIORNATA 2: LUNEDÌ 28 SETTEMBRE 2026
    {
        "date": "2026-09-28 20:45:00",
        "home": "Belgio",
        "away": "Francia",
        "group": "League A - Gruppo 1",
        "dna_cluster": "BALANCED_COMPETITIVE",
        "recommended_market": "Chance Mix X2 o Over 1.5",
        "target_odd": 1.32,
        "est_prob": 0.85,
        "tactical_notes": "Derby dei Paesi Bassi del Sud a Bruxelles. Rivalità storica altissima, partita aperta da 90 minuti di respiro."
    },
    {
        "date": "2026-09-28 20:45:00",
        "home": "Turchia",
        "away": "Italia",
        "group": "League A - Gruppo 1",
        "dna_cluster": "HIGH_HOSTILITY_CUP",
        "recommended_market": "MultiGol 1-3 Partita / X2",
        "target_odd": 1.35,
        "est_prob": 0.83,
        "tactical_notes": "Trasferta durissima per gli azzurri. Vietato 2 secco. La gestione tattica di Spalletti favorisce match a punteggio controllato."
    }
]

def init_nations_league_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS nations_league_fixtures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_date TEXT,
            home_team TEXT,
            away_team TEXT,
            stage_group TEXT,
            dna_cluster TEXT,
            recommended_market TEXT,
            target_odd REAL,
            est_prob REAL,
            tactical_notes TEXT,
            status TEXT DEFAULT 'SCHEDULED'
        )
    """)
    c.execute("DELETE FROM nations_league_fixtures")
    for f in FIXTURES_2026:
        c.execute("""
            INSERT INTO nations_league_fixtures 
            (match_date, home_team, away_team, stage_group, dna_cluster, recommended_market, target_odd, est_prob, tactical_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f["date"], f["home"], f["away"], f["group"], f["dna_cluster"],
            f["recommended_market"], f["target_odd"], f["est_prob"], f["tactical_notes"]
        ))
    conn.commit()
    conn.close()
    print(f"✅ Inserite con successo {len(FIXTURES_2026)} partite di UEFA Nations League 2026/27 in bagent.db!")

if __name__ == "__main__":
    init_nations_league_table()
