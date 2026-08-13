"""
db_updater.py — Aggiornamento automatico DB da API-Football.

Scarica fixtures, standings, team stats da API-Football e aggiorna
bagent.db senza CSV manuali. Gestione intelligente della quota:
  - Tier 1 (quotidiano): leghe top + coppe europee/sudamericane
  - Tier 2 (trisettimanale): leghe secondarie
  - Tier 3 (settimanale): campionati minori
  - "smart" mode: aggiorna solo le leghe con partite nei prossimi 3 giorni

Utilizzo:
    python scripts/db_updater.py                    # tier 1 (default)
    python scripts/db_updater.py --tier 2           # tier 1+2
    python scripts/db_updater.py --tier all         # tutte le leghe
    python scripts/db_updater.py --smart            # solo leghe con partite imminenti
    python scripts/db_updater.py --league 88 71     # leghe specifiche
    python scripts/db_updater.py --discover         # scopre tutte le leghe API e le mostra
    python scripts/db_updater.py --quota            # controlla quota rimanente
    python scripts/db_updater.py --list-leagues     # lista leghe configurate
    python scripts/db_updater.py --dry-run          # simula senza salvare

Costo API per tier (piano FREE = 100 req/giorno):
    Tier 1 (30 leghe):  ~60 req   — giornaliero OK
    Tier 1+2 (55 leghe): ~110 req — quasi al limite
    Tier all (85 leghe): ~170 req — richiede piano a pagamento
"""

from __future__ import annotations

import argparse
import os
import sys
import sqlite3
import time
from datetime import datetime, date, timedelta
from pathlib import Path

# ── path setup ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

def _load_env():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() and v.strip() and k.strip() not in os.environ:
            os.environ[k.strip()] = v.strip()

_load_env()

from services.football.external.collector import FootballExternalCollector

