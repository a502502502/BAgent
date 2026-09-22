#!/usr/bin/env python3
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

env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
HEADERS_ESPN = {"User-Agent": "ESPN/6.0.0 (iPhone; iOS 17.0; Scale/3.00)", "Accept": "*/*"}

MATCHES = {
    "atalanta": {"name": "Atalanta vs Cagliari", "league": "Serie A", "espn_league": "ita.1", "event_id": "401874979"},
    "parisfc": {"name": "Paris FC vs Lyon", "league": "Ligue 1", "espn_league": "fra.1", "event_id": "401876460"},
    "arsenal": {"name": "Sunderland vs Arsenal", "league": "Premier League", "espn_league": "eng.1", "event_id": "401878779"},
    "real": {"name": "Real Madrid vs Rayo Vallecano", "league": "La Liga", "espn_league": "esp.1", "event_id": "401882880"}
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
    if not DB_PATH.exists(): return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE bet_leg_ledger SET result_status = ? WHERE ticket_id = ? AND match_name LIKE ?", (status, ticket_id, f"%{match_sub}%"))
        conn.commit()
        conn.close()
        print(f"[DB] {ticket_id} | {match_sub} -> {status}", flush=True)
    except Exception as e:
        print("DB err:", e, flush=True)

def update_db_ticket(ticket_id: str, status: str, pnl: float):
    if not DB_PATH.exists(): return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE ticket_ledger SET status = ?, profit_loss_eur = ? WHERE ticket_id = ?", (status, pnl, ticket_id))
        conn.commit()
        conn.close()
        print(f"[DB TICKET] {ticket_id} -> {status} ({pnl:.2f} EUR)", flush=True)
    except Exception as e:
        print("DB err:", e, flush=True)

def fetch_summary(espn_league: str, event_id: str) -> dict:
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_league}/summary?event={event_id}"
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=10)
        if r.status_code == 200: return r.json()
    except Exception: pass
    return {}

