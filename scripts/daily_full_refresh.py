#!/usr/bin/env python3
"""
BAgent Master Runner: One-Click Daily Refresh (Passo A -> B -> C -> D)
Esegue:
  Passo A: Sincronizzazione telemetria 2026/27 in data/bagent.db
  Passo B: Scraping quote live di giornata in data/netwin_live_odds.json
  Passo C: Generazione di SNAPSHOT_OGGI.json fresco e allineato al portale
  Passo D: Validazione deterministica Gate 0 - Gate 8 (Manifesto BAgent)
"""

import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bagent.db"
NETWIN_PATH = ROOT / "data" / "netwin_live_odds.json"
ODDSPEDIA_PATH = ROOT / "reports" / "oddspedia" / "latest_signals.json"
SCHEDINE_PATH = ROOT / "portal" / "schedine.json"
SNAPSHOT_PATH = ROOT / "SNAPSHOT_OGGI.json"


def run_step_script(script_rel_path: str, step_label: str) -> bool:
    script_path = ROOT / script_rel_path
    print(f"\n============================================================")
    print(f"{step_label}: Esecuzione {script_rel_path}")
    print(f"============================================================")
    if not script_path.exists():
        print(f"[ERRORE] Script non trovato: {script_path}")
        return False

    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path)],
        cwd=str(ROOT),
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode == 0


def build_snapshot_oggi(today_str: str) -> Dict[str, Any]:
    schedine_data = {}
    if SCHEDINE_PATH.exists():
        schedine_data = json.loads(SCHEDINE_PATH.read_text(encoding="utf-8"))

    netwin_data = {"timestamp": "", "total_matches": 0, "matches": []}
    if NETWIN_PATH.exists():
        netwin_data = json.loads(NETWIN_PATH.read_text(encoding="utf-8"))

    oddspedia_data = {"scanned_at": datetime.now().isoformat(), "total_signals": 0, "signals": []}
    if ODDSPEDIA_PATH.exists():
        try:
            oddspedia_data = json.loads(ODDSPEDIA_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    active_portfolio = schedine_data.get("present", [])
    past_slips = schedine_data.get("past", [])
    profit_label = schedine_data.get("profit_label", "+0.00 EUR")

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "slate_date": today_str,
        "active_portfolio_tonight": active_portfolio,
        "historical_portfolio_performance": {
            "profit_label": profit_label,
            "past_slips_count": len(past_slips),
        },
        "oddspedia_market_signals": oddspedia_data,
        "netwin_live_odds": netwin_data,
    }

    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[PASSO C] SNAPSHOT_OGGI.json generato con successo per la data {today_str}.")
    return snapshot


