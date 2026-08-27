"""
BAgent Telegram Push for Ticket #35 (Recovery Counter-bet).
"""

import sys
import os
import requests
from datetime import datetime

# Windows UTF-8 stdout
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"

def send_telegram(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=8)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def push_ticket_35_counterbet():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"🛡️ <b>CONTROPARTITA DI RECUPERO PRONTA (TICKET #35)</b> ({now})\n\n"
        f"🎯 <b>QUATERNA D'ACCIAIO SERALE (START ORE 20:30):</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Chelsea vs Luton Town</b> (20:30)\n"
        f"   └ 🎯 1 + Over 1.5 Gol @ 1.30\n\n"
        f"2️⃣ 🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Brighton vs Tromsø</b> (20:30)\n"
        f"   └ 🎯 1X + Over 1.5 Gol @ 1.25\n\n"
        f"3️⃣ 🇪🇸 <b>Barcellona vs Athletic Bilbao</b> (21:00)\n"
        f"   └ 🎯 1X + Over 1.5 Gol @ 1.28\n\n"
        f"4️⃣ 🇷🇸 <b>Partizan vs Getafe</b> (21:00)\n"
        f"   └ 🎯 Over 3.5 Cartellini @ 1.45\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎟️ <b>Codice Netwin 1-Click</b>: <code>NW-2030-T35</code>\n"
        f"🎯 <b>Quota Totale</b>: <b>3.01×</b>\n"
        f"💵 <b>Stake Consigliato</b>: <b>15.00 € (o 20.00 €)</b>\n"
        f"💰 <b>Vincita a Cassa</b>: <b>45.15 € — 60.20 €</b>\n"
        f"📈 <b>Obiettivo</b>: Recupero 100% Ticket #30 + Profitto Netto Extra!\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 <i>Carica subito il codice NW-2030-T35 su Netwin per il via delle 20:30!</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_ticket_35_counterbet()
    if success:
        print("✅ Alert Contropartita Ticket #35 inviato su Telegram!")
