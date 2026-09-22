"""
Telegram Push for Ticket #86 (Sprint Mattina Ore 12:00).
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

def push_morning_sprint():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"🌅 <b>TICKET #86: SPRINT MATTINA & PRANZO PRONTO!</b> ({now})\n\n"
        f"🎯 <b>QUATERNA RAPIDA (START ORE 12:00):</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 🇯🇵 <b>FC Osaka vs Ehime</b> (12:00)\n"
        f"   └ 🎯 1X (Doppia Chance) @ 1.25\n\n"
        f"2️⃣ 🇸🇬 <b>Geylang vs Tanjong Pagar</b> (13:30)\n"
        f"   └ 🎯 Over 2.5 Gol @ 1.35 💣\n\n"
        f"3️⃣ 🌏 <b>Shan United vs Ezra FC</b> (13:30)\n"
        f"   └ 🎯 1 (1X2) @ 1.30\n\n"
        f"4️⃣ 🇺🇦 <b>Dynamo Kyiv vs Epitsentr</b> (14:30)\n"
        f"   └ 🎯 1 + Over 1.5 Gol @ 1.40\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎟️ <b>Codice Netwin 1-Click</b>: <code>NW-1200-T86</code>\n"
        f"🎯 <b>Quota Totale</b>: <b>3.07×</b>\n"
        f"💵 <b>Stake Consigliato</b>: 15.00 € (o 20.00 €)\n"
        f"💰 <b>VINCITA A CASSA</b>: <b>46.05 € — 61.40 €</b> 🚀\n"
        f"⏰ <i>Incasso completo previsto per le 16:15!</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_morning_sprint()
    if success:
        print("✅ Alert Ticket #86 inviato su Telegram!")