# ══════════════════════════════════════════════════════════════════════════════
# LEGHE CONFIGURATE (85 leghe)
# Formato: league_id → (nome_db, stagione, paese, tier)
# Tier 1 = quotidiano, Tier 2 = trisettimanale, Tier 3 = settimanale
# ══════════════════════════════════════════════════════════════════════════════
LEAGUES: dict[int, tuple[str, str, str, int]] = {

    # ── COPPE EUROPEE (Tier 1) ──────────────────────────────────────────────
    2:   ("Champions League",      "2026/2027", "Europe",        1),
    3:   ("Europa League",         "2026/2027", "Europe",        1),
    848: ("Conference League",     "2026/2027", "Europe",        1),

    # ── COPPE SUDAMERICANE (Tier 1) ─────────────────────────────────────────
    13:  ("Copa Libertadores",     "2026",      "South America", 1),
    11:  ("Copa Sudamericana",     "2026",      "South America", 1),

    # ── ITALIA (Tier 1) ─────────────────────────────────────────────────────
    135: ("Serie A",               "2026",      "Italy",         1),
    136: ("Serie B",               "2026",      "Italy",         1),
    547: ("Coppa Italia",          "2026",      "Italy",         1),

    # ── SPAGNA (Tier 1) ─────────────────────────────────────────────────────
    140: ("La Liga",               "2026",      "Spain",         1),
    141: ("La Liga 2",             "2026",      "Spain",         1),
    143: ("Copa del Rey",          "2026",      "Spain",         1),

    # ── INGHILTERRA (Tier 1) ────────────────────────────────────────────────
    39:  ("Premier League",        "2026",      "England",       1),
    40:  ("Championship",          "2026",      "England",       1),
    48:  ("Carabao Cup",           "2026",      "England",       1),

    # ── GERMANIA (Tier 1) ───────────────────────────────────────────────────
    78:  ("Bundesliga",            "2026",      "Germany",       1),
    79:  ("2. Bundesliga",         "2026",      "Germany",       1),

    # ── FRANCIA (Tier 1) ────────────────────────────────────────────────────
    61:  ("Ligue 1",               "2026",      "France",        1),
    62:  ("Ligue 2",               "2026",      "France",        1),

    # ── PORTOGALLO (Tier 1) ─────────────────────────────────────────────────
    94:  ("Primeira Liga",         "2026",      "Portugal",      1),
    95:  ("Liga Portugal 2",       "2026",      "Portugal",      1),

    # ── OLANDA (Tier 1) ─────────────────────────────────────────────────────
    88:  ("Eredivisie",            "2026/2027", "Netherlands",   1),
    89:  ("Eerste Divisie",        "2026/2027", "Netherlands",   1),

    # ── BRASILE (Tier 1) ────────────────────────────────────────────────────
    71:  ("Brazil Serie A",        "2026",      "Brazil",        1),
    72:  ("Brazil Serie B",        "2026",      "Brazil",        1),

    # ── ARGENTINA (Tier 1) ──────────────────────────────────────────────────
    128: ("Primera Division ARG",  "2026",      "Argentina",     1),

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — trisettimanale
    # ══════════════════════════════════════════════════════════════════════════

    # ── BELGIO ──────────────────────────────────────────────────────────────
    144: ("Jupiler Pro League",    "2026/2027", "Belgium",       2),

    # ── TURCHIA ─────────────────────────────────────────────────────────────
    203: ("Super Lig",             "2026",      "Turkey",        2),

    # ── GRECIA ──────────────────────────────────────────────────────────────
    197: ("Super League Greece",   "2026",      "Greece",        2),

    # ── SCOZIA ──────────────────────────────────────────────────────────────
    179: ("Scottish Premiership",  "2026",      "Scotland",      2),

    # ── SVIZZERA ────────────────────────────────────────────────────────────
    207: ("Swiss Super League",    "2026",      "Switzerland",   2),

    # ── AUSTRIA ─────────────────────────────────────────────────────────────
    218: ("Austrian Bundesliga",   "2026/2027", "Austria",       2),

    # ── POLONIA ─────────────────────────────────────────────────────────────
    106: ("Ekstraklasa",           "2026",      "Poland",        2),

    # ── DANIMARCA ───────────────────────────────────────────────────────────
    119: ("Superliga DEN",         "2026",      "Denmark",       2),

    # ── SVEZIA ──────────────────────────────────────────────────────────────
    113: ("Allsvenskan",           "2026",      "Sweden",        2),

    # ── NORVEGIA ────────────────────────────────────────────────────────────
    103: ("Eliteserien",           "2026",      "Norway",        2),

    # ── REP. CECA ───────────────────────────────────────────────────────────
    345: ("Czech First League",    "2026",      "Czech Republic",2),

    # ── SERBIA ──────────────────────────────────────────────────────────────
    286: ("Serbian SuperLiga",     "2026",      "Serbia",        2),

    # ── CROAZIA ─────────────────────────────────────────────────────────────
    210: ("Croatian HNL",          "2026",      "Croatia",       2),

    # ── ROMANIA ─────────────────────────────────────────────────────────────
    283: ("Liga 1 ROU",            "2026",      "Romania",       2),

    # ── UCRAINA ─────────────────────────────────────────────────────────────
    333: ("Ukrainian Premier",     "2026",      "Ukraine",       2),

    # ── RUSSIA ──────────────────────────────────────────────────────────────
    235: ("Russian Premier",       "2026",      "Russia",        2),

    # ── MESSICO ─────────────────────────────────────────────────────────────
    262: ("Liga MX",               "2026",      "Mexico",        2),

    # ── USA ─────────────────────────────────────────────────────────────────
    253: ("MLS",                   "2026",      "USA",           2),

    # ── COLOMBIA ────────────────────────────────────────────────────────────
    239: ("Liga BetPlay",          "2026",      "Colombia",      2),

    # ── CILE ────────────────────────────────────────────────────────────────
    265: ("Primera Division CHI",  "2026",      "Chile",         2),

    # ── ECUADOR ─────────────────────────────────────────────────────────────
    269: ("Liga Pro ECU",          "2026",      "Ecuador",       2),

    # ── PERU ────────────────────────────────────────────────────────────────
    281: ("Liga 1 PER",            "2026",      "Peru",          2),

    # ── URUGUAY ─────────────────────────────────────────────────────────────
    268: ("Primera Division URU",  "2026",      "Uruguay",       2),

    # ── GIAPPONE ────────────────────────────────────────────────────────────
    98:  ("J1 League",             "2026",      "Japan",         2),

    # ── COREA DEL SUD ───────────────────────────────────────────────────────
    292: ("K League 1",            "2026",      "South Korea",   2),

    # ── ARABIA SAUDITA ──────────────────────────────────────────────────────
    307: ("Saudi Pro League",      "2026",      "Saudi Arabia",  2),

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 3 — settimanale
    # ══════════════════════════════════════════════════════════════════════════

    # ── INGHILTERRA INFERIORE ───────────────────────────────────────────────
    41:  ("League One ENG",        "2026",      "England",       3),
    42:  ("League Two ENG",        "2026",      "England",       3),
    45:  ("FA Cup",                "2026",      "England",       3),

    # ── ITALIA INFERIORE ────────────────────────────────────────────────────
    140: ("Serie C",               "2026",      "Italy",         3),  # placeholder
    548: ("Supercoppa Italiana",   "2026",      "Italy",         3),

    # ── SPAGNA INFERIORE ────────────────────────────────────────────────────
    142: ("Segunda Division B",    "2026",      "Spain",         3),

    # ── GERMANIA INFERIORE ──────────────────────────────────────────────────
    80:  ("3. Liga",               "2026",      "Germany",       3),
    81:  ("DFB-Pokal",             "2026",      "Germany",       3),

    # ── FRANCIA INFERIORE ───────────────────────────────────────────────────
    63:  ("National FRA",          "2026",      "France",        3),
    65:  ("Coupe de France",       "2026",      "France",        3),

    # ── ISRAELE ─────────────────────────────────────────────────────────────
    384: ("Israeli Premier",       "2026/2027", "Israel",        3),

    # ── ARMENIA ─────────────────────────────────────────────────────────────
    383: ("Armenian First League", "2026",      "Armenia",       3),

    # ── FINLANDIA ───────────────────────────────────────────────────────────
    244: ("Veikkausliiga",         "2026",      "Finland",       3),

    # ── UNGHERIA ────────────────────────────────────────────────────────────
    271: ("OTP Bank Liga",         "2026",      "Hungary",       3),

    # ── SLOVACCHIA ──────────────────────────────────────────────────────────
    332: ("Slovak Super Liga",     "2026",      "Slovakia",      3),

    # ── BIELORUSSIA ─────────────────────────────────────────────────────────
    322: ("Belarusian Premier",    "2026",      "Belarus",       3),

    # ── KAZAKISTAN ──────────────────────────────────────────────────────────
    338: ("Kazakhstan Premier",    "2026",      "Kazakhstan",    3),

    # ── UZBEKISTAN ──────────────────────────────────────────────────────────
    337: ("Uzbekistan Super",      "2026",      "Uzbekistan",    3),

    # ── AUSTRALIA ───────────────────────────────────────────────────────────
    188: ("A-League",              "2026",      "Australia",     3),

    # ── CINA ────────────────────────────────────────────────────────────────
    169: ("Chinese Super League",  "2026",      "China",         3),

    # ── INDIA ───────────────────────────────────────────────────────────────
    323: ("Indian Super League",   "2026",      "India",         3),

    # ── SUDAFRICA ───────────────────────────────────────────────────────────
    288: ("South African PSL",     "2026",      "South Africa",  3),

    # ── MAROCCO ─────────────────────────────────────────────────────────────
    200: ("Botola Pro",            "2026",      "Morocco",       3),

    # ── CANADA ──────────────────────────────────────────────────────────────
    250: ("Canadian Premier",      "2026",      "Canada",        3),

    # ── PARAGUAY ────────────────────────────────────────────────────────────
    270: ("Apertura PAR",          "2026",      "Paraguay",      3),

    # ── VENEZUELA ───────────────────────────────────────────────────────────
    262: ("Liga Futve",            "2026",      "Venezuela",     3),

    # ── CONCACAF Champions ──────────────────────────────────────────────────
    26:  ("CONCACAF Champions",    "2026",      "CONCACAF",      3),

    # ── CAF Champions League ────────────────────────────────────────────────
    20:  ("CAF Champions League",  "2026",      "Africa",        3),

    # ── AFC Champions League ────────────────────────────────────────────────
    17:  ("AFC Champions League",  "2026",      "Asia",          3),
}

