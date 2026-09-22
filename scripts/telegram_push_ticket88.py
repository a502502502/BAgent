"""
Telegram Push for Ticket #88 (Super Early Bird Start 11:30).
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

def push_ticket_88():
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"⚡ <b>TICKET #88: SUPER EARLY BIRD (START ORE 11:30!)</b> ({now})\n\n"
        f"🏆 <b>QUINTINA RAPIDA DEL MATTINO (Quota: 3.74×):</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 🇮🇳 <b>East Bengal vs Mohammedan</b> (11:30) ➔ 🎯 <b>1X @ 1.22</b>\n"
        f"2️⃣ 🇯🇵 <b>FC Osaka vs Ehime</b> (12:00) ➔ 🎯 <b>1X @ 1.25</b>\n"
        f"3️⃣ 🇸🇬 <b>Geylang vs Tanjong Pagar</b> (13:30) ➔ 🎯 <b>Over 2.5 Gol @ 1.35</b> 💣\n"
        f"4️⃣ 🌏 <b>Shan United vs Ezra FC</b> (13:30) ➔ 🎯 <b>1 (1X2) @ 1.30</b>\n"
        f"5️⃣ 🇺🇦 <b>Dynamo Kyiv vs Epitsentr</b> (14:30) ➔ 🎯 <b>1 + Over 1.5 Gol @ 1.40</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎟️ <b>Codice Netwin 1-Click</b>: <code>NW-1130-T88</code>\n"
        f"💵 <b>Stake Consigliato</b>: 15.00 € (o 20.00 €)\n"
        f"💰 <b>VINCITA A CASSA</b>: <b>56.10 € — 74.80 €</b> 🚀\n"
        f"⏰ <i>Mancano meno di 45 minuti al via dell'East Bengal!</i>"
    )
    return send_telegram(msg)

if __name__ == "__main__":
    success = push_ticket_88()
    if success:
        print("✅ Alert Ticket #88 inviato su Telegram!")
