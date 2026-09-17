# -*- coding: utf-8 -*-
"""
services/football/external/sources/flashscore_live.py — Motore Live Feed in Tempo Reale.
Interroga direttamente il feed delta ad alta frequenza di Flashscore/Diretta.it
(local-it.flashscore.ninja), azzerando la latenza dei motori di ricerca.
"""
from __future__ import annotations
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

        if not text:
            return []

        matches = []
        blocks = text.split("~AA÷")
        for b in blocks[1:]:
            fields = {}
            for p in b.split("¬"):
                if "÷" in p:
                    k, v = p.split("÷", 1)
                    fields[k] = v

            home = fields.get("AE", "").strip()
            away = fields.get("AF", "").strip()
            if not home or not away:
                continue

            status_raw = fields.get("AB", "1")
            status_desc = self.STATUS_MAP.get(status_raw, f"Codice {status_raw}")
            
            s_home = fields.get("AG", "")
            s_away = fields.get("AH", "")
            score_str = f"{s_home}-{s_away}" if (s_home != "" or s_away != "") else "0-0" if status_raw in ["2", "11", "12", "13"] else "-"

            s1_home = fields.get("BC", "")
            s1_away = fields.get("BD", "")
            minute_val = fields.get("AC", "")
            start_ts = int(fields.get("AD", 0) or 0)

            match_id = b.split("¬")[0].strip()

            # Calcolo del minuto reale di gioco
            real_minute, minute_label = self._calculate_minute(status_raw, minute_val, start_ts)

            matches.append({
                "match_id": match_id,
                "home": home,
                "away": away,
                "score": score_str,
                "home_score": s_home,
                "away_score": s_away,
                "status_code": status_raw,
                "status": status_desc,
                "period": minute_val,
                "minute": real_minute,
                "minute_label": minute_label,
                "start_timestamp": start_ts,
                "ht_score": f"{s1_home}-{s1_away}" if s1_home else "",
            })

        return matches

    def fetch_match_stats(self, match_id: str) -> Dict[str, int]:
        """Estrae statistiche live in tempo reale (tiri, corner, cartellini) per un dato match."""
        if not match_id:
            return {"home_corners": 0, "away_corners": 0, "home_shots": 0, "away_shots": 0}
        url = f"https://local-it.flashscore.ninja/2/x/feed/df_st_1_{match_id}"
        stats = {
            "home_corners": 0, "away_corners": 0,
            "home_shots": 0, "away_shots": 0,
            "home_shots_on_target": 0, "away_shots_on_target": 0,
            "home_yellow_cards": 0, "away_yellow_cards": 0,
        }
        def _to_int(v: Any) -> int:
            try:
                s = str(v).split()[0].replace("%", "").strip()
                return int(float(s))
            except Exception:
                return 0

        try:
            req = urllib.request.Request(url, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=4) as resp:
                raw_text = resp.read().decode("utf-8", errors="ignore")
                for block in raw_text.split("~"):
                    if "SG÷" not in block:
                        continue
                    parts = dict([p.split("÷", 1) for p in block.split("¬") if "÷" in p])
                    name = parts.get("SG", "").lower()
                    sh = _to_int(parts.get("SH", 0))
                    si = _to_int(parts.get("SI", 0))
                    if "corner" in name or "calci d'angolo" in name:
                        stats["home_corners"] = sh
                        stats["away_corners"] = si
                    elif "total shots" in name or "tiri totali" in name:
                        stats["home_shots"] = sh
                        stats["away_shots"] = si
                    elif "shots on target" in name or "tiri in porta" in name:
                        stats["home_shots_on_target"] = sh
                        stats["away_shots_on_target"] = si
                    elif "yellow cards" in name or "cartellini gialli" in name:
                        stats["home_yellow_cards"] = sh
                        stats["away_yellow_cards"] = si
        except Exception:
            pass
        return stats

    @staticmethod
    def _calculate_minute(status_code: str, period_code: str, start_timestamp: int) -> tuple[int, str]:
        """Calcola il minuto esatto in base a start_timestamp e status."""
        import time
        if not start_timestamp or status_code not in ["2", "11", "12", "13"]:
            if status_code == "3":
                return 90, "Finale"
            return 0, "Pre-Match"

        if status_code == "11" or period_code == "11":
            return 45, "Intervallo"

        now_ts = int(time.time())
        diff_sec = now_ts - start_timestamp
        if diff_sec < 0:
            return 1, "1'"

        diff_min = diff_sec // 60

        # 1° Tempo
        if period_code == "12" or (diff_min <= 48 and period_code != "13"):
            m = min(45, max(1, diff_min))
            if diff_min > 45:
                return 45, f"45+{diff_min-45}'"
            return m, f"{m}'"

        # Intervallo
        if 48 < diff_min < 62 and period_code != "13":
            return 45, "Intervallo"

        # 2° Tempo (period 13 o dopo 60 min dall'avvio)
        # Sottrae 60 minuti (45' primo tempo + 15' intervallo)
        m2 = 45 + max(1, diff_min - 60)
        if m2 > 90:
            recup = m2 - 90
            return 90, f"90+{recup}'"
        return m2, f"{m2}'"

    def find_match(self, team_keyword: str) -> List[Dict[str, Any]]:
        """Cerca match per parola chiave (case-insensitive)."""
        kw = team_keyword.lower().strip()
        all_matches = self.fetch_feed()
        return [
            m for m in all_matches 
            if kw in m["home"].lower() or kw in m["away"].lower()
        ]

if __name__ == "__main__":
    engine = FlashscoreLiveEngine()
    print("Test FlashscoreLiveEngine...")
    results = engine.find_match("Borneo")
    for r in results:
        print(f"  {r['home']} vs {r['away']} | Risultato: {r['score']} | Stato: {r['status']}")
