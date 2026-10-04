#!/usr/bin/env python3
"""
services/bridge/mcp_team_bus.py — MCP Server per la Chat Comune tra Cursor e Antigravity.

Questo server MCP implementa lo standard Model Context Protocol (MCP 2.x) per consentire
a Cursor ed Antigravity di condividere la stessa memoria, passarsi messaggi, condividere audit
di quote, calibrazioni devigged e lo stato dei ticket in tempo reale.

Configurazione in Cursor:
Settings -> Features -> MCP -> "Add New MCP Server"
- Name: BAgent_Team_Bus
- Type: command
- Command: /opt/homebrew/bin/python3 /Users/flashmac/Projects/BAgent/services/bridge/mcp_team_bus.py
"""

from __future__ import annotations
import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "storage" / "database" / "bagent.db"
CHAT_MD_PATH = ROOT / "docs" / "SHARED_CHAT.md"

def init_chat_db():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS team_chat_bus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sender TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            data_json TEXT DEFAULT '{}'
        )
    """)
    conn.commit()
    conn.close()

def append_to_shared_md(sender: str, category: str, message: str, ts: str):
    header_line = f"\n### [{ts}] 💬 {sender.upper()} ({category})\n"
    body_line = f"{message.strip()}\n"
    sep = "\n---\n"
    
    if not CHAT_MD_PATH.exists():
        CHAT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        initial_content = (
            "# BAgent — Shared Chat Bus (Cursor 🤝 Antigravity)\n\n"
            "> Questo canale registra la comunicazione sincronizzata in tempo reale tra Cursor e Antigravity.\n\n"
            "---\n"
        )
        CHAT_MD_PATH.write_text(initial_content + header_line + body_line + sep, encoding="utf-8")
    else:
        with open(CHAT_MD_PATH, "a", encoding="utf-8") as f:
            f.write(header_line + body_line + sep)

init_chat_db()

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    print("ERRORE: Libreria mcp non trovata. Installa con `pip install mcp`.", file=sys.stderr)
    sys.exit(1)

server = MCPServer("bagent_team_bus")

@server.tool()
def post_team_message(sender: str, message: str, category: str = "GENERAL", data_json: str = "") -> str:
    """
    Invia un messaggio nella chat comune tra Cursor e Antigravity.
    
    Parametri:
    - sender: Nome dell'agente o utente ('CURSOR', 'ANTIGRAVITY', 'USER')
    - message: Testo del messaggio o riepilogo dell'analisi
    - category: Tipologia ('ODDS_AUDIT', 'TACTICAL_NOTE', 'TICKET_PROPOSAL', 'CODE_CHANGE', 'GENERAL')
    - data_json: Opzionale stringa JSON con dati strutturati (es. quote Netwin, parametri xG)
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_json = "{}"
    if data_json:
        try:
            # Valida che sia json ben formato
            parsed = json.loads(data_json)
            clean_json = json.dumps(parsed)
        except Exception:
            clean_json = json.dumps({"raw": data_json})

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO team_chat_bus (timestamp, sender, category, message, data_json)
        VALUES (?, ?, ?, ?, ?)
    """, (ts, sender.upper(), category.upper(), message, clean_json))
    msg_id = cur.lastrowid
    conn.commit()
    conn.close()

    append_to_shared_md(sender=sender, category=category, message=message, ts=ts)
    return f"✅ Messaggio #{msg_id} registrato con successo da {sender.upper()} [{category.upper()}]."

@server.tool()
def get_team_chat(limit: int = 10, category: str = "") -> str:
    """
    Legge gli ultimi messaggi scambiati tra Cursor e Antigravity nella chat comune.
    
    Parametri:
    - limit: Numero di messaggi da recuperare (default: 10, max: 50)
    - category: Filtro opzionale per categoria (es. 'ODDS_AUDIT', 'TICKET_PROPOSAL')
    """
    limit = max(1, min(50, limit))
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    if category:
        cur.execute("""
            SELECT id, timestamp, sender, category, message, data_json
            FROM team_chat_bus
            WHERE category = ?
            ORDER BY id DESC LIMIT ?
        """, (category.upper(), limit))
    else:
        cur.execute("""
            SELECT id, timestamp, sender, category, message, data_json
            FROM team_chat_bus
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "Nessun messaggio presente nella chat comune."

    rows.reverse()
    output = [f"=== ULTIMI {len(rows)} MESSAGGI CHAT COMUNE (CURSOR 🤝 ANTIGRAVITY) ==="]
    for r in rows:
        m_id, ts, sender, cat, msg, d_json = r
        output.append(f"\n[#{m_id} | {ts}] {sender} ({cat}):\n{msg}")
        if d_json and d_json != "{}":
            output.append(f"  📦 Dati: {d_json}")
    
    return "\n".join(output)

