#!/usr/bin/env python3
"""
services/analysis/tipster_intelligence.py — Modulo di Ingestion & Auto-Apprendimento Schedine di Terzi.

Consente al core di BAgent di:
1. Ingerire schedine vincenti/perdenti di tipster esterni (da screenshot, chat o JSON).
2. Classificare automaticamente ogni selezione in famiglie di mercato (es. TIME_SPLIT_MULTIGOL, TEAM_CORNERS_VOLUME, TEAM_CARDS_VOLUME, TOTAL_SHOTS_ON_TARGET, CHANCE_MIX).
3. Calcolare il tasso di successo empirico e i moltiplicatori di efficacia (Market Efficacy Weights).
4. Fornire pesi dinamici al Balanced Safety Score (BSS) e allo scanner dei mercati per premiare le tipologie vincenti e penalizzare quelle fragili.
"""

from __future__ import annotations
import sqlite3
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from services.database.schema import DB_PATH

_DDL_TIPSTER_INTELLIGENCE = """
CREATE TABLE IF NOT EXISTS tipster_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipster_name TEXT NOT NULL,
    ticket_date TEXT NOT NULL,
    total_odds REAL NOT NULL,
    stake REAL,
    payout REAL,
    status TEXT NOT NULL, -- 'WON', 'LOST', 'VOID'
    num_legs INTEGER NOT NULL,
    source TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tipster_legs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER REFERENCES tipster_tickets(id) ON DELETE CASCADE,
    match_name TEXT NOT NULL,
    tournament TEXT,
    kickoff_time TEXT,
    market_name TEXT NOT NULL,
    market_family TEXT NOT NULL,
    odds REAL NOT NULL,
    outcome TEXT NOT NULL -- 'WON', 'LOST', 'VOID'
);

CREATE TABLE IF NOT EXISTS market_family_stats (
    market_family TEXT PRIMARY KEY,
    total_bets INTEGER NOT NULL DEFAULT 0,
    won_bets INTEGER NOT NULL DEFAULT 0,
    lost_bets INTEGER NOT NULL DEFAULT 0,
    win_rate REAL NOT NULL DEFAULT 0.0,
    avg_odds REAL NOT NULL DEFAULT 0.0,
    empirical_roi REAL NOT NULL DEFAULT 0.0,
    efficacy_weight REAL NOT NULL DEFAULT 1.0,
    updated_at TEXT NOT NULL
);
"""

# Famiglie di mercato canoniche e loro prior di base
CANONICAL_FAMILIES = {
    "TIME_SPLIT_MULTIGOL": {"name": "MultiGol Asimmetrico Tempi (1°T/2°T)", "base_prior": 1.25},
    "TEAM_CORNERS_VOLUME": {"name": "Corner Squadra Favorita (Assedio)", "base_prior": 1.20},
    "TEAM_CARDS_VOLUME": {"name": "Cartellini Squadra Sfavorita/Fisica", "base_prior": 1.20},
    "TOTAL_SHOTS_ON_TARGET": {"name": "Tiri in Porta Totali (Volume Balistico)", "base_prior": 1.20},
    "PLAYER_PROPS_COMBO": {"name": "Marcatore / Sostituto / Legno (Player Props)", "base_prior": 1.25},
    "CHANCE_MIX": {"name": "Chance Mix (X o GG, 1X o Over 1.5)", "base_prior": 1.20},
    "DC_PLUS_GOALS": {"name": "Doppia Chance + MultiGol/Over aperto", "base_prior": 1.15},
    "FIRST_HALF_MULTIGOL": {"name": "MultiGol 1° Tempo (0-1 o 1-3)", "base_prior": 1.15},
    "DOPPIA_CHANCE": {"name": "Doppia Chance Semplice (1X/X2)", "base_prior": 1.10},
    "OPEN_MULTIGOL": {"name": "MultiGol Totale Aperto (1-4, 1-5, 2-5)", "base_prior": 1.10},
    "BOTH_HALVES_GOALS": {"name": "Gol in Entrambi i Tempi", "base_prior": 1.10},
    "STRAIGHT_1X2": {"name": "Segno 1 o 2 Fisso (Trappola Varianza)", "base_prior": 0.65},
    "RIGID_COMBO_1X2": {"name": "Combo Rigida 1/2 Fisso + Over", "base_prior": 0.60},
    "UNDER_STRETTO": {"name": "Under Stretto (Under 1.5 / Under 2.5 rigido)", "base_prior": 0.70},
    "OTHER": {"name": "Altri Mercati Non Classificati", "base_prior": 1.00},
}


