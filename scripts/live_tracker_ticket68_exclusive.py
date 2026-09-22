#!/usr/bin/env python3
"""
scripts/live_tracker_ticket68_exclusive.py — Monitoraggio Real-Time PUSH ISTANTANEO Ticket #68
Invia una notifica Telegram a OGNI singolo corner o variazione falli!
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)

class Ticket68ExclusiveTracker:
    def __init__(self):
        self.collector = FootballExternalCollector()
        self.notified_legs = set()
        
        # State tracking
        self.last_city_corners = None
        self.last_bvb_corners = None
        self.last_real_fouls = None
        self.last_inter_fouls = None
        
        self.ht_notified = False
        self.ticket_won_sent = False

    def run(self):
        print("[TICKET #68 TRACKER] Avviato con push istantaneo ad ogni corner/fallo.", flush=True)

        while True:
            try:
                self.poll()
            except Exception as e:
                print(f"[POLL ERROR] {e}", flush=True)
            time.sleep(30)

    def poll(self):
        # 1. Porto vs Manchester City (1635654) - Corner City
        st_city = self.collector._get("fixtures/statistics", {"fixture": 1635654}).get("response", [])
        f_city = self.collector._get("fixtures", {"id": 1635654})["response"][0]
        el_city = f_city["fixture"]["status"].get("elapsed") or 0
        
        c_city = 0
        if len(st_city) >= 2:
            for s in st_city[1].get("statistics", []):
                if s["type"] == "Corner Kicks":
                    c_city = s["value"] or 0
        
        if self.last_city_corners is not None and c_city > self.last_city_corners:
            if c_city >= 5 and "city_corners_won" not in self.notified_legs:
                self.notified_legs.add("city_corners_won")
                send_telegram(f"🚩🚩 <b>CASSA CORNER MAN CITY! ({el_city}')</b>\nIl Manchester City ha raggiunto <b>{c_city} CORNER</b>! Over 4.5 Corner PRESO! 🟢 (1/3)")
            else:
                send_telegram(f"🚩 <b>NUOVO CORNER CITY! ({el_city}')</b>\nManchester City a quota <b>{c_city} / 5 corner</b> battuti! ⏳")
        self.last_city_corners = c_city

        # 2. Dortmund vs Villarreal (1635652) - Corner BVB
        st_bvb = self.collector._get("fixtures/statistics", {"fixture": 1635652}).get("response", [])
        f_bvb = self.collector._get("fixtures", {"id": 1635652})["response"][0]
        el_bvb = f_bvb["fixture"]["status"].get("elapsed") or 0
        
        c_bvb = 0
        if len(st_bvb) >= 1:
            for s in st_bvb[0].get("statistics", []):
                if s["type"] == "Corner Kicks":
                    c_bvb = s["value"] or 0
        
        if self.last_bvb_corners is not None and c_bvb > self.last_bvb_corners:
            if c_bvb >= 5 and "bvb_corners_won" not in self.notified_legs:
                self.notified_legs.add("bvb_corners_won")
                send_telegram(f"🚩🚩 <b>CASSA CORNER BORUSSIA DORTMUND! ({el_bvb}')</b>\nIl BVB ha raggiunto <b>{c_bvb} CORNER</b>! Over 4.5 Corner BVB PRESO! 🟢 (2/3)")
            else:
                send_telegram(f"🚩 <b>NUOVO CORNER DORTMUND! ({el_bvb}')</b>\nBorussia Dortmund a quota <b>{c_bvb} / 5 corner</b> battuti! ⏳")
        self.last_bvb_corners = c_bvb

        # 3. Real Madrid vs Inter (1635714) - Falli Commessi Inter
        st_real = self.collector._get("fixtures/statistics", {"fixture": 1635714}).get("response", [])
        f_real = self.collector._get("fixtures", {"id": 1635714})["response"][0]
        status_real = f_real["fixture"]["status"]["short"]
        el_real = f_real["fixture"]["status"].get("elapsed") or 0

        rf, inf = 0, 0
        if len(st_real) >= 2:
            for s in st_real[0].get("statistics", []):
                if s["type"] == "Fouls": rf = s["value"] or 0
            for s in st_real[1].get("statistics", []):
                if s["type"] == "Fouls": inf = s["value"] or 0

        if self.last_real_fouls is not None and (rf, inf) != (self.last_real_fouls, self.last_inter_fouls):
            diff = inf - rf
            tag = f"🟢 INTER AVANTI (+{diff})" if diff > 0 else (f"⚠️ REAL AVANTI (+{-diff})" if diff < 0 else "⚖️ PARITÀ")
            send_telegram(f"⚔️ <b>FALLI AGGIORNATI BERNABÉU ({el_real}')</b>\nReal Madrid <b>{rf} - {inf} INTER</b>\nSituazione 1X2 Falli: <b>{tag}</b>")
        self.last_real_fouls = rf
        self.last_inter_fouls = inf

        # Intervallo
        if status_real == "HT" and not self.ht_notified:
            self.ht_notified = True
            diff_ht = inf - rf
            status_ht = f"🟢 FAVOREVOLE (+{diff_ht} falli Inter)" if diff_ht > 0 else (f"⚠️ SOTTO" if diff_ht < 0 else "⚖️ PARI")
            send_telegram(
                f"⏸️ <b>RESOCONTO INTERVALLO (45' HT) — TICKET #68</b>\n\n"
                f"⚔️ <b>Falli Real-Inter</b>: Real {rf} - <b>{inf} INTER</b> ({status_ht})\n"
                f"🚩 <b>Corner Man City</b>: {self.last_city_corners} / 5\n"
                f"🚩 <b>Corner Dortmund</b>: {self.last_bvb_corners} / 5\n\n"
                f"💰 <i>In palio: 351.27 € netti!</i>"
            )

        # Finale Match Real Madrid vs Inter
        if status_real in ("FT", "AET", "PEN") and "fouls_final" not in self.notified_legs:
            self.notified_legs.add("fouls_final")
            if inf > rf:
                self.notified_legs.add("inter_fouls_won")
                send_telegram(f"✅ <b>CASSA FALLI INTER FT!</b>\nReal Madrid {rf} - <b>{inf} Inter</b>\n1X2 Falli: 2 (Inter) CENTRATO! 🟢")
            else:
                send_telegram(f"❌ Finale Falli FT: Real {rf} - {inf} Inter.")

        # Boato Cassa Totale
        if "city_corners_won" in self.notified_legs and "bvb_corners_won" in self.notified_legs and "inter_fouls_won" in self.notified_legs:
            if not self.ticket_won_sent:
                self.ticket_won_sent = True
                send_telegram(
                    "🏆🎉💰 <b>BOATOOO TOTALE! TICKET #68 SBANCATO AL 100%!</b> 💰🎉🏆\n\n"
                    "• 🚩 Corner City Over 4.5 PRESI! 🟢\n"
                    "• 🚩 Corner Dortmund Over 4.5 PRESI! 🟢\n"
                    "• ⚔️ Falli Inter PRESO! 🟢\n\n"
                    "💵 Puntata: <b>88.00 €</b>\n"
                    "💰 <b>VINCITA INCASSATA: 351.27 € NETTI!</b>\n\n"
                    "Saldo Netwin schizza oltre quota 450 €! 🔥"
                )

if __name__ == "__main__":
    tracker = Ticket68ExclusiveTracker()
    tracker.run()
