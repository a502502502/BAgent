"""
services/football/player_registry_resolver.py — Motore Anagrafico & Validatore Player Props 2026/27.

Risolve e certifica l'assegnazione Giocatore-Squadra direttamente dai mercati reali Netwin/SNAI,
eliminando le allucinazioni da memoria storica pregressa (Regola #84).
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "bagent.db"


@dataclass
class ParsedPlayerProp:
    raw_market: str
    player_name: str
    canonical_name: str
    team_name: str
    prop_type: str
    threshold: Optional[float]
    has_substitute_clause: bool
    substitute_clause_type: Optional[str]  # 'OR_SUB' (o Sostituto) o 'AND_SUB' (e Sostituto)
    condition_description: str


class PlayerRegistryResolver:
    """
    Risolutore anagrafico che estrae, normalizza e certifica l'appartenenza dei giocatori
    alle squadre della stagione 2026/27 estraendo i dati dal testo ufficiale dei mercati.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db_schema()

    def _ensure_db_schema(self) -> None:
        """Crea la tabella dedicata player_registry_2026 se non esiste."""
        if not self.db_path.exists():
            return
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS player_registry_2026 (
                    canonical_name TEXT PRIMARY KEY,
                    display_name TEXT,
                    team_name TEXT NOT NULL,
                    role TEXT,
                    source TEXT,
                    last_verified TEXT
                )
                """
            )
            conn.commit()

    def parse_market_string(self, market_text: str) -> Optional[ParsedPlayerProp]:
        """
        Analizza pattern bookmaker come:
        - "U/O Sommer, Yann (Club Brugge) Parate 3.5 : OVER"
        - "Hojlund, Rasmus (Napoli) e Sostituto in Totale Almeno 1 Tiri in Porta : SI"
        - "Martinez, Lisandro (Manchester United) o Sostituto Cartellino o almeno 2 Falli Commessi : SI"
        - "Sabbe, Kyriani (Club Brugge) o Sostituto Cartellino o almeno 2 Falli Commessi : SI"
        - "Leao, Rafael (Galatasaray) e Sostituto in Totale Almeno 1 Tiri in Porta : SI"
        """
        text = market_text.strip()
        # Pattern estrazione giocatore e squadra tra parentesi: "Cognome, Nome (Squadra)"
        # oppure "Nome Cognome (Squadra)"
        match = re.search(r"(?:U/O\s+)?([A-Za-zÀ-ÿ'\s-]+),\s*([A-Za-zÀ-ÿ'\s-]+)\s*\(([^)]+)\)", text)
        if match:
            surname = match.group(1).strip()
            name = match.group(2).strip()
            team = match.group(3).strip()
            canonical = f"{name} {surname}".title()
            display = f"{surname}, {name}"
        else:
            match_alt = re.search(r"([A-Za-zÀ-ÿ'\s-]+)\s*\(([^)]+)\)", text)
            if match_alt:
                full_name = match_alt.group(1).strip()
                team = match_alt.group(2).strip()
                canonical = full_name.title()
                display = full_name
            else:
                return None

        # Identificazione tipo prop e clausole
        has_or_sub = bool(re.search(r"\bo\s+sostituto\b", text, re.IGNORECASE))
        has_and_sub = bool(re.search(r"\be\s+sostituto\b", text, re.IGNORECASE))
        sub_type = "OR_SUB" if has_or_sub else ("AND_SUB" if has_and_sub else None)
        has_sub = has_or_sub or has_and_sub

        prop_type = "UNKNOWN"
        threshold = None

        if "parate" in text.lower():
            prop_type = "PARATE"
            th_match = re.search(r"parate\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
            if th_match:
                threshold = float(th_match.group(1))
        elif "tiri in porta" in text.lower():
            prop_type = "TIRI_IN_PORTA"
            th_match = re.search(r"almeno\s*(\d+)\s*tiri", text, re.IGNORECASE)
            if th_match:
                threshold = float(th_match.group(1))
            else:
                threshold = 1.0
        elif "falli" in text.lower() or "cartellino" in text.lower():
            prop_type = "CARTELLINO_O_FALLI"
            th_match = re.search(r"almeno\s*(\d+)\s*falli", text, re.IGNORECASE)
            if th_match:
                threshold = float(th_match.group(1))
            else:
                threshold = 2.0

        prop = ParsedPlayerProp(
            raw_market=text,
            player_name=display,
            canonical_name=canonical,
            team_name=team,
            prop_type=prop_type,
            threshold=threshold,
            has_substitute_clause=has_sub,
            substitute_clause_type=sub_type,
            condition_description=text,
        )

        # Registra immediatamente nel database SQLite
        self.register_player(prop.canonical_name, prop.player_name, prop.team_name, source="NETWIN_FEED")
        return prop

    def register_player(
        self, canonical_name: str, display_name: str, team_name: str, role: Optional[str] = None, source: str = "MANUAL"
    ) -> None:
        """Registra o aggiorna l'appartenenza del giocatore alla squadra 2026/27 nel DB."""
        if not self.db_path.exists():
            return
        now_str = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO player_registry_2026 (canonical_name, display_name, team_name, role, source, last_verified)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(canonical_name) DO UPDATE SET
                        team_name=excluded.team_name,
                        display_name=excluded.display_name,
                        source=excluded.source,
                        last_verified=excluded.last_verified
                    """,
                    (canonical_name, display_name, team_name, role, source, now_str),
                )
                conn.commit()
        except Exception:
            pass

    def get_player_team(self, player_query: str) -> Optional[str]:
        """Recupera la squadra ufficiale 2026/27 registrata per il giocatore."""
        if not self.db_path.exists():
            return None
        q = f"%{player_query.strip()}%"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT team_name FROM player_registry_2026
                    WHERE canonical_name LIKE ? OR display_name LIKE ?
                    LIMIT 1
                    """,
                    (q, q),
                )
                row = cur.fetchone()
                return row[0] if row else None
        except Exception:
            return None

    def validate_player_team_match(
        self, player_prop: ParsedPlayerProp, home_team: str, away_team: str
    ) -> tuple[bool, str]:
        """
        Verifica che la squadra del giocatore corrisponda a una delle due squadre della partita.
        Previene lo scambio casa/trasferta o l'assegnazione errata.
        """
        pt = player_prop.team_name.lower()
        ht = home_team.lower()
        at = away_team.lower()

        is_home = pt in ht or ht in pt
        is_away = pt in at or at in pt

        if not is_home and not is_away:
            return False, (
                f"ERRORE DI ATTRIBUZIONE: {player_prop.canonical_name} è indicato come giocatore di '{player_prop.team_name}', "
                f"ma il match è '{home_team} vs {away_team}'. Nessuna corrispondenza!"
            )

        side_str = "CASA" if is_home else "TRASFERTA"
        team_real = home_team if is_home else away_team
        return True, f"OK: {player_prop.canonical_name} milita in {team_real} ({side_str})."
