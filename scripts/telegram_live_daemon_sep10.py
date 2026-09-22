#!/usr/bin/env python3
"""
scripts/telegram_live_daemon_sep10.py — Demone Autonomo Notifiche Live Telegram BAgent.
Invia aggiornamenti in tempo reale su Telegram (@A502502_bot, chat: 466378357) ad ogni cambio:
- Gol segnato (marcatore, minuto, parziale)
- Sostituzioni chiave (es. Muriqi / Lukaku per Ticket #84)
- Fine 1° Tempo (HT)
- Fine Partita (FT) e calcolo vincite

Traccia:
• Ticket #82 (60.00 € @ 3.51 ➔ 216.72 €)
• Ticket #83 (20.00 € @ 10.98 ➔ 226.26 €)
• Ticket #84 (49.00 € @ 3.50 ➔ 171.35 €)
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# Fixtures ID
FID_PSV = 1635708
FID_FENER = 1635659
FID_BAYERN = 1635632
FID_MANUTD = 1635697
FID_COMO = 1635648

ALL_FIXTURES = {
    FID_PSV: "PSV Eindhoven vs Shakhtar Donetsk",
    FID_FENER: "Fenerbahce vs AS Roma",
    FID_BAYERN: "Bayern Monaco vs Bodo/Glimt",
    FID_MANUTD: "Manchester United vs Sabah Masazir",
    FID_COMO: "Como vs RB Leipzig"
}

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

def main():
    print(f"🚀 Avvio Demone Live Telegram 10 Settembre 2026 ({datetime.now().strftime('%H:%M:%S')})...")
    
    welcome_msg = (
        "🤖 <b>BAGENT LIVE SENTINEL ATTIVATO!</b>\n\n"
        "📊 <b>I 3 Ticket Monitorati Live:</b>\n"
        "• <b>Ticket #82 (Invincibile 5 Eventi)</b>: 60€ @ 3.51 ➔ <b>216.72 €</b>\n"
        "• <b>Ticket #83 (Assalto 11x)</b>: 20€ @ 10.98 ➔ <b>226.26 €</b>\n"
        "• <b>Ticket #84 (Doppia 18:45)</b>: 49€ @ 3.50 ➔ <b>171.35 €</b>\n\n"
        "🏆 <b>Montepremi in Gioco: 614.33 €</b>\n"
        "<i>Riceverai una notifica immediata ad OGNI GOL, SOSTITUZIONE CHIAVE (Muriqi/Lukaku) e risultato parziale!</i>"
    )
    send_tg(welcome_msg)

    # State tracking
    last_scores = {fid: (-1, -1) for fid in ALL_FIXTURES}
    last_status = {fid: "" for fid in ALL_FIXTURES}
    seen_events = {fid: set() for fid in ALL_FIXTURES}
    last_heartbeat = time.time()

    while True:
        try:
            for fid, match_name in ALL_FIXTURES.items():
                data = get_fixture_data(fid)
                if not data:
                    continue

                fix = data.get("fixture", {})
                st = fix.get("status", {})
                short_status = st.get("short", "")
                elapsed = st.get("elapsed") or 0
                goals = data.get("goals", {})
                gh = goals.get("home") if goals.get("home") is not None else 0
                ga = goals.get("away") if goals.get("away") is not None else 0
                home_team = data.get("teams", {}).get("home", {}).get("name", "")
                away_team = data.get("teams", {}).get("away", {}).get("name", "")

                # 1. Controllo Cambio Punteggio (GOL!)
                prev_gh, prev_ga = last_scores[fid]
                if (prev_gh, prev_ga) != (-1, -1) and (gh != prev_gh or ga != prev_ga):
                    goal_msg = (
                        f"⚽ <b>GOL! CAMBIO RISULTATO!</b>\n\n"
                        f"🏟️ <b>{home_team} {gh} - {ga} {away_team}</b> ({elapsed}')\n\n"
                    )
                    # Verifica impatto sui ticket
                    if fid == FID_PSV:
                        goal_msg += f"📊 <b>PSV 1X + Over 1.5:</b> {'🟢 OVER 1.5 CENTRATO!' if (gh+ga)>=2 else f'Manca 1 gol (Tot: {gh+ga})'}\n"
                        goal_msg += f"📊 <b>PSV 1 + Over 2.5:</b> {'🟢 GOL A -1!' if (gh+ga)==2 else f'Totale gol: {gh+ga}'}\n"
                    elif fid == FID_FENER:
                        goal_msg += f"📊 <b>Fener-Roma 1X + GG:</b> {'🟢 GG CENTRATO!' if (gh>0 and ga>0) else 'In attesa di gol entrambe'}\n"
                        goal_msg += f"📊 <b>Roma MultiGol 1-3:</b> {'🟢 ROMA A SEGNO!' if (1<=ga<=3) else 'In attesa gol Roma'}\n"
                    
                    send_tg(goal_msg)

                last_scores[fid] = (gh, ga)

                # 2. Controllo Eventi (Nuovi Marcatori e Sostituzioni Chiave)
                events = data.get("events", [])
                for e in events:
                    e_type = e.get("type")
                    e_time = e.get("time", {}).get("elapsed")
                    p_name = e.get("player", {}).get("name", "")
                    a_name = e.get("assist", {}).get("name", "")
                    event_key = f"{e_type}_{e_time}_{p_name}_{a_name}"

                    if event_key not in seen_events[fid]:
                        seen_events[fid].add(event_key)

                        # Notifica Gol Dettagliato
                        if e_type == "Goal":
                            team_name = e.get("team", {}).get("name", "")
                            detail = e.get("detail", "")
                            send_tg(
                                f"🎯 <b>MARCATORE UFFICIALE!</b>\n"
                                f"⚽ <b>{p_name}</b> ({detail})\n"
                                f"🏟️ {match_name} al {e_time}' ({team_name})"
                            )

                        # Notifica Sostituzione Muriqi / Lukaku (Ticket #84)
                        elif e_type == "subst" and ("muriqi" in p_name.lower() or "muriqi" in a_name.lower() or "lukaku" in p_name.lower() or "lukaku" in a_name.lower()):
                            send_tg(
                                f"🔄 <b>SOSTITUZIONE CHIAVE (TICKET #84)!</b>\n\n"
                                f"Esce: <b>{p_name}</b> ➔ Entra: <b>{a_name}</b> ({e_time}')\n"
                                f"🚨 <b>IL TESTIMONE PASSA A ROMELU LUKAKU!</b>\n"
                                f"<i>Ogni gol o legno di Lukaku fino al 95' renderà VERDE il Ticket #84!</i>"
                            )

                # 3. Controllo Fine Primo Tempo (HT)
                prev_st = last_status[fid]
                if prev_st in ["1H", "NS"] and short_status == "HT":
                    send_tg(
                        f"⏸️ <b>FINE PRIMO TEMPO (HT)!</b>\n\n"
                        f"🏟️ <b>{home_team} {gh} - {ga} {away_team}</b> (45')\n"
                        f"Le squadre rientrano negli spogliatoi. Monitoraggio 2° tempo attivo!"
                    )

                # 4. Controllo Fine Partita (FT)
                if prev_st in ["2H", "HT"] and short_status in ["FT", "AET", "PEN"]:
                    send_tg(
                        f"🏁 <b>FISCHIO FINALE!</b>\n\n"
                        f"🏟️ <b>{home_team} {gh} - {ga} {away_team}</b> (FINALE)\n"
                        f"Verifica schedine in corso..."
                    )

                last_status[fid] = short_status

            # Heartbeat ogni 20 minuti
            if time.time() - last_heartbeat > 1200:
                last_heartbeat = time.time()
                send_tg(
                    f"💓 <i>Bagent Live Sentinel attivo ({datetime.now().strftime('%H:%M')})... connessione con i campi stabile.</i>"
                )

        except Exception as err:
            print(f"Errore ciclo live: {err}")

        # Polling ogni 35 secondi
        time.sleep(35)

if __name__ == "__main__":
    main()