# Rimuovi duplicati per league_id (prende il primo in caso di conflitto)
_seen_ids: set[int] = set()
_cleaned: dict[int, tuple] = {}
for _lid, _val in LEAGUES.items():
    if _lid not in _seen_ids:
        _seen_ids.add(_lid)
        _cleaned[_lid] = _val
LEAGUES = _cleaned

# ── DB helpers ─────────────────────────────────────────────────────────────────
DB_PATH = ROOT / "data" / "bagent.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def safe(v):
    if v in ("", "N/A", "None", None): return None
    try: return float(v)
    except (TypeError, ValueError): return v

# ── Upsert ─────────────────────────────────────────────────────────────────────
def upsert_league(conn, league_id, data):
    name, season, country, tier = LEAGUES[league_id]
    conn.execute("""
        INSERT INTO leagues (name, season, country, avg_goals_per_match, matches_completed)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name, season) DO UPDATE SET
            avg_goals_per_match = excluded.avg_goals_per_match,
            matches_completed   = excluded.matches_completed
    """, (name, season, country,
          safe(data.get("avg_goals")),
          safe(data.get("matches_played"))))

def upsert_fixture(conn, f, league_name, season):
    fix   = f.get("fixture", {})
    teams = f.get("teams", {})
    goals = f.get("goals", {})
    score = f.get("score", {})

    home_team = teams.get("home", {}).get("name", "")
    away_team = teams.get("away", {}).get("name", "")
    dt = fix.get("date", "")
    date_gmt = dt[:10] if dt else None
    hg = goals.get("home"); ag = goals.get("away")
    total = (hg or 0) + (ag or 0) if hg is not None else None
    ht = score.get("halftime", {})

    conn.execute("""
        INSERT INTO matches (league, season, date_gmt, timestamp, status,
                             home_team, away_team,
                             home_goals, away_goals, home_goals_ht, away_goals_ht,
                             total_goals, referee)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(league, season, home_team, away_team, date_gmt) DO UPDATE SET
            status        = excluded.status,
            home_goals    = COALESCE(excluded.home_goals,    matches.home_goals),
            away_goals    = COALESCE(excluded.away_goals,    matches.away_goals),
            home_goals_ht = COALESCE(excluded.home_goals_ht, matches.home_goals_ht),
            away_goals_ht = COALESCE(excluded.away_goals_ht, matches.away_goals_ht),
            total_goals   = COALESCE(excluded.total_goals,   matches.total_goals)
    """, (league_name, season, date_gmt, fix.get("timestamp"),
          fix.get("status", {}).get("short", "NS"),
          home_team, away_team, hg, ag,
          ht.get("home"), ht.get("away"), total,
          fix.get("referee")))

