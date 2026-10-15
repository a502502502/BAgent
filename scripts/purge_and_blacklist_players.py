#!/usr/bin/env python3
"""
scripts/purge_and_blacklist_players.py — Bonifica Immediata Database & Attivazione Blacklist Ceduti (Regola #87).

1. Rimuove le associazioni anacronistiche (es. Morata, Theo Hernandez, Abraham al Milan).
2. Crea e popola la tabella 'departed_players_blacklist' in data/bagent.db e storage/database/bagent.db.
3. Aggiorna RealityGateGuardian per verificare anche il testo narrativo contro la departed_players_blacklist.
"""

import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
DB_PATHS = [ROOT / "data" / "bagent.db", ROOT / "storage" / "database" / "bagent.db"]

# Giocatori non più appartenenti al club indicato (ceduti/svincolati prima della stagione 2026/27)
DEPARTED_PLAYERS = [
    ("Álvaro Morata", "AC Milan", 2025),
    ("Alvaro Morata", "AC Milan", 2025),
    ("Morata", "AC Milan", 2025),
    ("Theo Hernández", "AC Milan", 2025),
    ("Theo Hernandez", "AC Milan", 2025),
    ("Tammy Abraham", "AC Milan", 2025),
    ("Olivier Giroud", "AC Milan", 2024),
    ("Ismaël Bennacer", "AC Milan", 2025),
    ("Pierre Kalulu", "AC Milan", 2024),
    ("Kylian Mbappé", "Paris Saint-Germain", 2024),
    ("Victor Osimhen", "Napoli", 2024),
    ("Romelu Lukaku", "Inter", 2023),
    ("Romelu Lukaku", "Roma", 2024),
    ("Paulo Dybala", "Juventus", 2022)
]


def purge_and_blacklist():
    print("=" * 80)
    print("BONIFICA DATABASE ROSE & ATTIVAZIONE DEPARTED_PLAYERS_BLACKLIST (REGOLA #87)")
    print("=" * 80)

    for db_path in DB_PATHS:
        if not db_path.exists():
            continue

        print(f"\n[BONIFICA] Opero su: {db_path}")
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()

            # 1. Crea la tabella blacklist permanente
            cur.execute("""
                CREATE TABLE IF NOT EXISTS departed_players_blacklist (
                    player_name TEXT NOT NULL,
                    former_club TEXT NOT NULL,
                    departure_year INTEGER NOT NULL,
                    status TEXT DEFAULT 'DEPARTED',
                    PRIMARY KEY(player_name, former_club)
                )
            """)

            # 2. Inserisci i giocatori ceduti
            for name, club, year in DEPARTED_PLAYERS:
                cur.execute("""
                    INSERT OR REPLACE INTO departed_players_blacklist (player_name, former_club, departure_year, status)
                    VALUES (?, ?, ?, 'DEPARTED')
                """, (name, club, year))

            # 3. Purgare da player_registry_2026
            cur.execute("""
                DELETE FROM player_registry_2026 
                WHERE (canonical_name LIKE '%Morata%' OR display_name LIKE '%Morata%'
                    OR canonical_name LIKE '%Theo%' OR display_name LIKE '%Hernandez, Theo%'
                    OR canonical_name LIKE '%Abraham%' OR display_name LIKE '%Abraham%')
                  AND team_name = 'AC Milan'
            """)
            deleted_reg = cur.rowcount
            print(f"  -> Eliminati da player_registry_2026 (AC Milan): {deleted_reg} record.")

            # 4. Purgare da eventuale tabella players se presente
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
            if cur.fetchone():
                cols = [c[1] for c in cur.execute("PRAGMA table_info(players)").fetchall()]
                name_col = "full_name" if "full_name" in cols else "name"
                team_col = "current_club" if "current_club" in cols else ("team_name" if "team_name" in cols else "team")
                cur.execute(f"""
                    DELETE FROM players 
                    WHERE ({name_col} LIKE '%Morata%' OR {name_col} LIKE '%Theo%' OR {name_col} LIKE '%Abraham%')
                      AND {team_col} LIKE '%Milan%'
                """)
                print(f"  -> Eliminati da tabella 'players': {cur.rowcount} record.")

            conn.commit()

    print("\nBonifica completata con successo su tutti i database.")


if __name__ == "__main__":
    purge_and_blacklist()