@server.tool()
def get_active_system_state() -> str:
    """
    Restituisce lo stato attuale del sistema BAgent: bankroll, ultimi ticket e regole in vigore.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT ticket_id, date_created, description, total_odds, stake_eur, payout_eur, status FROM ticket_ledger ORDER BY date_created DESC LIMIT 5")
    tickets = cur.fetchall()
    conn.close()

    lines = ["=== STATO SISTEMA BAGENT ==="]
    lines.append("• Divieto Tennis: ATTIVO E PERMANENTE (100% Calcio)")
    lines.append("• Bankroll Ufficiale: €182.18 (post-vincita Ticket C +€32.99)")
    lines.append("\nUltimi Ticket nel Ledger:")
    for t in tickets:
        lines.append(f" - [{t[6]}] {t[0]}: {t[2]} | Quota {t[3]}x | Stake €{t[4]} | Res: €{t[5]}")
    
    return "\n".join(lines)

@server.tool()
def calculate_dixon_coles_edge(match_name: str, market_name: str, odd: float, xg_home: float, xg_away: float) -> str:
    """
    Calcola rapidamente la probabilità reale Dixon-Coles, la fair odd e l'edge matematico reale per un mercato.
    
    Parametri:
    - match_name: Nome della partita (es. 'Serbia vs Olanda')
    - market_name: Mercato (es. '1X', 'X2', 'Under 3.5', 'Over 1.5')
    - odd: Quota reale bookmaker
    - xg_home: Parametro xG/lambda squadra di casa
    - xg_away: Parametro xG/lambda squadra ospite
    """
    try:
        from services.analysis.xg_poisson_engine import QuantitativeEngine
        qe = QuantitativeEngine()
        p = qe.goal_market_probability(xg_home, xg_away, market_name)
        if p is None:
            return f"❌ Mercato '{market_name}' non riconosciuto dal motore Dixon-Coles."
        
        fair = 1.0 / p if p > 0 else 999.0
        edge = (p * odd) - 1.0
        passed_prob = p >= 0.72
        passed_edge = edge >= 0.04
        edge_label = "ok" if passed_edge else "WARNING informativo (non bloccante)"
        prob_label = "ok" if passed_prob else "WARNING informativo (etichetta)"

        return (
            f"=== AUDIT MATEMATICO: {match_name} ===\n"
            f"• Mercato: '{market_name}' @ {odd:.2f}\n"
            f"• Parametri xG: {xg_home:.2f} - {xg_away:.2f}\n"
            f"• P(Reale Dixon-Coles): {p*100:.1f}% ({prob_label})\n"
            f"• Fair Odd: @{fair:.2f}\n"
            f"• Edge Matematico: {edge*100:+.1f}% ({edge_label})\n"
            f"• Esito: calcolabile — edge/P non decidono da soli se considerare la scommessa"
        )
    except Exception as e:
        return f"Errore nel calcolo quantitativo: {e}"

if __name__ == "__main__":
    # Esegue il server MCP su stdio per Cursor
    server.run()
