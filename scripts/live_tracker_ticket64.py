#!/usr/bin/env python3
"""
scripts/live_tracker_ticket64.py — Live Real-Time Push Daemon per Ticket #64
Monitora le 5 partite di Champions League di stasera:
1. AEK Atene vs LASK Linz (1635609): Doppia Chance 1X @ 1.20
2. Lilla vs Real Betis (1635683): Under 3.5 Gol @ 1.41
3. Borussia Dortmund vs Villarreal (1635652): BVB Over 4.5 Corner @ 1.42
4. FC Porto vs Manchester City (1635654): 1X2 Corner City @ 1.52
5. Real Madrid vs Inter (1635714): Real Madrid Over 1.5 Cartellini @ 1.71

Quota totale: 6.24x + Bonus = 128.64 € (su 20.00 € puntati)
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

class Ticket64Tracker:
    def __init__(self):
        self.collector = FootballExternalCollector()
        self.notified_legs = set()
        self.last_scores = {}
        self.last_corners_bvb = 0
        self.last_corners_city = (0, 0)
        self.last_cards_real = 0
        self.ticket_won_sent = False

    def run(self):
        start_msg = (
            "🚀 <b>SENTINELLA LIVE ATTIVA — TICKET #64 REGISTRATO!</b>\n\n"
            "🎫 <b>Ticket #64: La Cinquina d'Oro Micro-Statistica</b>\n"
            "💵 Puntata: <b>20.00 €</b> | Quota: <b>6.24×</b> | Bonus: <b>3.74 €</b>\n"
            "💰 <b>Vincita Potenziale: 128.64 €</b>\n\n"
            "1. 🇬🇷 AEK Atene vs LASK ➔ <b>1X</b> @ 1.20 ⏳ (1-0 HT)\n"
            "2. 🇫🇷 Lille vs Betis ➔ <b>Under 3.5 Gol</b> @ 1.41 ⏳ (ore 21:00)\n"
            "3. 🇩🇪 Dortmund vs Villarreal ➔ <b>BVB Over 4.5 Corner</b> @ 1.42 ⏳ (ore 21:00)\n"
            "4. 🇵🇹 Porto vs Man City ➔ <b>City 1X2 Corner</b> @ 1.52 ⏳ (ore 21:00)\n"
            "5. 🇪🇸 Real Madrid vs Inter ➔ <b>Real Over 1.5 Cartellini</b> @ 1.71 ⏳ (ore 21:00)\n\n"
            "<i>Riceverai notifiche push su gol, corner ed espulsioni in tempo reale!</i>"
        )
        send_telegram(start_msg)
        print("[TRACKER] Notifica di avvio inviata a Telegram.", flush=True)

        while True:
            try:
                self.poll()
            except Exception as e:
                print(f"[TRACKER ERROR] {e}", flush=True)
            time.sleep(50)

    def poll(self):
        # 1. AEK vs LASK (1635609)
        if "aek_lask" not in self.notified_legs:
            f_aek = self.collector._get("fixtures", {"id": 1635609})["response"][0]
            status = f_aek["fixture"]["status"]["short"]
            gh = f_aek["goals"]["home"] or 0
            ga = f_aek["goals"]["away"] or 0
            elapsed = f_aek["fixture"]["status"].get("elapsed")
            
            prev = self.last_scores.get(1635609)
            if prev is not None and (gh, ga) != prev:
                send_telegram(f"⚽ <b>GOL IN GRECIA!</b> AEK Atene {gh}-{ga} LASK Linz ({elapsed}')\n1X: {'🟢 OK' if gh >= ga else '⚠️ SOTTO'}")
            self.last_scores[1635609] = (gh, ga)

            if status in ("FT", "AET", "PEN"):
                if gh >= ga:
                    self.notified_legs.add("aek_lask")
                    send_telegram(f"✅ <b>PRESA! LEGA 1 CONCLUSA: AEK Atene {gh}-{ga} LASK FT</b>\nDoppia Chance 1X centrata in pieno! 🟢 (1/5)")
                else:
                    self.notified_legs.add("aek_lask_lost")
                    send_telegram(f"❌ <b>AEK Atene {gh}-{ga} LASK FT</b> — 1X mancata.")

        # 2. Lille vs Betis (1635683)
        if "lille_betis" not in self.notified_legs:
            f_lil = self.collector._get("fixtures", {"id": 1635683})["response"][0]
            status = f_lil["fixture"]["status"]["short"]
            gh = f_lil["goals"]["home"] or 0
            ga = f_lil["goals"]["away"] or 0
            tot = gh + ga
            elapsed = f_lil["fixture"]["status"].get("elapsed")

            prev = self.last_scores.get(1635683)
            if prev is not None and (gh, ga) != prev:
                send_telegram(f"⚽ <b>GOL A LILLA!</b> Lille {gh}-{ga} Betis ({elapsed}')\nTotale Gol: {tot}/3 (Under 3.5: {'🟢 AL SICURO' if tot <= 3 else '❌ SUPERATO'})")
            self.last_scores[1635683] = (gh, ga)

            if status in ("FT", "AET", "PEN"):
                if tot <= 3:
                    self.notified_legs.add("lille_betis")
                    send_telegram(f"✅ <b>PRESA! LEGA 2 CONCLUSA: Lille {gh}-{ga} Betis FT</b>\nUnder 3.5 Gol centrato! 🟢")
                else:
                    self.notified_legs.add("lille_betis_lost")

        # 3. Dortmund vs Villarreal (1635652)
        if "bvb_corners" not in self.notified_legs:
            st = self.collector._get("fixtures/statistics", {"fixture": 1635652}).get("response", [])
            bvb_c = 0
            if st and len(st) >= 1:
                for s in st[0].get("statistics", []):
                    if s["type"] == "Corner Kicks":
                        bvb_c = s["value"] or 0
            if bvb_c > self.last_corners_bvb:
                self.last_corners_bvb = bvb_c
                if bvb_c >= 5:
                    self.notified_legs.add("bvb_corners")
                    send_telegram(f"🚩🚩 <b>CASSA CORNER DORTMUND!</b>\nIl Borussia Dortmund ha raggiunto <b>{bvb_c} CORNER</b>! Over 4.5 Corner BVB PRESO AL 100%! 🟢")
                else:
                    print(f"[BVB CORNERS] Saliti a {bvb_c}/5", flush=True)

        # 4. Porto vs Man City (1635654)
        if "city_corners" not in self.notified_legs:
            st = self.collector._get("fixtures/statistics", {"fixture": 1635654}).get("response", [])
            p_c, c_c = 0, 0
            if st and len(st) >= 2:
                for s in st[0].get("statistics", []):
                    if s["type"] == "Corner Kicks": p_c = s["value"] or 0
                for s in st[1].get("statistics", []):
                    if s["type"] == "Corner Kicks": c_c = s["value"] or 0
            self.last_corners_city = (p_c, c_c)
            f_city = self.collector._get("fixtures", {"id": 1635654})["response"][0]
            if f_city["fixture"]["status"]["short"] in ("FT", "AET", "PEN"):
                if c_c > p_c:
                    self.notified_legs.add("city_corners")
                    send_telegram(f"✅ <b>PRESA! CORNER CITY FT: Porto {p_c} - {c_c} Man City</b>\n1X2 Corner: 2 (City) centrato! 🟢")

        # 5. Real Madrid vs Inter (1635714)
        if "real_cards" not in self.notified_legs:
            st = self.collector._get("fixtures/statistics", {"fixture": 1635714}).get("response", [])
            r_yc, r_rc = 0, 0
            if st and len(st) >= 1:
                for s in st[0].get("statistics", []):
                    if s["type"] == "Yellow Cards": r_yc = s["value"] or 0
                    if s["type"] == "Red Cards": r_rc = s["value"] or 0
            tot_cards_real = r_yc + r_rc
            if tot_cards_real > self.last_cards_real:
                self.last_cards_real = tot_cards_real
                if tot_cards_real >= 2:
                    self.notified_legs.add("real_cards")
                    send_telegram(f"🟨🟨 <b>CASSA CARTELLINI REAL MADRID!</b>\nIl Real Madrid ha ricevuto <b>{tot_cards_real} CARTELLINI</b>! Over 1.5 Cartellini Squadra 1 PRESO AL 100%! 🟢")

        # Final ticket check
        won_count = len([x for x in ["aek_lask", "lille_betis", "bvb_corners", "city_corners", "real_cards"] if x in self.notified_legs])
        if won_count == 5 and not self.ticket_won_sent:
            self.ticket_won_sent = True
            send_telegram(
                "🏆🎉💰 <b>CASSA TOTALE EN PLEIN! TICKET #64 VINTO AL 100%!</b> 💰🎉🏆\n\n"
                "Tutte e 5 le selezioni sono entrate!\n"
                "💵 Importo Puntato: 20.00 €\n"
                "💰 <b>VINCITA INCASSATA: 128.64 € NETTI!</b>\n\n"
                "Saldo Netwin aggiornato verso quota 358.64 €! 🔥"
            )

if __name__ == "__main__":
    tracker = Ticket64Tracker()
    tracker.run()
