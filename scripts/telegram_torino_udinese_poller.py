#!/usr/bin/env python3
"""
BAgent Telegram Sentinel: ESCLUSIVO CARTELLINI TORINO - UDINESE
Invia notifiche via Telegram ESCLUSIVAMENTE quando viene estratto un cartellino.
Nessun altro messaggio o notifica viene inviato.
"""

import os
import sys
import time
import requests
from datetime import datetime

# Windows encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TELEGRAM_TOKEN = "8852289931:AAFwuMzlNXDBkMbbMhE3HsxfudIbrGQQ0co"
TELEGRAM_CHAT_ID = "466378357"

def send_card_alert(card_number: int, player_name: str, team: str, minute: str = ""):
    """Invia SOLO alert sui cartellini."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    if card_number == 1:
        text = f"🟡 <b>1° Cartellino Estratto</b>: {player_name} ({team}) {minute}\n\n<i>Manca 1 cartellino all'Over 1.5 (Vincita 57.90 EUR).</i>"
    elif card_number == 2:
        text = f"🟡 <b>2° Cartellino Estratto</b>: {player_name} ({team}) {minute}\n\n🎯 <b>CASSA OVER 1.5 CARTELLINI CONFERMATA!</b>\nSchedina 1 vinta: <b>57.90 EUR</b>!"
    else:
        text = f"🟡 <b>{card_number}° Cartellino Estratto</b>: {player_name} ({team}) {minute}"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=8)
    except Exception as e:
        print(f"Error sending card alert: {e}")

if __name__ == "__main__":
    print("Sentinel cartellini configurato in modalita rigorosa (SOLO cartellini).")
