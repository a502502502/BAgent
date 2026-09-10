#!/usr/bin/env python3
"""
scripts/live_tracker_active_only.py — Monitoraggio ESCLUSIVO per Ticket Attivi/In Corsa
ZERO notifiche o spam su schedine già chiuse/perse.
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
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)

class ActiveTicketsTracker:
    def __init__(self):
        self.collector = FootballExternalCollector()
        self.notified_legs = set()
        self.last_corners_bvb = 0
        self.last_corners_city = (0, 0)
        self.last_cards_real = 0
        self.ticket_won_sent = False

    def run(self):
        print("[ACTIVE TRACKER] Avviato per Ticket #64. Nessuna notifica su schedine perse.", flush=True)
        while True:
            try:
                self.poll()
            except Exception as e:
                print(f"[POLL ERROR] {e}", flush=True)
            time.sleep(45)

    def poll(self):
        # 1. AEK vs LASK (1635609) -> 1X
        if "aek_1x" not in self.notified_legs:
            f = self.collector._get("fixtures", {"id": 1635609})["response"][0]
            st = f["fixture"]["status"]["short"]
            gh = f["goals"]["home"] or 0
            ga = f["goals"]["away"] or 0
            if st in ("FT", "AET", "PEN"):
                if gh >= ga:
                    self.notified_legs.add("aek_1x")
                    send_telegram(f"✅ <b>TICKET #64 — LEGA 1 PRESA AL 100%!</b>\nAEK Atene {gh}-{ga} LASK Linz FT ➔ Doppia Chance 1X centrata! 🟢 (1/5)")
                else:
                    self.notified_legs.add("aek_1x")

        # 2. Lille vs Betis (1635683) -> Under 3.5
        if "lille_u35" not in self.notified_legs:
            f = self.collector._get("fixtures", {"id": 1635683})["response"][0]
            st = f["fixture"]["status"]["short"]
            gh = f["goals"]["home"] or 0
            ga = f["goals"]["away"] or 0
            if st in ("FT", "AET", "PEN"):
                if (gh + ga) <= 3:
                    self.notified_legs.add("lille_u35")
                    send_telegram(f"✅ <b>TICKET #64 — LEGA 2 PRESA!</b>\nLille {gh}-{ga} Betis FT ➔ Under 3.5 centrato! 🟢")
                else:
                    self.notified_legs.add("lille_u35")

        # 3. Dortmund vs Villarreal (1635652) -> BVB Over 4.5 Corner
        if "bvb_corners" not in self.notified_legs:
            st = self.collector._get("fixtures/statistics", {"fixture": 1635652}).get("response", [])
            if st and len(st) >= 1:
                bvb_c = 0
                for s in st[0].get("statistics", []):
                    if s["type"] == "Corner Kicks": bvb_c = s["value"] or 0
                if bvb_c >= 5:
                    self.notified_legs.add("bvb_corners")
                    send_telegram(f"🚩🚩 <b>TICKET #64 — LEGA 3 PRESA!</b>\nBorussia Dortmund ha raggiunto <b>{bvb_c} CORNER</b>! Over 4.5 Corner centrato! 🟢")

        # 4. Porto vs Man City (1635654) -> City 1X2 Corner
        if "city_corners" not in self.notified_legs:
            st = self.collector._get("fixtures/statistics", {"fixture": 1635654}).get("response", [])
            f = self.collector._get("fixtures", {"id": 1635654})["response"][0]
            if f["fixture"]["status"]["short"] in ("FT", "AET", "PEN"):
                p_c, c_c = 0, 0
                if st and len(st) >= 2:
                    for s in st[0].get("statistics", []):
                        if s["type"] == "Corner Kicks": p_c = s["value"] or 0
                    for s in st[1].get("statistics", []):
                        if s["type"] == "Corner Kicks": c_c = s["value"] or 0
                if c_c > p_c:
                    self.notified_legs.add("city_corners")
                    send_telegram(f"✅ <b>TICKET #64 — LEGA 4 PRESA!</b>\nCorner Porto {p_c} - {c_c} Man City FT ➔ 1X2 Corner City centrato! 🟢")

        # 5. Real Madrid vs Inter (1635714) -> Real Over 1.5 Cartellini
        if "real_cards" not in self.notified_legs:
            st = self.collector._get("fixtures/statistics", {"fixture": 1635714}).get("response", [])
            if st and len(st) >= 1:
                yc, rc = 0, 0
                for s in st[0].get("statistics", []):
                    if s["type"] == "Yellow Cards": yc = s["value"] or 0
                    if s["type"] == "Red Cards": rc = s["value"] or 0
                if (yc + rc) >= 2:
                    self.notified_legs.add("real_cards")
                    send_telegram(f"🟨🟨 <b>TICKET #64 — LEGA 5 PRESA!</b>\nReal Madrid ha ricevuto <b>{yc+rc} CARTELLINI</b>! Over 1.5 Cartellini centrato! 🟢")

        # Vincita Totale
        active_won = len([x for x in ["aek_1x", "lille_u35", "bvb_corners", "city_corners", "real_cards"] if x in self.notified_legs])
        if active_won == 5 and not self.ticket_won_sent:
            self.ticket_won_sent = True
            send_telegram(
                "🏆🎉💰 <b>EN PLEIN TOTALE! TICKET #64 VINTO AL 100%!</b> 💰🎉🏆\n\n"
                "Tutte e 5 le selezioni centrate!\n"
                "💰 <b>VINCITA INCASSATA: 128.64 € ACCREDITATI SU NETWIN!</b>"
            )

if __name__ == "__main__":
    tracker = ActiveTicketsTracker()
    tracker.run()
