#!/usr/bin/env python3
"""
scripts/live_tracker_argentine_suite.py
Live Sentinel dedicato alla Quartina Notturna Argentina (31.00 EUR -> 93.32 EUR):
- Midland vs Chacarita (1 @ 1.12)
- Argentinos vs Gimnasia (2 @ 1.22)
- Independiente vs San Lorenzo (1X + Under 3.5 @ 1.44)
- Huracán vs Racing Club (1X + Under 3.5 @ 1.53)
"""

import os
import sys
import time
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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

TICKET_ID = "CONFIRMED_SUNDAY_31EUR_ARGENTINE_CORAZZATA"
STAKE = 31.00
PAYOUT = 93.32

MATCHES = {
    "midland": {
        "name": "CA Ferrocarril Midland vs Chacarita Juniors",
        "sport": "arg.2",
        "event_id": "401844127",
        "market": "1",
        "sub_db": "Midland"
    },
    "gimnasia": {
        "name": "Argentinos Juniors vs Gimnasia La Plata",
        "sport": "arg.1",
        "event_id": "401841560",
        "market": "2",
        "sub_db": "Argentinos"
    },
    "independiente": {
        "name": "Independiente vs San Lorenzo",
        "sport": "arg.1",
        "event_id": "401841568",
        "market": "1X + Under 3.5",
        "sub_db": "Independiente"
    },
    "huracan": {
        "name": "Huracán vs Racing Club",
        "sport": "arg.1",
        "event_id": "401841561",
        "market": "1X + Under 3.5",
        "sub_db": "Huracán"
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
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE bet_leg_ledger SET result_status = ? WHERE ticket_id = ? AND match_name LIKE ?",
            (status, TICKET_ID, f"%{match_sub}%")
        )
        conn.commit()
        conn.close()
        print(f"[DB LEG] {TICKET_ID} | {match_sub} -> {status}", flush=True)
    except Exception as e:
        print("DB leg err:", e, flush=True)


def update_db_ticket(status: str, pnl: float):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE ticket_ledger SET status = ?, profit_loss_eur = ? WHERE ticket_id = ?",
            (status, pnl, TICKET_ID)
        )
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
    print(f"=== [BAGENT] Live Sentinel Notturno Argentina ({TICKET_ID}) Avviato ===", flush=True)

    state = {}
    for k, info in MATCHES.items():
        state[k] = {
            "home_score": 0,
            "away_score": 0,
            "status": "SCHEDULED",
            "completed": False
        }
        data = get_event_summary(info["sport"], info["event_id"])
        if not data:
            continue
        header = data.get("header", {})
        comp = header.get("competitions", [{}])[0]
        status_obj = comp.get("status", {}).get("type", {})
        status_desc = status_obj.get("description", "Scheduled")
        completed = status_obj.get("completed", False)
        competitors = comp.get("competitors", [])
        h_score, a_score = 0, 0
        if len(competitors) >= 2:
            h_score = int(competitors[0].get("score", 0)) if competitors[0].get("score") else 0
            a_score = int(competitors[1].get("score", 0)) if competitors[1].get("score") else 0

        state[k]["home_score"] = h_score
        state[k]["away_score"] = a_score
        state[k]["status"] = "Full Time" if completed else status_desc
        state[k]["completed"] = completed
        print(f"  -> {info['name']}: {state[k]['status']} ({h_score}-{a_score})", flush=True)

    send_tg(
        f"🇦🇷 <b>BAGENT LIVE SENTINEL: CORAZZATA ARGENTINA ATTIVA!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Stake</b>: {STAKE:.2f} € ➔ <b>Quota</b>: 3.01 ➔ <b>Incasso</b>: {PAYOUT:.2f} €\n\n"
        f"1️⃣ <b>Midland vs Chacarita</b>: 1 @ 1.12 (Live {state['midland']['home_score']}-{state['midland']['away_score']})\n"
        f"2️⃣ <b>Argentinos vs Gimnasia</b>: 2 @ 1.22 (Live {state['gimnasia']['home_score']}-{state['gimnasia']['away_score']})\n"
        f"3️⃣ <b>Independiente vs San Lorenzo</b>: 1X + Under 3.5 @ 1.44 (00:15)\n"
        f"4️⃣ <b>Huracán vs Racing Club</b>: 1X + Under 3.5 @ 1.53 (02:30)"
    )

    ticket_failed = False

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
            status_detail = comp.get("status", {}).get("displayClock", "") or status_obj.get("detail", "")
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
                if not ticket_failed:
                    msg = f"⚽ <b>GOL! {info['name']}</b> ➔ {h_score} - {a_score} ({status_detail})"
                    print(msg, flush=True)
                    send_tg(msg)

            # Kickoff detection
            if old_status == "SCHEDULED" and status_desc in ["In Progress", "First Half"]:
                state[k]["status"] = status_desc
                if not ticket_failed:
                    msg = f"⏱️ <b>KICKOFF! {info['name']}</b> ({status_detail})"
                    print(msg, flush=True)
                    send_tg(msg)

            # Halftime detection
            if old_status != "Halftime" and status_desc == "Halftime":
                state[k]["status"] = "Halftime"
                if not ticket_failed:
                    msg = f"⏸️ <b>HT: {info['name']}</b> ➔ {h_score} - {a_score}"
                    print(msg, flush=True)
                    send_tg(msg)

            # Completed detection
            if completed and not state[k]["completed"]:
                state[k]["completed"] = True
                state[k]["status"] = "Full Time"
                state[k]["home_score"] = h_score
                state[k]["away_score"] = a_score
                tot_goals = h_score + a_score

                is_won = False
                if k == "midland":
                    is_won = (h_score > a_score)
                elif k == "gimnasia":
                    is_won = (a_score > h_score)
                elif k in ["independiente", "huracan"]:
                    is_won = (h_score >= a_score) and (tot_goals <= 3)

                status_str = "WON" if is_won else "LOST"
                update_db_leg(info["sub_db"], status_str)

                if not is_won:
                    ticket_failed = True
                    update_db_ticket("LOST", -STAKE)
                    print(f"Leg {k} persa! Ticket compromesso. Sentinel silenziato.", flush=True)
                    # Non invia notifiche di perdita secondo le regole utente
                else:
                    if not ticket_failed:
                        msg = f"✅ <b>PRESA! {info['name']}</b> ({info['market']}) ➔ Risultato: {h_score} - {a_score}"
                        print(msg, flush=True)
                        send_tg(msg)

        if ticket_failed:
            print("Ticket fallito. Monitoraggio interrotto per silenzio assoluto.", flush=True)
            break

        if all_completed:
            print("Tutti i 4 match completati!", flush=True)
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT result_status FROM bet_leg_ledger WHERE ticket_id = ?", (TICKET_ID,))
                statuses = [r[0] for r in c.fetchall()]
                conn.close()
                if all(s == "WON" for s in statuses):
                    update_db_ticket("WON", round(PAYOUT - STAKE, 2))
                    send_tg(f"🏆🎉🇦🇷 <b>CORAZZATA ARGENTINA VINTA! INCASSATI {PAYOUT:.2f} €!</b> (Netto: +{PAYOUT - STAKE:.2f} €)")
            except Exception as e:
                print("Settle err:", e)
            break

        time.sleep(30)


if __name__ == "__main__":
    main()