def upsert_team_stats(conn, stats, league_name, season, country):
    tname = stats.get("team_name", "")
    if not tname: return
    mp   = stats.get("matches_played") or 0
    gf   = stats.get("goals_scored") or 0
    ga   = stats.get("goals_conceded") or 0
    conn.execute("""
        INSERT INTO teams (team_name, common_name, league, season, country,
            matches_played, wins, draws, losses,
            goals_scored, goals_conceded,
            goals_scored_home, goals_conceded_home,
            goals_scored_away, goals_conceded_away,
            goals_scored_per_match, goals_conceded_per_match,
            win_pct, ppg)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(team_name, league, season) DO UPDATE SET
            matches_played       = excluded.matches_played,
            wins                 = excluded.wins,
            draws                = excluded.draws,
            losses               = excluded.losses,
            goals_scored         = excluded.goals_scored,
            goals_conceded       = excluded.goals_conceded,
            goals_scored_home    = excluded.goals_scored_home,
            goals_conceded_home  = excluded.goals_conceded_home,
            goals_scored_away    = excluded.goals_scored_away,
            goals_conceded_away  = excluded.goals_conceded_away,
            goals_scored_per_match  = excluded.goals_scored_per_match,
            goals_conceded_per_match= excluded.goals_conceded_per_match,
            win_pct = excluded.win_pct,
            ppg     = excluded.ppg
    """, (tname, stats.get("common_name", tname), league_name, season, country,
          mp,
          stats.get("wins"), stats.get("draws"), stats.get("losses"),
          gf, ga,
          stats.get("goals_scored_home"), stats.get("goals_conceded_home"),
          stats.get("goals_scored_away"), stats.get("goals_conceded_away"),
          round(gf/mp, 2) if mp else None,
          round(ga/mp, 2) if mp else None,
          stats.get("win_pct"), stats.get("ppg")))

