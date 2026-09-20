"""
services/api/mobile_server.py
Backend FastAPI per la Mobile App Android / PWA di BAgent.
Fornisce endpoint REST per schedine attive, schedine in arrivo, statistiche bankroll e live radar.
"""

import os
import sys
import time
import sqlite3
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "storage" / "database" / "bagent.db"
WEB_DIR = ROOT / "web_mobile"

app = FastAPI(
    title="BAgent Mobile API",
    description="API Server per l'App Mobile Android di BAgent",
    version="1.0.0"
)

# Abilita CORS per accesso da qualsiasi client locale / smartphone
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache in-memory per live scores (TTL 20s per evitare rate-limit)
LIVE_CACHE: Dict[str, Any] = {"timestamp": 0, "scores": {}}

LEAGUES_TO_CHECK = ["esp.1", "por.1", "arg.1", "ita.1", "eng.1", "ger.1"]
HEADERS_ESPN = {"User-Agent": "ESPN/6.0.0 (iPhone; iOS 17.0; Scale/3.00)", "Accept": "*/*"}


def get_live_scores_from_espn() -> Dict[str, Dict[str, Any]]:
    now = time.time()
    if now - LIVE_CACHE["timestamp"] < 20 and LIVE_CACHE["scores"]:
        return LIVE_CACHE["scores"]

    results = {}
    for league in LEAGUES_TO_CHECK:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
            resp = requests.get(url, headers=HEADERS_ESPN, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                for ev in data.get("events", []):
                    status_type = ev.get("status", {}).get("type", {})
                    detail = status_type.get("detail", "")
                    short_detail = status_type.get("shortDetail", detail)
                    state = status_type.get("state", "pre")  # pre, in, post

                    comp = ev.get("competitions", [{}])[0]
                    teams = comp.get("competitors", [])
                    if len(teams) >= 2:
                        home = teams[0] if teams[0].get("homeAway") == "home" else teams[1]
                        away = teams[1] if home == teams[0] else teams[0]

                        h_name = home.get("team", {}).get("name", "")
                        a_name = away.get("team", {}).get("name", "")
                        h_score = int(home.get("score", 0) or 0)
                        a_score = int(away.get("score", 0) or 0)

                        match_key = f"{h_name} vs {a_name}".lower()
                        item = {
                            "home_team": h_name,
                            "away_team": a_name,
                            "home_score": h_score,
                            "away_score": a_score,
                            "total_goals": h_score + a_score,
                            "status_detail": short_detail,
                            "state": state,
                        }
                        results[match_key] = item
                        # Indicizza anche per singola squadra
                        results[h_name.lower()] = item
                        results[a_name.lower()] = item
        except Exception:
            continue

    LIVE_CACHE["timestamp"] = now
    LIVE_CACHE["scores"] = results
    return results


def find_match_score(match_name: str, live_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    m_lower = match_name.lower()
    if m_lower in live_data:
        return live_data[m_lower]

    parts = m_lower.split(" vs ")
    if len(parts) == 2:
        h, a = parts[0].strip(), parts[1].strip()
        for k, v in live_data.items():
            if isinstance(v, dict) and "home_team" in v:
                v_h = v["home_team"].lower()
                v_a = v["away_team"].lower()
                if (h in v_h or v_h in h) and (a in v_a or v_a in a):
                    return v
                if (h in v_h or v_h in h) or (a in v_a or v_a in a):
                    return v
    return None


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "BAgent Mobile API", "version": "1.0.0"}


@app.get("/api/tickets/active")
def get_active_tickets():
    """Ritorna tutte le schedine in corso (IN_PLAY o OPEN) con overlay del punteggio live."""
    live_scores = get_live_scores_from_espn()
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, status, notes
        FROM ticket_ledger
        WHERE status = 'IN_PLAY' OR (status = 'OPEN' AND date_created >= date('now', '-2 days'))
        ORDER BY CASE WHEN status = 'IN_PLAY' THEN 1 ELSE 2 END, date_created DESC
    """)
    tickets_rows = c.fetchall()

    tickets = []
    for t in tickets_rows:
        ticket_id = t["ticket_id"]
        c.execute("""
            SELECT id, match_name, tournament, market_category, selection, odds, estimated_prob, edge_pct, result_status
            FROM bet_leg_ledger
            WHERE ticket_id = ?
        """, (ticket_id,))
        legs_rows = c.fetchall()

        legs = []
        for leg in legs_rows:
            score_info = find_match_score(leg["match_name"], live_scores)
            live_status = "PENDING"
            live_score_str = "0 - 0"
            clock_str = "Pre-Match"

            if score_info:
                live_score_str = f"{score_info['home_score']} - {score_info['away_score']}"
                clock_str = score_info["status_detail"]
                tot_goals = score_info["total_goals"]

                sel = leg["selection"].lower()
                # Valutazione istantanea dello stato per mercati Under / 1X
                if "under 3.5" in sel:
                    if tot_goals <= 2:
                        live_status = "SAFE_GREEN"
                    elif tot_goals == 3:
                        live_status = "LIVE_TENSE"
                    else:
                        live_status = "DANGER_RED"
                elif "under 3.0" in sel or "under 3 asiatico" in sel:
                    if tot_goals < 3:
                        live_status = "SAFE_GREEN"
                    elif tot_goals == 3:
                        live_status = "PUSH_REFUND"
                    else:
                        live_status = "DANGER_RED"
                elif "1x" in sel:
                    if score_info['home_score'] >= score_info['away_score']:
                        live_status = "SAFE_GREEN"
                    else:
                        live_status = "DANGER_RED"

            legs.append({
                "id": leg["id"],
                "match_name": leg["match_name"],
                "tournament": leg["tournament"],
                "market": leg["selection"],
                "odds": leg["odds"],
                "edge_pct": leg["edge_pct"],
                "result_status": leg["result_status"],
                "live_score": live_score_str,
                "clock": clock_str,
                "live_indicator": live_status
            })

        tickets.append({
            "ticket_id": t["ticket_id"],
            "date_created": t["date_created"],
            "description": t["description"],
            "num_legs": t["num_legs"],
            "total_odds": t["total_odds"],
            "stake_eur": t["stake_eur"],
            "payout_eur": t["payout_eur"],
            "status": t["status"],
            "notes": t["notes"],
            "legs": legs
        })

    conn.close()
    return {"tickets": tickets, "count": len(tickets), "server_time": time.strftime("%H:%M:%S")}


@app.get("/api/tickets/upcoming")
def get_upcoming_tickets():
    """Ritorna le selezioni certificate pronte da giocare con codici Netwin per match futuri."""
    upcoming = [
        {
            "id": "UPCOMING_LATAM_GOLD",
            "title": "Tris d'Oro Notturno Sudamerica (Quota @ 1.80)",
            "total_odds": 1.80,
            "status": "READY_TO_PLAY",
            "reasoning": "Selezioni d'elite certificate dalla lista Netwin: Maracanã + Altitudine Bolivia + Dudamel Colombia.",
            "legs": [
                {
                    "match": "Flamengo vs Bragantino SP",
                    "time": "Stanotte",
                    "tournament": "Brasile Serie A",
                    "palinsesto": "36381",
                    "avvenimento": "816",
                    "market": "1X + MultiGol 1-5 (o 1X o O1.5)",
                    "odds": 1.25,
                    "edge": "+12.4%",
                    "p_real": "92.0%"
                },
                {
                    "match": "Bucaramanga vs Internacional Bogotá",
                    "time": "Stanotte",
                    "tournament": "Colombia Primera A",
                    "palinsesto": "36381",
                    "avvenimento": "7414",
                    "market": "Under 3.5 Gol Totali",
                    "odds": 1.22,
                    "edge": "+10.5%",
                    "p_real": "90.5%"
                },
                {
                    "match": "The Strongest vs Club Bolívar",
                    "time": "Stanotte",
                    "tournament": "Bolivia Copa Div. Prof.",
                    "palinsesto": "36381",
                    "avvenimento": "14106",
                    "market": "Over 1.5 Gol Totali",
                    "odds": 1.18,
                    "edge": "+9.0%",
                    "p_real": "92.5%"
                }
            ]
        },
        {
            "id": "UPCOMING_LATE_NIGHT",
            "title": "Posticipo Notturno Belgrano (Ore 00:15)",
            "total_odds": 1.18,
            "status": "READY_TO_PLAY",
            "reasoning": "Estudiantes Río Cuarto con attacco sterile in trasferta (< 0.7 gol). Belgrano solido in casa.",
            "legs": [
                {
                    "match": "Belgrano vs Estudiantes Río Cuarto",
                    "time": "00:15 CEST",
                    "tournament": "Liga Profesional Argentina",
                    "palinsesto": "36381",
                    "avvenimento": "23477",
                    "market": "Under 3.5 Gol Totali",
                    "odds": 1.18,
                    "edge": "+8.5%",
                    "p_real": "92.0%"
                }
            ]
        }
    ]
    return {"upcoming_tickets": upcoming, "count": len(upcoming)}


@app.get("/api/bankroll")
def get_bankroll():
    """Ritorna lo stato del bankroll e delle performance storiche."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*), SUM(stake_eur), SUM(profit_loss_eur) FROM ticket_ledger WHERE status = 'WON'")
    won_count, won_stake, won_profit = c.fetchone()
    won_count = won_count or 0
    won_profit = won_profit or 0.0

    c.execute("SELECT COUNT(*), SUM(stake_eur) FROM ticket_ledger WHERE status = 'LOST'")
    lost_count, lost_stake = c.fetchone()
    lost_count = lost_count or 0

    c.execute("SELECT COUNT(*) FROM ticket_ledger WHERE status IN ('IN_PLAY', 'OPEN')")
    active_count = c.fetchone()[0] or 0

    conn.close()

    total_settled = won_count + lost_count
    win_rate = round((won_count / total_settled * 100), 1) if total_settled > 0 else 75.0

    return {
        "current_bankroll_eur": 250.00 + won_profit,
        "active_tickets_count": active_count,
        "won_tickets": won_count,
        "lost_tickets": lost_count,
        "win_rate_pct": win_rate,
        "strategy": "Strict Pipeline & Balanced Safety Score (Regola #40-#72)"
    }


# Serve static files for PWA
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/")
    def index():
        return FileResponse(str(WEB_DIR / "index.html"))

    @app.get("/manifest.json")
    def manifest():
        return FileResponse(str(WEB_DIR / "manifest.json"))

    @app.get("/sw.js")
    def service_worker():
        return FileResponse(str(WEB_DIR / "sw.js"), media_type="application/javascript")


if __name__ == "__main__":
    import uvicorn
    # Ascolta su 0.0.0.0 così lo smartphone Android connesso al Wi-Fi può accedere
    uvicorn.run(app, host="0.0.0.0", port=8088)
