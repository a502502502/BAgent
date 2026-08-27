"""
BAgent - Track-Record Analytics & Market Performance Engine
Modulo per la memorizzazione strutturata, backtesting e calcolo del ROI/Yield
per ciascuna tipologia di mercato (Corner, Gol/DC, Cartellini, Player Props).
"""

import sys
import sqlite3
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

DEFAULT_DB_PATH = root_dir / "storage" / "database" / "bagent.db"

@dataclass
class MarketMetric:
    category: str
    total_bets: int
    won_bets: int
    lost_bets: int
    win_rate_pct: float
    total_staked_eur: float
    total_returned_eur: float
    net_profit_eur: float
    yield_roi_pct: float
    avg_odds: float
    verdict: str

class PerformanceTracker:
    """
    Gestore analitico del Track-Record storico e calcolo delle metriche di performance.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _get_connection(self):
        return sqlite3.connect(str(self.db_path))

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabella Ticket Storici
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_ledger (
                ticket_id TEXT PRIMARY KEY,
                date_created TEXT,
                description TEXT,
                num_legs INTEGER,
                total_odds REAL,
                stake_eur REAL,
                payout_eur REAL,
                profit_loss_eur REAL,
                status TEXT, -- WON, LOST, PENDING, CASHOUT
                strategy_type TEXT, -- SUPER_SICURA, CORNER_TOTALI, DUELLI_1V1, ALTA_QUOTA
                notes TEXT
            )
            """)

            # Tabella Singole Gambe/Selezioni per Mercato
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bet_leg_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT,
                match_name TEXT,
                tournament TEXT,
                market_category TEXT, -- CORNER, GOL_DC, CARTELLINI, PLAYER_PROPS, MULTIGOL, 1X2
                selection TEXT,
                odds REAL,
                estimated_prob REAL,
                edge_pct REAL,
                result_status TEXT, -- WON, LOST, VOID, PENDING
                clv_pct REAL,
                FOREIGN KEY (ticket_id) REFERENCES ticket_ledger(ticket_id)
            )
            """)
            conn.commit()

    def record_ticket(
        self,
        ticket_id: str,
        date_created: str,
        description: str,
        num_legs: int,
        total_odds: float,
        stake_eur: float,
        payout_eur: float,
        status: str,
        strategy_type: str,
        legs: List[Dict[str, Any]],
        notes: str = ""
    ):
        """Registra un ticket completo con tutte le sue selezioni disaggregate."""
        profit_loss = payout_eur - stake_eur if status == "WON" else (-stake_eur if status == "LOST" else 0.0)
        if status == "CASHOUT":
            profit_loss = payout_eur - stake_eur

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO ticket_ledger 
            (ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss, status, strategy_type, notes))

            # Inserisci le gambe
            for leg in legs:
                cursor.execute("""
                INSERT INTO bet_leg_ledger
                (ticket_id, match_name, tournament, market_category, selection, odds, estimated_prob, edge_pct, result_status, clv_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticket_id,
                    leg.get("match", ""),
                    leg.get("tournament", ""),
                    leg.get("category", "GOL_DC"),
                    leg.get("selection", ""),
                    leg.get("odds", 1.0),
                    leg.get("prob", 0.5),
                    leg.get("edge", 0.0),
                    leg.get("status", "PENDING"),
                    leg.get("clv", 0.0)
                ))
            conn.commit()

    def get_market_analytics(self) -> List[MarketMetric]:
        """Calcola Yield, ROI e Win Rate per ogni categoria di mercato."""
        metrics = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                market_category,
                COUNT(*) as total_bets,
                SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) as won_bets,
                SUM(CASE WHEN result_status = 'LOST' THEN 1 ELSE 0 END) as lost_bets,
                AVG(odds) as avg_odds
            FROM bet_leg_ledger
            WHERE result_status IN ('WON', 'LOST')
            GROUP BY market_category
            """)
            rows = cursor.fetchall()

            for r in rows:
                cat, total, won, lost, avg_o = r
                win_rate = (won / total * 100.0) if total > 0 else 0.0
                
                # Stima Stake / Return proporzionale per gamba (base 10€ flat per leg)
                staked = total * 10.0
                returned = (won * avg_o * 10.0)
                net = returned - staked
                yield_roi = (net / staked * 100.0) if staked > 0 else 0.0

                if yield_roi >= 15.0 and win_rate >= 75.0:
                    verdict = "💎 ELITE MARKET (Massimizza Allocazione Kelly)"
                elif yield_roi > 0:
                    verdict = "⭐ PROFITABLE (Mercato Solido e Positivo)"
                elif win_rate >= 60.0:
                    verdict = "👀 NEUTRAL / BREAK-EVEN (Da calibrare)"
                else:
                    verdict = "⚠️ SOTTO-PERFORMANTE (Riduci Stake o Filtra)"

                metrics.append(MarketMetric(
                    category=cat,
                    total_bets=total,
                    won_bets=won,
                    lost_bets=lost,
                    win_rate_pct=round(win_rate, 2),
                    total_staked_eur=round(staked, 2),
                    total_returned_eur=round(returned, 2),
                    net_profit_eur=round(net, 2),
                    yield_roi_pct=round(yield_roi, 2),
                    avg_odds=round(avg_o, 2),
                    verdict=verdict
                ))
        return metrics

    def get_global_ledger_summary(self) -> Dict[str, Any]:
        """Riepilogo generale del conto e dei ticket."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                COUNT(*) as total_tickets,
                SUM(CASE WHEN status = 'WON' THEN 1 ELSE 0 END) as won_tickets,
                SUM(CASE WHEN status = 'LOST' THEN 1 ELSE 0 END) as lost_tickets,
                SUM(stake_eur) as total_staked,
                SUM(payout_eur) as total_payout,
                SUM(profit_loss_eur) as total_profit
            FROM ticket_ledger
            WHERE status IN ('WON', 'LOST', 'CASHOUT')
            """)
            row = cursor.fetchone()
            tot, won, lost, staked, payout, profit = row
            tot = tot or 0
            won = won or 0
            lost = lost or 0
            staked = staked or 0.0
            payout = payout or 0.0
            profit = profit or 0.0
            yield_pct = (profit / staked * 100.0) if staked > 0 else 0.0

            return {
                "total_tickets": tot,
                "won_tickets": won,
                "lost_tickets": lost,
                "win_rate_pct": round((won / tot * 100.0) if tot > 0 else 0.0, 2),
                "total_staked_eur": round(staked, 2),
                "total_payout_eur": round(payout, 2),
                "net_profit_eur": round(profit, 2),
                "yield_pct": round(yield_pct, 2)
            }