# ── Fetch da API ────────────────────────────────────────────────────────────────
def fetch_standings(c, league_id, season) -> list[dict]:
    year = season[:4]
    try:
        raw = c._get("standings", {"league": league_id, "season": year})
    except Exception as e:
        print(f"    ⚠️  Standings error: {e}")
        return []
    results = []
    for block in raw.get("response", []):
        for group in block.get("league", {}).get("standings", []):
            for entry in group:
                team  = entry.get("team", {})
                all_s = entry.get("all", {})
                home_s = entry.get("home", {})
                away_s = entry.get("away", {})
                mp    = all_s.get("played", 0) or 0
                wins  = all_s.get("win", 0) or 0
                draws = all_s.get("draw", 0) or 0
                losses= all_s.get("lose", 0) or 0
                pts   = entry.get("points", 0) or 0
                gf    = (all_s.get("goals") or {}).get("for", 0) or 0
                ga    = (all_s.get("goals") or {}).get("against", 0) or 0
                results.append({
                    "team_name":   team.get("name", ""),
                    "common_name": team.get("name", ""),
                    "matches_played": mp, "wins": wins, "draws": draws, "losses": losses,
                    "goals_scored": gf, "goals_conceded": ga,
                    "goals_scored_home":   (home_s.get("goals") or {}).get("for", 0),
                    "goals_conceded_home": (home_s.get("goals") or {}).get("against", 0),
                    "goals_scored_away":   (away_s.get("goals") or {}).get("for", 0),
                    "goals_conceded_away": (away_s.get("goals") or {}).get("against", 0),
                    "ppg":     round(pts/mp, 2) if mp else 0,
                    "win_pct": round(wins/mp*100, 1) if mp else 0,
                })
    return results

def fetch_fixtures(c, league_id, season, from_date=None, to_date=None) -> list[dict]:
    year = season[:4]
    params = {"league": league_id, "season": year}
    if from_date: params["from"] = from_date
    if to_date:   params["to"]   = to_date
    try:
        raw = c._get("fixtures", params)
        return raw.get("response", [])
    except Exception as e:
        print(f"    ⚠️  Fixtures error: {e}")
        return []

def fetch_upcoming(c, league_id, season, days=3) -> bool:
    """Ritorna True se la lega ha partite nei prossimi `days` giorni."""
    today = date.today()
    end   = today + timedelta(days=days)
    fixtures = fetch_fixtures(c, league_id, season,
                              from_date=today.isoformat(),
                              to_date=end.isoformat())
    return len(fixtures) > 0

# ── Core: aggiorna singola lega ─────────────────────────────────────────────────
def update_league(c, conn, league_id, dry_run=False, from_date=None, to_date=None) -> dict:
    name, season, country, tier = LEAGUES[league_id]
    stats = {"fixtures": 0, "teams": 0}

    print(f"  [standings] {name}...", end=" ", flush=True)
    standings = fetch_standings(c, league_id, season)
    print(f"{len(standings)} squadre")

    if not dry_run and standings:
        upsert_league(conn, league_id, {
            "matches_played": sum(t.get("matches_played", 0) for t in standings) // 2
        })
        for t in standings:
            upsert_team_stats(conn, t, name, season, country)
            stats["teams"] += 1
        conn.commit()

    print(f"  [fixtures]  {name}...", end=" ", flush=True)
    fixtures = fetch_fixtures(c, league_id, season, from_date=from_date, to_date=to_date)
    print(f"{len(fixtures)} partite")

    if not dry_run and fixtures:
        for f in fixtures:
            upsert_fixture(conn, f, name, season)
            stats["fixtures"] += 1
        conn.commit()

    return stats

