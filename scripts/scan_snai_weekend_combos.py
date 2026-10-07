"""
scripts/scan_snai_weekend_combos.py — Scansione mercati speciali e combinazioni SNAI nei JSON del weekend.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLATE_DIR = ROOT / "reports" / "snai" / "2026-10-07-11"

TARGET_FILES = [
    # Venerdi 9 Ottobre
    "ger-bundesliga--borussia-dortmund-werder-brema.json",
    "fra-ligue-1--lens-lione.json",
    "esp-liga--malaga-espanyol.json",
    # Sabato 10 Ottobre
    "eng-premier-league--manchester-united-tottenham.json",
    "esp-liga--real-madrid-villarreal.json",
    "ita-serie-a--inter-parma.json",
    "eng-premier-league--arsenal-leeds.json",
    # Domenica 11 Ottobre
    "eng-premier-league--liverpool-manchester-city.json",
    "ita-serie-a--como-roma.json",
    "ita-serie-a--cagliari-juventus.json",
    "ita-serie-a--lazio-monza.json",
]


def scan_file(fname: str) -> None:
    p = SLATE_DIR / fname
    if not p.exists():
        print(f"File non trovato: {fname}")
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    match = data.get("match")
    ko = data.get("kickoff_time")
    ev_id = data.get("event_id")
    print(f"\n=======================================================")
    print(f"MATCH: {match} ({ko}) | Event ID: {ev_id} | File: {fname}")
    print(f"=======================================================")

    categories = [
        "COMBO CHANCE",
        "COMBO: 1X2 + U/O",
        "COMBO: 1X2 + MULTIGOAL",
        "MULTIGOAL 1T + MULTIGOAL 2T",
        "MULTIGOAL CASA + MULTIGOAL OSPITE",
        "DOPPIA CHANCE",
        "GOAL/NOGOAL",
        "TIRI",
        "MARCATORE",
    ]

    for cat in categories:
        found_in_cat = []
        for m in data.get("markets", []):
            m_name = m.get("market", "").upper()
            line = m.get("line", "").upper()
            if cat in m_name or cat in line:
                for o in m.get("outcomes", []):
                    odd = o.get("odds", 0)
                    sel = o.get("selection", "")
                    if o.get("open", True) and 1.15 <= odd <= 2.80:
                        found_in_cat.append((m_name, line, sel, odd))
        if found_in_cat:
            print(f"\n--- {cat} ({len(found_in_cat)} esiti disponibili) ---")
            for m_name, line, sel, odd in found_in_cat[:6]:
                print(f"  {line} -> {sel} @ {odd:.2f}")


def main() -> None:
    for f in TARGET_FILES:
        scan_file(f)


if __name__ == "__main__":
    main()
