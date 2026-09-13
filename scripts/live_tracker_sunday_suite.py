#!/usr/bin/env python3
"""
scripts/live_tracker_sunday_suite.py
Live Sentinel Domenicale con integrazione di:
- Ticket Pomeriggio (T1): WON (+41.00 EUR)
- Master Hepta (T2): LOST (-10.00 EUR)
- Master Penta Quota 10 (T3): PENDING (10.00 EUR -> 95.32 EUR)
- Corazzata 4 Eventi (T4): PENDING (30.00 EUR -> 123.78 EUR)
- LiveSiegeEngine (Regola #50)
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

from services.live.siege_engine import LiveSiegeEngine, SiegeOpportunity

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

TICKET_PENTA = "CONFIRMED_SUNDAY_10EUR_MASTER_PENTA"
TICKET_CORAZZATA = "CONFIRMED_SUNDAY_30EUR_NIGHT_CORAZZATA"

MATCHES = {
    "juve": {
        "name": "Sassuolo vs Juventus",
        "sport": "ita.1",
        "event_id": "401874750",
        "t3_market": "MultiGol 0-1 1°T",
        "t4_market": "MultiGol 1-3 Ospite",
        "pre_odd_h": 4.50,
        "pre_odd_a": 1.75
    },
    "psg": {
        "name": "Brest vs Paris Saint-Germain",
        "sport": "fra.1",
        "event_id": "401876465",
        "t3_market": "2 + Over 2.5",
        "t4_market": "2 + Over 2.5",
        "pre_odd_h": 7.50,
        "pre_odd_a": 1.30
    },
    "sociedad": {
        "name": "Real Sociedad vs Atletico Madrid",
        "sport": "esp.1",
        "event_id": "401882879",
        "t3_market": "Over 4.5 Cartellini",
        "pre_odd_h": 3.10,
        "pre_odd_a": 2.45
    },
    "sporting": {
        "name": "FC Famalicao vs Sporting CP",
        "sport": "por.1",
        "event_id": "401885443",
        "t3_market": "2 + Over 1.5",
        "t4_market": "X2 + Over 1.5",
        "pre_odd_h": 6.00,
        "pre_odd_a": 1.50
    },
    "flamengo": {
        "name": "Flamengo vs Corinthians",
        "sport": "bra.1",
        "event_id": "401841237",
        "t3_market": "1 + Over 1.5",
        "t4_market": "1X + Under 3.5",
        "pre_odd_h": 1.30,
        "pre_odd_a": 10.00
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


def update_db_leg(ticket_id: str, match_sub: str, status: str):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE bet_leg_ledger SET result_status = ? WHERE ticket_id = ? AND match_name LIKE ?",
            (status, ticket_id, f"%{match_sub}%")
        )
        conn.commit()
        conn.close()
        print(f"[DB LEG] {ticket_id} | {match_sub} -> {status}", flush=True)
    except Exception as e:
        print("DB leg err:", e, flush=True)


def update_db_ticket(ticket_id: str, status: str, pnl: float):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE ticket_ledger SET status = ?, profit_loss_eur = ? WHERE ticket_id = ?",
            (status, pnl, ticket_id)
        )
        conn.commit()
        conn.close()
        print(f"[DB TICKET] {ticket_id} -> {status} (pnl: {pnl})", flush=True)
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


def parse_minute(clock_str: str, status_desc: str) -> int:
    if not clock_str:
        if status_desc == "First Half":
            return 25
        if status_desc == "Halftime":
            return 45
        if status_desc == "Second Half":
            return 65
        return 0
    clean = clock_str.replace("'", "").split("+")[0].strip()
    try:
        return int(clean)
    except:
        return 45 if status_desc == "Halftime" else 0


def extract_box_stats(data: dict):
    stats_dict = {
        "h_corners": 0, "a_corners": 0,
        "h_cards": 0, "a_cards": 0,
        "h_shots": 0, "a_shots": 0
    }
    teams = data.get("boxscore", {}).get("teams", [])
    if len(teams) >= 2:
        h_s = {s.get("name"): s.get("displayValue") for s in teams[0].get("statistics", [])}
        a_s = {s.get("name"): s.get("displayValue") for s in teams[1].get("statistics", [])}
        try:
            stats_dict["h_corners"] = int(h_s.get("wonCorners", 0))
            stats_dict["a_corners"] = int(a_s.get("wonCorners", 0))
            stats_dict["h_cards"] = int(h_s.get("yellowCards", 0))
            stats_dict["a_cards"] = int(a_s.get("yellowCards", 0))
            stats_dict["h_shots"] = int(h_s.get("totalShots", 0))
            stats_dict["a_shots"] = int(a_s.get("totalShots", 0))
        except:
            pass
    return stats_dict


def main():
    print(f"=== [BAGENT] Live Sentinel Notturno (T3 Penta + T4 Corazzata) Avviato ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===", flush=True)

    siege_engine = LiveSiegeEngine()
    siege_alerted = set()
    cards_alerted_5 = False
    juve_ht_settled = False

    state = {k: {"status": "SCHEDULED", "home_score": 0, "away_score": 0, "completed": False} for k in MATCHES}

    print("[INIT] Sincronizzazione iniziale...", flush=True)
    for k, info in MATCHES.items():
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
        "🚀 <b>BAGENT LIVE SENTINEL ATTIVO SUI 2 NUOVI TICKET!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ <b>Cinquina Quota 10 (10.00 € ➔ 95.32 €)</b>: Attiva!\n"
        "2️⃣ <b>Corazzata 4 Eventi (30.00 € ➔ 123.78 €)</b>: Attiva!\n\n"
        "⚡ <i>Brest vs PSG già sullo 0 - 1! Sassuolo-Juve 0 - 0 al 12'!</i>"
    )

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
            h_name, a_name = "", ""
            if len(competitors) >= 2:
                h_score = int(competitors[0].get("score", 0)) if competitors[0].get("score") else 0
                a_score = int(competitors[1].get("score", 0)) if competitors[1].get("score") else 0
                h_name = competitors[0].get("team", {}).get("displayName", "")
                a_name = competitors[1].get("team", {}).get("displayName", "")

            old_h = state[k]["home_score"]
            old_a = state[k]["away_score"]
            old_status = state[k]["status"]

            cur_minute = parse_minute(comp.get("status", {}).get("displayClock", ""), status_desc)

            # Goal detection
            if (h_score != old_h or a_score != old_a) and status_desc in ["In Progress", "First Half", "Second Half"]:
                state[k]["home_score"] = h_score
                state[k]["away_score"] = a_score
                msg = f"⚽ <b>GOL! {info['name']}</b> ➔ {h_score} - {a_score} ({status_detail})"
                print(msg, flush=True)
                send_tg(msg)

            # Kickoff detection
            if old_status == "SCHEDULED" and status_desc in ["In Progress", "First Half"]:
                state[k]["status"] = status_desc
                msg = f"⏱️ <b>KICKOFF! {info['name']}</b> ({status_detail})"
                print(msg, flush=True)
                send_tg(msg)

            # Halftime detection & Juve MultiGol 0-1 1°T check
            if old_status != "Halftime" and status_desc == "Halftime":
                state[k]["status"] = "Halftime"
                msg = f"⏸️ <b>HT: {info['name']}</b> ➔ {h_score} - {a_score}"
                print(msg, flush=True)
                send_tg(msg)

                if k == "juve" and not juve_ht_settled:
                    juve_ht_settled = True
                    ht_goals = h_score + a_score
                    if ht_goals <= 1:
                        update_db_leg(TICKET_PENTA, "Sassuolo", "WON")
                        send_tg("✅ <b>Sassuolo-Juve: MultiGol 0-1 1°Tempo VINTO!</b> (0-0 o 1 gol a HT)")
                    else:
                        update_db_leg(TICKET_PENTA, "Sassuolo", "LOST")

            # Cartellini check in Real Sociedad vs Atletico Madrid
            if k == "sociedad" and not cards_alerted_5:
                box_stats = extract_box_stats(data)
                tot_c = box_stats["h_cards"] + box_stats["a_cards"]
                if tot_c >= 5:
                    cards_alerted_5 = True
                    update_db_leg(TICKET_PENTA, "Sociedad", "WON")
                    send_tg(f"🟨🟨 <b>OVER 4.5 CARTELLINI CENTRATO! ({tot_c} cartellini)</b> in Real Sociedad vs Atlético!")

            # Completed detection
            if completed and not state[k]["completed"]:
                state[k]["completed"] = True
                state[k]["status"] = "Full Time"
                state[k]["home_score"] = h_score
                state[k]["away_score"] = a_score
                tot_goals = h_score + a_score

                # PSG leg check
                if k == "psg":
                    psg_won_2ov25 = (a_score > h_score) and (tot_goals >= 3)
                    update_db_leg(TICKET_PENTA, "PSG", "WON" if psg_won_2ov25 else "LOST")
                    update_db_leg(TICKET_CORAZZATA, "PSG", "WON" if psg_won_2ov25 else "LOST")

                # Juve leg check (Corazzata MultiGol 1-3 Ospite)
                if k == "juve":
                    juve_won_mg = (1 <= a_score <= 3)
                    update_db_leg(TICKET_CORAZZATA, "Juve", "WON" if juve_won_mg else "LOST")

                # Sporting leg check
                if k == "sporting":
                    sp_won_penta = (a_score > h_score) and (tot_goals >= 2)
                    sp_won_corazzata = (a_score >= h_score) and (tot_goals >= 2)
                    update_db_leg(TICKET_PENTA, "Sporting", "WON" if sp_won_penta else "LOST")
                    update_db_leg(TICKET_CORAZZATA, "Sporting", "WON" if sp_won_corazzata else "LOST")

                # Flamengo leg check
                if k == "flamengo":
                    fla_won_penta = (h_score > a_score) and (tot_goals >= 2)
                    fla_won_corazzata = (h_score >= a_score) and (tot_goals <= 3)
                    update_db_leg(TICKET_PENTA, "Flamengo", "WON" if fla_won_penta else "LOST")
                    update_db_leg(TICKET_CORAZZATA, "Flamengo", "WON" if fla_won_corazzata else "LOST")

                msg = f"🏁 <b>FT: {info['name']}</b> ➔ {h_score} - {a_score}"
                print(msg, flush=True)
                send_tg(msg)

        if all_completed:
            print("Tutti i match notturni completati!", flush=True)
            # Final settle tickets
            for tid, payout, stake in [(TICKET_PENTA, 95.32, 10.00), (TICKET_CORAZZATA, 123.78, 30.00)]:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT result_status FROM bet_leg_ledger WHERE ticket_id = ?", (tid,))
                    statuses = [r[0] for r in c.fetchall()]
                    conn.close()
                    if all(s == "WON" for s in statuses):
                        update_db_ticket(tid, "WON", round(payout - stake, 2))
                        send_tg(f"🏆🎉 <b>{tid} VINTO! INCASSATI {payout:.2f} €!</b>")
                    else:
                        update_db_ticket(tid, "LOST", -stake)
                except Exception as e:
                    print("Settle err:", e)
            break

        time.sleep(30)


if __name__ == "__main__":
    main()