def main():
    print(f"=== [BAGENT] Live Sentinel Notturno Avviato ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===", flush=True)
    send_tg("🌙 <b>SESSIONE SERALE NETWIN CONFERMATA & ATTIVA!</b>\nTotale Giocato: 30.00 € | Incasso Potenziale: <b>94.62 €</b>\n\n🎟️ <b>Doppia (20 €):</b> Arsenal 1T 1-3 @ 1.43 + Real MG Combo @ 1.65\n🎟️ <b>Quartina (10 €):</b> Atalanta 1X+OV @ 1.51 + Paris FC Gol @ 1.51 + Arsenal X2+OV @ 1.53 + Real 1+OV @ 1.32")
    
    match_state = {k: {"seen_kickoff": False, "seen_ht": False, "seen_ft": False, "h_score": 0, "a_score": 0, "ht_goals": 0} for k in MATCHES}
    finished_count = 0

    while finished_count < len(MATCHES):
        for mkey, mcfg in MATCHES.items():
            st = match_state[mkey]
            if st["seen_ft"]: continue
            data = fetch_summary(mcfg["espn_league"], mcfg["event_id"])
            if not data: continue

            comp = data.get("header", {}).get("competitions", [{}])[0]
            status_obj = comp.get("status", {})
            state_desc = status_obj.get("type", {}).get("description", "")
            state_id = status_obj.get("type", {}).get("state", "pre")
            clock = status_obj.get("displayClock", "")

            comps = comp.get("competitors", [])
            h_comp = next((c for c in comps if c.get("homeAway") == "home"), {})
            a_comp = next((c for c in comps if c.get("homeAway") == "away"), {})
            h_name = h_comp.get("team", {}).get("shortDisplayName", "Home")
            a_name = a_comp.get("team", {}).get("shortDisplayName", "Away")
            h_goals = int(h_comp.get("score", 0) or 0)
            a_goals = int(a_comp.get("score", 0) or 0)

            if state_id == "in" and not st["seen_kickoff"]:
                st["seen_kickoff"] = True
                send_tg(f"▶️ <b>CALCIO D'INIZIO:</b> {mcfg['name']} ({mcfg['league']})!")
                print(f"[KICKOFF] {mcfg['name']}", flush=True)

            if state_id == "in" and (h_goals != st["h_score"] or a_goals != st["a_score"]):
                st["h_score"] = h_goals
                st["a_score"] = a_goals
                extra = ""
                if mkey == "parisfc":
                    extra = f" (Status Gol: {'PRESO! ✅' if (h_goals >= 1 and a_goals >= 1) else 'Manca 1 gol'})"
                send_tg(f"⚽ <b>GOL ({clock})!</b> {mcfg['name']}\n{h_name} {h_goals} - {a_goals} {a_name}{extra}")
                print(f"[GOAL] {mcfg['name']} -> {h_goals}-{a_goals}", flush=True)

            if "Halftime" in state_desc and not st["seen_ht"]:
                st["seen_ht"] = True
                st["ht_goals"] = h_goals + a_goals
                print(f"[HT] {mcfg['name']} -> {h_goals}-{a_goals}", flush=True)
                if mkey == "arsenal":
                    mg_1t_ok = (1 <= st["ht_goals"] <= 3)
                    update_db_leg("CONFIRMED_NIGHT_20EUR_DOPPIA", "Arsenal", "WON" if mg_1t_ok else "LOST")
                    send_tg(f"⏸️ <b>INTERVALLO:</b> {mcfg['name']} {h_goals}-{a_goals}\n🎯 MultiGol 1-3 1°T: <b>{'VINTA! ✅' if mg_1t_ok else 'PERSA ❌'}</b>")
                else:
                    send_tg(f"⏸️ <b>INTERVALLO:</b> {mcfg['name']} {h_goals}-{a_goals}")

            if state_id == "post" and not st["seen_ft"]:
                st["seen_ft"] = True
                finished_count += 1
                tot_goals = h_goals + a_goals

                if mkey == "atalanta":
                    won = (h_goals >= a_goals and tot_goals >= 2)
                    update_db_leg("CONFIRMED_NIGHT_10EUR_QUARTINA", "Atalanta", "WON" if won else "LOST")
                    send_tg(f"🏁 <b>FINALE:</b> {mcfg['name']} {h_goals}-{a_goals}\n🎯 1X + Over 1.5: <b>{'VINTA ✅' if won else 'PERSA ❌'}</b>")

                elif mkey == "parisfc":
                    won = (h_goals >= 1 and a_goals >= 1)
                    update_db_leg("CONFIRMED_NIGHT_10EUR_QUARTINA", "Paris FC", "WON" if won else "LOST")
                    send_tg(f"🏁 <b>FINALE:</b> {mcfg['name']} {h_goals}-{a_goals}\n🎯 Gol: <b>{'VINTA ✅' if won else 'PERSA ❌'}</b>")

                elif mkey == "arsenal":
                    won = (a_goals >= h_goals and tot_goals >= 2)
                    update_db_leg("CONFIRMED_NIGHT_10EUR_QUARTINA", "Arsenal", "WON" if won else "LOST")
                    send_tg(f"🏁 <b>FINALE:</b> {mcfg['name']} {h_goals}-{a_goals}\n🎯 X2 + Over 1.5: <b>{'VINTA ✅' if won else 'PERSA ❌'}</b>")

                elif mkey == "real":
                    t1_won = (2 <= h_goals <= 4 and a_goals <= 1)
                    update_db_leg("CONFIRMED_NIGHT_20EUR_DOPPIA", "Real Madrid", "WON" if t1_won else "LOST")
                    t2_won = (h_goals > a_goals and tot_goals >= 3)
                    update_db_leg("CONFIRMED_NIGHT_10EUR_QUARTINA", "Real Madrid", "WON" if t2_won else "LOST")
                    send_tg(f"🏁 <b>FINALE:</b> {mcfg['name']} {h_goals}-{a_goals}\n🎯 Doppia Real: <b>{'VINTA ✅' if t1_won else 'PERSA ❌'}</b>\n🎯 Quartina Real: <b>{'VINTA ✅' if t2_won else 'PERSA ❌'}</b>")

                print(f"[FT] {mcfg['name']} -> {h_goals}-{a_goals}", flush=True)

        time.sleep(30)

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT result_status FROM bet_leg_ledger WHERE ticket_id = 'CONFIRMED_NIGHT_20EUR_DOPPIA'")
        d_won = all(s == "WON" for s in [r[0] for r in c.fetchall()])
        update_db_ticket("CONFIRMED_NIGHT_20EUR_DOPPIA", "WON" if d_won else "LOST", 27.19 if d_won else -20.00)

        c.execute("SELECT result_status FROM bet_leg_ledger WHERE ticket_id = 'CONFIRMED_NIGHT_10EUR_QUARTINA'")
        q_won = all(s == "WON" for s in [r[0] for r in c.fetchall()])
        update_db_ticket("CONFIRMED_NIGHT_10EUR_QUARTINA", "WON" if q_won else "LOST", 37.43 if q_won else -10.00)
        conn.close()

        net = (27.19 if d_won else -20.0) + (37.43 if q_won else -10.0)
        send_tg(f"🏁 <b>SESSIONE NOTTURNA CONCLUSA!</b>\nDoppia: <b>{'VINTA (+27.19 €) ✅' if d_won else 'PERSA ❌'}</b>\nQuartina: <b>{'VINTA (+37.43 €) ✅' if q_won else 'PERSA ❌'}</b>\nBilancio Serale: <b>{net:+.2f} €</b>")
    except Exception as e:
        print("Settle err:", e)

if __name__ == "__main__":
    main()