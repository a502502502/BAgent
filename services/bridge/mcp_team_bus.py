#!/usr/bin/env python3
"""
MCP Team Bus — bridge locale Cursor ⟷ Antigravity (Model Context Protocol).

Espone due tool standard:
  • send_agent_message(from_agent, message, data_json)
  • get_agent_inbox(agent, limit, unread_only)

Persistenza: SQLite dedicato (`storage/database/team_bus.db`) + mirror `docs/SHARED_CHAT.md`.

Cursor (project):
  .cursor/mcp.json → server "bagent-team-bus"

Avvio manuale (stdio):
  .venv/bin/python3.14 services/bridge/mcp_team_bus.py

Richiede Python ≥ 3.10 e pacchetto `mcp` (v2: MCPServer).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "storage" / "database" / "team_bus.db"
CHAT_MD_PATH = ROOT / "docs" / "SHARED_CHAT.md"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_chat_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS team_chat_bus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL DEFAULT 'BROADCAST',
                category TEXT NOT NULL DEFAULT 'GENERAL',
                message TEXT NOT NULL,
                data_json TEXT NOT NULL DEFAULT '{}',
                read_by TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        # Migrate older schemas missing recipient/read_by
        cols = {r[1] for r in conn.execute("PRAGMA table_info(team_chat_bus)")}
        if "recipient" not in cols:
            conn.execute(
                "ALTER TABLE team_chat_bus ADD COLUMN recipient TEXT NOT NULL DEFAULT 'BROADCAST'"
            )
        if "read_by" not in cols:
            conn.execute(
                "ALTER TABLE team_chat_bus ADD COLUMN read_by TEXT NOT NULL DEFAULT '[]'"
            )
        conn.commit()


def _parse_data_json(data_json: str) -> str:
    if not data_json or not str(data_json).strip():
        return "{}"
    try:
        return json.dumps(json.loads(data_json), ensure_ascii=False)
    except Exception:
        return json.dumps({"raw": data_json}, ensure_ascii=False)


def append_to_shared_md(sender: str, category: str, message: str, ts: str) -> None:
    header = f"\n### [{ts}] 💬 {sender.upper()} ({category})\n"
    body = f"{message.strip()}\n"
    sep = "\n---\n"
    if not CHAT_MD_PATH.exists():
        CHAT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHAT_MD_PATH.write_text(
            "# BAgent — Shared Chat Bus (Cursor 🤝 Antigravity)\n\n"
            "> Canale sincronizzato tra agenti via MCP Team Bus.\n\n"
            "---\n"
            + header
            + body
            + sep,
            encoding="utf-8",
        )
        return
    with open(CHAT_MD_PATH, "a", encoding="utf-8") as f:
        f.write(header + body + sep)


def store_message(
    from_agent: str,
    message: str,
    data_json: str = "",
    *,
    to_agent: str = "BROADCAST",
    category: str = "GENERAL",
) -> int:
    ts = _now()
    clean = _parse_data_json(data_json)
    sender = (from_agent or "UNKNOWN").strip().upper()
    recipient = (to_agent or "BROADCAST").strip().upper()
    cat = (category or "GENERAL").strip().upper()

    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO team_chat_bus
                (timestamp, sender, recipient, category, message, data_json, read_by)
            VALUES (?, ?, ?, ?, ?, ?, '[]')
            """,
            (ts, sender, recipient, cat, message.strip(), clean),
        )
        msg_id = int(cur.lastrowid)
        conn.commit()

    append_to_shared_md(sender=sender, category=cat, message=message, ts=ts)
    return msg_id


def fetch_inbox(
    agent: str = "CURSOR",
    limit: int = 20,
    unread_only: bool = True,
) -> list[dict[str, Any]]:
    limit = max(1, min(50, int(limit)))
    agent_u = (agent or "CURSOR").strip().upper()

    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp, sender, recipient, category, message, data_json, read_by
            FROM team_chat_bus
            WHERE recipient IN ('BROADCAST', ?) OR sender = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (agent_u, agent_u, 200),
        ).fetchall()

        out: list[dict[str, Any]] = []
        to_mark: list[int] = []
        for r in rows:
            read_by = []
            try:
                read_by = json.loads(r["read_by"] or "[]")
            except Exception:
                read_by = []
            if not isinstance(read_by, list):
                read_by = []
            is_unread = agent_u not in {str(x).upper() for x in read_by}
            if unread_only and not is_unread:
                continue
            # Don't treat own sends as inbox items unless addressed to self
            if r["sender"] == agent_u and r["recipient"] == "BROADCAST":
                if unread_only:
                    continue
            out.append(
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "from": r["sender"],
                    "to": r["recipient"],
                    "category": r["category"],
                    "message": r["message"],
                    "data": json.loads(r["data_json"] or "{}"),
                    "unread": is_unread,
                }
            )
            if is_unread:
                to_mark.append(int(r["id"]))
            if len(out) >= limit:
                break

        for mid in to_mark:
            row = conn.execute(
                "SELECT read_by FROM team_chat_bus WHERE id = ?", (mid,)
            ).fetchone()
            if not row:
                continue
            try:
                rb = json.loads(row["read_by"] or "[]")
            except Exception:
                rb = []
            if not isinstance(rb, list):
                rb = []
            if agent_u not in {str(x).upper() for x in rb}:
                rb.append(agent_u)
                conn.execute(
                    "UPDATE team_chat_bus SET read_by = ? WHERE id = ?",
                    (json.dumps(rb), mid),
                )
        conn.commit()

    out.reverse()
    return out


