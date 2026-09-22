#!/usr/bin/env python3
"""
scripts/live_tracker_all_active.py — Monitoraggio Real-Time PUSH ISTANTANEO
Monitora Ticket #68 (priorità assoluta) e tutte le altre schedine attive (#66, #67, #64, #69).
Invia notifiche Telegram per ogni evento rilevante e un heartbeat periodico.
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
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print(f"[TELEGRAM] Sent ({r.status_code}): {msg[:50]}...", flush=True)
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}", flush=True)

class ChampionsLiveMonitor:
    def __init__(self):
        self.collector = FootballExternalCollector()
        self.notified_legs = set()
        
        # State tracking
        self.last_city_corners = None
        self.last_bvb_corners = None
        self.last_real_fouls = None
        self.last_inter_fouls = None
        self.last_real_yellows = None
        self.last_lille_goals = None
        
        # Player fouls state
        self.player_stats_cache = {}
        
        # Heartbeat
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 300  # 5 minuti

    def run(self):
        print("[CHAMPIONS LIVE MONITOR] Avviato!", flush=True)
        # Invia messaggio di inizio monitoraggio 2° tempo
        self.send_startup_summary()

        while True:
            try:
                self.poll()
            except Exception as e:
                print(f"[POLL ERROR] {e}", flush=True)
            time.sleep(25)

    def send_startup_summary(self):
        msg = (
            "🔥 <b>MONITORAGGIO 2° TEMPO ATTIVO (48')</b> 🔥\n\n"
            "🎯 <b>TICKET #68 (Principale - 88€ ➔ 351.27€)</b>:\n"
            "• 🚩 Corner Dortmund: <b>4 / 5</b> (manca 1 corner!)\n"
            "• 🚩 Corner Man City: <b>1 / 5</b>\n"
            "• ⚔️ Falli Real-Inter: Real 4 - <b>6 INTER</b> (Inter +2! 🟢)\n\n"
            "📋 <b>ALTRE SCHEDINE IN CORSO</b>:\n"
            "• <b>#66 Falli Commessi Real-Inter (66.99€)</b>:\n"
            "  - Lautaro 1 commesso 🟢 (PRESO!)\n"
            "  - Dumfries, Rüdiger, Bastoni in attesa di falli.\n"
            "• <b>#67 Falli Subiti Real-Inter (65.11€)</b>:\n"
            "  - Bellingham 4 subiti 🟢 (PRESO!)\n"
            "  - Barella 1 subito 🟢 (PRESO!)\n"
            "  - Mbappé, Vinícius, Brahim in attesa.\n"
            "• <b>#64 & #69 Cinquine (128.64€ + 64.32€)</b>:\n"
            "  - AEK 1-0 LASK FT 🟢 (PRESO!)\n"
            "  - Lille 2-1 Betis (Under 3.5 in bilico)\n"
            "  - City 1-0 Porto sui corner 🟢\n\n"
            "⚡ <i>Notifiche istantanee attive su ogni corner/fallo/gol!</i>"
        )
        send_telegram(msg)

    def poll(self):
        # 1. Porto vs Manchester City (1635654)
        st_city = self.collector._get("fixtures/statistics", {"fixture": 1635654}).get("response", [])
        f_city = self.collector._get("fixtures", {"id": 1635654})["response"][0]
        el_city = f_city["fixture"]["status"].get("elapsed") or 0
        status_city = f_city["fixture"]["status"]["short"]
        
        c_city = 0
        c_porto = 0
        if len(st_city) >= 2:
            for s in st_city[0].get("statistics", []):
                if s["type"] == "Corner Kicks": c_porto = s["value"] or 0
            for s in st_city[1].get("statistics", []):
                if s["type"] == "Corner Kicks": c_city = s["value"] or 0
        
        if self.last_city_corners is not None and c_city > self.last_city_corners:
            if c_city >= 5 and "city_corners_won" not in self.notified_legs:
                self.notified_legs.add("city_corners_won")
                send_telegram(f"🚩🚩 <b>CASSA CORNER MAN CITY! ({el_city}')</b>\nIl City ha battuto il <b>{c_city}° CORNER</b>!\nOver 4.5 Corner City CENTRATO! 🟢 (Ticket #68)")
            else:
                send_telegram(f"🚩 <b>CORNER MAN CITY! ({el_city}')</b>\nManchester City a quota <b>{c_city} / 5 corner</b>! (Porto: {c_porto})")
        self.last_city_corners = c_city

        # 2. Dortmund vs Villarreal (1635652)
        st_bvb = self.collector._get("fixtures/statistics", {"fixture": 1635652}).get("response", [])
        f_bvb = self.collector._get("fixtures", {"id": 1635652})["response"][0]
        el_bvb = f_bvb["fixture"]["status"].get("elapsed") or 0
        status_bvb = f_bvb["fixture"]["status"]["short"]
        
        c_bvb = 0
        if len(st_bvb) >= 1:
            for s in st_bvb[0].get("statistics", []):
                if s["type"] == "Corner Kicks": c_bvb = s["value"] or 0
        
        if self.last_bvb_corners is not None and c_bvb > self.last_bvb_corners:
            if c_bvb >= 5 and "bvb_corners_won" not in self.notified_legs:
                self.notified_legs.add("bvb_corners_won")
                send_telegram(f"🚩🚩 <b>CASSA CORNER DORTMUND! ({el_bvb}')</b>\nIl BVB ha raggiunto <b>{c_bvb} CORNER</b>!\nOver 4.5 Corner BVB PRESO AL 100%! 🟢 (Ticket #68, #64, #69)")
            else:
                send_telegram(f"🚩 <b>CORNER DORTMUND! ({el_bvb}')</b>\nBorussia Dortmund a quota <b>{c_bvb} / 5 corner</b>!")
        self.last_bvb_corners = c_bvb

        # Ticket #70: Dortmund Over 1.5 Gol
        gh_bvb = f_bvb["goals"]["home"] or 0
        ga_bvb = f_bvb["goals"]["away"] or 0
        if (gh_bvb + ga_bvb) >= 2 and "bvb_over15_won" not in self.notified_legs:
            self.notified_legs.add("bvb_over15_won")
            send_telegram(f"⚽⚽ <b>CASSA OVER 1.5 GOL DORTMUND! ({el_bvb}')</b>\nRisultato BVB {gh_bvb} - {ga_bvb} Villarreal!\nSelezione Ticket #70 PRESA! 🟢 (1/2)")

        # 3. Real Madrid vs Inter (1635714)
        st_real = self.collector._get("fixtures/statistics", {"fixture": 1635714}).get("response", [])
        f_real = self.collector._get("fixtures", {"id": 1635714})["response"][0]
        el_real = f_real["fixture"]["status"].get("elapsed") or 0
        status_real = f_real["fixture"]["status"]["short"]

        rf, inf, ry = 0, 0, 0
        if len(st_real) >= 2:
            for s in st_real[0].get("statistics", []):
                if s["type"] == "Fouls": rf = s["value"] or 0
                if s["type"] == "Yellow Cards": ry = s["value"] or 0
            for s in st_real[1].get("statistics", []):
                if s["type"] == "Fouls": inf = s["value"] or 0

        if self.last_real_fouls is not None and (rf, inf) != (self.last_real_fouls, self.last_inter_fouls):
            diff = inf - rf
            tag = f"🟢 INTER AVANTI (+{diff})" if diff > 0 else (f"⚠️ REAL AVANTI (+{-diff})" if diff < 0 else "⚖️ PARITÀ")
            send_telegram(f"⚔️ <b>VARIAZIONE FALLI REAL-INTER ({el_real}')</b>\nReal Madrid <b>{rf} - {inf} INTER</b>\n1X2 Falli Ticket #68: <b>{tag}</b>")
        self.last_real_fouls = rf
        self.last_inter_fouls = inf

        if self.last_real_yellows is not None and ry > self.last_real_yellows:
            send_telegram(f"🟨 <b>CARTELLINO REAL MADRID! ({el_real}')</b>\nReal a quota <b>{ry} / 2 cartellini</b>! (Ticket #64/#69)")
            if ry >= 2 and "real_cards_won" not in self.notified_legs:
                self.notified_legs.add("real_cards_won")
                send_telegram(f"🟨🟨 <b>CASSA CARTELLINI REAL MADRID!</b> Over 1.5 Cartellini Real PRESO! 🟢")
        self.last_real_yellows = ry

        # Ticket #70: Inter Segna Gol
        ga_real = f_real["goals"]["away"] or 0
        if ga_real >= 1 and "inter_goal_won" not in self.notified_legs:
            self.notified_legs.add("inter_goal_won")
            send_telegram(f"⚽⚽ <b>CASSA INTER SEGNA GOL! ({el_real}')</b>\nL'Inter ha segnato al Bernabéu!\nSelezione Ticket #70 PRESA! 🟢")

        if "bvb_over15_won" in self.notified_legs and "inter_goal_won" in self.notified_legs and "ticket70_won" not in self.notified_legs:
            self.notified_legs.add("ticket70_won")
            send_telegram("🏆🎉💰 <b>CASSA TOTALE TICKET #70!</b>\n• Dortmund Over 1.5 Gol 🟢\n• Inter Segna Gol 🟢\nDoppia Live SBANCATA! 🔥")

        # 4. Lille vs Real Betis (1635683)
        f_lille = self.collector._get("fixtures", {"id": 1635683})["response"][0]
        el_lille = f_lille["fixture"]["status"].get("elapsed") or 0
        gh = f_lille["goals"]["home"] or 0
        ga = f_lille["goals"]["away"] or 0
        tot_goals = gh + ga
        if self.last_lille_goals is not None and tot_goals > self.last_lille_goals:
            if tot_goals >= 4:
                send_telegram(f"❌ <b>GOL A LILLA ({el_lille}')</b>: Lille {gh} - {ga} Betis. Purtroppo Under 3.5 superato ({tot_goals} gol).")
            else:
                send_telegram(f"⚽ <b>GOL A LILLA ({el_lille}')</b>: Lille {gh} - {ga} Betis (Totale {tot_goals} gol, Under 3.5 ancora vivo!).")
        self.last_lille_goals = tot_goals

        # 5. Monitoraggio Giocatori Real-Inter (ogni 60s circa)
        if int(time.time()) % 60 < 25:
            self.check_player_props(el_real)

        # Heartbeat periodico ogni 5 minuti se non ci sono eventi
        if time.time() - self.last_heartbeat > self.heartbeat_interval:
            self.last_heartbeat = time.time()
            send_telegram(
                f"⏱️ <b>LIVE UPDATE ({el_real}')</b>\n\n"
                f"• <b>Real-Inter</b>: Real {rf} - <b>{inf} INTER</b> (1X2 Falli #68: {'🟢' if inf > rf else '⚠️'})\n"
                f"• <b>Corner BVB</b>: {self.last_bvb_corners} / 5\n"
                f"• <b>Corner City</b>: {self.last_city_corners} / 5 (Porto: {c_porto})\n"
                f"• <b>Lille-Betis</b>: {gh} - {ga} (Under 3.5: {'🟢' if tot_goals <= 3 else '❌'})\n\n"
                f"💰 <i>Ticket #68 potenziale: 351.27 €</i>"
            )

        # Finale Match
        if status_real in ("FT", "AET", "PEN") and "fouls_final" not in self.notified_legs:
            self.notified_legs.add("fouls_final")
            if inf > rf:
                self.notified_legs.add("inter_fouls_won")
                send_telegram(f"✅ <b>CASSA FALLI INTER FT!</b>\nReal Madrid {rf} - <b>{inf} Inter</b>\n1X2 Falli CENTRATO! 🟢")
            else:
                send_telegram(f"❌ Finale Falli FT: Real {rf} - {inf} Inter.")

        # Boato Cassa Totale Ticket #68
        if "city_corners_won" in self.notified_legs and "bvb_corners_won" in self.notified_legs and "inter_fouls_won" in self.notified_legs:
            if not getattr(self, "ticket_won_sent", False):
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

    def check_player_props(self, elapsed):
        try:
            pl_data = self.collector._get("fixtures/players", {"fixture": 1635714}).get("response", [])
            for team in pl_data:
                for p in team.get("players", []):
                    pname = p["player"]["name"]
                    stats = p["statistics"][0]
                    fc = stats["fouls"]["committed"] or 0
                    fd = stats["fouls"]["drawn"] or 0
                    
                    old_fc, old_fd = self.player_stats_cache.get(pname, (fc, fd))
                    
                    # Notifiche Ticket #66 (Commessi)
                    if "Dumfries" in pname and fc > old_fc:
                        send_telegram(f"🎯 <b>DUMFRIES FALLO COMMESSO! ({elapsed}')</b> Over 0.5 Falli Commessi PRESO! 🟢 (Ticket #66)")
                    if "Rüdiger" in pname and fc > old_fc:
                        send_telegram(f"🎯 <b>RÜDIGER FALLO COMMESSO! ({elapsed}')</b> Over 0.5 Falli Commessi PRESO! 🟢 (Ticket #66)")
                    if "Bastoni" in pname and fc > old_fc:
                        send_telegram(f"🎯 <b>BASTONI FALLO COMMESSO! ({elapsed}')</b> ({fc}/2 falli) (Ticket #66)")
                        if fc >= 2:
                            send_telegram(f"🎯🎯 <b>BASTONI OVER 1.5 FALLI COMMESSI PRESO! 🟢</b>")
                    
                    # Notifiche Ticket #67 (Subiti)
                    if "Mbappé" in pname and fd > old_fd:
                        send_telegram(f"🎯 <b>MBAPPÉ FALLO SUBITO! ({elapsed}')</b> Over 0.5 Falli Subiti PRESO! 🟢 (Ticket #67)")
                    if "Vinícius" in pname and fd > old_fd:
                        send_telegram(f"🎯 <b>VINÍCIUS FALLO SUBITO! ({elapsed}')</b> ({fd}/2 subiti) (Ticket #67)")
                        if fd >= 2:
                            send_telegram(f"🎯🎯 <b>VINÍCIUS OVER 1.5 FALLI SUBITI PRESO! 🟢</b>")
                    if "Brahim" in pname and fd > old_fd:
                        send_telegram(f"🎯 <b>BRAHIM DÍAZ FALLO SUBITO! ({elapsed}')</b> ({fd}/2 subiti) (Ticket #67)")
                        if fd >= 2:
                            send_telegram(f"🎯🎯 <b>BRAHIM OVER 1.5 FALLI SUBITI PRESO! 🟢</b>")
                            
                    self.player_stats_cache[pname] = (fc, fd)
        except Exception as e:
            print(f"[PLAYER PROPS ERROR] {e}", flush=True)

if __name__ == "__main__":
    monitor = ChampionsLiveMonitor()
    monitor.run()
