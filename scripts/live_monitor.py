#!/usr/bin/env python3
"""
BAgent Live Monitor
Monitora punteggi live via Sofascore API e consiglia pick live con edge calcolato.
Notifica su desktop quando il punteggio cambia.

Uso: python3 scripts/live_monitor.py
"""

import time
import math
import os
import requests
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")

MATCHES = [
    {
        "id": 9992,
        "home": "Tartu JK Welco",
        "away": "FCI Levadia Tallinn U21",
        "league": "Estonia Esiliiga",
        "kickoff": "14:00",
        "our_pick": "Over 5.5 @3.30 (DC 1X @1.13)",
        "avg_goals": 3.8,
        "home_prob": 0.70,
        "draw_prob": 0.18,
        "away_prob": 0.12,
        "btts_prob": 0.75,
    },
    {
        "id": 3204,
        "home": "El Mansurah",
        "away": "Baladiyyat AL Mehalla",
        "league": "Egypt 2nd Division",
        "kickoff": "15:30",
        "our_pick": "Under 2.5 @1.34",
        "avg_goals": 1.5,
        "home_prob": 0.35,
        "draw_prob": 0.40,
        "away_prob": 0.25,
        "btts_prob": 0.30,
    },
    {
        "id": 9989,
        "home": "CSC 1599 Selimbar",
        "away": "Botosani",
        "league": "Cupa Romaniei",
        "kickoff": "16:30",
        "our_pick": "2 Botosani @1.46 (DC X2 @1.11)",
        "avg_goals": 2.2,
        "home_prob": 0.18,
        "draw_prob": 0.26,
        "away_prob": 0.56,
        "btts_prob": 0.45,
    },
    {
        "id": 9997,
        "home": "Rosenborg BK Kvinner",
        "away": "Lyn",
        "league": "Toppserien Femminile",
        "kickoff": "18:00",
        "our_pick": "Over 2.5 @1.40",
        "avg_goals": 3.2,
        "home_prob": 0.72,
        "draw_prob": 0.18,
        "away_prob": 0.10,
        "btts_prob": 0.55,
    },
    {
        "id": 4261,
        "home": "Mjallby",
        "away": "Red Bull Salisburgo",
        "league": "UEFA Europa League",
        "kickoff": "18:00",
        "our_pick": "Over 3.5 Cartellini @1.71 (1X2 Cartellini @1.65)",
        "avg_goals": 2.8,
        "home_prob": 0.22,
        "draw_prob": 0.25,
        "away_prob": 0.53,
        "btts_prob": 0.52,
    },
    {
        "id": 1472,
        "home": "Jagiellonia Bialystok",
        "away": "Iberia",
        "league": "UEFA Europa League",
        "kickoff": "18:00",
        "our_pick": "Over 8.5 Corner @1.59 (1 Corner @1.30)",
        "avg_goals": 3.0,
        "home_prob": 0.70,
        "draw_prob": 0.20,
        "away_prob": 0.10,
        "btts_prob": 0.48,
    },
]

# ─── Colori ANSI ─────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ─── Notifiche ───────────────────────────────────────────────────────────────

def notify_desktop(title: str, message: str):
    """Notifica desktop macOS."""
    try:
        script = f'display notification "{message}" with title "{title}" sound name "Ping"'
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)
    except Exception:
        pass

def notify_telegram(message: str):
    """Invia messaggio Telegram."""
    if not TELEGRAM_TOKEN:
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        if not r.ok:
            print(f"{YELLOW}⚠ Telegram errore {r.status_code}: {r.text[:80]}{RESET}")
    except Exception as e:
        print(f"{RED}✗ Telegram: {e}{RESET}")

def notify(title: str, message: str, picks_text: str = ""):
    """Invia notifica desktop + Telegram."""
    notify_desktop(title, message)
    tg_msg = f"<b>{title}</b>\n{message}"
    if picks_text:
        tg_msg += f"\n\n{picks_text}"
    notify_telegram(tg_msg)

# ─── Sofascore API ───────────────────────────────────────────────────────────

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_HOST = "v3.football.api-sports.io"

AF_HEADERS = {
    "x-rapidapi-host": API_FOOTBALL_HOST,
    "x-rapidapi-key": API_FOOTBALL_KEY,
}

# Mappa: sofascore_id → api_football_fixture_id (da scoprire al primo run)
AF_FIXTURE_MAP: dict[int, int] = {}