init_chat_db()

try:
    from mcp.server.mcpserver import MCPServer
except ImportError as exc:
    print(
        "ERRORE: pacchetto mcp non trovato o Python < 3.10.\n"
        "Usa: .venv/bin/python3.14 -m pip install 'mcp>=2.0'\n"
        f"Dettaglio: {exc}",
        file=sys.stderr,
    )
    sys.exit(1)

server = MCPServer(
    name="bagent_team_bus",
    instructions=(
        "BAgent Team Bus: scambia report, audit quote e stato ticket tra Cursor e Antigravity. "
        "Usa send_agent_message per pubblicare, get_agent_inbox per leggere i messaggi in arrivo."
    ),
)


@server.tool()
def send_agent_message(
    from_agent: str,
    message: str,
    data_json: str = "",
    to_agent: str = "BROADCAST",
    category: str = "GENERAL",
) -> str:
    """
    Pubblica un messaggio sul bus condiviso Cursor ⟷ Antigravity.

    Args:
        from_agent: Mittente ('CURSOR', 'ANTIGRAVITY', 'USER', …).
        message: Testo del report / nota / proposta.
        data_json: JSON opzionale (quote Netwin, xG, edge, ticket_id, …).
        to_agent: Destinatario ('BROADCAST' di default, oppure 'CURSOR' / 'ANTIGRAVITY').
        category: ODDS_AUDIT | TACTICAL_NOTE | TICKET_PROPOSAL | CODE_CHANGE | GENERAL.
    """
    if not message or not str(message).strip():
        return "❌ Messaggio vuoto: rifiutato."
    msg_id = store_message(
        from_agent=from_agent,
        message=message,
        data_json=data_json or "",
        to_agent=to_agent,
        category=category,
    )
    return (
        f"✅ Messaggio #{msg_id} da {from_agent.strip().upper()} "
        f"→ {(to_agent or 'BROADCAST').strip().upper()} "
        f"[{(category or 'GENERAL').strip().upper()}]"
    )


@server.tool()
def get_agent_inbox(
    agent: str = "CURSOR",
    limit: int = 20,
    unread_only: bool = True,
) -> str:
    """
    Legge la inbox dell'agente sul bus condiviso (segna come letti i messaggi restituiti).

    Args:
        agent: Agente che sta leggendo ('CURSOR' o 'ANTIGRAVITY').
        limit: Max messaggi (1–50, default 20).
        unread_only: Se True, solo messaggi non ancora letti da questo agente.
    """
    items = fetch_inbox(agent=agent, limit=limit, unread_only=unread_only)
    if not items:
        return f"Inbox vuota per {agent.strip().upper()} (unread_only={unread_only})."

    lines = [
        f"=== INBOX {agent.strip().upper()} — {len(items)} messaggi ===",
    ]
    for it in items:
        flag = "🆕" if it["unread"] else "·"
        lines.append(
            f"\n{flag} [#{it['id']} | {it['timestamp']}] "
            f"{it['from']} → {it['to']} ({it['category']})\n{it['message']}"
        )
        if it["data"] and it["data"] != {}:
            lines.append(f"  📦 {json.dumps(it['data'], ensure_ascii=False)}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Smoke senza stdio: BAGENT_TEAM_BUS_SMOKE=1
    if os.environ.get("BAGENT_TEAM_BUS_SMOKE") == "1":
        mid = store_message(
            "CURSOR",
            "Smoke test Team Bus",
            data_json='{"ok": true}',
            category="GENERAL",
        )
        inbox = fetch_inbox("ANTIGRAVITY", limit=5, unread_only=True)
        print(json.dumps({"stored_id": mid, "inbox_count": len(inbox)}, indent=2))
        sys.exit(0)
    server.run()
