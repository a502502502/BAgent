#!/usr/bin/env python3
"""
scripts/export_certified_snapshot.py

Esporta uno snapshot certificato leggero da data/bagent.db (o storage/database/bagent.db)
in un JSON che può essere condiviso o committato.

Uso:
    python scripts/export_certified_snapshot.py
    python scripts/export_certified_snapshot.py --teams "Bayern,Arsenal,Real Madrid"
    python scripts/export_certified_snapshot.py --output data/certified_snapshot.json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def find_db() -> Path | None:
    candidates = [
        ROOT / "data" / "bagent.db",
        ROOT / "storage" / "database" / "bagent.db",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def table_info(conn: sqlite3.Connection) -> dict[str, Any]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    summary = {}
    for t in tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            count = cur.fetchone()[0]
        except Exception:
            count = None
        # Sample columns
        try:
            cur.execute(f'PRAGMA table_info("{t}")')
            cols = [row[1] for row in cur.fetchall()]
        except Exception:
            cols = []
        summary[t] = {"count": count, "columns": cols[:30]}
    return {"tables": summary, "table_names": tables}


def safe_query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        return [{"_error": str(e), "_sql": sql}]


def export_team_stats(conn: sqlite3.Connection, team_filter: list[str] | None = None) -> list[dict]:
    # Try common patterns
    candidates = [
        "SELECT * FROM team_stats LIMIT 500",
        "SELECT * FROM teams LIMIT 300",
        "SELECT * FROM team LIMIT 300",
    ]
    for sql in candidates:
        rows = safe_query(conn, sql)
        if rows and "_error" not in rows[0]:
            if team_filter:
                filtered = []
                for r in rows:
                    text = json.dumps(r, default=str).lower()
                    if any(t.lower() in text for t in team_filter):
                        filtered.append(r)
                return filtered[:200]
            return rows[:200]
    return []


def export_recent_matches(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    candidates = [
        "SELECT * FROM matches ORDER BY rowid DESC LIMIT ?",
        "SELECT * FROM fixtures ORDER BY rowid DESC LIMIT ?",
        "SELECT * FROM tracked_fixtures ORDER BY rowid DESC LIMIT ?",
    ]
    for sql in candidates:
        rows = safe_query(conn, sql, (limit,))
        if rows and "_error" not in rows[0]:
            return rows
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Export certified snapshot from bagent.db")
    parser.add_argument("--output", "-o", default="data/certified_snapshot.json", help="Output JSON path")
    parser.add_argument("--teams", help="Comma-separated team names to filter")
    parser.add_argument("--db", help="Explicit path to bagent.db")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else find_db()
    if not db_path or not db_path.exists():
        print("ERRORE: bagent.db non trovato. Cerca in data/bagent.db o storage/database/bagent.db", file=sys.stderr)
        return 1

    team_filter = [t.strip() for t in args.teams.split(",")] if args.teams else None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    snapshot = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_db": str(db_path.relative_to(ROOT)) if db_path.is_relative_to(ROOT) else str(db_path),
        "schema": table_info(conn),
        "team_stats_sample": export_team_stats(conn, team_filter),
        "recent_matches": export_recent_matches(conn),
        "notes": "Snapshot leggero per condivisione. Non sostituisce il DB completo né il Reality Gate live.",
    }

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

    print(f"Snapshot esportato: {out}")
    print(f"Tabelle trovate: {len(snapshot['schema']['table_names'])}")
    print(f"Team stats sample: {len(snapshot['team_stats_sample'])} righe")
    print(f"Match recenti: {len(snapshot['recent_matches'])} righe")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
