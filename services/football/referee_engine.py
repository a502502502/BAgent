"""
BAgent - Referee Strictness Index & Database Engine (Step 1)
Gestisce le statistiche storiche degli arbitri (Falli/Partita, Cartellini Gialli/Rossi, Rigori)
e calibra la severità per i mercati di Cartellini e Falli.
"""

import sys
import sqlite3
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

DEFAULT_DB_PATH = root_dir / "storage" / "database" / "bagent.db"

@dataclass
class RefereeProfile:
    name: str
    country: str
    league: str
    matches_tracked: int
    avg_fouls_per_match: float
    avg_yellow_cards: float
    avg_red_cards: float
    avg_penalties: float
    strictness_level: str # PERMISSIVO, MODERATO, SEVERO, INCANDESCENTE
    betting_advice: str

class RefereeEngine:
    """
    Motore di analisi del profilo arbitrale per la calibrazione delle scommesse su Falli e Sanzioni.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._seed_referees()

    def _get_connection(self):
        return sqlite3.connect(str(self.db_path))

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS referee_stats (
                name TEXT PRIMARY KEY,
                country TEXT,
                league TEXT,
                matches_tracked INTEGER,
                avg_fouls REAL,
                avg_yellow REAL,
                avg_red REAL,
                avg_penalties REAL,
                strictness_level TEXT,
                betting_advice TEXT
            )
            """)
            conn.commit()

    def _seed_referees(self):
        """Popola il DB con gli arbitri di punta europei e italiani."""
        referees = [
            # Italia
            ("Fabio Maresca", "Italia", "Serie A / UEFA", 45, 27.8, 5.2, 0.28, 0.35, "INCANDESCENTE", "Cartellino facile: ottimo per Over 4.5/5.5 Cartellini e Over Falli."),
            ("Matteo Marcenaro", "Italia", "Serie A / UEFA", 38, 26.1, 4.8, 0.18, 0.29, "SEVERO", "Metro rigoroso sui contrasti: favorisce i Falli Subiti dei fantasisti."),
            ("Marco Di Bello", "Italia", "Serie A", 52, 21.4, 3.8, 0.15, 0.22, "PERMISSIVO", "Lascia correre molto a centrocampo (metro all'inglese): NO Over Falli Totali alti."),
            ("Giovanni Ayroldi", "Italia", "Serie A", 40, 26.5, 5.1, 0.32, 0.38, "SEVERO", "Sanziona le proteste e i falli tattici: alta probabilità di cartellini nel 2° tempo."),
            ("Antonio Rapuano", "Italia", "Serie A", 36, 22.1, 4.0, 0.14, 0.25, "MODERATO", "Arbitraggio fisico e permissivo sui contatti leggeri."),
            ("Luca Zufferli", "Italia", "Serie A", 28, 20.8, 3.9, 0.10, 0.18, "PERMISSIVO", "Bassa media falli fischiati: sconsigliato Over 24.5 falli."),
            # Internazionali / UEFA / Spagna / UK
            ("Jesus Gil Manzano", "Spagna", "LaLiga / UCL", 65, 27.2, 5.4, 0.30, 0.40, "INCANDESCENTE", "Non tollera il gioco duro: ideale per Over Cartellini in Spagna."),
            ("Szymon Marciniak", "Polonia", "UEFA Champions League", 70, 24.0, 4.2, 0.12, 0.28, "MODERATO", "Arbitro d'élite UEFA: ritmo alto e gestione autoritaria senza sanzioni isteriche."),
            ("Michael Oliver", "Inghilterra", "Premier League / UEFA", 60, 21.0, 3.7, 0.11, 0.24, "PERMISSIVO", "Metro Premier: fischia solo falli netti, pochissime interruzioni."),
            ("Anthony Taylor", "Inghilterra", "Premier League / UEFA", 62, 22.4, 4.4, 0.16, 0.30, "MODERATO", "Sanziona severamente i falli di mano e le trattenute in area."),
            ("Clement Turpin", "Francia", "Ligue 1 / UEFA", 58, 23.5, 3.9, 0.14, 0.26, "MODERATO", "Equilibrato nelle gare internazionali.")
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for r in referees:
                cursor.execute("""
                INSERT OR REPLACE INTO referee_stats 
                (name, country, league, matches_tracked, avg_fouls, avg_yellow, avg_red, avg_penalties, strictness_level, betting_advice)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, r)
            conn.commit()

    def get_referee(self, name: str) -> Optional[RefereeProfile]:
        """Cerca un arbitro nel database (anche con match parziale del nome)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT name, country, league, matches_tracked, avg_fouls, avg_yellow, avg_red, avg_penalties, strictness_level, betting_advice
            FROM referee_stats
            WHERE LOWER(name) LIKE LOWER(?) OR LOWER(name) LIKE LOWER(?)
            LIMIT 1
            """, (f"%{name}%", f"{name}%"))
            row = cursor.fetchone()
            if row:
                return RefereeProfile(
                    name=row[0], country=row[1], league=row[2], matches_tracked=row[3],
                    avg_fouls_per_match=row[4], avg_yellow_cards=row[5], avg_red_cards=row[6],
                    avg_penalties=row[7], strictness_level=row[8], betting_advice=row[9]
                )
        return None
