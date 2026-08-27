"""
BAgent Telegram Push for Recalibrated Ticket #35.
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

def push_ticket_35_recalibrated():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"⚡ <b>QUOTE NETWIN LIVE RICALIBRATE (TICKET #35)</b> ({now})\n\n"
        f"🛡️ <b>QUATERNA D'ACCIAIO RECUPERO & RILANCIO (START 20:30):</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Chelsea vs Luton Town</b> (20:30)\n"
        f"   └ 🎯 1 + Over 1.5 Gol @ <b>1.28</b>\n\n"
        f"2️⃣ 🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Brighton vs Tromsø</b> (20:30)\n"
        f"   └ 🎯 1X + Over 1.5 Gol @ <b>1.25</b>\n\n"
        f"3️⃣ 🇪🇸 <b>Barcellona vs Athletic Bilbao</b> (21:00)\n"
        f"   └ 🎯 1X + Over 1.5 Gol @ <b>1.28</b>\n\n"
        f"4️⃣ 🇷🇸 <b>Partizan vs Getafe</b> (21:00)\n"
        f"   └ 🎯 Over 4.5 Cartellini @ <b>1.83</b> 🟨\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎟️ <b>Codice Netwin 1-Click</b>: <code>NW-2030-T35</code>\n"
        f"🎯 <b>Nuova Quota Totale</b>: <b>3.75×</b> 🚀\n"
        f"💵 <b>Stake Consigliato</b>: <b>15.00 € (o 20.00 €)</b>\n"
        f"💰 <b>VINCITA A CASSA</b>: <b>56.25 € — 75.00 €</b>\n"
        f"📈 <b>Guadagno Netto Pulito</b>: <b>+{21.25 if True else 0:.2f} € — +35.00 €</b>!\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 <i>Incolla NW-2030-T35 su Netwin prima del via delle 20:30!</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_ticket_35_recalibrated()
    if success:
        print("✅ Alert Ticket #35 ricalibrato inviato su Telegram!")
