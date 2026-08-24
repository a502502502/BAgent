#!/usr/bin/env python3
"""
download_livescore.py — Scarica e analizza qualsiasi partita da livescore.in / Diretta.it / Flashscore.

Uso:
    python scripts/download_livescore.py "b1nulsUp"
    python scripts/download_livescore.py "https://www.livescore.in/it/partita/calcio/osasuna-levante/...?mid=b1nulsUp"
"""

import sys
import re
import json
import requests
from datetime import datetime
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "x-fsign": "SW9D1eZo",
}

def extract_match_id(query: str) -> str:
    query = query.strip()
    if "mid=" in query:
        return query.split("mid=")[1].split("#")[0].split("&")[0]
    if "/" in query:
        # Check if match id is in URL path
        parts = query.rstrip("/").split("/")
        for p in reversed(parts):
            if len(p) == 8 and p.isalnum():
                return p
    return query

def fetch_livescore_match(mid: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📥 Download dati da LiveScore.in (Match ID: {mid})...\n")
    
    # 1. Stats
    url_stats = f"https://local-global.flashscore.ninja/2/x/feed/df_st_1_{mid}"
    r_stats = requests.get(url_stats, headers=HEADERS, timeout=8)
    
    # 2. Lineups
    url_lineups = f"https://local-global.flashscore.ninja/2/x/feed/df_li_1_{mid}"
    r_lineups = requests.get(url_lineups, headers=HEADERS, timeout=8)

    # 3. Incidents / Events
    url_inc = f"https://local-global.flashscore.ninja/2/x/feed/df_sui_1_{mid}"
    r_inc = requests.get(url_inc, headers=HEADERS, timeout=8)

    stats = {}
    if r_stats.status_code == 200:
        for block in r_stats.text.split("¬~SD÷"):
            if "SG÷" in block and "SH÷" in block and "SI÷" in block:
                name = block.split("SG÷")[1].split("¬")[0]
                val_h = block.split("SH÷")[1].split("¬")[0]
                val_a = block.split("SI÷")[1].split("¬")[0]
                stats[name] = {"home": val_h, "away": val_a}

    print("="*65)
    print(f"{'STATISTICA LIVESCORE.IN':<32} | {'CASA':<12} | {'OSPITE'}")
    print("="*65)
    for k, v in stats.items():
        print(f"{k:<32} | {v['home']:<12} | {v['away']}")
    print("="*65)

    # Salva in json locale
    out_dir = Path("storage/snapshots/livescore")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{mid}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"mid": mid, "updated_at": str(datetime.now()), "stats": stats}, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Dati salvati con successo in: {out_file}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/download_livescore.py <MATCH_ID_OPPURE_URL>")
        sys.exit(1)
    target = sys.argv[1]
    mid = extract_match_id(target)
    fetch_livescore_match(mid)
