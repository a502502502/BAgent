#!/usr/bin/env python3
"""
BAgent Night Live Daemon
Monitora in tempo reale le partite del Ticket #14 (Sestina Overseas) e invia notifiche Telegram per:
1. Inizio partita (Kickoff / Fischio d'inizio)
2. Gol in tempo reale con marcatore / minuto
3. Fine partita (Full-Time / Risultato finale ed esito del pronostico)
4. Avanzamento complessivo del Ticket #14

Uso: python3 scripts/night_live_daemon.py
"""

import time
import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Carica .env
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for encoding in ("utf-8", "utf-16", "utf-8-sig", "latin-1"):
        try:
            content = env_path.read_text(encoding=encoding)
            for line in content.splitlines():
                line = line.replace("\x00", "").strip()
                if "=" in line and not line.startswith("#") and line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip()
                    if k and v:
                        os.environ.setdefault(k, v)
            break
        except Exception:
            continue

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_HOST = "v3.football.api-sports.io"

AF_HEADERS = {
    "x-rapidapi-host": API_FOOTBALL_HOST,
    "x-rapidapi-key": API_FOOTBALL_KEY,
}

# ─── Configurazione Match Ticket #14 ──────────────────────────────────────────
MATCHES = [
    {
        "id": "jaguares_boyaca",
        "home": "Jaguares de Cordoba",
        "away": "Boyaca Chico",
        "home_kw": ["jaguares", "cordoba"],
        "away_kw": ["boyaca", "chico"],
        "flag": "🇨🇴",
        "country": "Colombia",
        "league": "Primera A",
        "kickoff": "23:05",
        "pick_desc": "1X2: 1",
        "odds": "@1.20",
        "evaluator": lambda h, a: (h > a, f"Vittoria {h}-{a}"),
    },
    {
        "id": "the_strongest_vinto",
        "home": "The Strongest",
        "away": "Universitario de Vinto",
        "home_kw": ["strongest"],
        "away_kw": ["vinto", "universitario"],
        "flag": "🇧🇴",
        "country": "Bolivia",
        "league": "Division Profesional",
        "kickoff": "00:30",
        "pick_desc": "1 + Over 1.5 Gol",
        "odds": "@1.40",
        "evaluator": lambda h, a: (h > a and (h + a) >= 2, f"1 + Over 1.5 ({h}-{a})"),
    },
    {
        "id": "cashmere_dunedin",
        "home": "Cashmere Technical",
        "away": "Dunedin City Royals",
        "home_kw": ["cashmere"],
        "away_kw": ["dunedin"],
        "flag": "🇳🇿",
        "country": "Nuova Zelanda",
        "league": "Southern League",
        "kickoff": "02:00",
        "pick_desc": "Over 3.5 Gol",
        "odds": "@1.25",
        "evaluator": lambda h, a: ((h + a) >= 4, f"Over 3.5 ({h + a} Gol totali)"),
    },
    {
        "id": "western_suburbs_karori",
        "home": "Western Suburbs FC",
        "away": "Waterside Karori",
        "home_kw": ["western suburbs"],
        "away_kw": ["karori", "waterside"],
        "flag": "🇳🇿",
        "country": "Nuova Zelanda",
        "league": "Central League",
        "kickoff": "02:30",
        "pick_desc": "1 + Over 1.5 Gol",
        "odds": "@1.27",
        "evaluator": lambda h, a: (h > a and (h + a) >= 2, f"1 + Over 1.5 ({h}-{a})"),
    },
    {
        "id": "tigres_atlante",
        "home": "Tigres UANL",
        "away": "Atlante FC",
        "home_kw": ["tigres", "uanl"],
        "away_kw": ["atlante"],
        "flag": "🇲🇽",
        "country": "Messico",
        "league": "Amichevole / Coppe",
        "kickoff": "03:00",
        "pick_desc": "1X2: 1",
        "odds": "@1.51",
        "evaluator": lambda h, a: (h > a, f"Vittoria {h}-{a}"),
    },
    {
        "id": "upper_hutt_western",
        "home": "Upper Hutt City FC",
        "away": "FC Western",
        "home_kw": ["upper hutt"],
        "away_kw": ["fc western", "western"],
        "flag": "🇳🇿",
        "country": "Nuova Zelanda",
        "league": "Central League",
        "kickoff": "03:00",
        "pick_desc": "1 + Over 2.5 Gol",
        "odds": "@1.25",
        "evaluator": lambda h, a: (h > a and (h + a) >= 3, f"1 + Over 2.5 ({h}-{a})"),
    },
]

# ─── Telegram Helper ──────────────────────────────────────────────────────────
def notify_telegram(msg: str):
    if not TELEGRAM_TOKEN:
        print("Telegram token non configurato.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        if r.status_code == 200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram notifica inviata con successo!")
        else:
            print(f"Telegram warning: status {r.status_code} - {r.text[:80]}")
    except Exception as e:
        print("Telegram send error:", e)

