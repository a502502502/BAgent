#!/usr/bin/env python3
"""Manda un messaggio Telegram a ogni cambio di punteggio delle selezioni in ticket."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.football.external.sources.flashscore_live import FlashscoreLiveEngine
from services.live.score_change_watch import changed_rows
from services.telegram.telegram_sentinel import TelegramSentinel

TICKET = ROOT / "reports" / "tickets" / "ticket_nations_league_25set.json"
STATE = ROOT / "data" / "score_watch_nl25.json"
PAUSE_SECONDS = 30
_PHASE = {"scheduled": "non iniziata", "live": "in corso", "ht": "intervallo", "ft": "finale"}


def _load_state() -> dict:
    if not STATE.exists():
        return {}
    return json.loads(STATE.read_text(encoding="utf-8"))


def _save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _message(alert: dict) -> str:
    phase = _PHASE.get(alert["phase"], alert["phase"])
    minute = f" · {alert['minute']}'" if alert["phase"] == "live" and alert["minute"] else ""
    return (
        f"{alert['match']}\n"
        f"{alert['score']} · {phase}{minute}\n"
        f"{alert['pick']} · {alert['note']}"
    )


def main() -> None:
    ticket = json.loads(TICKET.read_text(encoding="utf-8"))
    legs = ticket["legs"]
    engine = FlashscoreLiveEngine()
    sentinel = TelegramSentinel()
    state = _load_state()
    armed = sentinel.send_message(
        "Notifiche attive sulla Nations League di stasera. "
        "Ti scrivo solo quando cambia un punteggio o la partita va all'intervallo o al finale."
    )
    print(f"avvio ticket={ticket['ticket_id']} telegram={'ok' if armed else 'no'}", flush=True)
    while True:
        try:
            alerts, state = changed_rows(state, legs, engine.fetch_feed())
            _save_state(state)
            for alert in alerts:
                text = _message(alert)
                sent = sentinel.send_message(text)
                print(f"cambio inviato={sent} {text.replace(chr(10), ' | ')}", flush=True)
        except Exception as exc:
            print(f"ciclo saltato: {exc}", flush=True)
        time.sleep(PAUSE_SECONDS)


if __name__ == "__main__":
    main()
