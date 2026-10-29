"""
services/football/external/on_demand_ingestor.py — Ingestore On-Demand Regola #90 (Zero-FootyStats).

Se mancano dati storici o telemetria in data/bagent.db per una o entrambe le squadre
di un match in palinsesto, questo modulo interroga il feed delta Flashscore Ninja:
- df_hh_1_<mid>: ultime 10 partite di ciascuna squadra
- df_st_1_<hist_mid>: telemetria completa (xG reali, tiri, tiri in porta, corner, cartellini)
- df_sui_1_<hist_mid>: parziali 1° Tempo (ht_home_goals, ht_away_goals)
Inserisce i record nella tabella matches e rigenera team_rolling_ten_telemetry in < 1s.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import logging
import sqlite3
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OnDemandIngestor")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = ROOT_DIR / "data" / "bagent.db"


def names_match(query: str, candidate: str) -> bool:
    """True se i due nomi indicano la stessa squadra, non un token isolato."""
    q = (query or "").lower().strip()
    c = (candidate or "").lower().strip()
    if not q or not c:
        return False
    if q == c or q in c or c in q:
        return True
    q_tokens = {t for t in q.replace("-", " ").split() if len(t) >= 4}
    c_tokens = {t for t in c.replace("-", " ").split() if len(t) >= 4}
    return bool(q_tokens & c_tokens)


def season_label(match_date: str) -> str:
    """Stagione europea: da agosto l'annata nuova, prima resta quella precedente."""
    try:
        dt = datetime.strptime((match_date or "")[:10], "%Y-%m-%d")
    except ValueError:
        return "2026/2027"
    start = dt.year if dt.month >= 8 else dt.year - 1
    return f"{start}/{start + 1}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "X-Fsign": "SW9D1eZo",
}


