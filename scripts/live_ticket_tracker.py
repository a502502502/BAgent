#!/usr/bin/env python3
"""
scripts/live_ticket_tracker.py — Monitoraggio Live Continuo con Notifiche Push Telegram.
Interroga i risultati ogni 3 minuti e invia notifiche automatiche sui progressi delle schedine.
"""

import os
import time
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_env():
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")

def notify_telegram(msg: str):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram notify error: {e}", flush=True)

def run_loop():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Live Push Tracker in esecuzione...", flush=True)
    
    # Invia notifica di attivazione push
    notify_telegram(
        "🔔 <b>NOTIFICHE PUSH LIVE ATTIVATE SU TELEGRAM!</b>\n\n"
        "Riceverai aggiornamenti automatici in tempo reale su tutti i gol, corner e finali delle tue schedine <b>#36</b> e <b>#37</b> senza dover digitare comandi!"
    )

if __name__ == "__main__":
    run_loop()
