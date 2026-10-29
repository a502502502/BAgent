# -*- coding: utf-8 -*-
"""
services/football/external/sources/flashscore_live.py — Motore Live Feed in Tempo Reale.
Interroga direttamente il feed delta ad alta frequenza di Flashscore/Diretta.it
(local-it.flashscore.ninja), azzerando la latenza dei motori di ricerca.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import time
import urllib.request
import sys
from typing import Dict, List, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

class FlashscoreLiveEngine:
    FEED_URLS = [
        "https://local-it.flashscore.ninja/2/x/feed/f_1_0_1_it_1",
        "https://local-it.flashscore.ninja/2/x/feed/f_1_0_2_it_1",
        "https://local-it.flashscore.ninja/2/x/feed/f_1_0_3_it_1",
    ]
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "X-Fsign": "SW9D1eZo",
        "Accept": "*/*",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    STATUS_MAP = {
        "1": "Programmata",
        "2": "In Corso",
        "3": "Finale",
        "4": "Tempi Suppl.",
        "5": "Rigori",
        "6": "Posticipata",
        "7": "Cancellata",
        "8": "Sospesa",
        "9": "Interrotta",
        "10": "Abbandonata",
        "11": "Intervallo",
        "12": "1° Tempo",
        "13": "2° Tempo",
    }

    LIVE_STATUS = {"2", "4", "5", "11", "12", "13"}

    def fetch_feed(self) -> List[Dict[str, Any]]:
        """Recupera e decodifica tutti i match in corso e in programma da Flashscore."""
        text = ""
        for url in self.FEED_URLS:
            try:
                req = urllib.request.Request(url, headers=self.HEADERS)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    text = resp.read().decode("utf-8", errors="ignore")
                    if text and len(text) > 50000:
                        break
            except Exception:
                continue
        return self.parse_feed(text)

    def parse_feed(self, text: str) -> List[Dict[str, Any]]:
        """Decodifica un blocco del feed delta. Il testo vuoto restituisce una lista vuota."""
        if not text:
            return []
        matches = []
        current_league = ""
        for chunk in text.split("~"):
            if chunk.startswith("ZA÷"):
                for piece in chunk.split("¬"):
                    if piece.startswith("ZA÷"):
                        current_league = piece[3:].strip()
                        break
            elif chunk.startswith("AA÷"):
                block = chunk[3:]
                match_id, _, rest = block.partition("¬")
                fields: Dict[str, str] = {}
                for piece in rest.split("¬"):
                    if "÷" in piece:
                        key, value = piece.split("÷", 1)
                        fields[key] = value
                parsed = self._match_from_fields(match_id.strip(), fields, league=current_league)
                if parsed is not None:
                    matches.append(parsed)
        return matches

    def _match_from_fields(self, match_id: str, fields: Dict[str, str], league: str = "") -> Dict[str, Any] | None:
        home = fields.get("AE", "").strip()
        away = fields.get("AF", "").strip()
        if not home or not away:
            return None
        status_raw = fields.get("AB", "1")
        ac_raw = fields.get("AC", "")
        ao_raw = fields.get("AO", "")
        status_desc = self.STATUS_MAP.get(status_raw, f"Codice {status_raw}")
        period_val = ac_raw
        if status_raw == "2" and ao_raw.isdigit():
            now_ts = int(time.time())
            elapsed_min = max(1, (now_ts - int(ao_raw)) // 60 + 1)
            if ac_raw == "12":
                status_desc = "1° Tempo"
                period_val = str(min(45, elapsed_min))
            elif ac_raw in {"38", "11"}:
                status_desc = "Intervallo"
                period_val = "45"
            elif ac_raw == "13":
                status_desc = "2° Tempo"
                period_val = str(45 + min(49, elapsed_min))
            elif ac_raw in {"6", "4"}:
                status_desc = "Tempi Suppl."
                period_val = str(90 + min(30, elapsed_min))
        s_home = fields.get("AG", "")
        s_away = fields.get("AH", "")
        live = status_raw in self.LIVE_STATUS
        if s_home != "" or s_away != "":
            score_str = f"{s_home}-{s_away}"
        elif live:
            score_str = "0-0"
        else:
            score_str = "-"
        s2_home = fields.get("BC", "")
        s2_away = fields.get("BD", "")
        ba_val = fields.get("BA", "")
        bb_val = fields.get("BB", "")
        if ba_val != "" and bb_val != "":
            s1_home, s1_away = ba_val, bb_val
        elif s_home.isdigit() and s_away.isdigit() and s2_home.isdigit() and s2_away.isdigit():
            s1_home = str(max(0, int(s_home) - int(s2_home)))
            s1_away = str(max(0, int(s_away) - int(s2_away)))
        elif status_raw in {"11", "12"} and s_home.isdigit() and s_away.isdigit():
            s1_home, s1_away = s_home, s_away
        else:
            s1_home, s1_away = "", ""
        return {
            "match_id": match_id or fields.get("AA", ""),
            "league": league,
            "home": home,
            "away": away,
            "score": score_str,
            "home_score": s_home,
            "away_score": s_away,
            "status_code": status_raw,
            "status": status_desc,
            "period": period_val,
            "ht_score": f"{s1_home}-{s1_away}" if s1_home != "" else "",
            "ht_home": s1_home,
            "ht_away": s1_away,
            "s2_score": f"{s2_home}-{s2_away}" if s2_home != "" else "",
            "s2_home": s2_home,
            "s2_away": s2_away,
            "home_yellow": "",
            "away_yellow": "",
            "home_red": fields.get("GRA", ""),
            "away_red": fields.get("GRB", ""),
        }

    def fetch_match_stats(self, match_id: str) -> Dict[str, Any]:
        """Scarica e decodifica la telemetria live df_st_1_<match_id> (xG, tiri, SOT, corner, gialli)."""
        if not match_id:
            return {}
        from services.football.external.on_demand_ingestor import OnDemandMatchIngestor

        url = f"https://local-global.flashscore.ninja/2/x/feed/df_st_1_{match_id}"
        try:
            req = urllib.request.Request(url, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw_stats = resp.read().decode("utf-8", errors="ignore")
            return OnDemandMatchIngestor.parse_stats_feed(raw_stats)
        except Exception:
            return {}

    def get_enriched_live_snapshots(self, feed_text: str | None = None, max_workers: int = 10):
        """Recupera gli snapshot live arricchiti in parallelo con xG, tiri, SOT e corner da df_st_1_."""
        snapshots = self.get_live_snapshots(feed_text=feed_text)
        if not snapshots:
            return snapshots

        def _enrich(snap):
            st = self.fetch_match_stats(snap.fixture_id)
            if st:
                snap.xg_home = st.get("home_xg")
                snap.xg_away = st.get("away_xg")
                snap.home_shots = int(st.get("home_shots") or 0)
                snap.away_shots = int(st.get("away_shots") or 0)
                snap.home_shots_on_target = int(st.get("home_sot") or 0)
                snap.away_shots_on_target = int(st.get("away_sot") or 0)
                snap.home_corners = int(st.get("home_corners") or 0)
                snap.away_corners = int(st.get("away_corners") or 0)
                if st.get("home_yellow") is not None:
                    snap.home_yellow_cards = int(st.get("home_yellow") or 0)
                if st.get("away_yellow") is not None:
                    snap.away_yellow_cards = int(st.get("away_yellow") or 0)
            return snap

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            list(pool.map(_enrich, snapshots))
        return snapshots

    def get_live_snapshots(self, feed_text: str | None = None):
        """Converte le gare in corso in snapshot pronti per il motore in-play.

        Il feed riepilogo pubblica i rossi su GRA/GRB e i gialli su BA/BB quando ci sono.
        Senza quei campi i cartellini restano a zero: non si inventa un tabellino.
        """
        from services.live.live_momentum_sniper import LiveMatchSnapshot

        rows = self.parse_feed(feed_text) if feed_text is not None else self.fetch_feed()
        snapshots = []
        for row in rows:
            if row.get("status_code") not in self.LIVE_STATUS:
                continue
            home_goals = _feed_int(row.get("home_score"))
            away_goals = _feed_int(row.get("away_score"))
            if home_goals is None or away_goals is None:
                continue
            ht_home = _feed_int(row.get("ht_home"))
            ht_away = _feed_int(row.get("ht_away"))
            snapshots.append(
                LiveMatchSnapshot(
                    fixture_id=str(row.get("match_id") or ""),
                    match_name=f"{row['home']} vs {row['away']}",
                    minute=_feed_minute(str(row.get("period") or ""), str(row.get("status_code") or "")),
                    home_team=row["home"],
                    away_team=row["away"],
                    home_goals=home_goals,
                    away_goals=away_goals,
                    home_yellow_cards=_feed_int(row.get("home_yellow")) or 0,
                    away_yellow_cards=_feed_int(row.get("away_yellow")) or 0,
                    home_red_cards=_feed_int(row.get("home_red")) or 0,
                    away_red_cards=_feed_int(row.get("away_red")) or 0,
                    ht_home_goals=ht_home,
                    ht_away_goals=ht_away,
                )
            )
        return snapshots

    def find_match(self, team_keyword: str) -> List[Dict[str, Any]]:
        """Cerca match per parola chiave (case-insensitive)."""
        kw = team_keyword.lower().strip()
        all_matches = self.fetch_feed()
        return [
            m for m in all_matches 
            if kw in m["home"].lower() or kw in m["away"].lower()
        ]


def _feed_int(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text or text == "-":
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _feed_minute(period: str, status_code: str) -> int:
    """Il minuto di gioco. All'intervallo, se il feed non manda i numeri, sono 45."""
    if status_code == "11" and not any(char.isdigit() for char in period):
        return 45
    cleaned = period.strip().rstrip("'")
    if "+" in cleaned:
        base, extra = cleaned.split("+", 1)
        return (_feed_int(base) or 0) + (_feed_int(extra) or 0)
    return _feed_int(cleaned) or 0


if __name__ == "__main__":
    engine = FlashscoreLiveEngine()
    print("Test FlashscoreLiveEngine...")
    results = engine.find_match("Borneo")
    for r in results:
        print(f"  {r['home']} vs {r['away']} | Risultato: {r['score']} | Stato: {r['status']}")
