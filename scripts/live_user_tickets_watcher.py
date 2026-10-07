#!/usr/bin/env python3
"""
scripts/live_user_tickets_watcher.py — Monitoraggio Live Schedine Utente e Notifiche Telegram.

Monitora in tempo reale (feed Flashscore) esclusivamente le schedine attive
e gli eventi odierni, ignorando rigorosamente eventi o ticket conclusi o nel passato.

Regole applicate:
- Nessun emoji o simbolo decorativo nei messaggi Telegram o nei log.
- Filtro temporale rigoroso: eventi con kickoff antecedente a 4 ore fa vengono esclusi dal monitoraggio.
- Solo ticket con status OPEN, PENDING o WAITING_LINEUPS vengono considerati.
- Deduplicazione automatica degli alert per prevenire notifiche ripetute.
"""

from __future__ import annotations
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.football.external.sources.flashscore_live import FlashscoreLiveEngine
from services.live.score_change_watch import find_row, coarse_phase, fingerprint
from services.portal.slip_archive import write_slip_archive
from services.telegram.telegram_sentinel import TelegramSentinel

ROME = ZoneInfo("Europe/Rome")
TICKETS_FILE = ROOT / "data" / "active_user_tickets.json"
STATE_FILE = ROOT / "data" / "live_user_tickets_state.json"
PAUSE_SECONDS = 30

_PHASE_IT = {
    "scheduled": "Non Iniziata",
    "live": "In Corso",
    "ht": "Intervallo (HT)",
    "ft": "Conclusa (FT)"
}


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"matches": {}, "sent_alerts": []}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"matches": {}, "sent_alerts": []}
        data.setdefault("matches", {})
        data.setdefault("sent_alerts", [])
        return data
    except Exception:
        return {"matches": {}, "sent_alerts": []}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_active_user_tickets() -> list[dict]:
    if not TICKETS_FILE.exists():
        return []
    try:
        tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
        if not isinstance(tickets, list):
            return []
        active_statuses = {"OPEN", "PENDING", "WAITING_LINEUPS"}
        return [
            t for t in tickets
            if t.get("status") in active_statuses and not t.get("settled", False)
        ]
    except Exception:
        return []


def parse_kickoff(ko_str: str) -> datetime | None:
    if not ko_str:
        return None
    m = re.search(r"(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2})", ko_str)
    if m:
        dt_str = f"{m.group(1)} {m.group(2)}"
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=ROME)
        except Exception:
            pass
    return None


def is_leg_eligible(leg: dict, now: datetime) -> bool:
    if leg.get("status") in ("WON", "LOST", "VOID"):
        return False
    ko_str = leg.get("kickoff") or leg.get("date_time") or leg.get("time") or ""
    dt = parse_kickoff(ko_str)
    if dt is None:
        return True
    
    # Eventi giocati prima della data odierna vengono scartati
    if dt.date() < now.date():
        return False
    
    # Se il kickoff e' passato da piu' di 4 ore, la partita e' conclusa
    diff_hours = (now - dt).total_seconds() / 3600.0
    if diff_hours > 4.0:
        return False
    
    return True


def run_cycle(engine: FlashscoreLiveEngine, sentinel: TelegramSentinel, state: dict) -> tuple[list[str], dict]:
    tickets = load_active_user_tickets()
    if not tickets:
        return [], state

    now = datetime.now(ROME)
    feed = engine.fetch_feed() or []
    notifications = []
    has_changes = False

    match_state = state.get("matches", {})
    sent_alerts = set(state.get("sent_alerts", []))

    for ticket in tickets:
        t_id = str(ticket.get("ticket_id", "TICKET"))
        for leg in ticket.get("legs", []):
            if not is_leg_eligible(leg, now):
                continue

            match_name = leg.get("match", "")
            if " vs " not in match_name and " - " not in match_name:
                continue
            parts = match_name.split(" vs ") if " vs " in match_name else match_name.split(" - ")
            home, away = parts[0].strip(), parts[1].strip()

            row = find_row(feed, home, away)
            if not row:
                continue

            current_fp = fingerprint(row)
            old_fp = match_state.get(match_name)

            if old_fp is not None and old_fp != current_fp:
                has_changes = True
                score = row.get("score") or "-"
                phase_code = coarse_phase(str(row.get("status_code") or ""))
                phase_label = _PHASE_IT.get(phase_code, phase_code)

                alert_key = f"{t_id}:{match_name}:{phase_code}:{score}"
                if alert_key not in sent_alerts:
                    alert_text = (
                        f"AGGIORNAMENTO LIVE BAGENT\n"
                        f"Partita: {home} vs {away}\n"
                        f"Risultato: {score} ({phase_label})\n"
                        f"Selezione: {leg.get('market')} @ {leg.get('odds')}\n"
                        f"Schedina: {t_id}"
                    )
                    notifications.append(alert_text)
                    sent_alerts.add(alert_key)

            match_state[match_name] = current_fp

    state["matches"] = match_state
    # Mantieni gli ultimi 200 alert per prevenire crescita infinita
    state["sent_alerts"] = list(sent_alerts)[-200:]

    if has_changes:
        try:
            write_slip_archive(ROOT / "portal" / "schedine.html")
            print(f"[{datetime.now(ROME).strftime('%H:%M:%S')}] Portale web aggiornato per variazioni live.")
        except Exception as e:
            print(f"Errore aggiornamento portale: {e}")

    return notifications, state


def main() -> None:
    print("=" * 75)
    print("AVVIO LIVE WATCHER & TELEGRAM DISPATCHER (BAGENT)")
    print("=" * 75)

    engine = FlashscoreLiveEngine()
    sentinel = TelegramSentinel()
    state = load_state()

    active_tickets = load_active_user_tickets()
    print(f"Monitoraggio attivo su {len(active_tickets)} schedine correnti in {TICKETS_FILE.name}.")
    print(f"Ciclo di verifica ogni {PAUSE_SECONDS}s...")

    while True:
        try:
            notifs, state = run_cycle(engine, sentinel, state)
            save_state(state)
            for msg in notifs:
                sentinel.send_message(msg)
                print(f"[ALERT LIVE] {msg.replace(chr(10), ' | ')}", flush=True)
        except Exception as e:
            print(f"Errore ciclo live: {e}", flush=True)

        time.sleep(PAUSE_SECONDS)


if __name__ == "__main__":
    main()
