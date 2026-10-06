#!/usr/bin/env python3
"""
scripts/monitor_user_ticket_06ott.py — Monitoraggio Live della Schedina SNAI a 8 Eventi.
Invia gli aggiornamenti su Telegram se il bot token e attivo, e traccia gli stati in locale.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Token o Chat ID non configurati.", flush=True)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8
        )
        if r.ok:
            print("[TELEGRAM] Notifica inviata con successo!", flush=True)
            return True
        else:
            print(f"[TELEGRAM ERRORE {r.status_code}] {r.text}", flush=True)
            return False
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] {e}", flush=True)
        return False


def notify_ticket_registration():
    ticket_file = ROOT / "reports/tickets/ticket_giocato_06ott_8legs.json"
    with open(ticket_file, encoding="utf-8") as f:
        ticket = json.load(f)

    lines = [
        "<b>SCHEDINA SNAI ATTIVA INSERITA NEL SISTEMA</b>",
        f"Data: <b>{ticket['date_played']}</b> | Quota: <b>{ticket['total_odds']}</b>",
        f"Puntata: <b>{ticket['stake_eur']:.2f} EUR</b> | Vincita Potenziale: <b>{ticket['potential_payout_eur']:.2f} EUR</b>",
        "------------------------------------"
    ]
    for m in ticket["matches"]:
        lines.append(f"• [{m['kickoff_cest'][11:]}] <b>{m['match']}</b>: {m['selection']} @ {m['odds']} ({m['target_desc']})")

    lines.append("------------------------------------")
    lines.append("Monitoraggio sentinella attivo sui risultati live.")
    msg = "\n".join(lines)
    return send_telegram(msg)


if __name__ == "__main__":
    print("Verifica connessione Telegram...")
    res = notify_ticket_registration()
    print("Esito invio Telegram:", res)
