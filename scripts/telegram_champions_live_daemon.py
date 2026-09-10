#!/usr/bin/env python3
"""
telegram_champions_live_daemon.py — Demone Autonomo Notifiche Telegram BAgent.
Invia aggiornamenti in tempo reale su Telegram (@A502502_bot) per le gare delle 21:00.
Traccia Ticket #74 (85.11 €) e Ticket #78 (100.96 €).
"""

from __future__ import annotations
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"


def send_tg(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Errore invio Telegram: {e}")
        return False


def get_fixture_data(fid: int):
    url = f"https://{API_HOST}/fixtures?id={fid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            return res[0] if res else None
    except Exception as e:
        print(f"Errore API {fid}: {e}")
    return None


def get_team_shots(fid: int, team_name: str) -> int:
    url = f"https://{API_HOST}/fixtures/statistics?fixture={fid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            for item in res:
                if team_name.lower() in item.get("team", {}).get("name", "").lower():
                    for s in item.get("statistics", []):
                        if s.get("type") == "Total Shots":
                            return int(s.get("value") or 0)
    except Exception as e:
        print(f"Errore stats {fid}: {e}")
    return 0


def main():
    print(f"🚀 Avvio Demone Notifiche Telegram Champions League ({datetime.now().strftime('%H:%M:%S')})...")
    
    # Invia messaggio di benvenuto con lo stato iniziale
    welcome_msg = (
        "🤖 <b>BAGENT CHAMPIONS LIVE TRACKER ATTIVATO!</b>\n\n"
        "📊 <b>Schedine in Corso di Monitoraggio:</b>\n"
        "• <b>Ticket #74 (La Principale da 85.11 €)</b>: 2/4 PRESE AL 100% (Stoccarda 3-1 & Barça 5-1). In attesa di Liverpool e Napoli!\n"
        "• <b>Ticket #78 (Live Raddoppio da 100.96 €)</b>: Atletico Over 9.5 Tiri + Napoli Over 1.5 Gol.\n"
        "• <b>Ticket #73 (Chicche da 103.82 €)</b>: ✅ <b>SBANCATO AL 100%!</b> (Dembele doppietta al 17' e 23')!\n\n"
        "💰 <b>Saldo Cassa Netwin</b>: <b>204.04 €</b>\n"
        "<i>Riceverai notifiche su ogni gol, traguardo tiri e verdetto finale!</i>"
    )
    send_tg(welcome_msg)

    last_liv_score = (-1, -1)
    last_nap_score = (-1, -1)
    last_psg_score = (-1, -1)
    last_atletico_shots = -1
    last_heartbeat = time.time()

    while True:
        try:
            # 1. Liverpool vs Atletico (1635686)
            liv = get_fixture_data(1635686)
            if liv:
                gh = liv["goals"]["home"] or 0
                ga = liv["goals"]["away"] or 0
                elapsed = liv["fixture"]["status"].get("elapsed") or 0
                status_short = liv["fixture"]["status"].get("short", "")

                if (gh, ga) != last_liv_score and last_liv_score != (-1, -1):
                    msg = (
                        f"⚽ <b>GOL AD ANFIELD! ({elapsed}')</b>\n"
                        f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Liverpool {gh} - {ga} Atletico Madrid</b>\n\n"
                        f"🎯 <b>Impatto Ticket #74 (1X + Over 1.5)</b>: "
                        f"{'🟢 In linea con la giocata!' if gh >= ga and (gh+ga)>=2 else '⏳ In evoluzione'}"
                    )
                    send_tg(msg)
                last_liv_score = (gh, ga)

            # Check tiri Atletico
            atletico_shots = get_team_shots(1635686, "Atletico")
            if atletico_shots >= 10 and last_atletico_shots < 10 and last_atletico_shots != -1:
                send_tg(
                    f"🎯 <b>TRAGUARDO RAGGIUNTO! (Ticket #78)</b>\n"
                    f"🔴⚪ <b>Atletico Madrid ha raggiunto {atletico_shots} Tiri Totali!</b>\n"
                    f"✅ <b>Over 9.5 Tiri Atletico @ 1.59 È PRESO AL 100%!</b> 🟢"
                )
            last_atletico_shots = atletico_shots

            # 2. Napoli vs Arsenal (1635698)
            nap = get_fixture_data(1635698)
            if nap:
                ngh = nap["goals"]["home"] or 0
                nga = nap["goals"]["away"] or 0
                nelapsed = nap["fixture"]["status"].get("elapsed") or 0
                nstatus_short = nap["fixture"]["status"].get("short", "")

                if (ngh, nga) != last_nap_score and last_nap_score != (-1, -1):
                    tot_g = ngh + nga
                    msg = (
                        f"⚽ <b>GOL AL MARADONA! ({nelapsed}')</b>\n"
                        f"🇮🇹 <b>Napoli {ngh} - {nga} Arsenal</b>\n\n"
                        f"🎯 <b>Impatto Ticket #74 & #78 (Over 1.5)</b>: "
                        f"{'🟢 OVER 1.5 INCASSATO AL 100%!' if tot_g >= 2 else '⏳ Manca 1 solo gol per l Over 1.5!'}"
                    )
                    send_tg(msg)
                last_nap_score = (ngh, nga)

            # 3. Heartbeat ogni 8 minuti per rassicurare l'utente
            now_t = time.time()
            if now_t - last_heartbeat >= 480:
                last_heartbeat = now_t
                liv_str = f"Liverpool {last_liv_score[0]}-{last_liv_score[1]} Atletico (Tiri Atl: {atletico_shots})"
                nap_str = f"Napoli {last_nap_score[0]}-{last_nap_score[1]} Arsenal"
                send_tg(
                    f"📡 <b>REPORT PERIODICO CHAMPIONS LEAGUE</b>\n\n"
                    f"• {liv_str}\n"
                    f"• {nap_str}\n\n"
                    f"⏳ <i>Monitoraggio costantemente attivo...</i>"
                )

            # Check if all matches FT
            if liv and nap:
                if liv["fixture"]["status"].get("short") == "FT" and nap["fixture"]["status"].get("short") == "FT":
                    send_tg(
                        f"🏁 <b>PARTITE DELLE 21:00 CONCLUSE!</b>\n\n"
                        f"• Liverpool {last_liv_score[0]} - {last_liv_score[1]} Atletico\n"
                        f"• Napoli {last_nap_score[0]} - {last_nap_score[1]} Arsenal\n\n"
                        f"Consuntivo finale in arrivo su BAgent!"
                    )
                    break

            time.sleep(30) # Poll ogni 30 secondi
        except Exception as e:
            print(f"Errore loop poller: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()
