"""
BAgent Telegram Push for Ticket #34 (Netwin Ref: DF07EA081B31840F2C06).
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

def push_ticket_34_registered():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"🟢 <b>NUOVO TICKET #34 GIOCATO & REGISTRATO!</b> ({now})\n\n"
        f"👑 <b>QUINTINA D'ELITE SERALE (Ref: <code>DF07EA081B31840F2C06</code>):</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 🇳🇱 <b>Ajax vs Sion</b> (20:00)\n"
        f"   └ 🎯 1X + Over 1.5 Gol @ 1.22 ➔ ⏳ <b>IN PARTENZA</b>\n\n"
        f"2️⃣ 🇮🇹 <b>Hapoel Tel Aviv vs Atalanta</b> (20:00)\n"
        f"   └ 🎯 X2 + Over 1.5 Gol @ 1.41 ➔ ⏳ <b>IN PARTENZA</b>\n\n"
        f"3️⃣ 🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Chelsea vs Luton Town</b> (20:30)\n"
        f"   └ 🎯 1 (1X2) @ 1.09 ➔ ⏳ <b>PRONTA</b>\n\n"
        f"4️⃣ 🇷🇸 <b>Partizan vs Getafe</b> (21:00)\n"
        f"   └ 🎯 Over 4.5 Cartellini @ 1.83 ➔ ⏳ <b>PRONTA</b>\n\n"
        f"5️⃣ 🇪🇸 <b>Barcellona vs Athletic Bilbao</b> (21:00)\n"
        f"   └ 🎯 1X + Over 2.5 Gol @ 1.40 ➔ ⏳ <b>PRONTA</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Stake Giocato</b>: <b>20.00 €</b>\n"
        f"🎯 <b>Quota Totale Netwin</b>: <b>4.80×</b>\n"
        f"💰 <b>VINCITA POTENZIALE</b>: <b>96.07 € (+76.07 € NETTO)</b> 🏆\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ <i>Radar Live BAgent attivato su tutte le 5 partite!</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_ticket_34_registered()
    if success:
        print("✅ Notifica Ticket #34 inviata con successo su Telegram!")
