#!/usr/bin/env python3
"""
scripts/live_tracker_night_ticket71.py — Monitoraggio Real-Time PUSH ISTANTANEO Ticket #71
Fluminense 1X2 (1) + Santa Fe Over 3.5 Corner Squadra 1.
Puntata: 80.00 € ➔ Vincita Potenziale: 169.37 €!
"""

import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from services.football.external.collector import FootballExternalCollector

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")

def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print(f"[TELEGRAM] Sent ({r.status_code}): {msg[:60]}...", flush=True)
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}", flush=True)

class Ticket71Tracker:
    def __init__(self):
        self.collector = FootballExternalCollector()
        self.notified_events = set()
        self.last_sf_corners = None
        self.last_flu_goals = None
        self.last_plat_goals = None
        self.ht_notified = False
        self.cassa_sent = False

    def run(self):
        print("[TICKET #71 TRACKER] Avviato con successo!", flush=True)
        self.send_startup()
        while True:
            try:
                self.poll()
            except Exception as e:
                print(f"[POLL ERROR] {e}", flush=True)
            time.sleep(25)

    def send_startup(self):
        msg = (
            "🌙 <b>TICKET #71 REGISTRATO & MONITORAGGIO ATTIVO!</b> 🌙\n\n"
            "💵 Puntata: <b>80.00 €</b> @ <b>2.12×</b> ➔ 💰 <b>Vincita Potenziale: 169.37 €</b>\n\n"
            "• 🇧🇷 <b>Fluminense 1 - 0 Platense (30')</b>: 1X2: 1 🟢 (Gol Nonato 21'!)\n"
            "• 🇨🇴 <b>Santa Fe vs Vasco (30')</b>: Over 3.5 Corner Squadra 1 (1 / 4 corner)\n\n"
            "⚡ <i>Notifiche push istantanee attive per ogni corner e gol!</i>"
        )
        send_telegram(msg)

    def poll(self):
        # 1. Santa Fe vs Vasco (1635576) - Corner Santa Fe
        f_sf = self.collector._get("fixtures", {"id": 1635576})["response"][0]
        st_sf = self.collector._get("fixtures/statistics", {"fixture": 1635576}).get("response", [])
        el_sf = f_sf["fixture"]["status"].get("elapsed") or 0
        status_sf = f_sf["fixture"]["status"]["short"]
        
        c_sf = 0
        if len(st_sf) >= 1:
            for s in st_sf[0].get("statistics", []):
                if s["type"] == "Corner Kicks": c_sf = s["value"] or 0

        if self.last_sf_corners is not None and c_sf > self.last_sf_corners:
            if c_sf >= 4 and "sf_corners_won" not in self.notified_events:
                self.notified_events.add("sf_corners_won")
                send_telegram(f"🚩🚩 <b>CASSA CORNER SANTA FE! ({el_sf}')</b>\nIl Santa Fe ha raggiunto <b>{c_sf} CORNER</b>!\nOver 3.5 Corner Squadra 1 PRESO AL 100%! 🟢 (1/2)")
            else:
                send_telegram(f"🚩 <b>NUOVO CORNER SANTA FE! ({el_sf}')</b>\nSanta Fe a quota <b>{c_sf} / 4 corner</b> battuti! ⏳")
        self.last_sf_corners = c_sf

        # 2. Fluminense vs Platense (1630777) - 1X2 (1)
        f_flu = self.collector._get("fixtures", {"id": 1630777})["response"][0]
        el_flu = f_flu["fixture"]["status"].get("elapsed") or 0
        status_flu = f_flu["fixture"]["status"]["short"]
        gh_flu = f_flu["goals"]["home"] or 0
        ga_flu = f_flu["goals"]["away"] or 0

        if self.last_flu_goals is not None and gh_flu > self.last_flu_goals:
            send_telegram(f"⚽ <b>RADDOPPIO FLUMINENSE! ({el_flu}')</b>\nFluminense <b>{gh_flu} - {ga_flu} Platense</b>! Maracanã in festa! 🟢")
        self.last_flu_goals = gh_flu

        if self.last_plat_goals is not None and ga_flu > self.last_plat_goals:
            send_telegram(f"⚠️ <b>Gol Platense ({el_flu}')</b>: Fluminense {gh_flu} - {ga_flu} Platense.")
        self.last_plat_goals = ga_flu

        # Intervallo
        if status_flu == "HT" and not self.ht_notified:
            self.ht_notified = True
            send_telegram(
                f"⏸️ <b>FINE PRIMO TEMPO (HT) — TICKET #71</b>\n\n"
                f"• 🇧🇷 <b>Fluminense {gh_flu} - {ga_flu} Platense</b> ({'🟢 Vantaggio Flu' if gh_flu > ga_flu else '⚖️ Parità'})\n"
                f"• 🇨🇴 <b>Corner Santa Fe</b>: <b>{self.last_sf_corners} / 4</b>\n\n"
                f"💰 <i>In palio: 169.37 € per portare il banco a 269.37 €!</i>"
            )

        # Finale Match Fluminense
        if status_flu in ("FT", "AET", "PEN") and "flu_final" not in self.notified_events:
            self.notified_events.add("flu_final")
            if gh_flu > ga_flu:
                self.notified_events.add("flu_won")
                send_telegram(f"✅ <b>CASSA FLUMINENSE FT!</b> Fluminense batte il Platense {gh_flu}-{ga_flu}! Selezione 1X2 CENTRATA! 🟢")
            else:
                send_telegram(f"❌ Finale Fluminense: {gh_flu}-{ga_flu}.")

        # BOATO CASSA TOTALE
        if "sf_corners_won" in self.notified_events and "flu_won" in self.notified_events:
            if not self.cassa_sent:
                self.cassa_sent = True
                send_telegram(
                    "🏆🎉💰 <b>BOATOOO TOTALE! TICKET #71 SBANCATO AL 100%!</b> 💰🎉🏆\n\n"
                    "• 🚩 Corner Santa Fe Over 3.5 PRESI! 🟢\n"
                    "• 🇧🇷 Fluminense Vincente PRESO! 🟢\n\n"
                    "💵 Puntata: <b>80.00 €</b>\n"
                    "💰 <b>VINCITA INCASSATA: 169.37 € NETTI!</b>\n\n"
                    "🚀 <b>Il banco schizza a 269.37 €! RECUPERO PIENO COMPLETATO!</b> 🔥"
                )

if __name__ == "__main__":
    tracker = Ticket71Tracker()
    tracker.run()
