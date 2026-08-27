"""
BAgent Telegram Live Goal Alert for Ajax vs Sion 2-2 Equalizer.
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

def push_ajax_equalizer():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"⚽⚽⚽ <b>PAREGGIO AJAX! 2 - 2 AD AMSTERDAM!</b> ({now})\n\n"
        f"🇳🇱 <b>Ajax vs FC Sion (46' 2°T)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚽ <b>Risultato Live</b>: <b>2 - 2</b> *(Gol di Klaassen al 39' e Arokodare al 45+1')*\n"
        f"🟢 <b>STATUS SELEZIONE TICKET #34</b>:\n"
        f"   • <b>1X (Doppia Chance Ajax)</b> ➔ <b>🟢 IN CASSA (2-2)</b>\n"
        f"   • <b>Over 1.5 Gol</b> ➔ <b>✅ VINTO (4 Gol Totali!)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🇮🇹 <b>Hapoel vs Atalanta (46' 2°T)</b>: 0 - 0 *(Inizio ripresa, Dea all'attacco)*\n"
        f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Chelsea vs Luton (20' 1°T)</b>: 0 - 0\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <i>Ticket #34 (96.07 €) viaggia a vele spiegate!</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_ajax_equalizer()
    if success:
        print("✅ Alert Pareggio Ajax 2-2 inviato su Telegram!")