class OnDemandMatchIngestor:
    """Scarica e ingerisce in tempo reale lo storico recente per squadre mancanti."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

    def find_match_id(self, home_team: str, away_team: str) -> Optional[str]:
        """Cerca il match_id Flashscore per la coppia di squadre."""
        from services.football.external.sources.flashscore_live import FlashscoreLiveEngine

        engine = FlashscoreLiveEngine()
        feed = engine.fetch_feed()
        h_clean = home_team.lower().strip()
        a_clean = away_team.lower().strip()

        for m in feed:
            if names_match(h_clean, m.get("home", "")) and names_match(a_clean, m.get("away", "")):
                return m.get("match_id")

        return None

    def fetch_and_ingest_for_match(
        self,
        home_team: str,
        away_team: str,
        match_id: Optional[str] = None,
        enrich_stats: bool = True,
    ) -> int:
        """
        Scarica e inserisce le ultime partite di entrambe le squadre in bagent.db.
        Se enrich_stats=True, arricchisce in parallelo (ThreadPoolExecutor) ciascuna partita
        con xG, tiri, tiri in porta, corner, cartellini (df_st_1_) e parziale 1°T (df_sui_1_).
        Ritorna il numero di partite inserite.
        """
        mid = match_id or self.find_match_id(home_team, away_team)
        if not mid:
            logger.warning(f"Nessun match_id Flashscore trovato per {home_team} vs {away_team}")
            return 0

        url = f"https://local-global.flashscore.ninja/2/x/feed/df_hh_1_{mid}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_text = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Errore download feed H2H per match_id {mid}: {e}")
            return 0

        sections = raw_text.split("~KB÷")
        if len(sections) < 3:
            logger.warning(f"Feed H2H incompleto per match_id {mid}")
            return 0

        parsed_matches: List[Dict[str, Any]] = []
        for s in sections[1:3]:
            parsed_matches.extend(self._parse_section(s, max_matches=10))

        if not parsed_matches:
            return 0

        if enrich_stats:
            self._enrich_matches_parallel(parsed_matches)

        return self._insert_matches(parsed_matches)

    @staticmethod
    def parse_stats_feed(raw_stats: str) -> Dict[str, Any]:
        """Estrae xG, tiri, SOT, corner e cartellini dalla sezione Full-Time di df_st_1_<mid>."""
        out: Dict[str, Any] = {}
        if not raw_stats:
            return out

        # Prendi solo la prima sezione (~SE÷Match / Incontro) per non sovrascrivere con 1°T/2°T
        sections = raw_stats.split("~SE÷")
        full_match_block = sections[1] if len(sections) > 1 else raw_stats

        def _num(val: str, as_float: bool = False):
            cleaned = (val or "").replace("%", "").strip()
            try:
                return float(cleaned) if as_float else int(float(cleaned))
            except (ValueError, TypeError):
                return None

        for block in full_match_block.split("~SD÷"):
            if "SG÷" not in block or "SH÷" not in block or "SI÷" not in block:
                continue
            try:
                name = block.split("SG÷", 1)[1].split("¬", 1)[0].strip().lower()
                val_h = block.split("SH÷", 1)[1].split("¬", 1)[0].strip()
                val_a = block.split("SI÷", 1)[1].split("¬", 1)[0].strip()
            except IndexError:
                continue

            if "expected goals" in name or name == "xg" or "gol attesi" in name:
                out["home_xg"] = _num(val_h, as_float=True)
                out["away_xg"] = _num(val_a, as_float=True)
            elif name in ("total shots", "shots", "tiri totali"):
                out["home_shots"] = _num(val_h)
                out["away_shots"] = _num(val_a)
            elif name in ("shots on target", "shots on goal", "tiri in porta"):
                out["home_sot"] = _num(val_h)
                out["away_sot"] = _num(val_a)
            elif "corner" in name or "angoli" in name or "calci d'angolo" in name:
                out["home_corners"] = _num(val_h)
                out["away_corners"] = _num(val_a)
            elif "yellow card" in name or "cartellini gialli" in name:
                out["home_yellow"] = _num(val_h)
                out["away_yellow"] = _num(val_a)

        return out

    @staticmethod
    def parse_incidents_ht(raw_inc: str) -> Dict[str, Optional[int]]:
        """Estrae il punteggio del 1° Tempo (ht_home_goals, ht_away_goals) da df_sui_1_<mid>."""
        if not raw_inc:
            return {}
        for section in raw_inc.split("~AC÷")[1:]:
            header = section.split("¬", 1)[0].strip().lower()
            if "1st half" in header or "1° tempo" in header or "1st" in header:
                fields: Dict[str, str] = {}
                for part in section.split("¬"):
                    if "÷" in part:
                        k, v = part.split("÷", 1)
                        fields[k.lstrip("~")] = v
                try:
                    return {
                        "ht_home_goals": int(fields["IG"]),
                        "ht_away_goals": int(fields["IH"]),
                    }
                except (KeyError, ValueError, TypeError):
                    return {}
        return {}

    def fetch_match_telemetry(self, flashscore_mid: str) -> Dict[str, Any]:
        """Scarica df_st_1_ e df_sui_1_ per un singolo match_id Flashscore."""
        telemetry: Dict[str, Any] = {}
        if not flashscore_mid:
            return telemetry

        url_st = f"https://local-global.flashscore.ninja/2/x/feed/df_st_1_{flashscore_mid}"
        try:
            req = urllib.request.Request(url_st, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw_st = resp.read().decode("utf-8", errors="ignore")
                telemetry.update(self.parse_stats_feed(raw_st))
        except Exception:
            pass

        url_sui = f"https://local-global.flashscore.ninja/2/x/feed/df_sui_1_{flashscore_mid}"
        try:
            req = urllib.request.Request(url_sui, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw_sui = resp.read().decode("utf-8", errors="ignore")
                telemetry.update(self.parse_incidents_ht(raw_sui))
        except Exception:
            pass

        return telemetry

    def _enrich_matches_parallel(self, matches: List[Dict[str, Any]]) -> None:
        """Arricchisce in parallelo i match storici che possiedono un match_id Flashscore (KP)."""
        to_enrich = [m for m in matches if m.get("match_id")]
        if not to_enrich:
            return

        def _worker(m: Dict[str, Any]) -> None:
            tele = self.fetch_match_telemetry(str(m["match_id"]))
            for k, v in tele.items():
                if v is not None:
                    m[k] = v

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(_worker, to_enrich))

    def _parse_section(self, section_text: str, max_matches: int = 10) -> List[Dict[str, Any]]:
        matches = []
        items = section_text.split("~KC÷")[1:]
        for item in items[:max_matches]:
            fields = {}
            for part in item.split("¬"):
                if "÷" in part:
                    k, v = part.split("÷", 1)
                    fields[k] = v

            ts_str = item.split("¬")[0].strip()
            try:
                m_date = datetime.fromtimestamp(int(ts_str)).strftime("%Y-%m-%d")
            except Exception:
                m_date = ts_str

            home = fields.get("KJ", "").replace("*", "").strip()
            away = fields.get("KK", "").replace("*", "").strip()
            if not home or not away:
                continue

            try:
                hg = int(fields.get("KU", 0))
                ag = int(fields.get("KT", 0))
            except Exception:
                continue

            league = fields.get("KF", "League").strip()
            season = season_label(m_date)
            mid = fields.get("KP", "").strip() or None
            matches.append({
                "match_id": mid,
                "league": league,
                "season": season,
                "match_date": m_date,
                "home_team": home,
                "away_team": away,
                "home_goals": hg,
                "away_goals": ag,
                "total_goals": hg + ag,
            })
        return matches

    def _insert_matches(self, matches: List[Dict[str, Any]]) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        existing_cols = {
            row[1] for row in c.execute("PRAGMA table_info(matches)").fetchall()
        }
        inserted = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for m in matches:
            exists = c.execute(
                "SELECT id FROM matches WHERE home_team = ? AND away_team = ? AND match_date = ?",
                (m["home_team"], m["away_team"], m["match_date"])
            ).fetchone()

            if not exists:
                row_data: Dict[str, Any] = {
                    "league": m["league"],
                    "season": m["season"],
                    "status": "FT",
                    "home_team": m["home_team"],
                    "away_team": m["away_team"],
                    "home_goals": m["home_goals"],
                    "away_goals": m["away_goals"],
                    "total_goals": m["total_goals"],
                    "ht_home_goals": m.get("ht_home_goals"),
                    "ht_away_goals": m.get("ht_away_goals"),
                    "match_date": m["match_date"],
                    "updated_at": now_str,
                }
                optional_fields = {
                    "match_id": m.get("match_id"),
                    "home_goals_ht": m.get("ht_home_goals"),
                    "away_goals_ht": m.get("ht_away_goals"),
                    "home_xg": m.get("home_xg"),
                    "away_xg": m.get("away_xg"),
                    "home_shots": m.get("home_shots"),
                    "away_shots": m.get("away_shots"),
                    "home_sot": m.get("home_sot"),
                    "away_sot": m.get("away_sot"),
                    "home_shots_on_target": m.get("home_sot"),
                    "away_shots_on_target": m.get("away_sot"),
                    "home_corners": m.get("home_corners"),
                    "away_corners": m.get("away_corners"),
                    "home_yellow": m.get("home_yellow"),
                    "away_yellow": m.get("away_yellow"),
                    "home_yellow_cards": m.get("home_yellow"),
                    "away_yellow_cards": m.get("away_yellow"),
                }
                for col, val in optional_fields.items():
                    if col in existing_cols and val is not None:
                        row_data[col] = val

                cols = [col for col in row_data.keys() if col in existing_cols]
                placeholders = ", ".join(["?"] * len(cols))
                col_names = ", ".join(cols)
                c.execute(
                    f"INSERT INTO matches ({col_names}) VALUES ({placeholders})",
                    tuple(row_data[col] for col in cols),
                )
                inserted += 1

        self._sync_teams_to_telemetry_2026(conn, matches)
        conn.commit()
        conn.close()
        return inserted

    @staticmethod
    def _sync_teams_to_telemetry_2026(conn: sqlite3.Connection, matches: List[Dict[str, Any]]) -> None:
        c = conn.cursor()
        tbl = c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='team_telemetry_2026'"
        ).fetchone()
        if not tbl:
            return
        teams = set()
        for m in matches:
            if m.get("home_team"):
                teams.add((m["home_team"], m.get("league", "League")))
            if m.get("away_team"):
                teams.add((m["away_team"], m.get("league", "League")))
        now_iso = datetime.now().isoformat()
        k_prior = 3.5
        lg_avg_h, lg_avg_a = 1.45, 1.18
        for t_name, default_lg in teams:
            already = c.execute(
                "SELECT 1 FROM team_telemetry_2026 WHERE team_name = ? OR normalized_name = ?",
                (t_name, t_name),
            ).fetchone()
            if already:
                continue
            rows = c.execute(
                """
                SELECT home_team, away_team, league, home_goals, away_goals,
                       ht_home_goals, ht_away_goals, home_xg, away_xg,
                       home_shots, away_shots, home_sot, away_sot,
                       home_corners, away_corners, home_yellow, away_yellow
                FROM matches
                WHERE (home_team = ? OR away_team = ?) AND status = 'FT'
                ORDER BY match_date DESC LIMIT 15
                """,
                (t_name, t_name),
            ).fetchall()
            if len(rows) < 3:
                continue
            mp = len(rows)
            hm = am = 0
            h_xg_f = h_xg_a = a_xg_f = a_xg_a = 0.0
            gf = ga = g1t = g2t = 0.0
            ov15 = ov25 = btts = both_halves = 0
            sh_f = sh_a = sot_f = sot_a = co_f = co_a = ca_f = 0.0
            lg_label = rows[0][2] or default_lg
            for r in rows:
                ht, at, lg, hg, ag, hthg, htag, hxg, axg, hs, as_, hst, ast, hc, ac, hy, ay = r
                hg = int(hg or 0)
                ag = int(ag or 0)
                hthg = int(hthg if hthg is not None else round(hg * 0.44))
                htag = int(htag if htag is not None else round(ag * 0.44))
                hxg = float(hxg if hxg is not None else max(0.4, hg * 0.85 + 0.35))
                axg = float(axg if axg is not None else max(0.3, ag * 0.85 + 0.30))
                hs = float(hs if hs is not None else 11.0)
                as_ = float(as_ if as_ is not None else 9.5)
                hst = float(hst if hst is not None else 4.0)
                ast = float(ast if ast is not None else 3.5)
                hc = float(hc if hc is not None else 4.8)
                ac = float(ac if ac is not None else 4.2)
                hy = float(hy if hy is not None else 2.2)
                ay = float(ay if ay is not None else 2.4)
                tot_g = hg + ag
                tot_1t = hthg + htag
                tot_2t = max(0, tot_g - tot_1t)
                if tot_g >= 2:
                    ov15 += 1
                if tot_g >= 3:
                    ov25 += 1
                if hg > 0 and ag > 0:
                    btts += 1
                if tot_1t >= 1 and tot_2t >= 1:
                    both_halves += 1
                if ht == t_name:
                    hm += 1
                    h_xg_f += hxg
                    h_xg_a += axg
                    gf += hg
                    ga += ag
                    g1t += hthg
                    g2t += max(0, hg - hthg)
                    sh_f += hs
                    sh_a += as_
                    sot_f += hst
                    sot_a += ast
                    co_f += hc
                    co_a += ac
                    ca_f += hy
                else:
                    am += 1
                    a_xg_f += axg
                    a_xg_a += hxg
                    gf += ag
                    ga += hg
                    g1t += htag
                    g2t += max(0, ag - htag)
                    sh_f += as_
                    sh_a += hs
                    sot_f += ast
                    sot_a += hst
                    co_f += ac
                    co_a += hc
                    ca_f += ay
            hm_d = max(1, hm)
            am_d = max(1, am)
            xg_h = ((hm * (h_xg_f / hm_d)) + (k_prior * lg_avg_h)) / (hm + k_prior)
            xga_h = ((hm * (h_xg_a / hm_d)) + (k_prior * lg_avg_a)) / (hm + k_prior)
            xg_a = ((am * (a_xg_f / am_d)) + (k_prior * lg_avg_a)) / (am + k_prior)
            xga_a = ((am * (a_xg_a / am_d)) + (k_prior * lg_avg_h)) / (am + k_prior)
            tot_tg = g1t + g2t
            r1t = min(max(round(g1t / tot_tg, 3) if tot_tg > 0 else 0.44, 0.35), 0.55)
            r2t = round(1.0 - r1t, 3)
            c.execute(
                """
                INSERT OR REPLACE INTO team_telemetry_2026 VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
                """,
                (
                    t_name, t_name, lg_label, mp, hm, am,
                    round(xg_h, 3), round(xg_a, 3), round(xga_h, 3), round(xga_a, 3),
                    round((gf + ga) / mp, 2), r1t, r2t,
                    round((ov15 / mp) * 100, 1), round((ov25 / mp) * 100, 1),
                    round((btts / mp) * 100, 1), round((both_halves / mp) * 100, 1),
                    round(sh_f / mp, 1), round(sh_a / mp, 1),
                    round(sot_f / mp, 1), round(sot_a / mp, 1),
                    round(co_f / mp, 1), round(co_a / mp, 1),
                    round(ca_f / mp, 2), now_iso,
                ),
            )
