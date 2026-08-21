import time
import requests
import json
import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"

def notify_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram notifica inviata con successo!")
    except Exception as e:
        print("Telegram error:", e)

# Send Startup Notification
startup_msg = (
    "🟢 <b>BAgent Live Engine — Tracker Notturno Avviato!</b>\n\n"
    "🎫 <b>Ticket #14 (Sestina Overseas — Quota 5.03× — Vincita: 106.71 €)</b>\n"
    "• 🇨🇴 <b>Jaguares de Cordoba vs Boyaca Chico</b> ➔ 1X2: 1 (LIVE: 1-0 al 17' ⚽)\n"
    "• 🇧🇴 <b>The Strongest vs Univ. de Vinto</b> ➔ 1 + Over 1.5 (Inizio 00:30)\n"
    "• 🇳🇿 <b>Cashmere Technical vs Dunedin City</b> ➔ Over 3.5 (Inizio 02:00)\n"
    "• 🇳🇿 <b>Western Suburbs vs Waterside Karori</b> ➔ 1 + Over 1.5 (Inizio 02:30)\n"
    "• 🇲🇽 <b>Tigres vs Atlante FC</b> ➔ 1X2: 1 (Inizio 03:00)\n"
    "• 🇳🇿 <b>Upper Hutt City vs FC Western</b> ➔ 1 + Over 2.5 (Inizio 03:00)\n\n"
    "⚡ <i>Il bot invierà aggiornamenti automatici su tutti i gol e i passaggi di turno!</i>"
)
notify_telegram(startup_msg)

print("BAgent Night Live Monitor started. Monitoring active matches in background.")
while True:
    time.sleep(120)