def get_all_live_fixtures() -> list[dict]:
    """Ritorna tutti i fixture live da API-Football."""
    try:
        r = requests.get(
            f"https://{API_FOOTBALL_HOST}/fixtures?live=all",
            headers=AF_HEADERS, timeout=15
        )
        if r.status_code == 200:
            return r.json().get("response", [])
        else:
            print(f"\n{YELLOW}⚠ API-Football: HTTP {r.status_code}{RESET}")
    except Exception as e:
        print(f"\n{RED}✗ API-Football: {e}{RESET}")
    return []

def find_fixture(home_kw: str, away_kw: str, fixtures: list[dict]) -> dict | None:
    """Cerca un fixture live per keyword."""
    home_kw = home_kw.lower()
    away_kw = away_kw.lower()
    for f in fixtures:
        h = f.get("teams", {}).get("home", {}).get("name", "").lower()
        a = f.get("teams", {}).get("away", {}).get("name", "").lower()
        if any(k in h for k in home_kw.split()) and any(k in a for k in away_kw.split()):
            return f
        if any(k in a for k in home_kw.split()) and any(k in h for k in away_kw.split()):
            return f
    return None

def get_live_event(match: dict, fixtures: list[dict]) -> dict | None:
    """Estrae dati live per un match dai fixture API-Football."""
    home_kw = match["home"].split()[0]  # es. "Kingsley"
    away_kw = match["away"].split()[0]  # es. "Gwelup"
    f = find_fixture(home_kw, away_kw, fixtures)
    if not f:
        return None
    goals = f.get("goals", {})
    status = f.get("fixture", {}).get("status", {})
    elapsed = f.get("fixture", {}).get("status", {}).get("elapsed") or 0
    return {
        "homeScore": {"current": goals.get("home") or 0},
        "awayScore": {"current": goals.get("away") or 0},
        "time": {"played": elapsed},
        "status": {"description": status.get("long", "")},
    }

def find_thailand_id() -> bool:
    """Per Thailand usiamo API-Football, non serve ID separato."""
    return True

# ─── Calcolo Pick Live con Poisson ───────────────────────────────────────────

def poisson_prob(lam: float, k: int) -> float:
    """P(X = k) con distribuzione di Poisson."""
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def poisson_over(lam: float, threshold: float) -> float:
    """P(X > threshold) con Poisson."""
    total = 0.0
    k = int(threshold) + 1
    while k <= 20:
        total += poisson_prob(lam, k)
        k += 1
    return total

def poisson_btts(lam_home: float, lam_away: float) -> float:
    """P(entrambe segnano) = P(home>=1) * P(away>=1)."""
    p_home = 1 - poisson_prob(lam_home, 0)
    p_away = 1 - poisson_prob(lam_away, 0)
    return p_home * p_away

