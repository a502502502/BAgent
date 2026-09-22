#!/usr/bin/env python3
"""
scripts/live_tracker_night_altitude.py — Live Sentinel Ticket #85 Altitudine Sudamerica.
Traccia:
1. Independiente del Valle vs Flamengo (Fixture 1635386) — Pick: 1X @ 1.53
2. Cienciano vs Atletico Torque (Fixture 1631511) — Pick: 1X + Over 1.5 @ 1.38

Invia notifiche Telegram:
- Formazioni ufficiali depositate (~01:30 CEST)
- Calcio d'inizio (02:30 CEST)
- Gol e variazioni live
- Risultati finali e calcolo vincita
"""

from __future__ import annotations
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_HOST = "v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
FID_IDV = 1635386
FID_CIEN = 1631511

MATCHES = {
    FID_IDV: {
        "name": "Independiente del Valle vs Flamengo",
        "pick": "Doppia Chance 1X",
        "odds": 1.53,
        "alt": "Quito (2.850m)",
    },
    FID_CIEN: {
        "name": "Cienciano vs Atletico Torque",
        "pick": "1X + Over 1.5",
        "odds": 1.38,
        "alt": "Cusco (3.400m)",
    }
}

def send_tg(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Errore invio TG: {e}")
        return False

def get_fixture_data(fid: int):
    url = f"https://{API_HOST}/fixtures?id={fid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            if res:
                return res[0]
    except Exception as e:
        print(f"Errore API per {fid}: {e}")
    return None

def main():
    print(f"=== Avvio Live Sentinel Ticket #85 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    init_msg = (
        "🏔️ <b>BAGENT TICKET #85 PIAZZATO — DOPPIA D'ORO ALTITUDINE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. 🇪🇨 <b>Independiente del Valle vs Flamengo</b>\n"
        "   • Pick: <b>1X</b> @ 1.53 (Quito 2.850m)\n"
        "2. 🇵🇪 <b>Cienciano vs Atletico Torque</b>\n"
        "   • Pick: <b>1X + Over 1.5</b> @ 1.38 (Cusco 3.400m)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <b>Quota Totale:</b> 2.11×\n"
        "💵 <b>Stake:</b> €2.50\n"
        "🎯 <b>Vincita Potenziale:</b> €5.28\n"
        "⏰ <b>Calcio d'inizio:</b> 02:30 CEST\n"
        "🛡️ <i>Strict Pipeline a 8 Fasi attiva: zero player props, 90' di respiro.</i>"
    )
    send_tg(init_msg)

    seen_lineups = set()
    seen_goals = {FID_IDV: 0, FID_CIEN: 0}
    finished = set()

    while len(finished) < len(MATCHES):
        now = datetime.now()
        
        for fid, info in MATCHES.items():
            if fid in finished:
                continue

            f_data = get_fixture_data(fid)
            if not f_data:
                continue

            status = f_data.get("fixture", {}).get("status", {}).get("short", "NS")
            elapsed = f_data.get("fixture", {}).get("status", {}).get("elapsed", 0)
            gh = f_data.get("goals", {}).get("home", 0) or 0
            ga = f_data.get("goals", {}).get("away", 0) or 0
            tot_goals = gh + ga

            # 1. Notifica formazioni ufficiali
            lineups = f_data.get("lineups", [])
            if lineups and fid not in seen_lineups:
                seen_lineups.add(fid)
                send_tg(
                    f"📋 <b>DISTINTE UFFICIALI DEPOSITATE:</b> {info['name']}\n"
                    f"Moduli: {lineups[0].get('formation')} vs {lineups[1].get('formation')}\n"
                    f"Altitudine: {info['alt']} | Calcio d'inizio alle 02:30!"
                )

            # 2. Notifica gol
            if tot_goals > seen_goals[fid] and status in ["1H", "2H", "ET"]:
                seen_goals[fid] = tot_goals
                # Dettagli ultimo evento
                events = f_data.get("events", [])
                scorer = "Gol"
                for ev in reversed(events):
                    if ev.get("type") == "Goal":
                        scorer = f"{ev.get('player', {}).get('name', 'Gol')} ({ev.get('team', {}).get('name')})"
                        break

                send_tg(
                    f"⚽ <b>GOL LIVE ({elapsed}')!</b> {info['name']}\n"
                    f"Risultato: <b>{gh} - {ga}</b>\n"
                    f"Marcatore: {scorer}\n"
                    f"🎯 Nostro Pick: <b>{info['pick']}</b>"
                )

            # 3. Fine partita
            if status in ["FT", "AET", "PEN"]:
                finished.add(fid)
                # Verifica esito
                won = False
                if fid == FID_IDV:
                    won = (gh >= ga) # 1X
                elif fid == FID_CIEN:
                    won = (gh >= ga) and (tot_goals >= 2) # 1X + Over 1.5

                status_emoji = "✅ PRESA!" if won else "❌ PERSA"
                send_tg(
                    f"🏁 <b>RISULTATO FINALE:</b> {info['name']}\n"
                    f"Finale: <b>{gh} - {ga}</b>\n"
                    f"Pick: {info['pick']} ➔ {status_emoji}"
                )

        # Polling ogni 45 secondi
        time.sleep(45)

    print("Tutti i match terminati. Sentinel concluso.")

if __name__ == "__main__":
    main()
