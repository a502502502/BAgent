#!/usr/bin/env python3
"""
scripts/live_tracker_saturday_afternoon.py
Sentinel Telegram & Database per la Schedina Ufficiale Netwin (10€ -> 67.95€).

Monitora in tempo reale tramite ESPN Live Scoreboard (Zero limiti API):
1. Sudtirol vs Modena (15:00) ➔ 1X @ 1.60
2. Borussia Dortmund vs Paderborn (15:30) ➔ 1X2 Corner: Dortmund @ 1.19
3. Augsburg vs Bayer Leverkusen (15:30) ➔ Gol (Entrambe Segnano) @ 1.36
4. Liverpool vs Fulham (16:00) ➔ 1X2 Corner: Liverpool @ 1.40
5. Osasuna vs Espanyol (16:15) ➔ 1X @ 1.31
6. Strasburgo vs Monaco (17:15) ➔ X2 @ 1.35
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
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "storage" / "database" / "bagent.db"

# Carica .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TICKET_ID = "CONFIRMED_SATURDAY_10EUR_MASTER"

HEADERS_ESPN = {
    "User-Agent": "ESPN/6.0.0 (iPhone; iOS 17.0; Scale/3.00)",
    "Accept": "*/*",
}

MATCHES = {
    "sudtirol": {
        "name": "Sudtirol vs Modena",
        "league": "Serie B",
        "espn_league": "ita.2",
        "event_id": "401899620",
        "home_kw": "sudtirol",
        "away_kw": "modena",
        "kickoff": "15:00",
        "market": "Doppia Chance 1X",
        "odds": 1.60,
        "type": "DC_1X"
    },
    "dortmund": {
        "name": "Borussia Dortmund vs Paderborn",
        "league": "Bundesliga",
        "espn_league": "ger.1",
        "event_id": "401884799",
        "home_kw": "dortmund",
        "away_kw": "paderborn",
        "kickoff": "15:30",
        "market": "1X2 Corner: Dortmund",
        "odds": 1.19,
        "type": "CORNER_1"
    },
    "augsburg": {
        "name": "Augsburg vs Bayer Leverkusen",
        "league": "Bundesliga",
        "espn_league": "ger.1",
        "event_id": "401884795",
        "home_kw": "augsburg",
        "away_kw": "leverkusen",
        "kickoff": "15:30",
        "market": "Gol (Entrambe Segnano)",
        "odds": 1.36,
        "type": "BTTS"
    },
    "liverpool": {
        "name": "Liverpool vs Fulham",
        "league": "Premier League",
        "espn_league": "eng.1",
        "event_id": "401879279",
        "home_kw": "liverpool",
        "away_kw": "fulham",
        "kickoff": "16:00",
        "market": "1X2 Corner: Liverpool",
        "odds": 1.40,
        "type": "CORNER_1"
    },
    "osasuna": {
        "name": "Osasuna vs Espanyol",
        "league": "La Liga",
        "espn_league": "esp.1",
        "event_id": "401882882",
        "home_kw": "osasuna",
        "away_kw": "espanyol",
        "kickoff": "16:15",
        "market": "Doppia Chance 1X",
        "odds": 1.31,
        "type": "DC_1X"
    },
    "monaco": {
        "name": "Strasburgo vs Monaco",
        "league": "Ligue 1",
        "espn_league": "fra.1",
        "event_id": "401876458",
        "home_kw": "strasbourg",
        "away_kw": "monaco",
        "kickoff": "17:15",
        "market": "Doppia Chance X2",
        "odds": 1.35,
        "type": "DC_X2"
    }
}

def send_tg(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Errore TG: {e}", flush=True)
        return False

def update_db_leg(match_name_sub: str, status: str):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE bet_leg_ledger
            SET result_status = ?
            WHERE ticket_id = ? AND match_name LIKE ?
        """, (status, TICKET_ID, f"%{match_name_sub}%"))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Errore update leg DB: {e}", flush=True)

