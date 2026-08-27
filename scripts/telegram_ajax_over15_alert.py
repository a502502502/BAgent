"""
BAgent Telegram Live Goal Alert for Ajax vs Sion Over 1.5.
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

def push_ajax_over15_hit():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"⚽⚽ <b>GOL AD AMSTERDAM! OVER 1.5 GOL PRESO AL 100%!</b> ({now})\n\n"
        f"🇳🇱 <b>Ajax vs FC Sion (36' 1°T)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚽ <b>Risultato Live</b>: <b>0 - 2</b> *(Doppietta di Winsley Boteli al 19' e 36')*\n"
        f"🟢 <b>STATUS SELEZIONE</b>: <b>OVER 1.5 GOL CENTRATO IN PIENO! ✅</b>\n"
        f"🎯 <b>Ticket #34</b>: 1ª gamba gol già in cassaforte!\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🇮🇹 <b>Hapoel Tel Aviv vs Atalanta (40' 1°T)</b>: <b>0 - 0</b> *(Dea all'attacco)*\n"
        f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Chelsea vs Luton Town (10' 1°T)</b>: <b>0 - 0</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <i>Ticket #34 (Stake 20.00 € ➔ Pot. 96.07 €)</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_ajax_over15_hit()
    if success:
        print("✅ Alert Over 1.5 Ajax inviato su Telegram!")
