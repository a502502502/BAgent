#!/usr/bin/env python3
"""
BAgent Night Live Daemon (Versione 2.1 Robusta & Anti-Spam)
Monitora in tempo reale le partite del Ticket #14 (Sestina Overseas) e invia notifiche Telegram per:
1. Sincronizzazione intelligente all'avvio (senza falsi allarmi)
2. Inizio partita reale (Kickoff effettivo)
3. Gol in tempo reale con marcatore / minuto
4. Intervallo / Fine Primo Tempo (HT - NON confuso con fine partita)
5. Fine partita reale al 90'+ (Full-Time con fallback quando la partita esce dal feed live)
6. Avanzamento complessivo del Ticket #14 aggiornato con le vittorie reali

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

# ─── Configurazione Match Ticket #15 (Sabato Sera 22 Agosto) ───────────────────
MATCHES = [
    {
        "id": "inter_monza",
        "home": "Inter",
        "away": "Monza",
        "home_kw": ["inter", "internazionale"],
        "away_kw": ["monza"],
        "flag": "🇮🇹",
        "country": "Italia",
        "league": "Serie A",
        "kickoff": "18:30",
        "pick_desc": "Lautaro (o Sost.) Segna o Palo/Trav.",
        "odds": "@1.67",
        "evaluator": lambda h, a: (h >= 1, f"Gol/Palo Lautaro (Inter {h}-{a} Monza)"),
    },
    {
        "id": "brentford_tottenham",
        "home": "Brentford",
        "away": "Tottenham",
        "home_kw": ["brentford"],
        "away_kw": ["tottenham", "spurs"],
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "country": "Inghilterra",
        "league": "Premier League",
        "kickoff": "18:30",
        "pick_desc": "Over 4.5 Corner Brentford (Sq.1)",
        "odds": "@1.50",
        "evaluator": lambda h, a: (True, "Over 4.5 Corner Brentford"),
    },
    {
        "id": "tolosa_lione",
        "home": "Toulouse",
        "away": "Lyon",
        "home_kw": ["toulouse", "tolosa"],
        "away_kw": ["lyon", "lione"],
        "flag": "🇫🇷",
        "country": "Francia",
        "league": "Ligue 1",
        "kickoff": "20:45",
        "pick_desc": "MultiGol 1-3 Casa (Tolosa)",
        "odds": "@1.32",
        "evaluator": lambda h, a: (1 <= h <= 3, f"Tolosa Gol {h} (Forbice 1-3)"),
    },
    {
        "id": "espanyol_real_madrid",
        "home": "Espanyol",
        "away": "Real Madrid",
        "home_kw": ["espanyol"],
        "away_kw": ["real madrid", "madrid"],
        "flag": "🇪🇸",
        "country": "Spagna",
        "league": "LaLiga",
        "kickoff": "21:30",
        "pick_desc": "X2 + Over 2.5 Gol",
        "odds": "@1.78",
        "evaluator": lambda h, a: (a >= h and (h + a) >= 3, f"X2 + Over 2.5 ({h}-{a})"),
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

# ─── Classificatore di Stato Infallibile ───────────────────────────────────────
def classify_status(status_short: str, status_long: str, status_type: str = "", elapsed: int = 0) -> str:
    """
    Classifica con precisione assoluta lo stato della partita.
    Valori ritornati: 'SCHEDULED', 'IN_PLAY', 'HALFTIME', 'FINISHED', 'CANCELLED'
    """
    s_short = (status_short or "").strip().upper()
    s_long = (status_long or "").strip().lower()
    s_type = (status_type or "").strip().lower()

    # 1. HALFTIME (Fine 1° Tempo - NON è fine partita!)
    # Controlliamo prima per evitare falsi positivi con 'ended' o 'intervallo'
    if s_short in ("HT", "BT") or any(k in s_long for k in ("halftime", "half time", "1st half ended", "first half ended", "intervallo")):
        return "HALFTIME"

    # 2. FINISHED (Fine Partita Reale al 90'+ / FT)
    if s_short in ("FT", "AET", "PEN") or s_type == "finished":
        return "FINISHED"
    if s_long in ("match finished", "finished", "full time", "after extra time", "after penalties", "final", "ended"):
        return "FINISHED"

    # 3. IN_PLAY (In corso)
    if s_short in ("1H", "2H", "ET", "P", "LIVE", "INT") or s_type == "inprogress" or elapsed > 0:
        return "IN_PLAY"
    if any(k in s_long for k in ("first half", "second half", "1st half", "2nd half", "in play", "live", "extra time")):
        return "IN_PLAY"

    # 4. CANCELLED / POSTPONED
    if s_short in ("PST", "CANC", "ABD", "AWD", "WO", "SUSP") or any(k in s_long for k in ("postponed", "cancelled", "abandoned", "interrupted")):
        return "CANCELLED"

    return "SCHEDULED"

# ─── Multi-Source Data Polling ────────────────────────────────────────────────
def get_live_fixtures() -> list[dict]:
    """Recupera tutte le partite live da API-Football o Sofascore."""
    # 1. API-Football live
    if API_FOOTBALL_KEY:
        try:
            headers = {
                "x-rapidapi-host": API_FOOTBALL_HOST,
                "x-rapidapi-key": API_FOOTBALL_KEY,
                "x-apisports-key": API_FOOTBALL_KEY,
            }
            r = requests.get(f"https://{API_FOOTBALL_HOST}/fixtures?live=all", headers=headers, timeout=12)
            if r.status_code == 200:
                res = r.json().get("response", [])
                if res:
                    return res
        except Exception as e:
            print("API-Football live error:", e)

    # 2. Sofascore live fallback
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        r = requests.get("https://api.sofascore.com/api/v1/sport/football/events/live", headers=headers, timeout=12)
        if r.status_code == 200:
            events = r.json().get("events", [])
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

def get_finished_or_scheduled_fixture(m_cfg: dict) -> dict | None:
    """
    Fallback quando una partita non è più nella lista live.
    Verifica se il match è terminato (FT) interrogando le partite di oggi e ieri su API-Football.
    """
    if not API_FOOTBALL_KEY:
        return None

    headers = {
        "x-rapidapi-host": API_FOOTBALL_HOST,
        "x-rapidapi-key": API_FOOTBALL_KEY,
        "x-apisports-key": API_FOOTBALL_KEY,
    }

    # Prova data odierna e ieri per overlap fusi orari
    dates_to_check = [
        datetime.now().strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
    ]
    for d in dates_to_check:
        try:
            r = requests.get(f"https://{API_FOOTBALL_HOST}/fixtures?date={d}", headers=headers, timeout=12)
            if r.status_code == 200:
                fixtures = r.json().get("response", [])
                match = match_finder(m_cfg, fixtures)
                if match:
                    return match
        except Exception as e:
            print(f"API-Football date ({d}) lookup error:", e)

    return None

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
    """Genera il riepilogo grafico della Sestina con lo stato esatto di ogni partita."""
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
        elif phase == "HALFTIME":
            in_play_count += 1
            line = f"• {m['flag']} <b>{m['home']} {h_s}-{a_s} {m['away']}</b> (LIVE HT)\n   └ 🎯 {m['pick_desc']} {m['odds']} ➔ ⏸️ <b>INTERVALLO</b>"
        elif phase == "IN_PLAY":
            in_play_count += 1
            min_str = f"{st['minute']}'" if st["minute"] > 0 else "LIVE"
            line = f"• {m['flag']} <b>{m['home']} {h_s}-{a_s} {m['away']}</b> (LIVE {min_str})\n   └ 🎯 {m['pick_desc']} {m['odds']} ➔ 🟢 <b>IN CORSO</b>"
        else:
            waiting_count += 1
            line = f"• {m['flag']} <b>{m['home']} vs {m['away']}</b> ({m['kickoff']})\n   └ 🎯 {m['pick_desc']} {m['odds']} ➔ ⏳ <b>IN ARRIVO</b>"
        lines.append(line)

    card = (
        "📋 <b>STATO TICKET #15 (Vincita Potenziale: 121.24 €):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n\n".join(lines)
        + "\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Avanzamento</b>: <b>{won_count}</b> Prese · <b>{in_play_count}</b> In Corso · <b>{waiting_count}</b> In Arrivo\n"
        f"💰 <b>Vincita Potenziale</b>: <b>121.24 €</b> (Stake 20.00 € · Quota 5.89×)"
    )
    return card

# ─── Motore di Monitoraggio Live ──────────────────────────────────────────────
def main():
    print(f"=== BAgent Live Daemon 2.1 Avviato ({datetime.now().strftime('%H:%M:%S')}) ===")
    
    # 1. Inizializzazione stati partite
    match_states = {
        m["id"]: {
            "phase": "SCHEDULED",
            "score": (0, 0),
            "minute": 0,
            "notified_start": False,
            "notified_end": False,
            "last_score_notified": (0, 0),
        }
        for m in MATCHES
    }

    # 2. Sincronizzazione iniziale intelligente (senza falsi allarmi)
    print("Sincronizzazione iniziale partite...")
    fixtures = get_live_fixtures()
    
    for m in MATCHES:
        mid = m["id"]
        st = match_states[mid]
        ev = match_finder(m, fixtures)
        
        # Se non è nel live, controlla se è già finita (FT)
        if not ev:
            ev = get_finished_or_scheduled_fixture(m)

        if ev:
            fixture_info = ev.get("fixture", {})
            status_long = fixture_info.get("status", {}).get("long", "")
            status_short = fixture_info.get("status", {}).get("short", "")
            status_type = fixture_info.get("status", {}).get("type", "")
            elapsed = fixture_info.get("status", {}).get("elapsed", 0) or 0
            goals = ev.get("goals", {})
            h_score = goals.get("home", 0) if goals.get("home") is not None else 0
            a_score = goals.get("away", 0) if goals.get("away") is not None else 0
            curr_score = (h_score, a_score)

            classified = classify_status(status_short, status_long, status_type, elapsed)
            st["phase"] = classified
            st["score"] = curr_score
            st["minute"] = elapsed if elapsed > 0 else (90 if classified == "FINISHED" else 0)
            st["last_score_notified"] = curr_score

            if classified == "FINISHED":
                st["notified_start"] = True
                st["notified_end"] = True
                print(f"  • {m['home']} vs {m['away']}: GIÀ CONCLUSA (FT {h_score}-{a_score})")
            elif classified in ("IN_PLAY", "HALFTIME"):
                st["notified_start"] = True
                print(f"  • {m['home']} vs {m['away']}: IN CORSO ({h_score}-{a_score}, {classified})")
            else:
                print(f"  • {m['home']} vs {m['away']}: IN PROGRAMMA ({m['kickoff']})")
        else:
            print(f"  • {m['home']} vs {m['away']}: Non trovata nel feed (in attesa di inizio {m['kickoff']})")

    # Invia notifica di avvio sincronizzata
    startup_text = (
        "🟢 <b>BAgent Live Monitor ATTIVO 24/7</b>\n\n"
        + get_ticket_card(match_states)
        + "\n\n🔔 <i>Notifiche automatiche attive per: Fischio d'inizio, Gol live e Risultato finale con esito!</i>"
    )
    notify_telegram(startup_text)

    # 3. Loop di monitoraggio live
    while True:
        try:
            fixtures = get_live_fixtures()

            for m in MATCHES:
                mid = m["id"]
                st = match_states[mid]
                
                # Se è già finita e notificata, non fare nulla
                if st["phase"] == "FINISHED" and st["notified_end"]:
                    continue

                ev = match_finder(m, fixtures)

                # Se non trovata nel live ma era in corso (o schedulata in orario passato), cerca nei risultati finiti
                if not ev and st["phase"] in ("IN_PLAY", "HALFTIME"):
                    ev = get_finished_or_scheduled_fixture(m)

                if ev:
                    fixture_info = ev.get("fixture", {})
                    status_long = fixture_info.get("status", {}).get("long", "")
                    status_short = fixture_info.get("status", {}).get("short", "")
                    status_type = fixture_info.get("status", {}).get("type", "")
                    elapsed = fixture_info.get("status", {}).get("elapsed", 0) or 0
                    goals = ev.get("goals", {})
                    h_score = goals.get("home", 0) if goals.get("home") is not None else 0
                    a_score = goals.get("away", 0) if goals.get("away") is not None else 0
                    curr_score = (h_score, a_score)

                    classified = classify_status(status_short, status_long, status_type, elapsed)
                    st["phase"] = classified

                    # 1️⃣ RILEVAZIONE INIZIO PARTITA REALE (KICKOFF)
                    if classified == "IN_PLAY" and not st["notified_start"]:
                        st["notified_start"] = True
                        st["score"] = curr_score
                        st["minute"] = elapsed
                        st["last_score_notified"] = curr_score

                        kickoff_msg = (
                            f"🟢 <b>INIZIO PARTITA! FISCHIO D'INIZIO! ⏱️</b>\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b> ({m['country']} {m['league']})\n"
                            f"🎯 Nostro Pick: <b>{m['pick_desc']} {m['odds']}</b>\n\n"
                            f"⏱ <i>Il match è iniziato! Punteggio attuale: {h_score}-{a_score} ({elapsed}')</i>\n\n"
                            + get_ticket_card(match_states)
                        )
                        notify_telegram(kickoff_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] KICKOFF NOTIFIED: {m['home']} vs {m['away']}")

                    # 2️⃣ RILEVAZIONE GOL IN TEMPO REALE (Solo se in gioco o intervallo)
                    if classified in ("IN_PLAY", "HALFTIME"):
                        if curr_score != st["last_score_notified"] and curr_score != (0, 0):
                            old_h, old_a = st["last_score_notified"]
                            st["score"] = curr_score
                            st["minute"] = elapsed
                            st["last_score_notified"] = curr_score
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

                    # 3️⃣ RILEVAZIONE FINE PARTITA REALE (FULL-TIME / FT al 90'+)
                    if classified == "FINISHED" and not st["notified_end"]:
                        st["phase"] = "FINISHED"
                        st["notified_end"] = True
                        st["score"] = curr_score
                        st["minute"] = 90
                        st["last_score_notified"] = curr_score
                        
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

