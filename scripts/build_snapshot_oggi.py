#!/usr/bin/env python3
"""
scripts/build_snapshot_oggi.py
Costruisce lo snapshot completo e fresco per Gemini 4 Argon:
- Quote live Netwin (data/netwin_live_odds.json)
- Segnali di mercato Oddspedia (reports/oddspedia/latest_signals.json)
- Campione tabelle da data/bagent.db e storage/database/bagent.db (xG, partite, team, ticket_ledger)
- Match UCL e palinsesto di oggi 14 ottobre 2026
- Salva in SNAPSHOT_OGGI.json nella root del progetto
"""

import json
import sqlite3
import datetime
from pathlib import Path

ROOT = Path("C:/Project/BAgent")

print("[1/4] Estrazione dati da data/bagent.db e storage/database/bagent.db...")
db_data = {}

for db_rel in ["data/bagent.db", "storage/database/bagent.db"]:
    db_path = ROOT / db_rel
    if not db_path.exists():
        continue
    prefix = db_rel.split("/")[0]
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in tables:
        try:
            cur.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 300")
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            key_name = f"{prefix}_{t}"
            db_data[key_name] = [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            pass
    conn.close()

print(f"  - Estratte {len(db_data)} tabelle di database.")

print("[2/4] Caricamento quote live Netwin...")
odds_path = ROOT / "data" / "netwin_live_odds.json"
odds = json.loads(odds_path.read_text(encoding="utf-8")) if odds_path.exists() else {}
print(f"  - Quote Netwin caricate: {odds.get('total_matches', 0)} partite.")

print("[3/4] Caricamento segnali Oddspedia e dati odierni...")
oddspedia_path = ROOT / "reports" / "oddspedia" / "latest_signals.json"
oddspedia = json.loads(oddspedia_path.read_text(encoding="utf-8")) if oddspedia_path.exists() else {}

today_matches_path = ROOT / "scratch" / "today_matches_14oct.json"
today_matches = json.loads(today_matches_path.read_text(encoding="utf-8")) if today_matches_path.exists() else {}

# Portafoglio odierno UCL 14 Ottobre
schedine_path = ROOT / "portal" / "schedine.json"
schedine = json.loads(schedine_path.read_text(encoding="utf-8")) if schedine_path.exists() else {}

print("[4/4] Assemblaggio SNAPSHOT_OGGI.json...")
out = {
    "timestamp": datetime.datetime.now().isoformat(),
    "slate_date": "2026-10-14",
    "ucl_matchday": "Champions League Matchday 3 - Night 2",
    "active_portfolio_tonight": schedine.get("present", []),
    "historical_portfolio_performance": {
        "profit_label": schedine.get("profit_label", "+6.61 EUR"),
        "past_slips_count": len(schedine.get("past", []))
    },
    "oddspedia_market_signals": oddspedia,
    "netwin_live_odds": odds,
    "db_tables_sample": db_data
}

target_file = ROOT / "SNAPSHOT_OGGI.json"
target_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
file_size_mb = target_file.stat().st_size / (1024 * 1024)
print(f"[OK] Creato {target_file} ({file_size_mb:.2f} MB).")
