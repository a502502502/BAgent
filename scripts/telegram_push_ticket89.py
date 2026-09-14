"""
scripts/telegram_push_ticket89.py — Notifica e Registrazione Ticket #89 (Pomeriggio Quantitativo Quota 10.78x).
"""

import sys
import os
import requests
from datetime import datetime

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

def push_ticket_89():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"🎯 <b>TICKET #89 ACQUISITO & IN CORSO!</b> ({now})\n\n"
        f"🔥 <b>QUINTINA POMERIDIANA QUANTITATIVA (Quota 10.78×)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 🇺🇦 <b>Dynamo Kiev vs Epitsentr</b> (14:30)\n"
        f"   ➔ 🛡️ <b>1X + Under 3.5 @ 1.78</b>\n\n"
        f"2️⃣ 🇬🇷 <b>Panionios vs Apollon</b> (15:00)\n"
        f"   ➔ 🔒 <b>Under 2.5 @ 1.62</b>\n\n"
        f"3️⃣ 🇬🇷 <b>Panthrakikos vs PAOK B</b> (16:00)\n"
        f"   ➔ 🛡️ <b>1X (Doppia Chance) @ 1.38</b>\n\n"
        f"4️⃣ 🇷🇴 <b>U. Cluj vs Otelul Galati</b> (17:00)\n"
        f"   ➔ 💥 <b>Over 2.5 Gol @ 1.76</b>\n\n"
        f"5️⃣ 🇺🇦 <b>Shakhtar vs Chernomorets</b> (17:00)\n"
        f"   ➔ ⚡ <b>1 + MultiGol 2-4 @ 1.54</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎟️ <b>Rif. Netwin</b>: <code>DF07EA090E31DF7C7806</code>\n"
        f"💵 <b>Importo Giocato</b>: <b>10.00 €</b>\n"
        f"🎁 <b>Bonus Multipla</b>: <b>+6.46 €</b>\n"
        f"💰 <b>VINCITA POTENZIALE</b>: <b>114.32 €</b> 🚀\n\n"
        f"⏳ <i>Kickoff primo evento (Dynamo Kiev) tra pochi minuti! Tracker live attivo.</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_ticket_89()
    if success:
        print("✅ Alert Ticket #89 inviato con successo su Telegram!")
    else:
        print("❌ Errore invio Telegram.")
