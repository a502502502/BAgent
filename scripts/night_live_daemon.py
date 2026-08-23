#!/usr/bin/env python3
"""
BAgent Corner & Foul Live Daemon (Domenica 23 Agosto 2026)
Monitora in tempo reale ESCLUSIVAMENTE i Calci d'Angolo per il Ticket #19 (e i Falli).
Zero spam di gol o notifiche inutili: solo avanzamento corner, alert traguardi e vittoria del target!

Uso: python3 scripts/night_live_daemon.py
"""

from __future__ import annotations
import time
import requests
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

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

# ─── Configurazione Match Ticket #19 (Domenica 23 Agosto 2026 - Corner) ───────
MATCHES = [
    {
        "id": "brighton_villa",
        "home": "Brighton",
        "away": "Aston Villa",
        "home_kw": ["brighton"],
        "away_kw": ["aston villa", "villa"],
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "country": "Inghilterra",
        "league": "Premier League",
        "kickoff": "15:00",
        "pick_desc": "Over 7.5 Corner Totali",
        "odds": "@1.24",
        "target_type": "TOTAL",
        "target_val": 8,
    },
    {
        "id": "mancity_bournemouth",
        "home": "Manchester City",
        "away": "Bournemouth",
        "home_kw": ["manchester city", "man city", "city"],
        "away_kw": ["bournemouth"],
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "country": "Inghilterra",
        "league": "Premier League",
        "kickoff": "15:00",
        "pick_desc": "Over 6.5 Corner Man City (Sq.1)",
        "odds": "@1.70",
        "target_type": "HOME",
        "target_val": 7,
    },
    {
        "id": "atletico_villarreal",
        "home": "Atlético Madrid",
        "away": "Villarreal",
        "home_kw": ["atletico", "atlético"],
        "away_kw": ["villarreal"],
        "flag": "🇪🇸",
        "country": "Spagna",
        "league": "LaLiga",
        "kickoff": "17:00",
        "pick_desc": "Over 7.5 Corner Totali Match",
        "odds": "@1.24",
        "target_type": "TOTAL",
        "target_val": 8,
    },
    {
        "id": "newcastle_liverpool",
        "home": "Newcastle",
        "away": "Liverpool",
        "home_kw": ["newcastle"],
        "away_kw": ["liverpool"],
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "country": "Inghilterra",
        "league": "Premier League",
        "kickoff": "17:30",
        "pick_desc": "Over 9.5 Corner Totali Match",
        "odds": "@1.50",
        "target_type": "TOTAL",
        "target_val": 10,
    },
    {
        "id": "frosinone_juventus",
        "home": "Frosinone",
        "away": "Juventus",
        "home_kw": ["frosinone"],
        "away_kw": ["juventus", "juve"],
        "flag": "🇮🇹",
        "country": "Italia",
        "league": "Serie A",
        "kickoff": "18:30",
        "pick_desc": "Over 4.5 Corner Juventus (Sq.2)",
        "odds": "@1.33",
        "target_type": "AWAY",
        "target_val": 5,
    },
    {
        "id": "elche_barcelona",
        "home": "Elche",
        "away": "Barcelona",
        "home_kw": ["elche"],
        "away_kw": ["barcelona", "barcellona", "barca", "barça"],
        "flag": "🇪🇸",
        "country": "Spagna",
        "league": "LaLiga",
        "kickoff": "21:30",
        "pick_desc": "Over 5.5 Corner Barcellona (Sq.2)",
        "odds": "@1.62",
        "target_type": "AWAY",
        "target_val": 6,
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

# ─── Classificatore di Stato ──────────────────────────────────────────────────
def classify_status(status_short: str, status_long: str, status_type: str = "", elapsed: int = 0) -> str:
    s_short = (status_short or "").strip().upper()
    s_long = (status_long or "").strip().lower()
    s_type = (status_type or "").strip().lower()

    if s_short in ("HT", "BT") or any(k in s_long for k in ("halftime", "half time", "1st half ended", "first half ended", "intervallo")):
        return "HALFTIME"
    if s_short in ("FT", "AET", "PEN") or s_type == "finished":
        return "FINISHED"
    if s_long in ("match finished", "finished", "full time", "after extra time", "after penalties", "final", "ended"):
        return "FINISHED"
    if s_short in ("1H", "2H", "ET", "P", "LIVE", "INT") or s_type == "inprogress" or elapsed > 0:
        return "IN_PLAY"
    if any(k in s_long for k in ("first half", "second half", "1st half", "2nd half", "in play", "live", "extra time")):
        return "IN_PLAY"
    if s_short in ("PST", "CANC", "ABD", "AWD", "WO", "SUSP") or any(k in s_long for k in ("postponed", "cancelled", "abandoned")):
        return "CANCELLED"
    return "SCHEDULED"

# ─── API-Football Live & Statistics ───────────────────────────────────────────
def get_live_fixtures_and_stats() -> list[dict]:
    """Recupera le partite live con le statistiche dei corner da API-Football."""
    if not API_FOOTBALL_KEY:
        return []
    
    headers = {
        "x-rapidapi-host": API_FOOTBALL_HOST,
        "x-rapidapi-key": API_FOOTBALL_KEY,
        "x-apisports-key": API_FOOTBALL_KEY,
    }
    try:
        r = requests.get(f"https://{API_FOOTBALL_HOST}/fixtures?live=all", headers=headers, timeout=12)
        if r.status_code == 200:
            return r.json().get("response", [])
    except Exception as e:
        print("API-Football live error:", e)
    return []

def get_fixture_corners(fixture_id: int) -> tuple[int, int]:
    """Recupera i corner precisi (home, away) per un dato fixture ID."""
    if not API_FOOTBALL_KEY or not fixture_id:
        return 0, 0
    headers = {
        "x-rapidapi-host": API_FOOTBALL_HOST,
        "x-rapidapi-key": API_FOOTBALL_KEY,
        "x-apisports-key": API_FOOTBALL_KEY,
    }
    try:
        r = requests.get(f"https://{API_FOOTBALL_HOST}/fixtures/statistics?fixture={fixture_id}", headers=headers, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            h_c, a_c = 0, 0
            for idx, team_stat in enumerate(res):
                stats = team_stat.get("statistics", [])
                for s in stats:
                    if s.get("type") == "Corner Kicks":
                        val = s.get("value")
                        c_val = int(val) if val is not None and str(val).isdigit() else 0
                        if idx == 0:
                            h_c = c_val
                        else:
                            a_c = c_val
            return h_c, a_c
    except Exception as e:
        print(f"Stats lookup error for fid {fixture_id}:", e)
    return 0, 0

def match_finder(m_cfg: dict, fixtures: list[dict]) -> dict | None:
    for f in fixtures:
        h = f.get("teams", {}).get("home", {}).get("name", "").lower()
        a = f.get("teams", {}).get("away", {}).get("name", "").lower()
        home_match = any(kw in h for kw in m_cfg["home_kw"])
        away_match = any(kw in a for kw in m_cfg["away_kw"])
        if home_match and away_match:
            return f
    return None

# ─── Ticket Progress Card (100% Corner Focus) ─────────────────────────────────
def get_corner_progress_bar(current: int, target: int) -> str:
    filled = min(current, target)
    bar = "■" * filled + "□" * max(0, target - filled)
    return f"[{bar}] {current}/{target}"

def get_ticket_card(match_states: dict) -> str:
    lines = []
    won_count = 0
    in_play_count = 0
    waiting_count = 0
    lost_count = 0

    for m in MATCHES:
        mid = m["id"]
        st = match_states.get(mid, {"phase": "SCHEDULED", "c_home": 0, "c_away": 0, "target_hit": False})
        phase = st["phase"]
        c_h = st.get("c_home", 0)
        c_a = st.get("c_away", 0)
        c_tot = c_h + c_a
        
        # Conteggio rilevante
        if m["target_type"] == "HOME":
            curr_tracked = c_h
        elif m["target_type"] == "AWAY":
            curr_tracked = c_a
        else:
            curr_tracked = c_tot

        target = m["target_val"]
        is_won = curr_tracked >= target
        prog_bar = get_corner_progress_bar(curr_tracked, target)

        if is_won:
            won_count += 1
            icon = "✅ TARGET PRESO!"
        elif phase == "FINISHED":
            lost_count += 1
            icon = "❌ NON RAGGIUNTO"
        elif phase in ("IN_PLAY", "HALFTIME"):
            in_play_count += 1
            icon = f"🟢 IN CORSO ({prog_bar})"
        else:
            waiting_count += 1
            icon = f"⏳ IN ARRIVO (Target: {target} corner)"

        lines.append(
            f"• {m['flag']} <b>{m['home']} vs {m['away']}</b> ({m['kickoff']})\n"
            f"   └ 🚩 {m['pick_desc']} {m['odds']} ➔ <b>{icon}</b>"
        )

    card = (
        "📋 <b>STATO TICKET #19 (SESTINA CORNER · Vincita: 255.97 €):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n\n".join(lines)
        + "\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Avanzamento</b>: <b>{won_count}</b> Prese · <b>{in_play_count}</b> In Gioco · <b>{waiting_count}</b> In Arrivo\n"
        f"💰 <b>Vincita Potenziale</b>: <b>255.97 €</b> (Stake 30.00 € · Quota 8.44×)"
    )
    return card

# ─── Motore di Monitoraggio Live Corner ───────────────────────────────────────
def main():
    print(f"=== BAgent Corner Live Monitor Avviato ({datetime.now().strftime('%H:%M:%S')}) ===")
    
    match_states = {
        m["id"]: {
            "phase": "SCHEDULED",
            "c_home": 0,
            "c_away": 0,
            "minute": 0,
            "target_hit": False,
            "notified_start": False,
            "notified_end": False,
            "last_c_notified": 0,
        }
        for m in MATCHES
    }

    startup_text = (
        "🟢 <b>BAgent Corner & Foul Monitor ATTIVO 24/7</b>\n\n"
        "🎯 <i>Modalità Attiva: Aggiornamenti ESCLUSIVI sui Calci d'Angolo e Duelli (Zero Spam di Gol)!</i>\n\n"
        + get_ticket_card(match_states)
    )
    notify_telegram(startup_text)

    while True:
        try:
            fixtures = get_live_fixtures_and_stats()

            for m in MATCHES:
                mid = m["id"]
                st = match_states[mid]
                
                if st["phase"] == "FINISHED" and st["notified_end"]:
                    continue

                ev = match_finder(m, fixtures)

                if ev:
                    fid = ev.get("fixture", {}).get("id")
                    fixture_info = ev.get("fixture", {})
                    status_long = fixture_info.get("status", {}).get("long", "")
                    status_short = fixture_info.get("status", {}).get("short", "")
                    status_type = fixture_info.get("status", {}).get("type", "")
                    elapsed = fixture_info.get("status", {}).get("elapsed", 0) or 0

                    classified = classify_status(status_short, status_long, status_type, elapsed)
                    st["phase"] = classified
                    st["minute"] = elapsed

                    # Recupera i corner esatti
                    if fid:
                        c_h, c_a = get_fixture_corners(fid)
                        st["c_home"] = c_h
                        st["c_away"] = c_a

                    c_h = st["c_home"]
                    c_a = st["c_away"]
                    c_tot = c_h + c_a
                    
                    if m["target_type"] == "HOME":
                        curr_tracked = c_h
                        desc_c = f"Corner {m['home']}: {c_h}"
                    elif m["target_type"] == "AWAY":
                        curr_tracked = c_a
                        desc_c = f"Corner {m['away']}: {c_a}"
                    else:
                        curr_tracked = c_tot
                        desc_c = f"Corner Totali: {c_tot} ({c_h}-{c_a})"

                    target = m["target_val"]

                    # 1️⃣ NOTIFICA KICKOFF
                    if classified == "IN_PLAY" and not st["notified_start"]:
                        st["notified_start"] = True
                        kickoff_msg = (
                            f"🟢 <b>INIZIO PARTITA! FISCHIO D'INIZIO! ⏱️</b>\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b> ({m['league']})\n"
                            f"🎯 Nostro Obiettivo: <b>{m['pick_desc']} {m['odds']}</b> (Target: {target} corner)\n\n"
                            + get_ticket_card(match_states)
                        )
                        notify_telegram(kickoff_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] KICKOFF: {m['home']} vs {m['away']}")

                    # 2️⃣ NOTIFICA TARGET RAGGIUNTO (Esito Vincente Live!)
                    if curr_tracked >= target and not st["target_hit"]:
                        st["target_hit"] = True
                        target_hit_msg = (
                            f"🎉 <b>TARGET CORNER RAGGIUNTO & VINTO! 🏁✅</b>\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b> ({elapsed}')\n"
                            f"🚩 <b>{desc_c}</b> (Target {target} RAGGIUNTO!)\n"
                            f"🎯 Pronostico: <b>{m['pick_desc']} {m['odds']} ➔ PRESO AL 100%!</b> 💰\n\n"
                            + get_ticket_card(match_states)
                        )
                        notify_telegram(target_hit_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] TARGET HIT: {m['home']} vs {m['away']} ({curr_tracked}/{target})")

                    # 3️⃣ NOTIFICA AGGIORNAMENTO CORNER (Ogni nuovo corner significativo)
                    elif curr_tracked > st["last_c_notified"] and classified in ("IN_PLAY", "HALFTIME"):
                        st["last_c_notified"] = curr_tracked
                        left_c = max(0, target - curr_tracked)
                        if not st["target_hit"] and left_c <= 3:
                            corner_alert_msg = (
                                f"🚩 <b>CORNER ALERT! ({elapsed}')</b>\n\n"
                                f"{m['flag']} <b>{m['home']} vs {m['away']}</b>\n"
                                f"📊 <b>{desc_c}</b>\n"
                                f"⏳ <i>Mancano solo <b>{left_c} corner</b> per centrare la quota {m['odds']}!</i>\n"
                                f"📈 Progresso: {get_corner_progress_bar(curr_tracked, target)}"
                            )
                            notify_telegram(corner_alert_msg)
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] CORNER UPDATE: {m['home']} vs {m['away']} ({curr_tracked}/{target})")

                    # 4️⃣ NOTIFICA FINE PARTITA (FT)
                    if classified == "FINISHED" and not st["notified_end"]:
                        st["notified_end"] = True
                        is_won = curr_tracked >= target
                        res_icon = "🏆 <b>✅ PRONOSTICO CORNER VINTO!</b>" if is_won else "⚠️ <b>❌ NON RAGGIUNTO</b>"
                        ft_msg = (
                            f"🏁 <b>FISCHIO FINALE! RISULTATO CORNER DEFINITIVO</b>\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b> (FT)\n"
                            f"🚩 <b>{desc_c}</b>\n"
                            f"🎯 Nostro Pick: <b>{m['pick_desc']} {m['odds']}</b>\n"
                            f"{res_icon}\n\n"
                            + get_ticket_card(match_states)
                        )
                        notify_telegram(ft_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] FULL-TIME: {m['home']} vs {m['away']} -> {res_icon}")

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Polling error:", e)

        time.sleep(25)

if __name__ == "__main__":
    main()
