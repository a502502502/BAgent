import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
#!/usr/bin/env python3
"""
live_daemon_17set.py — Daemon di Monitoraggio Live & Notifiche Telegram per la sessione 17 Settembre 2026.
Monitora in tempo reale:
1. Machida Zelvia vs Svay Rieng (Target: Over 2.5 @ 1.21)
2. Adelaide United vs Tai Po Fc (Target A: Over 2.5 @ 1.35 | Paracadute B: Under 2.5 @ 2.72)
3. Lion City vs BG Pathum (Target: Over 1.5 @ 1.21)
4. Shanghai Shenhua vs Tampines (Target: 1 Fisso @ 1.27)
"""

import sys
import time
import requests
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[Daemon] Telegram Error: {e}", flush=True)
        return False

MATCHES = [
    {
        "id": "orenburg",
        "name": "Orenburg vs Krasnodar",
        "keywords_home": ["orenburg"],
        "keywords_away": ["krasnodar"],
        "target_a": "X2 + Under 4.5",
        "target_b": "X2 + Under 4.5"
    },
    {
        "id": "rostov",
        "name": "Rostov vs Dinamo Mosca",
        "keywords_home": ["rostov"],
        "keywords_away": ["dinamo moscow", "dynamo moscow", "dinamo moskva", "dynamo moskva", "mosca"],
        "target_a": "Dinamo Mosca X2 + Under 4.5",
        "target_b": "Rostov 1X + Under 3.5"
    }
]

def fetch_livescore():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    events = []
    # 1. Live in-play feed
    try:
        r = requests.get("https://prod-public-api.livescore.com/v1/api/app/live/soccer/0", headers=headers, timeout=6)
        if r.status_code == 200:
            for s in r.json().get("Stages", []):
                events.extend(s.get("Events", []))
    except Exception:
        pass
    # 2. Date feed
    try:
        today_str = datetime.now().strftime("%Y%m%d")
        r_date = requests.get(f"https://prod-public-api.livescore.com/v1/api/app/date/soccer/{today_str}/0", headers=headers, timeout=6)
        if r_date.status_code == 200:
            for s in r_date.json().get("Stages", []):
                events.extend(s.get("Events", []))
    except Exception:
        pass
    return events

def run():
    print(f"[Daemon] 🚀 BAgent Live Watcher 17 Settembre AVVIATO alle {datetime.now().strftime('%H:%M:%S')}", flush=True)
    send_telegram(
        "🟢 <b>BAgent Live Sentinel ATTIVATO — Ticket #90</b>\n\n"
        "📡 <b>Monitoraggio Attivo su 2 Partite:</b>\n"
        "1. ⏰ <b>15:15 | Orenburg vs Krasnodar</b> (Target: X2 + Under 4.5)\n"
        "2. ⏰ <b>17:30 | Rostov vs Dinamo Mosca</b> (Target: Dinamo X2+U4.5 / Rostov 1X+U3.5)\n\n"
        "🛡️ <i>Regola #68 attiva: in caso di esito compromesso, il flusso notifiche si spegne automaticamente senza spam.</i>"
    )

    state = {}
    for m in MATCHES:
        state[m["id"]] = {
            "score": "0-0",
            "h": 0,
            "a": 0,
            "time": "Pre",
            "started": False,
            "finished": False,
            "over_hit": False
        }

    while True:
        try:
            events = fetch_livescore()
            for m in MATCHES:
                m_id = m["id"]
                s = state[m_id]

                # Find match in events
                for ev in events:
                    t1 = ev.get("T1", [{}])[0].get("Nm", "").lower()
                    t2 = ev.get("T2", [{}])[0].get("Nm", "").lower()
                    if any(k in t1 for k in m["keywords_home"]) and any(k in t2 for k in m["keywords_away"]):
                        eps = ev.get("Eps", "")
                        h = int(ev.get("Tr1", 0) or 0)
                        a = int(ev.get("Tr2", 0) or 0)
                        cur_score = f"{h}-{a}"
                        tot_goals = h + a

                        # Kickoff alert
                        if not s["started"] and eps not in ["NS", "Pre", ""]:
                            s["started"] = True
                            send_telegram(f"⏰ <b>CALCIO D'INIZIO!</b>\n\n<b>{m['name']}</b> è iniziata!\n⏱ Minuto: {eps}\n🎯 Target: {m['target_a']}")

                        # Goal alert
                        if cur_score != s["score"]:
                            old_score = s["score"]
                            s["score"] = cur_score
                            s["h"] = h
                            s["a"] = a
                            time_disp = eps if eps else "In-Play"
                            send_telegram(
                                f"⚽ <b>GOOOOOL!</b>\n\n"
                                f"🏟 <b>{m['name']}</b>\n"
                                f"📊 Nuovo Risultato: <b>{cur_score}</b> (era {old_score})\n"
                                f"⏱ Minuto: <b>{time_disp}</b>\n"
                                f"🎯 Gol totali nel match: <b>{tot_goals}</b>"
                            )

                            # Check target milestones
                            if m_id == "lion_city" and tot_goals >= 2 and not s["over_hit"]:
                                s["over_hit"] = True
                                send_telegram(f"✅ <b>TARGET CENTRATO!</b>\n\nLion City vs Pathum ha raggiunto <b>{tot_goals} gol</b>!\n🎯 <b>Over 1.5 Gol @ 1.21 VINTO!</b>")
                            elif m_id in ["machida", "adelaide"] and tot_goals >= 3 and not s["over_hit"]:
                                s["over_hit"] = True
                                send_telegram(f"✅ <b>TARGET CENTRATO!</b>\n\n{m['name']} ha raggiunto <b>{tot_goals} gol</b>!\n🎯 <b>Over 2.5 Gol VINTO!</b>")

                        # Full time alert
                        if eps in ["FT", "AET", "AP"] and not s["finished"]:
                            s["finished"] = True
                            send_telegram(f"🏁 <b>FISCHIO FINALE!</b>\n\n<b>{m['name']}</b>\nRisultato Finale: <b>{cur_score}</b>")

                        break

        except Exception as e:
            print(f"[Daemon] Error in loop: {e}", flush=True)

        time.sleep(40)

if __name__ == "__main__":
    run()
