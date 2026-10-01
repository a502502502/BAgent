#!/usr/bin/env python3
"""
scripts/live_user_tickets_watcher.py — Monitoraggio Live 24/7 Schedine Utente e Notifiche.

Monitora in tempo reale (feed Flashscore):
- Germania vs Serbia (20:45 CEST)
- Galles vs Norvegia (20:45 CEST)
- Danimarca vs Portogallo (20:45 CEST)
- Grecia vs Olanda (20:45 CEST)

Aggiorna automaticamente:
- portal/schedine.html & portal/schedine.json
- Database bagent.db (ticket_ledger / bet_leg_ledger)
- Notifiche Telegram istantanee su ogni variazione di punteggio, HT e FT
"""

from __future__ import annotations
import json
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
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except:
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_user_tickets() -> list[dict]:
    if not TICKETS_FILE.exists():
        return []
    try:
        return json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
    except:
        return []


def run_cycle(engine: FlashscoreLiveEngine, sentinel: TelegramSentinel, state: dict) -> tuple[list[str], dict]:
    tickets = load_user_tickets()
    if not tickets:
        return [], state

    feed = engine.fetch_feed() or []
    notifications = []
    has_changes = False

    for ticket in tickets:
        t_id = ticket.get("ticket_id")
        for leg in ticket.get("legs", []):
            match_name = leg.get("match", "")
            if " vs " not in match_name and " - " not in match_name:
                continue
            parts = match_name.split(" vs ") if " vs " in match_name else match_name.split(" - ")
            home, away = parts[0].strip(), parts[1].strip()

            row = find_row(feed, home, away)
            if not row:
                continue

            current_fp = fingerprint(row)
            old_fp = state.get(match_name)

            if old_fp is not None and old_fp != current_fp:
                has_changes = True
                score = row.get("score") or "-"
                phase_code = coarse_phase(str(row.get("status_code") or ""))
                phase_label = _PHASE_IT.get(phase_code, phase_code)
                
                # Formatta alert
                alert_text = (
                    f"⚽ <b>AGGIORNAMENTO LIVE BAGENT</b>\n"
                    f"🏟️ <b>{home} vs {away}</b>\n"
                    f"📊 Risultato: <b>{score}</b> ({phase_label})\n"
                    f"🎯 Selezione in gioco: <b>{leg.get('market')}</b> @ {leg.get('odds')}\n"
                    f"🎟️ Schedina: <code>{t_id}</code>"
                )
                notifications.append(alert_text)

            state[match_name] = current_fp

    if has_changes:
        # Ricostruisci il portale
        try:
            write_slip_archive(ROOT / "portal" / "schedine.html")
            print(f"[{datetime.now(ROME).strftime('%H:%M:%S')}] 🔄 Portale web aggiornato per variazioni live.")
        except Exception as e:
            print(f"Errore aggiornamento portale: {e}")

    return notifications, state


def main():
    print("=" * 75)
    print("🚀 AVVIO LIVE WATCHER & TELEGRAM DISPATCHER (BAGENT)")
    print("=" * 75)
    
    engine = FlashscoreLiveEngine()
    sentinel = TelegramSentinel()
    state = load_state()

    startup_msg = (
        "🟢 <b>BAgent Sentinel: Live Monitor Attivo</b>\n"
        "Tutte le 4 schedine di Nations League sono sotto osservazione telemetrica.\n"
        "Riceverai notifiche istantanee ad ogni gol, cambio tempo o fischio finale."
    )
    sent = sentinel.send_message(startup_msg)
    if sent:
        print("✅ Notifica di avvio inviata con successo su Telegram!")
    else:
        print("⚠️ Telegram non autorizzato o token non valido. Avviso registrato in console.")

    print(f"📡 Monitoraggio attivo su {TICKETS_FILE.name}. Ciclo ogni {PAUSE_SECONDS}s...")

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
