#!/usr/bin/env python3
"""
scripts/live_ticket_watcher_daemon.py — Daemon di Monitoraggio Live in Tempo Reale per Ticket #89.
Utilizza il feed LiveScore sub-secondo per aggiornamenti istantanei sui gol in-play
e invia notifiche PUSH immediate su Telegram ad ogni variazione!
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"
STATE_FILE = ROOT / "data" / "ticket_89_live_state.json"

def send_telegram(msg: str) -> bool:
    if not TELEGRAM_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[Watcher] Telegram Error: {e}", flush=True)
        return False

# Definizioni delle 5 selezioni di Ticket #89 con pattern di matching
MATCHES = [
    {
        "id": "dynamo_epitsentr",
        "name": "Dynamo Kyiv vs Epitsentr",
        "market": "1X + Under 3.5",
        "quota": 1.78,
        "kickoff": "14:30",
        "country": "Ucraina",
        "keywords_home": ["dynamo", "kyiv", "kiev"],
        "keywords_away": ["epicentr", "epitsentr", "kamianets"]
    },
    {
        "id": "panionios_apollon",
        "name": "Panionios vs Apollon",
        "market": "Under 2.5",
        "quota": 1.62,
        "kickoff": "15:00",
        "country": "Grecia",
        "keywords_home": ["panionios"],
        "keywords_away": ["apollon", "kalamaria", "pontou"]
    },
    {
        "id": "panthrakikos_paok",
        "name": "Panthrakikos vs PAOK B",
        "market": "Doppia Chance 1X",
        "quota": 1.38,
        "kickoff": "16:00",
        "country": "Grecia",
        "keywords_home": ["panthrakikos"],
        "keywords_away": ["paok"]
    },
    {
        "id": "ucluj_otelul",
        "name": "U. Cluj vs Otelul Galati",
        "market": "Over 2.5",
        "quota": 1.76,
        "kickoff": "17:00",
        "country": "Romania",
        "keywords_home": ["cluj", "universitatea cluj"],
        "keywords_away": ["otelul", "galati"]
    },
    {
        "id": "shakhtar_chernomorets",
        "name": "Shakhtar vs Chernomorets",
        "market": "1 + MultiGol 2-4",
        "quota": 1.54,
        "kickoff": "17:00",
        "country": "Ucraina",
        "keywords_home": ["shakhtar"],
        "keywords_away": ["chernomorets", "chornomorets"]
    }
]

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def eval_status(market: str, h_goals: int, a_goals: int, is_finished: bool = False) -> str:
    total = h_goals + a_goals
    m = market.lower()
    
    if "under 2.5" in m:
        if total > 2:
            return "❌ PERSA"
        elif is_finished:
            return "✅ VINTA"
        else:
            return f"🛡️ Regge bene ({total}/2 gol, serve non prenderne un altro)"
            
    if "1x + under 3.5" in m:
        if total > 3:
            return "❌ PERSA (Over 3.5 superato)"
        elif is_finished:
            if h_goals >= a_goals:
                return "✅ VINTA (1X + Under 3.5 centrata!)"
            else:
                return "❌ PERSA (Vittoria ospite)"
        else:
            if h_goals >= a_goals:
                return f"🟢 FAVOREVOLE ({h_goals}-{a_goals}, mancano {3-total} gol per il limite)"
            else:
                return f"⚠️ SOTTO NEL PUNTEGGIO ({h_goals}-{a_goals})"
            
    if "1x" in m:
        if is_finished:
            return "✅ VINTA" if h_goals >= a_goals else "❌ PERSA"
        else:
            return "🛡️ In corso (1X coperto)" if h_goals >= a_goals else "⚠️ Sotto nel punteggio"
            
    if "over 2.5" in m:
        if total >= 3:
            return "✅ VINTA"
        elif is_finished:
            return "❌ PERSA"
        else:
            return f"⏳ In corso ({total}/3 gol)"
            
    if "1 + multigol 2-4" in m:
        if is_finished:
            if h_goals > a_goals and 2 <= total <= 4:
                return "✅ VINTA"
            else:
                return "❌ PERSA"
        else:
            return f"⏳ In corso ({h_goals}-{a_goals})"
            
    return "⏳ In corso"

def fetch_livescore_feed():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    stages = []
    # 1. Live in-play feed
    try:
        r = requests.get("https://prod-public-api.livescore.com/v1/api/app/live/soccer/0", headers=headers, timeout=6)
        if r.status_code == 200:
            stages.extend(r.json().get("Stages", []))
    except Exception:
        pass
    # 2. Date feed (for completed FT or upcoming matches)
    try:
        today_str = datetime.now().strftime("%Y%m%d")
        r_date = requests.get(f"https://prod-public-api.livescore.com/v1/api/app/date/soccer/{today_str}/0", headers=headers, timeout=6)
        if r_date.status_code == 200:
            stages.extend(r_date.json().get("Stages", []))
    except Exception:
        pass
    return {"Stages": stages}


def find_match_in_feed(feed, m_def):
    if not feed or "Stages" not in feed:
        return None
    for stage in feed.get("Stages", []):
        for ev in stage.get("Events", []):
            t1 = ev.get("T1", [{}])[0].get("Nm", "").lower()
            t2 = ev.get("T2", [{}])[0].get("Nm", "").lower()
            match_h = any(k in t1 for k in m_def["keywords_home"])
            match_a = any(k in t2 for k in m_def["keywords_away"])
            if match_h and match_a:
                h_goals = int(ev.get("Tr1", 0) or 0)
                a_goals = int(ev.get("Tr2", 0) or 0)
                eps = ev.get("Eps", "")
                is_ft = eps in ["FT", "AET", "AP"]
                is_ht = eps == "HT" or "45" in eps
                return {
                    "home_score": h_goals,
                    "away_score": a_goals,
                    "time_str": eps,
                    "is_finished": is_ft,
                    "is_ht": is_ht
                }
    return None

def run_loop():
    print("[Live Notifier] 🚀 Watcher LiveScore Daemon ATTIVO su Telegram!", flush=True)
    state = load_state()

    while True:
        try:
            feed = fetch_livescore_feed()
            if feed:
                for m in MATCHES:
                    mid = m["id"]
                    live = find_match_in_feed(feed, m)
                    if not live:
                        continue
                    
                    h = live["home_score"]
                    a = live["away_score"]
                    score_str = f"{h}-{a}"
                    time_str = live["time_str"]
                    is_ft = live["is_finished"]
                    
                    prev = state.get(mid, {
                        "announced_score": "",
                        "announced_ft": False,
                        "announced_ht": False
                    })
                    
                    # 1. NOTIFICA CAMBIO PUNTEGGIO
                    if score_str != prev.get("announced_score"):
                        verdict = eval_status(m["market"], h, a, is_ft)
                        now_str = datetime.now().strftime("%H:%M:%S")
                        msg = (
                            f"🔔 <b>AGGIORNAMENTO LIVE ({now_str})</b>\n\n"
                            f"⚽ <b>{m['name']}</b> ({m['country']})\n"
                            f"⏱️ Minuto: <b>{time_str}</b>\n"
                            f"🔢 Punteggio: <b>{score_str}</b>\n"
                            f"🎯 Nostro Mercato: <b>{m['market']} @ {m['quota']}</b>\n"
                            f"📊 Stato Selezione: <b>{verdict}</b>"
                        )
                        send_telegram(msg)
                        state[mid] = {
                            "announced_score": score_str,
                            "announced_ft": is_ft,
                            "announced_ht": prev.get("announced_ht", False),
                            "h": h,
                            "a": a
                        }
                        save_state(state)
                        print(f"[{now_str}] Alert inviato per {m['name']}: {score_str}", flush=True)

                    # 2. NOTIFICA FINE PARTITA
                    if is_ft and not prev.get("announced_ft"):
                        verdict = eval_status(m["market"], h, a, True)
                        now_str = datetime.now().strftime("%H:%M:%S")
                        msg = (
                            f"🏁 <b>FINALE MATCH! ({now_str})</b>\n\n"
                            f"🏆 <b>{m['name']}</b>\n"
                            f"🔢 Risultato Ufficiale: <b>{score_str}</b>\n"
                            f"🎯 Mercato: <b>{m['market']}</b>\n"
                            f"📌 Esito Leg: <b>{verdict}</b>"
                        )
                        send_telegram(msg)
                        if mid in state:
                            state[mid]["announced_ft"] = True
                            save_state(state)
                        print(f"[{now_str}] Finale inviato per {m['name']}: {score_str}", flush=True)

            time.sleep(30)  # Polling ogni 30 secondi
            
        except Exception as err:
            print(f"[Daemon Error]: {err}", flush=True)
            time.sleep(30)

if __name__ == "__main__":
    run_loop()