# ── CLI ─────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Aggiorna bagent.db da API-Football.")
    parser.add_argument("--league",   type=int, nargs="*")
    parser.add_argument("--tier",     type=str, default="1",
                        help="1, 2, 3, o 'all' (default: 1)")
    parser.add_argument("--smart",    action="store_true",
                        help="Aggiorna solo leghe con partite nei prossimi 3 giorni")
    parser.add_argument("--discover", action="store_true",
                        help="Mostra tutte le leghe disponibili su API-Football")
    parser.add_argument("--from-date", type=str, default=None)
    parser.add_argument("--to-date",   type=str, default=None)
    parser.add_argument("--dry-run",   action="store_true")
    parser.add_argument("--quota",     action="store_true")
    parser.add_argument("--list-leagues", action="store_true")
    args = parser.parse_args()

    if args.list_leagues:
        print(f"\n{'ID':>6}  {'Lega':<30} {'Stagione':<12} {'Paese':<18} Tier")
        print("─" * 80)
        for tier_n in [1, 2, 3]:
            rows = [(lid, n, s, c, t) for lid,(n,s,c,t) in sorted(LEAGUES.items()) if t==tier_n]
            if rows:
                print(f"\n── TIER {tier_n} ({'quotidiano' if tier_n==1 else 'trisettimanale' if tier_n==2 else 'settimanale'}) ──")
            for lid, n, s, c, t in rows:
                print(f"  {lid:>5}  {n:<30} {s:<12} {c:<18} {t}")
        print(f"\nTotale: {len(LEAGUES)} leghe")
        return

    c = FootballExternalCollector()

    if args.quota:
        try:
            status = c.quota_status()
            req = status.get("requests", {})
            sub = status.get("subscription", {})
            used  = int(req.get("current", 0))
            limit = int(req.get("limit_day", 100))
            print(f"\n  Piano:     {sub.get('plan', 'N/A')}")
            print(f"  Usate:     {used} / {limit}")
            print(f"  Restanti:  {limit - used}")
            tier1 = sum(1 for _,_,_,t in LEAGUES.values() if t==1)
            tier2 = sum(1 for _,_,_,t in LEAGUES.values() if t==2)
            print(f"\n  Costo stimato:")
            print(f"    Tier 1 ({tier1} leghe): ~{tier1*2} req")
            print(f"    Tier 1+2 ({tier1+tier2} leghe): ~{(tier1+tier2)*2} req")
            print(f"    Tutte ({len(LEAGUES)} leghe): ~{len(LEAGUES)*2} req")
        except Exception as e:
            print(f"Errore: {e}")
        return

    if args.discover:
        print("Ricerca leghe disponibili su API-Football...")
        try:
            raw = c._get("leagues", {"current": "true"})
            leagues = raw.get("response", [])
            print(f"\nTrovate {len(leagues)} leghe attive:\n")
            for l in sorted(leagues, key=lambda x: x.get("league",{}).get("name","")):
                lid  = l.get("league", {}).get("id")
                name = l.get("league", {}).get("name", "")
                ctry = l.get("country", {}).get("name", "")
                season = [s.get("year") for s in l.get("seasons",[]) if s.get("current")]
                print(f"  {lid:>6}  {name:<35} {ctry:<20} {season}")
        except Exception as e:
            print(f"Errore: {e}")
        return

    # Selezione leghe
    if args.league:
        target_ids = [lid for lid in args.league if lid in LEAGUES]
        unknown = [lid for lid in args.league if lid not in LEAGUES]
        if unknown:
            print(f"⚠️  ID non configurati: {unknown}. Usa --discover per vedere tutte le leghe.")
    else:
        max_tier = {"1": 1, "2": 2, "3": 3, "all": 99}.get(args.tier, 1)
        target_ids = [lid for lid,(n,s,c,t) in LEAGUES.items() if t <= max_tier]

    if not target_ids:
        print("Nessuna lega da aggiornare.")
        return

    # Smart mode: filtra solo leghe con partite imminenti
    if args.smart and not args.league:
        print(f"Smart mode: verifico partite nei prossimi 3 giorni su {len(target_ids)} leghe...")
        active = []
        for lid in target_ids:
            name, season, _, _ = LEAGUES[lid]
            has = fetch_upcoming(c, lid, season)
            status = "✅" if has else "⏭️ "
            print(f"  {status} {name}")
            if has:
                active.append(lid)
        target_ids = active
        print(f"\nLeghe attive: {len(target_ids)}")

    # Stima quota
    est_req = len(target_ids) * 2
    print(f"\n{'='*55}")
    print(f"  DB UPDATER — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Leghe da aggiornare: {len(target_ids)}")
    print(f"  Richieste stimate:   ~{est_req}")
    print(f"  Dry-run: {args.dry_run}")
    print(f"{'='*55}\n")

    conn = get_conn()
    totals = {"fixtures": 0, "teams": 0, "errors": 0}

    for i, league_id in enumerate(target_ids, 1):
        name, season, country, tier = LEAGUES[league_id]
        print(f"[{i}/{len(target_ids)}] {name} (T{tier})")
        try:
            res = update_league(c, conn, league_id, dry_run=args.dry_run,
                                from_date=args.from_date, to_date=args.to_date)
            totals["fixtures"] += res["fixtures"]
            totals["teams"]    += res["teams"]
        except Exception as e:
            print(f"  ❌ Errore: {e}")
            totals["errors"] += 1

    conn.close()
    print(f"\n{'='*55}")
    print(f"  COMPLETATO — {datetime.now().strftime('%H:%M')}")
    print(f"  Partite salvate: {totals['fixtures']}")
    print(f"  Squadre salvate: {totals['teams']}")
    print(f"  Errori:          {totals['errors']}")
    if not args.dry_run:
        print(f"  DB: {DB_PATH}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