def calc_live_picks(match: dict, home_score: int, away_score: int,
                    minute: int, period: str) -> list[dict]:
    """
    Calcola i pick live consigliati in base al punteggio e minuto corrente.
    Restituisce lista di dict con: mercato, pick, prob_nostra, edge_soglia
    """
    picks = []
    avg = match["avg_goals"]
    h_base = match["home_prob"]
    a_base = match["away_prob"]
    d_base = match["draw_prob"]

    total_score = home_score + away_score
    is_second_half = period in ("2nd half", "2HT")

    # Minuti rimanenti stimati (compatibile con API-Football e Sofascore)
    p = period.lower()
    if any(x in p for x in ("first", "1st", "primo")):
        remaining = max(45 - minute, 5)
    elif any(x in p for x in ("second", "2nd", "secondo")):
        remaining = max(90 - minute, 3)
    elif any(x in p for x in ("extra", "overtime", "supplement")):
        remaining = max(120 - minute, 2)
    else:
        remaining = 90

    frac = remaining / 90.0  # frazione del match rimanente

    # Lambda aggiustata per tempo rimanente
    lam_total_remaining = avg * frac
    lam_home_rem = (avg * h_base / (h_base + a_base)) * frac
    lam_away_rem = (avg * a_base / (h_base + a_base)) * frac

    # ── Over/Under ────────────────────────────────────────────────────────────
    for threshold in [1.5, 2.5, 3.5, 4.5]:
        goals_needed = max(0, threshold + 1 - total_score)
        if goals_needed <= 0:
            picks.append({
                "mercato": f"Over {threshold}",
                "pick": f"✅ GIÀ VINTA ({total_score} gol)",
                "prob": 1.0,
                "edge": None,
                "priority": 0,
            })
        elif goals_needed == 1 and lam_total_remaining > 0.3:
            prob = poisson_over(lam_total_remaining, 0)  # almeno 1 gol rimanente
            picks.append({
                "mercato": f"Over {threshold}",
                "pick": f"Serve ancora 1 gol ({total_score} attuali)",
                "prob": round(prob, 2),
                "edge": None,
                "priority": 1,
            })

    # ── BTTS ─────────────────────────────────────────────────────────────────
    home_scored = home_score > 0
    away_scored = away_score > 0

    if home_scored and away_scored:
        picks.append({
            "mercato": "BTTS Gol",
            "pick": "✅ GIÀ VINTA (entrambe hanno segnato)",
            "prob": 1.0,
            "edge": None,
            "priority": 0,
        })
    elif home_scored and not away_scored:
        prob_away_scores = 1 - poisson_prob(lam_away_rem, 0)
        picks.append({
            "mercato": "BTTS Gol",
            "pick": f"Serve gol {match['away']} ({remaining}' rimanenti)",
            "prob": round(prob_away_scores, 2),
            "edge": None,
            "priority": 1,
        })
    elif away_scored and not home_scored:
        prob_home_scores = 1 - poisson_prob(lam_home_rem, 0)
        picks.append({
            "mercato": "BTTS Gol",
            "pick": f"Serve gol {match['home']} ({remaining}' rimanenti)",
            "prob": round(prob_home_scores, 2),
            "edge": None,
            "priority": 1,
        })
    else:
        # 0-0: BTTS serve che segnino entrambe
        prob = poisson_btts(lam_home_rem, lam_away_rem)
        picks.append({
            "mercato": "BTTS Gol",
            "pick": "Entrambe devono ancora segnare",
            "prob": round(prob, 2),
            "edge": None,
            "priority": 2,
        })

    # ── 1X2 Live ─────────────────────────────────────────────────────────────
    # Probabilità aggiornata basata su score attuale + Poisson rimanente
    diff = home_score - away_score

    # Stima prob vittoria finale
    if diff > 1:
        p_home_win = 0.95 + (diff - 2) * 0.02
        p_draw     = 0.04
        p_away_win = 0.01
    elif diff == 1:
        p_home_win = 0.75 + frac * 0.10
        p_draw     = 0.18 - frac * 0.08
        p_away_win = 0.07 - frac * 0.02
    elif diff == 0:
        # 0-0: usa probabilità base aggiustate per forma
        home_adj = h_base * (1 + frac * 0.2)
        away_adj = a_base * (1 + frac * 0.2)
        draw_adj = d_base
        tot = home_adj + away_adj + draw_adj
        p_home_win = home_adj / tot
        p_away_win = away_adj / tot
        p_draw     = draw_adj / tot
    elif diff == -1:
        p_away_win = 0.75 + frac * 0.10
        p_draw     = 0.18 - frac * 0.08
        p_home_win = 0.07 - frac * 0.02
    else:
        p_away_win = 0.95
        p_draw     = 0.04
        p_home_win = 0.01

    # Clamp
    p_home_win = max(0.01, min(0.99, p_home_win))
    p_away_win = max(0.01, min(0.99, p_away_win))
    p_draw     = max(0.01, min(0.99, p_draw))

    picks.append({
        "mercato": "1X2",
        "pick": f"1 {match['home']}",
        "prob": round(p_home_win, 2),
        "edge": None,
        "priority": 3,
    })
    picks.append({
        "mercato": "1X2",
        "pick": f"X Pareggio",
        "prob": round(p_draw, 2),
        "edge": None,
        "priority": 3,
    })
    picks.append({
        "mercato": "1X2",
        "pick": f"2 {match['away']}",
        "prob": round(p_away_win, 2),
        "edge": None,
        "priority": 3,
    })

    return picks

def format_pick_table(picks: list[dict]) -> str:
    lines = []
    for p in picks:
        prob = p["prob"]
        if prob >= 0.80:
            verdict = "⭐⭐"
            color = GREEN
        elif prob >= 0.65:
            verdict = "⭐ "
            color = GREEN
        elif prob >= 0.50:
            verdict = "👀 "
            color = YELLOW
        else:
            verdict = "❌ "
            color = RED

        prob_str = f"{int(prob * 100)}%" if prob < 1.0 else "✅ VINTA"
        mercato = p['mercato'][:10]
        pick = p['pick'][:42]
        lines.append(f"  {color}{verdict} {mercato:<12} {pick:<42} {prob_str:>6}{RESET}")
    return "\n".join(lines)

# ─── Monitor Loop ────────────────────────────────────────────────────────────

