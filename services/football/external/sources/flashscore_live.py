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

            matches.append({
                "match_id": fields.get("AA", ""),
                "home": home,
                "away": away,
                "score": score_str,
                "home_score": s_home,
                "away_score": s_away,
                "status_code": status_raw,
                "status": status_desc,
                "period": minute_val,
                "ht_score": f"{s1_home}-{s1_away}" if s1_home else "",
            })

        return matches

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
