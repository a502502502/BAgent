"""
scripts/extract_best_snai_combos.py — Estrae le combinazioni reali SNAI per il fine settimana.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLATE_DIR = ROOT / "reports" / "snai" / "2026-10-07-11"

TARGETS = [
    ("Venerdi", "ger-bundesliga--borussia-dortmund-werder-brema.json"),
    ("Venerdi", "fra-ligue-1--lens-lione.json"),
    ("Venerdi", "esp-liga--malaga-espanyol.json"),
    ("Sabato", "eng-premier-league--manchester-united-tottenham.json"),
    ("Sabato", "esp-liga--real-madrid-villarreal.json"),
    ("Sabato", "ita-serie-a--inter-parma.json"),
    ("Domenica", "eng-premier-league--liverpool-manchester-city.json"),
    ("Domenica", "ita-serie-a--como-roma.json"),
    ("Domenica", "ita-serie-a--cagliari-juventus.json"),
]


def inspect_combos() -> None:
    for day, fname in TARGETS:
        p = SLATE_DIR / fname
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        match = data.get("match")
        ko = data.get("kickoff_time")
        ev_id = data.get("event_id")

        print(f"\n=======================================================")
        print(f"[{day.upper()}] {match} ({ko}) | Event ID: {ev_id}")
        print(f"=======================================================")

        for m in data.get("markets", []):
            m_name = m.get("market", "")
            line = m.get("line", "")

            # Combo Chance Mix
            if "COMBO CHANCE" in m_name.upper():
                for o in m.get("outcomes", []):
                    odd = o.get("odds", 0)
                    sel = o.get("selection", "")
                    if o.get("open", True) and 1.20 <= odd <= 1.65 and sel == "SI":
                        print(f"  [CHANCE MIX] {line} -> {sel} @ {odd:.2f}")

            # Combo DC + U/O
            if "COMBO: 1X2 + U/O" in m_name.upper() or "COMBO: DC + U/O" in m_name.upper():
                for o in m.get("outcomes", []):
                    odd = o.get("odds", 0)
                    sel = o.get("selection", "")
                    if o.get("open", True) and 1.25 <= odd <= 1.95:
                        print(f"  [COMBO GOAL] {line} -> {sel} @ {odd:.2f}")

            # MultiGol Combinati 1T + 2T
            if "MULTIGOAL PRIMO TEMPO + MULTIGOAL SECONDO TEMPO" in line.upper():
                for o in m.get("outcomes", []):
                    odd = o.get("odds", 0)
                    sel = o.get("selection", "").strip()
                    if o.get("open", True) and sel in ("0-1/0-3", "0-1/0-4", "0-2/0-2", "0-2/0-3", "0-1/1-3"):
                        print(f"  [MG 1T+2T] {sel} @ {odd:.2f}")

            # Marcatore con sostituto e pali/traverse
            if "SOSTITUTO SEGNA O PRENDE PALO/TRAVERSA" in line.upper():
                for o in m.get("outcomes", []):
                    odd = o.get("odds", 0)
                    sel = o.get("selection", "")
                    if o.get("open", True) and 1.50 <= odd <= 2.80 and sel == "SI":
                        print(f"  [PARACADUTE MARCATORE/LEGNI] {line} -> @ {odd:.2f}")


if __name__ == "__main__":
    inspect_combos()
