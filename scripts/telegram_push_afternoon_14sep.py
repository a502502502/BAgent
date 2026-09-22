"""
Telegram Push for Ticket #83 and #84 (Afternoon slate 14 September 2026).
"""

import sys
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import requests
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=8)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def push_afternoon_tickets():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"☀️ <b>SCHEDINA POMERIDIANA PRONTA! (START ORE 14:30)</b> ({now})\n\n"
        f"🏆 <b>TICKET #83: QUATERNA D'ORO (Quota: 4.06×)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 🇺🇦 <b>Dynamo Kyiv vs Epitsentr</b> (14:30)\n"
        f"   └ 🎯 1 + Over 1.5 Gol @ 1.40\n\n"
        f"2️⃣ 🇺🇦 <b>Shakhtar Donetsk vs Ch. Odesa</b> (17:00)\n"
        f"   └ 🎯 1 + Over 1.5 Gol @ 1.42\n\n"
        f"3️⃣ 🇷🇴 <b>U. Cluj vs Otelul Galati</b> (17:00)\n"
        f"   └ 🎯 1X + Under 3.5 Gol @ 1.48\n\n"
        f"4️⃣ 🇸🇦 <b>Al Shamal vs Al Ittihad</b> (18:00)\n"
        f"   └ 🎯 X2 + Over 1.5 Gol @ 1.38\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎟️ <b>Codice Netwin 1-Click</b>: <code>NW-1430-T83</code>\n"
        f"💵 <b>Stake Consigliato</b>: 15.00 € (o 20.00 €)\n"
        f"💰 <b>VINCITA A CASSA</b>: <b>60.90 € — 81.20 €</b> 🚀\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ <b>TICKET #84: RADDOPPIO BLINDATO (Quota: 2.38×)</b>\n"
        f"🎟️ <b>Codice Netwin</b>: <code>NW-1430-T84</code>\n"
        f"👉 Dinamo Kyiv 1+O1.5 + Shakhtar 1+O1.5 + U. Cluj 1X\n"
        f"💰 20.00 € ➔ <b>47.60 € a Cassa</b>!"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_afternoon_tickets()
    if success:
        print("✅ Alert Schedina Pomeridiana inviato con successo su Telegram!")