def classify_market_family(market_name: str) -> str:
    """Classifica automaticamente qualsiasi stringa di mercato nella famiglia canonica."""
    m = market_name.lower().strip()
    
    # 0. Player props / Marcatore / Palo o Traversa / Tiri Giocatore
    if any(w in m for w in ["segna o colpisce", "marcatore", "palo/trav", "palo", "traversa", "tiri giocatore"]):
        return "PLAYER_PROPS_COMBO"

    # 1. MultiGol Tempi (0-2 1°T + 1-3 2°T o varianti)
    if ("1°tempo" in m or "1° tempo" in m or "1°t" in m) and ("2°tempo" in m or "2° tempo" in m or "2°t" in m):
        return "TIME_SPLIT_MULTIGOL"
    if "multigol" in m and ("1°t" in m and "2°t" in m):
        return "TIME_SPLIT_MULTIGOL"
        
    # 2. Gol entrambi i tempi / Squadra segna in entrambi i tempi
    if "entrambi i tempi" in m or "ov 1°t + ov 2°t" in m or "entrambi tempi" in m:
        return "BOTH_HALVES_GOALS"
        
    # 3. Corner Squadra
    if "corner" in m and any(w in m for w in ["squadra", "casa", "ospite", "team"]):
        return "TEAM_CORNERS_VOLUME"
        
    # 4. Cartellini Squadra
    if ("cartellin" in m or "card" in m or "ammoniz" in m) and any(w in m for w in ["squadra", "casa", "ospite", "team"]):
        return "TEAM_CARDS_VOLUME"
        
    # 5. Tiri in porta
    if "tiri in porta" in m or "shots on target" in m or "tiri specchio" in m:
        return "TOTAL_SHOTS_ON_TARGET"
        
    # 6. Chance Mix
    if "chance mix" in m or (" o " in m and any(w in m for w in ["gg", "gol", "nogol", "over", "under"])):
        return "CHANCE_MIX"
        
    # 7. Doppia Chance + Gol/MultiGol / Over / Under
    if ("1x +" in m or "x2 +" in m or "1x+" in m or "x2+" in m or "1x + u/o" in m or "x2 + u/o" in m) and any(w in m for w in ["multigol", "over", "under", "ov", "un"]):
        return "DC_PLUS_GOALS"
        
    # 8. Primo Tempo MultiGol / Under / Over
    if any(pt in m for pt in ["1° tempo", "1°tempo", "primo tempo"]):
        return "FIRST_HALF_MULTIGOL"
        
    # 9. 1X2 Rigido o Combo Rigida
    if m in ["1", "2", "1 fisso", "2 fisso", "esito finale 1", "esito finale 2"]:
        return "STRAIGHT_1X2"
    if (m.startswith("1 +") or m.startswith("2 +") or m.startswith("1+") or m.startswith("2+")) and not ("1x" in m or "x2" in m):
        return "RIGID_COMBO_1X2"
        
    # 10. Doppia Chance semplice
    if m in ["1x", "x2", "12", "doppia chance 1x", "doppia chance x2"]:
        return "DOPPIA_CHANCE"
        
    # 11. MultiGol aperti (compresi MultiGol Casa/Ospite 2-5)
    if "multigol" in m:
        return "OPEN_MULTIGOL"
        
    # 12. Under stretti
    if "under 1.5" in m or "under 2.5" in m:
        return "UNDER_STRETTO"
        
    return "OTHER"


@dataclass
class TipsterLegInput:
    match_name: str
    market_name: str
    odds: float
    outcome: str = "WON"
    tournament: Optional[str] = None
    kickoff_time: Optional[str] = None
    market_family: Optional[str] = None


@dataclass
class TipsterTicketInput:
    tipster_name: str
    ticket_date: str
    legs: List[TipsterLegInput]
    total_odds: Optional[float] = None
    stake: Optional[float] = None
    payout: Optional[float] = None
    status: str = "WON"
    source: str = "EXTERNAL_MANUAL"


