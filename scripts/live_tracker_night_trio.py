#!/usr/bin/env python3
import os
import sys
import time
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "storage" / "database" / "bagent.db"

env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")
HEADERS_ESPN = {"User-Agent": "ESPN/6.0.0 (iPhone; iOS 17.0; Scale/3.00)", "Accept": "*/*"}

TICKET_ID = "CONFIRMED_NIGHT_20EUR_AMERICAS_TRIO"

MATCHES = {
    "palmeiras": {
        "name": "Palmeiras vs Sao Paulo",
        "sport": "bra.1",
        "event_id": "401841234",
        "market": "1X + Under 3.5",
        "odd": 1.45
    },
    "toluca": {
        "name": "Deportivo Toluca vs Atlas",
        "sport": "mex.1",
        "event_id": "401876982",
        "market": "1X + Over 1.5",
        "odd": 1.32
    },
    "miami": {
        "name": "Inter Miami vs Nashville",
        "sport": "usa.1",
        "event_id": "761800",
        "market": "1X + Over 1.5",
        "odd": 1.50
    }
}

def send_tg(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print("TG err:", e, flush=True)
        return False

def update_db_leg(match_sub: str, status: str):
    if not DB_PATH.exists(): return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE bet_leg_ledger SET result_status = ? WHERE ticket_id = ? AND match_name LIKE ?", (status, TICKET_ID, f"%{match_sub}%"))
        conn.commit()
        conn.close()
        print(f"[DB LEG] {match_sub} -> {status}", flush=True)
    except Exception as e:
        print("DB leg err:", e, flush=True)

def update_db_ticket(status: str, pnl: float):
    if not DB_PATH.exists(): return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE ticket_ledger SET status = ?, profit_loss_eur = ? WHERE ticket_id = ?", (status, pnl, TICKET_ID))
        conn.commit()
        conn.close()
        print(f"[DB TICKET] {TICKET_ID} -> {status} (pnl: {pnl})", flush=True)
    except Exception as e:
        print("DB ticket err:", e, flush=True)

def get_event_summary(sport: str, event_id: str):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{sport}/summary?event={event_id}"
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

def main():
    print(f"=== [BAGENT] Live Sentinel Trio Notturno Avviato ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===", flush=True)
    send_tg("🛡️ <b>[BAGENT] Live Sentinel Trio Notturno Avviato</b>\nTicket: <b>Palmeiras + Toluca + Inter Miami</b>\nQuota Totale: <b>@2.87</b> | Stake: <b>20.00 €</b>\nPayout: <b>57.42 €</b>")

    state = {k: {"status": "SCHEDULED", "home_score": 0, "away_score": 0, "completed": False} for k in MATCHES}

    while True:
        all_completed = True
        for k, info in MATCHES.items():
            if state[k]["completed"]:
                continue
            all_completed = False

            data = get_event_summary(info["sport"], info["event_id"])
            if not data:
                continue

            header = data.get("header", {})
            comp = header.get("competitions", [{}])[0]
            status_obj = comp.get("status", {}).get("type", {})
            status_desc = status_obj.get("description", "Scheduled")
            status_detail = status_obj.get("detail", "")
            completed = status_obj.get("completed", False)

            competitors = comp.get("competitors", [])
            h_score, a_score = 0, 0
            if len(competitors) >= 2:
                h_score = int(competitors[0].get("score", 0)) if competitors[0].get("score") else 0
                a_score = int(competitors[1].get("score", 0)) if competitors[1].get("score") else 0

            old_h = state[k]["home_score"]
            old_a = state[k]["away_score"]
            old_status = state[k]["status"]

            # Goal detection
            if (h_score != old_h or a_score != old_a) and status_desc in ["In Progress", "First Half", "Second Half"]:
                state[k]["home_score"] = h_score
                state[k]["away_score"] = a_score
                msg = f"⚽ <b>GOL! {info['name']}</b> -> {h_score} - {a_score} ({status_detail})\nMercato: {info['market']}"
                print(msg, flush=True)
                send_tg(msg)

            # Kickoff detection
            if old_status == "SCHEDULED" and status_desc in ["In Progress", "First Half"]:
                state[k]["status"] = status_desc
                msg = f"⏱️ <b>KICKOFF! {info['name']}</b> ({info['market']})"
                print(msg, flush=True)
                send_tg(msg)

            # Halftime detection
            if old_status != "Halftime" and status_desc == "Halftime":
                state[k]["status"] = "Halftime"
                msg = f"⏸️ <b>HT: {info['name']}</b> -> {h_score} - {a_score}"
                print(msg, flush=True)
                send_tg(msg)

            # Completed detection
            if completed and not state[k]["completed"]:
                state[k]["completed"] = True
                state[k]["status"] = "Full Time"
                state[k]["home_score"] = h_score
                state[k]["away_score"] = a_score
                
                # Check outcome
                total_goals = h_score + a_score
                leg_won = False
                if k == "palmeiras":
                    # 1X + Under 3.5 (Palmeiras home)
                    leg_won = (h_score >= a_score) and (total_goals <= 3)
                elif k == "toluca":
                    # 1X + Over 1.5 (Toluca home)
                    leg_won = (h_score >= a_score) and (total_goals >= 2)
                elif k == "miami":
                    # 1X + Over 1.5 (Miami home)
                    leg_won = (h_score >= a_score) and (total_goals >= 2)

                status_str = "WON" if leg_won else "LOST"
                emoji = "✅" if leg_won else "❌"
                update_db_leg(k, status_str)
                msg = f"{emoji} <b>FT: {info['name']}</b> -> {h_score} - {a_score}\nMercato: {info['market']} -> <b>{status_str}</b>"
                print(msg, flush=True)
                send_tg(msg)

        if all_completed:
            print("Tutti i match del trio completati!", flush=True)
            # Check full ticket status
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT result_status FROM bet_leg_ledger WHERE ticket_id = ?", (TICKET_ID,))
                statuses = [r[0] for r in c.fetchall()]
                conn.close()
                if all(s == "WON" for s in statuses):
                    update_db_ticket("WON", 37.42)
                    send_tg("🎉🎉 <b>TICKET VINTO! TRIO NOTTURNO INCASSATO!</b>\nPayout: <b>57.42 €</b> (+37.42 € netti!)")
                else:
                    update_db_ticket("LOST", -20.00)
                    send_tg("❌ <b>TICKET CHIUSO: NON VINTO.</b>")
            except Exception as e:
                print("Final check err:", e)
            break

        time.sleep(30)

if __name__ == "__main__":
    main()