def update_db_ticket(status: str, pnl: float):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE ticket_ledger
            SET status = ?, profit_loss_eur = ?
            WHERE ticket_id = ?
        """, (status, pnl, TICKET_ID))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Errore update ticket DB: {e}", flush=True)

def fetch_espn_data(espn_league: str) -> list[dict]:
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_league}/scoreboard"
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=10)
        if r.status_code == 200:
            return r.json().get("events", [])
        else:
            print(f"ESPN {espn_league} status code: {r.status_code}", flush=True)
    except Exception as e:
        print(f"Errore fetch ESPN {espn_league}: {e}", flush=True)
    return []

def fetch_event_summary(espn_league: str, event_id: str) -> dict:
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_league}/summary?event={event_id}"
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

def main():
    print(f"=== [BAGENT] Live Sentinel Sabato Pomeriggio Avviato ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===", flush=True)

    welcome_msg = (
        "🎟️ <b>SCHEDINA UFFICIALE SABATO PIAZZATA SU NETWIN!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <b>Puntata:</b> 10.00 € | 🎯 <b>Vincita Potenziale:</b> <b>67.95 €</b>\n"
        "📈 <b>Quota Totale:</b> 6.41× (+3.84 € Bonus)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ <b>Sudtirol vs Modena</b> (15:00) ➔ <b>1X</b> @ 1.60\n"
        "2️⃣ <b>B. Dortmund vs Paderborn</b> (15:30) ➔ <b>1X2 Corner: 1</b> @ 1.19\n"
        "3️⃣ <b>Augsburg vs Leverkusen</b> (15:30) ➔ <b>Gol (GG)</b> @ 1.36\n"
        "4️⃣ <b>Liverpool vs Fulham</b> (16:00) ➔ <b>1X2 Corner: 1</b> @ 1.40\n"
        "5️⃣ <b>Osasuna vs Espanyol</b> (16:15) ➔ <b>1X</b> @ 1.31\n"
        "6️⃣ <b>Strasburgo vs Monaco</b> (17:15) ➔ <b>X2</b> @ 1.35\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📡 <i>Sentinel live attivo: monitoraggio gol e corner in corso!</i>"
    )
    send_tg(welcome_msg)
    print("Welcome message inviato a Telegram.", flush=True)

    match_state = {}
    for mkey, mcfg in MATCHES.items():
        match_state[mkey] = {
            "seen_kickoff": False,
            "seen_halftime": False,
            "seen_finished": False,
            "home_score": 0,
            "away_score": 0,
            "home_corners": 0,
            "away_corners": 0,
            "leg_status": "OPEN",
            "event_id": None
        }

    finished_count = 0
    total_matches = len(MATCHES)

    while finished_count < total_matches:
        league_cache = {}

        for mkey, mcfg in MATCHES.items():
            st = match_state[mkey]
            if st["seen_finished"]:
                continue

            l_code = mcfg["espn_league"]
            if l_code not in league_cache:
                league_cache[l_code] = fetch_espn_data(l_code)
            events = league_cache[l_code]

            # Find matching event
            ev_found = None
            target_eid = mcfg.get("event_id")
            for ev in events:
                if target_eid and str(ev.get("id")) == str(target_eid):
                    ev_found = ev
                    break
                name_l = ev.get("name", "").lower()
                if mcfg["home_kw"] in name_l and mcfg["away_kw"] in name_l:
                    ev_found = ev
                    break

            if not ev_found:
                continue

            st["event_id"] = str(ev_found.get("id"))
            status_obj = ev_found.get("status", {})
            status_type = status_obj.get("type", {})
            state_desc = status_type.get("description", "Scheduled")
            state_id = status_type.get("state", "pre")
            clock_display = status_obj.get("displayClock", "")

            competitors = ev_found.get("competitions", [{}])[0].get("competitors", [])
            h_comp = next((c for c in competitors if c.get("homeAway") == "home"), {})
            a_comp = next((c for c in competitors if c.get("homeAway") == "away"), {})

            h_goals = int(h_comp.get("score", 0) or 0)
            a_goals = int(a_comp.get("score", 0) or 0)

            # Check Corners if needed
            if mcfg["type"] == "CORNER_1" and st["event_id"] and state_id in ["in", "post"]:
                summary = fetch_event_summary(l_code, st["event_id"])
                box = summary.get("boxscore", {})
                for team_entry in box.get("teams", []):
                    t_info = team_entry.get("team", {})
                    t_name = (t_info.get("name", "") + " " + t_info.get("displayName", "")).lower()
                    stats = {s.get("name"): s.get("displayValue") for s in team_entry.get("statistics", [])}
                    c_val = int(stats.get("wonCorners", stats.get("cornerKicks", 0)) or 0)
                    is_home = (t_info.get("uniform", {}).get("type") == "home") or (mcfg["home_kw"] in t_name)
                    is_away = (t_info.get("uniform", {}).get("type") == "away") or (mcfg["away_kw"] in t_name)
                    if is_home:
                        st["home_corners"] = c_val
                    elif is_away:
                        st["away_corners"] = c_val

            # 1. Calcio d'inizio
            if state_id == "in" and not st["seen_kickoff"]:
                st["seen_kickoff"] = True
                send_tg(
                    f"▶️ <b>CALCIO D'INIZIO:</b> {mcfg['name']} ({mcfg['league']})!\n"
                    f"🎯 Nostro Pick: <b>{mcfg['market']} @ {mcfg['odds']}</b>"
                )
                print(f"[KICKOFF] {mcfg['name']}", flush=True)

            # 2. Gol update
            if (h_goals > st["home_score"] or a_goals > st["away_score"]) and state_id == "in":
                st["home_score"] = h_goals
                st["away_score"] = a_goals
                btts_note = ""
                if mcfg["type"] == "BTTS":
                    btts_ok = (h_goals >= 1 and a_goals >= 1)
                    btts_note = f"\n🔥 Status Gol: <b>{'PRESO! Entrambe hanno segnato! ✅' if btts_ok else 'Manca ancora 1 gol'}</b>"

                send_tg(
                    f"⚽ <b>GOL LIVE ({clock_display})!</b> {mcfg['name']}\n"
                    f"Risultato: <b>{h_goals} - {a_goals}</b>{btts_note}"
                )
                print(f"[GOAL] {mcfg['name']} -> {h_goals}-{a_goals}", flush=True)

            # 3. Intervallo
            if "Halftime" in state_desc and not st["seen_halftime"]:
                st["seen_halftime"] = True
                corner_str = ""
                if mcfg["type"] == "CORNER_1":
                    corner_str = f"\n🚩 Corner: <b>{st['home_corners']} - {st['away_corners']}</b>"

                send_tg(
                    f"⏸️ <b>INTERVALLO (45'):</b> {mcfg['name']}\n"
                    f"Parziale: <b>{h_goals} - {a_goals}</b>{corner_str}"
                )
                print(f"[HT] {mcfg['name']} -> {h_goals}-{a_goals}", flush=True)

            # 4. Fine partita
            if state_id == "post" and not st["seen_finished"]:
                st["seen_finished"] = True
                finished_count += 1

                # Determina esito selezione
                leg_won = False
                res_detail = ""
                if mcfg["type"] == "DC_1X":
                    leg_won = (h_goals >= a_goals)
                    res_detail = f"Finale {h_goals}-{a_goals} (1X: {'✅' if leg_won else '❌'})"
                elif mcfg["type"] == "DC_X2":
                    leg_won = (a_goals >= h_goals)
                    res_detail = f"Finale {h_goals}-{a_goals} (X2: {'✅' if leg_won else '❌'})"
                elif mcfg["type"] == "BTTS":
                    leg_won = (h_goals >= 1 and a_goals >= 1)
                    res_detail = f"Finale {h_goals}-{a_goals} (Entrambe a segno: {'✅' if leg_won else '❌'})"
                elif mcfg["type"] == "CORNER_1":
                    leg_won = (st["home_corners"] > st["away_corners"])
                    res_detail = f"Corner {st['home_corners']}-{st['away_corners']} ({'✅' if leg_won else '❌'})"

                st["leg_status"] = "WON" if leg_won else "LOST"
                update_db_leg(mcfg["name"].split()[0], st["leg_status"])

                send_tg(
                    f"🏁 <b>RISULTATO FINALE:</b> {mcfg['name']}\n"
                    f"Esito: <b>{'VINTA ✅' if leg_won else 'PERSA ❌'}</b> ({res_detail})\n"
                    f"🎯 Nostro Pick: {mcfg['market']} @ {mcfg['odds']}"
                )
                print(f"[FT] {mcfg['name']} -> Leg: {st['leg_status']} ({res_detail})", flush=True)

        time.sleep(35)

    # Verifica finale intero ticket
    all_won = all(st["leg_status"] == "WON" for st in match_state.values())
    pnl = (67.95 - 10.00) if all_won else -10.00
    update_db_ticket("WON" if all_won else "LOST", pnl)

    final_msg = (
        f"{'🎉🎉🎉 <b>SCHEDINA SABATO VINTA! INCASSO: 67.95 €!</b> 🎉🎉🎉' if all_won else '❌ Schedina Conclusa.'}\n"
        f"Utile netto: <b>{'+57.95 €' if all_won else '-10.00 €'}</b>\n"
        f"Ottimo money management controllato a 10 €!"
    )
    send_tg(final_msg)
    print(f"Live Sentinel Sabato Concluso. Status: {'WON' if all_won else 'LOST'}", flush=True)

if __name__ == "__main__":
    main()