class TipsterIntelligenceEngine:
    """Motore di ingestion e computazione dell'efficacia empirica dei mercati."""

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(_DDL_TIPSTER_INTELLIGENCE)
            conn.commit()
        finally:
            conn.close()

    def ingest_ticket(self, ticket: TipsterTicketInput) -> int:
        """Salva un ticket esterno con tutte le sue selezioni e aggiorna i pesi del core."""
        # Se total_odds non è specificato, calcolalo dal prodotto
        tot_odds = ticket.total_odds
        if tot_odds is None or tot_odds <= 1.0:
            tot_odds = 1.0
            for leg in ticket.legs:
                tot_odds *= leg.odds
            tot_odds = round(tot_odds, 2)

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            now_iso = datetime.now().isoformat()
            cur.execute("""
                INSERT INTO tipster_tickets (
                    tipster_name, ticket_date, total_odds, stake, payout,
                    status, num_legs, source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket.tipster_name,
                ticket.ticket_date,
                tot_odds,
                ticket.stake,
                ticket.payout,
                ticket.status.upper(),
                len(ticket.legs),
                ticket.source,
                now_iso
            ))
            ticket_id = cur.lastrowid

            for leg in ticket.legs:
                fam = leg.market_family or classify_market_family(leg.market_name)
                cur.execute("""
                    INSERT INTO tipster_legs (
                        ticket_id, match_name, tournament, kickoff_time,
                        market_name, market_family, odds, outcome
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticket_id,
                    leg.match_name,
                    leg.tournament or "",
                    leg.kickoff_time or "",
                    leg.market_name,
                    fam,
                    leg.odds,
                    leg.outcome.upper()
                ))

            conn.commit()
            # Ricalcola i pesi statistici di efficacia empirica
            self._recalculate_family_weights(conn)
            conn.execute("PRAGMA wal_checkpoint(FULL)")
            return ticket_id
        finally:
            conn.close()

    def _recalculate_family_weights(self, conn: sqlite3.Connection) -> None:
        """Ricalcola win rate ed efficacy_weight per ciascuna famiglia di mercato."""
        cur = conn.cursor()
        rows = cur.execute("""
            SELECT 
                market_family,
                COUNT(*) as total,
                SUM(CASE WHEN outcome = 'WON' THEN 1 ELSE 0 END) as won,
                SUM(CASE WHEN outcome = 'LOST' THEN 1 ELSE 0 END) as lost,
                AVG(odds) as avg_odd
            FROM tipster_legs
            GROUP BY market_family
        """).fetchall()

        now_iso = datetime.now().isoformat()

        # Inserisci o aggiorna per ciascuna famiglia
        for r in rows:
            fam, total, won, lost, avg_odd = r[0], r[1], r[2], r[3], r[4] or 1.0
            win_rate = (won / total) if total > 0 else 0.0
            prior = CANONICAL_FAMILIES.get(fam, {}).get("base_prior", 1.0)
            
            # Formula di shrinkage bayesiano per il moltiplicatore:
            # Pesa la storia: ogni vittoria sposta positivamente il prior
            # Se win_rate > 70%, riceve un boost fino a +35%
            # Se win_rate < 40%, viene penalizzato fino a -35%
            edge_factor = (win_rate - 0.50) * 0.70
            adjusted_weight = round(prior * (1.0 + edge_factor), 3)

            cur.execute("""
                INSERT INTO market_family_stats (
                    market_family, total_bets, won_bets, lost_bets,
                    win_rate, avg_odds, empirical_roi, efficacy_weight, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(market_family) DO UPDATE SET
                    total_bets = excluded.total_bets,
                    won_bets = excluded.won_bets,
                    lost_bets = excluded.lost_bets,
                    win_rate = excluded.win_rate,
                    avg_odds = excluded.avg_odds,
                    efficacy_weight = excluded.efficacy_weight,
                    updated_at = excluded.updated_at
            """, (
                fam, total, won, lost, win_rate, round(avg_odd, 2),
                round((win_rate * avg_odd - 1.0), 3),
                adjusted_weight,
                now_iso
            ))
        conn.commit()

    def get_market_efficacy_weight(self, market_name: str) -> float:
        """Restituisce il moltiplicatore empirico di efficacia per un dato mercato (da usare nel BSS)."""
        fam = classify_market_family(market_name)
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            row = cur.execute("""
                SELECT efficacy_weight FROM market_family_stats WHERE market_family = ?
            """, (fam,)).fetchone()
            if row and row[0] is not None:
                return float(row[0])
            return CANONICAL_FAMILIES.get(fam, {}).get("base_prior", 1.0)
        finally:
            conn.close()

    def get_intelligence_summary(self) -> List[Dict[str, Any]]:
        """Restituisce il riepilogo tabellare dell'apprendimento su tutte le famiglie di mercato."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM market_family_stats ORDER BY efficacy_weight DESC
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