# ─── Live Match Polling ───────────────────────────────────────────────────────
def get_live_fixtures() -> list[dict]:
    """Recupera partite live da API-Football o Sofascore."""
    # 1. Prova API-Football
    if API_FOOTBALL_KEY:
        try:
            r = requests.get(f"https://{API_FOOTBALL_HOST}/fixtures?live=all", headers=AF_HEADERS, timeout=12)
            if r.status_code == 200:
                return r.json().get("response", [])
        except Exception as e:
            print("API-Football live error:", e)

    # 2. Fallback Sofascore API
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get("https://api.sofascore.com/api/v1/sport/football/events/live", headers=headers, timeout=12)
        if r.status_code == 200:
            data = r.json()
            events = data.get("events", [])
            normalized = []
            for ev in events:
                h_name = ev.get("homeTeam", {}).get("name", "")
                a_name = ev.get("awayTeam", {}).get("name", "")
                h_score = ev.get("homeScore", {}).get("current", 0) or 0
                a_score = ev.get("awayScore", {}).get("current", 0) or 0
                status_desc = ev.get("status", {}).get("description", "")
                status_type = ev.get("status", {}).get("type", "")
                elapsed = ev.get("time", {}).get("played", 0) or 0
                normalized.append({
                    "teams": {"home": {"name": h_name}, "away": {"name": a_name}},
                    "goals": {"home": h_score, "away": a_score},
                    "fixture": {"status": {"long": status_desc, "short": status_type, "elapsed": elapsed}}
                })
            return normalized
    except Exception as e:
        print("Sofascore live error:", e)

    return []

def match_finder(m_cfg: dict, fixtures: list[dict]) -> dict | None:
    """Trova il fixture corrispondente alle keyword del match."""
    for f in fixtures:
        h = f.get("teams", {}).get("home", {}).get("name", "").lower()
        a = f.get("teams", {}).get("away", {}).get("name", "").lower()
        
        home_match = any(kw in h for kw in m_cfg["home_kw"])
        away_match = any(kw in a for kw in m_cfg["away_kw"])
        if home_match and away_match:
            return f
    return None

# ─── Ticket Progress Card ─────────────────────────────────────────────────────
def get_ticket_card(match_states: dict) -> str:
    """Genera il riepilogo grafico della Sestina con lo stato di ogni partita."""
    lines = []
    won_count = 0
    in_play_count = 0
    waiting_count = 0
    lost_count = 0

    for m in MATCHES:
        mid = m["id"]
        st = match_states.get(mid, {"phase": "SCHEDULED", "score": (0, 0), "minute": 0, "final_won": None})
        phase = st["phase"]
        h_s, a_s = st["score"]
        
        if phase == "FINISHED":
            is_won, desc = m["evaluator"](h_s, a_s)
            if is_won:
                won_count += 1
                icon = "✅ VINTO"
            else:
                lost_count += 1
                icon = "❌ PERSO"
            line = f"• {m['flag']} <b>{m['home']} {h_s}-{a_s} {m['away']}</b> (FT)\n   └ 🎯 {m['pick_desc']} {m['odds']} ➔ <b>{icon}</b>"
        elif phase in ("IN_PLAY", "HALFTIME"):
            in_play_count += 1
            min_str = f"{st['minute']}'" if phase == "IN_PLAY" else "HT"
            line = f"• {m['flag']} <b>{m['home']} {h_s}-{a_s} {m['away']}</b> (LIVE {min_str})\n   └ 🎯 {m['pick_desc']} {m['odds']} ➔ 🟢 <b>IN CORSO</b>"
        else:
            waiting_count += 1
            line = f"• {m['flag']} <b>{m['home']} vs {m['away']}</b> ({m['kickoff']})\n   └ 🎯 {m['pick_desc']} {m['odds']} ➔ ⏳ <b>IN ARRIVO</b>"
        lines.append(line)

    card = (
        "📋 <b>STATO TICKET #14 (Vincita: 106.71 €):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n\n".join(lines)
        + "\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Avanzamento</b>: <b>{won_count}</b> Prese · <b>{in_play_count}</b> In Corso · <b>{waiting_count}</b> In Arrivo\n"
        f"💰 <b>Vincita Potenziale</b>: <b>106.71 €</b> (Stake 20.00 €)"
    )
    return card