def validate_gates_0_to_8(snapshot: Dict[str, Any], today_str: str) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if snapshot.get("slate_date") != today_str:
        errors.append(f"[GATE 0] slate_date ({snapshot.get('slate_date')}) non corrisponde a oggi ({today_str}).")

    active_tickets = snapshot.get("active_portfolio_tonight", [])
    iso_date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}")
    for t in active_tickets:
        t_id = t.get("id", "UNKNOWN")
        for leg in t.get("legs", []):
            when_str = str(leg.get("when", "")).strip()
            if not iso_date_pattern.match(when_str):
                errors.append(
                    f"[GATE 0 / REGOLA #76] Formato data/ora incompleto in {t_id} ({leg.get('match')}): '{when_str}'. "
                    "Richiesto formato YYYY-MM-DD HH:MM CEST."
                )

    if not DB_PATH.exists():
        errors.append("[GATE 1 / REGOLA #55] Database data/bagent.db non trovato.")
    else:
        conn = sqlite3.connect(str(DB_PATH))
        try:
            cnt_m = conn.execute("SELECT COUNT(*) FROM matches;").fetchone()[0]
            cnt_t = conn.execute("SELECT COUNT(*) FROM team_telemetry_2026;").fetchone()[0]
            if cnt_m < 50 or cnt_t < 20:
                errors.append(f"[GATE 1 / REGOLA #55] Telemetria insufficiente in bagent.db (matches={cnt_m}, teams={cnt_t}).")
        except Exception as e:
            errors.append(f"[GATE 1 / REGOLA #55] Errore lettura tabelle SQLite: {e}")
        finally:
            conn.close()

    netwin_matches = snapshot.get("netwin_live_odds", {}).get("matches", [])
    today_compact = today_str.replace("-", "")
    today_matches = [
        m for m in netwin_matches
        if today_str in str(m.get("kickoff", "")) or today_compact in str(m.get("kickoff", ""))
    ]
    if len(today_matches) == 0:
        warnings.append(f"[GATE 2] 0 match trovati con kickoff odierno ({today_str}) in data/netwin_live_odds.json.")

    for t in active_tickets:
        t_id = t.get("id", "UNKNOWN")
        for leg in t.get("legs", []):
            try:
                odd_val = float(str(leg.get("odd", "0")).replace(",", "."))
                if odd_val < 1.20:
                    errors.append(f"[GATE 3] Quota sotto il minimo legale (1.20) in {t_id}: {leg.get('match')} @ {odd_val}")
            except ValueError:
                errors.append(f"[GATE 3] Quota non numerica in {t_id}: {leg.get('odd')}")

            pick_clean = str(leg.get("pick", "")).strip().upper()
            if pick_clean in ("1", "X", "2", "1X2: 1", "1X2: X", "1X2: 2", "1X2: 1", "1X2: 2"):
                if t_id.startswith("TICKET_USER_"):
                    warnings.append(f"[GATE 3 / REGOLA #82 (AVVISO UTENTE)] Segno 1X2 fisso manuale utente in {t_id}: {leg.get('match')} -> {pick_clean}")
                else:
                    errors.append(f"[GATE 3 / REGOLA #82] Segno 1X2 fisso non protetto rilevato in {t_id}: {leg.get('match')} -> {pick_clean}")

    for t in active_tickets:
        t_id = t.get("id", "UNKNOWN")
        legs_count = len(t.get("legs", []))
        if "GEMME" in t_id.upper() and legs_count > 2:
            errors.append(f"[GATE 4 / REGOLA #83] Il Ticket Gemme ({t_id}) contiene {legs_count} selezioni (massimo consentito: 2).")
        elif legs_count > 6:
            warnings.append(f"[GATE 4] Il ticket {t_id} contiene {legs_count} selezioni (consigliato max 3-4 da Manifesto).")

    for t in active_tickets:
        t_id = t.get("id", "UNKNOWN")
        for leg in t.get("legs", []):
            pick_str = str(leg.get("pick", ""))
            if any(k in pick_str.lower() for k in ("tiri in porta", "cartellino", "assist", "marcatore", "parate")):
                if "sostituto" not in pick_str.lower() and "squadra" not in pick_str.lower() and "over" not in pick_str.lower():
                    warnings.append(f"[GATE 5 / REGOLA #84] Player Prop senza dicitura 'Sostituto' in {t_id}: {pick_str}")

    rosters_dir = ROOT / "data" / "rosters_2026"
    if not rosters_dir.exists():
        warnings.append("[GATE 6 / REGOLA #85] Cartella data/rosters_2026 non trovata.")

    seen_matches: Dict[str, List[str]] = {}
    for t in active_tickets:
        t_id = t.get("id", "UNKNOWN")
        for leg in t.get("legs", []):
            m_norm = str(leg.get("match", "")).lower().strip()
            if m_norm:
                seen_matches.setdefault(m_norm, []).append(t_id)
    for m_norm, t_list in seen_matches.items():
        if len(t_list) > 1:
            warnings.append(
                f"[GATE 7 / REGOLA #86] Partita duplicata su piu schedine attive ('{m_norm}' presente in: {', '.join(t_list)})."
            )

    total_stake = 0.0
    for t in active_tickets:
        raw_s = re.sub(r"[^\d.,]", "", str(t.get("stake", "0"))).replace(",", ".")
        try:
            total_stake += float(raw_s)
        except ValueError:
            pass
    if total_stake > 30.0:
        warnings.append(f"[GATE 8] Esposizione totale attiva elevata: {total_stake:.2f} EUR (soglia raccomandata <= 22.50 EUR su 150 EUR).")

    print("\n============================================================")
    print("PASSO D: REPORT DI CONFORMITA (GATE 0 - GATE 8)")
    print("============================================================")
    for w in warnings:
        print(f"  [AVVISO] {w}")
    for e in errors:
        print(f"  [ERRORE BLOCCANTE] {e}")

    if not errors:
        print("  [OK] TUTTI I GATE OBBLIGATORI SUPERATI CON SUCCESSO.")
    return (len(errors) == 0), errors


def main() -> int:
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"AVVIO BAGENT ONE-CLICK DAILY REFRESH - DATA: {today_str}")

    ok_a = run_step_script("scripts/sync_live_telemetry.py", "PASSO A (Telemetria SQLite 2026/27)")
    if not ok_a:
        print("[ERRORE CRITICO] Passo A fallito.")
        return 1

    ok_b = run_step_script("scripts/fetch_netwin_daily_odds.py", "PASSO B (Quote Live Netwin di Giornata)")
    if not ok_b:
        print("[AVVISO] Passo B terminato con codice non-zero, procedo con i dati disponibili.")

    snapshot = build_snapshot_oggi(today_str)

    passed, _ = validate_gates_0_to_8(snapshot, today_str)
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
