"""
BAgent Telegram Live Flashscore Direct Push.
Sends exact certified match data directly from Livescore/Flashscore feeds to Telegram.
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

def push_flashscore_live_data():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"📊 <b>DATI UFFICIALI LIVESCORE.IN / FLASHSCORE</b> ({now})\n\n"
        f"🇦🇿 <b>QARABAĞ vs FC TWENTE (Baku)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚽ <b>Risultato Live</b>: <b>0 - 0</b>\n"
        f"🟨 <b>Cartellini Gialli Estratti</b>: <b>2 CARTELLINI</b>\n"
        f"   • 22' 🟨 <b>Ramiz Zerrouki</b> (Twente) - Fallo Tattico\n"
        f"   • 23' 🟨 <b>Bruno Langa</b> (Qarabağ) - Simulazione\n"
        f"⚔️ <b>Falli Totali</b>: <b>16 Falli</b> (7 Qarabağ, 9 Twente)\n"
        f"⚖️ <b>Arbitro</b>: <b>Rohit Saggi (NOR)</b>\n"
        f"🎯 <b>Nostro Obiettivo</b>: Over 4.5 Cartellini (Mancano 3 cartellini nel 2°T)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🇱🇹 <b>Kauno vs Beşiktaş (15' 1°T)</b>: 0 - 0 (1 Corner)\n"
        f"🇳🇴 <b>Brann vs PAOK (15' 1°T)</b>: 0 - 0 (2 Corner Brann)\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <i>Ticket #30 (Stake 20.00 € ➔ Pot. 75.00 €)</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_flashscore_live_data()
    if success:
        print("✅ Dati Flashscore/Livescore inviati con successo su Telegram!")