# ─── Motore di Monitoraggio Live ──────────────────────────────────────────────
def main():
    print(f"=== BAgent 24/7 Live Daemon Avviato ({datetime.now().strftime('%H:%M:%S')}) ===")
    
    # Invia notifica di avvio
    init_states = {m["id"]: {"phase": "SCHEDULED", "score": (0, 0), "minute": 0, "final_won": None} for m in MATCHES}
    startup_text = (
        "🟢 <b>BAgent Live Monitor ATTIVO 24/7 su Raspberry Pi!</b>\n\n"
        + get_ticket_card(init_states)
        + "\n\n🔔 <i>Notifiche automatiche attive per: Fischio d'inizio, Gol live e Risultato finale con esito!</i>"
    )
    notify_telegram(startup_text)

    # Memoria stati partite
    match_states = {
        m["id"]: {
            "phase": "SCHEDULED",
            "score": (0, 0),
            "minute": 0,
            "notified_start": False,
            "notified_end": False,
        }
        for m in MATCHES
    }

    while True:
        try:
            fixtures = get_live_fixtures()

            for m in MATCHES:
                mid = m["id"]
                st = match_states[mid]
                ev = match_finder(m, fixtures)

                if ev:
                    fixture_info = ev.get("fixture", {})
                    status_long = fixture_info.get("status", {}).get("long", "")
                    status_short = fixture_info.get("status", {}).get("short", "")
                    elapsed = fixture_info.get("status", {}).get("elapsed", 0) or 0
                    goals = ev.get("goals", {})
                    h_score = goals.get("home", 0) or 0
                    a_score = goals.get("away", 0) or 0
                    curr_score = (h_score, a_score)

                    status_lower = (status_long + " " + status_short).lower()

                    # 1️⃣ RILEVAZIONE INIZIO PARTITA (KICKOFF)
                    is_in_play = any(k in status_lower for k in ("1h", "2h", "first half", "second half", "in play", "live", "halftime", "ht")) or elapsed > 0
                    is_finished = any(k in status_lower for k in ("ft", "finished", "match finished", "ended", "aet", "pen"))

                    if is_in_play and not st["notified_start"] and not is_finished:
                        st["phase"] = "IN_PLAY"
                        st["notified_start"] = True
                        st["score"] = curr_score
                        st["minute"] = elapsed

                        kickoff_msg = (
                            f"🟢 <b>INIZIO PARTITA! FISCHIO D'INIZIO! ⏱️</b>\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b> ({m['country']} {m['league']})\n"
                            f"🎯 Nostro Pick: <b>{m['pick_desc']} {m['odds']}</b>\n\n"
                            f"⏱ <i>Il match è iniziato! Punteggio attuale: {h_score}-{a_score} ({elapsed}')</i>\n\n"
                            + get_ticket_card(match_states)
                        )
                        notify_telegram(kickoff_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] KICKOFF NOTIFIED: {m['home']} vs {m['away']}")

                    # 2️⃣ RILEVAZIONE GOL IN TEMPO REALE
                    if is_in_play and not is_finished:
                        if curr_score != st["score"]:
                            old_h, old_a = st["score"]
                            st["score"] = curr_score
                            st["minute"] = elapsed
                            scorer_team = m["home"] if h_score > old_h else m["away"]

                            goal_msg = (
                                f"⚽ <b>GOL! {m['home']} {h_score} - {a_score} {m['away']}</b> ({elapsed}')\n\n"
                                f"🔥 Rete per: <b>{scorer_team}</b>\n"
                                f"🎯 Nostro Pick: <b>{m['pick_desc']} {m['odds']}</b>\n\n"
                                + get_ticket_card(match_states)
                            )
                            notify_telegram(goal_msg)
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] GOAL NOTIFIED: {m['home']} {h_score}-{a_score} {m['away']}")

                        st["minute"] = elapsed
                        st["score"] = curr_score

                    # 3️⃣ RILEVAZIONE FINE PARTITA (FULL-TIME / FT)
                    if is_finished and not st["notified_end"]:
                        st["phase"] = "FINISHED"
                        st["notified_end"] = True
                        st["score"] = curr_score
                        
                        is_won, desc = m["evaluator"](h_score, a_score)
                        res_icon = "🏆 <b>✅ PRONOSTICO VINTO AL 100%!</b>" if is_won else "⚠️ <b>❌ PRONOSTICO NON VINCENTE</b>"

                        ft_msg = (
                            f"🏁 <b>FISCHIO FINALE! RISULTATO DEFINITIVO (FT)</b>\n\n"
                            f"{m['flag']} <b>{m['home']} {h_score} - {a_score} {m['away']}</b> (FT)\n"
                            f"🎯 Nostro Pick: <b>{m['pick_desc']} {m['odds']}</b>\n"
                            f"{res_icon} <i>({desc})</i>\n\n"
                            + get_ticket_card(match_states)
                        )
                        notify_telegram(ft_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] FULL-TIME NOTIFIED: {m['home']} {h_score}-{a_score} {m['away']} -> {res_icon}")

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Polling error:", e)

        time.sleep(25)

if __name__ == "__main__":
    main()