def run():
    print(f"\n{BOLD}{BLUE}╔══════════════════════════════════════════════════════╗")
    print(f"║         BAgent Live Monitor — {datetime.now().strftime('%d/%m/%Y %H:%M')}          ║")
    print(f"╚══════════════════════════════════════════════════════╝{RESET}\n")

    # Verifica configurazione Telegram
    if TELEGRAM_TOKEN:
        print(f"{GREEN}✓ Telegram configurato (chat_id: {TELEGRAM_CHAT_ID}){RESET}")
    else:
        print(f"{RED}✗ TELEGRAM_TOKEN mancante nel .env — notifiche Telegram disabilitate{RESET}")
        print(f"  .env cercato in: {env_path}")
    print()

    # Stato precedente punteggi
    prev_scores: dict[int, tuple] = {}

    if not API_FOOTBALL_KEY:
        print(f"{RED}✗ API_FOOTBALL_KEY mancante nel .env{RESET}")
        sys.exit(1)
    print(f"{GREEN}✓ API-Football configurata{RESET}\n")

    print(f"{BOLD}{'Partita':<22} {'Orario':<8} {'Pick'}{RESET}")
    print("─" * 60)
    for m in MATCHES:
        home = m['home'].split()[0][:3].upper()
        away = m['away'].split()[0][:3].upper()
        partita = f"{home} vs {away}"
        print(f"  {partita:<20} {m['kickoff']:<8} {m['our_pick']}")

    print(f"\n{YELLOW}Polling ogni 30 secondi... (Ctrl+C per uscire){RESET}\n")
    print("─" * 60)

    # Test Telegram all'avvio
    partite_str = "\n".join([
        f"• {m['home'].split()[0][:3].upper()} vs {m['away'].split()[0][:3].upper()} ({m['kickoff']}) — {m['our_pick']}"
        for m in MATCHES
    ])
    notify_telegram(f"🤖 <b>BAgent Live Monitor attivo!</b>\n\nPartite monitorate:\n{partite_str}\n\n⏱ Polling ogni 30 secondi.")

    while True:
        now = datetime.now().strftime("%H:%M:%S")

        # Fetch unico per tutti i live
        fixtures = get_all_live_fixtures()

        found_any = False
        for match in MATCHES:
            ev = get_live_event(match, fixtures)
            if not ev:
                continue
            found_any = True

            status = ev.get("status", {}).get("description", "")
            home_score = ev.get("homeScore", {}).get("current", 0) or 0
            away_score = ev.get("awayScore", {}).get("current", 0) or 0
            minute = ev.get("time", {}).get("played", 0) or 0
            period = status.lower()

            score_key = (home_score, away_score)
            prev = prev_scores.get(match["id"])

            # Rileva cambio punteggio o primo check
            changed = (prev is not None and prev != score_key)
            first_time = (prev is None)

            if changed or first_time:
                prefix = f"\n{BOLD}{'🚨 GOL!' if changed else '📊'} [{now}] {match['home']} {home_score}-{away_score} {match['away']}{RESET}"
                prefix += f" | {match['league']} | {status} {minute}'"
                print(prefix)

                # Calcola pick live
                picks = calc_live_picks(match, home_score, away_score, minute, period)
                relevant = [p for p in picks if p["prob"] >= 0.50 or p["prob"] == 1.0]

                # Testo pick per Telegram (senza colori ANSI)
                tg_picks = ""
                for p in relevant:
                    prob_str = f"{int(p['prob']*100)}%" if p['prob'] < 1.0 else "✅ VINTA"
                    verdict = "⭐⭐" if p['prob'] >= 0.80 else ("⭐" if p['prob'] >= 0.65 else "👀")
                    tg_picks += f"{verdict} [{p['mercato']}] {p['pick']} — {prob_str}\n"
                tg_picks += f"\n🎯 Nostro pick: {match['our_pick']}"
                tg_picks += f"\n🔗 Netwin live: https://www.netwin.it/scommesse/live"

                if changed:
                    scorer_team = match['home'] if home_score > (prev[0] if prev else 0) else match['away']
                    notify(
                        f"⚽ GOL! {match['home']} {home_score}-{away_score} {match['away']}",
                        f"{scorer_team} ha segnato! {minute}' — {match['league']}",
                        picks_text=tg_picks,
                    )
                elif first_time and status not in ("Not started", ""):
                    notify(
                        f"📊 Live: {match['home']} {home_score}-{away_score} {match['away']}",
                        f"{match['league']} | {minute}'",
                        picks_text=tg_picks,
                    )

                if relevant:
                    print(f"\n  {BOLD}Pick Live Consigliati:{RESET}")
                    print(format_pick_table(relevant))

                # Mostra stato pick in ticket
                print(f"\n  {BLUE}Nostro pick in ticket: {match['our_pick']}{RESET}")
                print(f"  Netwin live: https://www.netwin.it/scommesse/live")
                print("─" * 60)

                prev_scores[match["id"]] = score_key

        if not found_any:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] nessuna partita live trovata — in attesa...", end="\r")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] polling...", end="\r")
        time.sleep(30)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Monitor fermato.{RESET}")
