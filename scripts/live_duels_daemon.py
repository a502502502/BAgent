#!/usr/bin/env python3
"""
live_duels_daemon.py — Monitoraggio Live dei Falli Giocatore ogni 20s con report automatico ogni 5 minuti.
Traccia entrambe le partite:
1. Roma vs Fiorentina (Ticket #24 e Ticket #25)
2. Fulham vs Chelsea (Ticket #22)
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")
API_KEY = os.getenv("API_FOOTBALL_KEY", "")

HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY,
    "x-apisports-key": API_KEY,
}

# Configurazione giocatori per entrambi i match
PLAYERS_ROMA_FIO = {
    "Koné": {"type": "FS", "target": 2, "quota": "@1.65", "name": "Manu Koné", "team": "Roma", "val": 0, "won": False},
    "Wesley": {"type": "FS", "target": 1, "quota": "@1.10", "name": "Wesley Franca", "team": "Roma", "val": 0, "won": False},
    "Dybala": {"type": "FS", "target": 2, "quota": "@1.40", "name": "Paulo Dybala", "team": "Roma", "val": 0, "won": False},
    "Cristante": {"type": "FS", "target": 1, "quota": "@2.00", "name": "Bryan Cristante", "team": "Roma", "val": 0, "won": False},
    "Ndour": {"type": "FC", "target": 2, "quota": "@1.70", "name": "Cher Ndour (FC)", "team": "Fiorentina", "val": 0, "won": False},
    "Ndour_FS": {"type": "FS", "target": 1, "quota": "@1.25", "name": "Cher Ndour (FS)", "team": "Fiorentina", "val": 0, "won": False},
    "Fagioli": {"type": "FS", "target": 1, "quota": "@1.20", "name": "Nicolò Fagioli", "team": "Fiorentina", "val": 0, "won": False},
    "Mora": {"type": "FS", "target": 1, "quota": "@1.47", "name": "Rodrigo Mora", "team": "Roma", "val": 0, "won": False},
    "Joao": {"type": "FC", "target": 1, "quota": "@1.20", "name": "Joao Mário (FC)", "team": "Fiorentina", "val": 0, "won": False},
}

PLAYERS_FULHAM_CHE = {
    "Palmer": {"type": "FS", "target": 2, "quota": "@1.80", "name": "Cole Palmer", "team": "Chelsea", "val": 0, "won": False},
    "Berge": {"type": "FC", "target": 1, "quota": "@1.20", "name": "Sander Berge", "team": "Fulham", "val": 0, "won": False},
    "Caicedo": {"type": "FC", "target": 2, "quota": "@1.55", "name": "Moisés Caicedo", "team": "Chelsea", "val": 0, "won": False},
}

def notify_telegram(msg: str):
    if not TELEGRAM_TOKEN:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=6)
    except Exception as e:
        print("Telegram error:", e, flush=True)

def generate_unified_report() -> str:
    lines_roma = []
    for k, v in PLAYERS_ROMA_FIO.items():
        desc = "FS" if v["type"] == "FS" else "FC"
        icon = f"✅ PRESO! ({v['val']}/{v['target']})" if v["val"] >= v["target"] else f"⏳ In Corsa ({v['val']}/{v['target']})"
        lines_roma.append(f"• <b>{v['name']}</b> ({v['quota']}) ➔ <b>{icon}</b>")

    lines_ful = []
    for k, v in PLAYERS_FULHAM_CHE.items():
        desc = "FS" if v["type"] == "FS" else "FC"
        icon = f"✅ PRESO! ({v['val']}/{v['target']})" if v["val"] >= v["target"] else f"⏳ In Corsa ({v['val']}/{v['target']})"
        lines_ful.append(f"• <b>{v['name']}</b> ({v['quota']}) ➔ <b>{icon}</b>")

    msg = (
        f"⏱️ <b>REPORT LIVE AUTOMATICO (OGNI 5 MINUTI — {datetime.now().strftime('%H:%M')}):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🇮🇹 <b>ROMA vs FIORENTINA (Serie A):</b>\n"
        + "\n".join(lines_roma)
        + "\n\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>FULHAM vs CHELSEA (Premier League):</b>\n"
        + "\n".join(lines_ful)
        + "\n━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <i>Monitoraggio attivo al minuto su tutti i ticket.</i>"
    )
    return msg

def main():
    print(f"=== BAgent Dual-Match Live Monitor Avviato ({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
    last_broadcast_time = time.time()

    while True:
        try:
            # 1. Check Roma vs Fiorentina (ID 1550087)
            r_roma = requests.get("https://v3.football.api-sports.io/fixtures/players?fixture=1550087", headers=HEADERS, timeout=8)
            if r_roma.status_code == 200:
                for tdata in r_roma.json().get("response", []):
                    for p in tdata.get("players", []):
                        pname = p["player"]["name"]
                        st = p["statistics"][0]
                        fs = st["fouls"]["drawn"] or 0
                        fc = st["fouls"]["committed"] or 0
                        for k, v in PLAYERS_ROMA_FIO.items():
                            check_name = "ndour" if "ndour" in k.lower() else k.lower()
                            if check_name in pname.lower():
                                val = fs if v["type"] == "FS" else fc
                                v["val"] = val
                                if val >= v["target"] and not v["won"]:
                                    v["won"] = True
                                    hit_msg = (
                                        f"🎉 <b>SELEZIONE CENTRATA & VINTA! 🏁✅</b>\n\n"
                                        f"👤 <b>{v['name']}</b> ({v['team']}) — Quota {v['quota']}\n"
                                        f"🛑 <b>Valore: {val}/{v['target']} RAGGIUNTO!</b> 💰\n\n"
                                        + generate_unified_report()
                                    )
                                    notify_telegram(hit_msg)
                                    print(f"[{datetime.now().strftime('%H:%M:%S')}] HIT ROMA: {v['name']} ({val}/{v['target']})", flush=True)

            # 2. Check Fulham vs Chelsea (ID 1557376)
            r_ful = requests.get("https://v3.football.api-sports.io/fixtures/players?fixture=1557376", headers=HEADERS, timeout=8)
            if r_ful.status_code == 200:
                for tdata in r_ful.json().get("response", []):
                    for p in tdata.get("players", []):
                        pname = p["player"]["name"]
                        st = p["statistics"][0]
                        fs = st["fouls"]["drawn"] or 0
                        fc = st["fouls"]["committed"] or 0
                        for k, v in PLAYERS_FULHAM_CHE.items():
                            if k.lower() in pname.lower():
                                val = fs if v["type"] == "FS" else fc
                                v["val"] = val
                                if val >= v["target"] and not v["won"]:
                                    v["won"] = True
                                    hit_msg = (
                                        f"🎉 <b>SELEZIONE CENTRATA & VINTA! 🏁✅</b>\n\n"
                                        f"👤 <b>{v['name']}</b> ({v['team']}) — Quota {v['quota']}\n"
                                        f"🛑 <b>Valore: {val}/{v['target']} RAGGIUNTO!</b> 💰\n\n"
                                        + generate_unified_report()
                                    )
                                    notify_telegram(hit_msg)
                                    print(f"[{datetime.now().strftime('%H:%M:%S')}] HIT PL: {v['name']} ({val}/{v['target']})", flush=True)

            # Broadcast ogni 5 minuti esatti (300 secondi)
            if time.time() - last_broadcast_time >= 300:
                last_broadcast_time = time.time()
                report_msg = generate_unified_report()
                notify_telegram(report_msg)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 5-Minute Unified Report sent to Telegram.", flush=True)

        except Exception as e:
            print("Dual monitor error:", e, flush=True)

        time.sleep(20)

if __name__ == "__main__":
    main()
