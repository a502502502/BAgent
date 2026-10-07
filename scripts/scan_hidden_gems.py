#!/usr/bin/env python3
"""
scripts/scan_hidden_gems.py — CLI Scanner Automatico delle Gemme Nascoste.

Scansiona i cataloghi freschi della giornata (SNAI, Netwin), calcola xG dal database,
estrae e classifica le opportunità a valore asimmetrico (Player Props protette e Combo Asimmetriche),
e produce il Gems Board del giorno.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from services.analysis.gems_discovery_engine import GemsDiscoveryEngine, GemPick
from services.analysis.match_market_optimizer import MatchMarketOptimizer
from services.analysis.snai_goal_book import MAX_AGE_HOURS, catalog_age_hours, goal_odds_from_catalog
from services.betting.netwin_cache_reader import CachedMatch

CEST = timezone(timedelta(hours=2))
OUT_DIR = ROOT / "reports" / "gems"
SOURCES = [
    ROOT / "reports" / "snai" / "2026-10-07",
    ROOT / "reports" / "snai" / "2026-10-06-sera",
    ROOT / "reports" / "snai_nl" / "catalog",
]


def load_fresh_catalogs(now: datetime) -> list[dict]:
    found: dict[str, dict] = {}
    for folder in SOURCES:
        if not folder.exists():
            continue
        for p in folder.glob("*.json"):
            if p.name in {"index.json", "picks.json"}:
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            data["_path"] = str(p)
            match = data.get("match") or ""
            if not match or " - " not in match or "GIORNATA" in match:
                continue
            age = catalog_age_hours(data, now)
            if age is None or age > MAX_AGE_HOURS:
                continue
            prev = found.get(match)
            if prev is None or (catalog_age_hours(data, now) or 99) < (catalog_age_hours(prev, now) or 99):
                found[match] = data
    return list(found.values())


def main() -> None:
    now = datetime.now(CEST)
    engine = GemsDiscoveryEngine()
    optimizer = MatchMarketOptimizer()

    catalogs = load_fresh_catalogs(now)
    print(f"Cataloghi freschi trovati (< {MAX_AGE_HOURS} ore): {len(catalogs)}")

    all_gems: list[GemPick] = []

    for cat in catalogs:
        match = cat["match"]
        home, away = match.split(" - ", 1)
        odds = goal_odds_from_catalog(cat)
        cached = CachedMatch(
            match_name=f"{home.strip()} vs {away.strip()}",
            home_team=home.strip(),
            away_team=away.strip(),
            tournament="Nations League",
            kickoff=cat["kickoff_time"],
            odds_dict={k: odds[k] for k in ("1", "X", "2", "Under 2.5", "Over 2.5") if k in odds},
        )
        xg_h, xg_a, _rho, _source, _hn, _an = optimizer.lambdas_for(cached)
        match_gems = engine.scan_catalog_for_gems(cat, xg_h, xg_a, now=now)
        all_gems.extend(match_gems)

    print(f"Totale gemme asimmetriche scovate: {len(all_gems)}")

    # Seleziona le top gemme garantendo 1 per partita per preservare l'indipendenza
    top_slate = engine.select_best_gems_slate(all_gems, max_total=6, max_per_match=1)

    print("\n==========================================================================================")
    print("GEMS BOARD: SELEZIONI A VALORE ASIMMETRICO E CLAUSOLE DI PROTEZIONE")
    print("==========================================================================================")
    print(f"{'Partita':<32} | {'Selezione':<30} | {'Quota':<6} | {'P Reale':<7} | {'Edge':<7} | {'Tier'}")
    print("-" * 100)
    for g in top_slate:
        print(f"{g.match_name:<32} | {g.selection:<30} | {g.book_odd:<6.2f} | {g.probability*100:>5.1f}% | {g.edge*100:>+5.1f}% | {g.tier}")
        print(f"  Clausola: {g.safety_clause}")
        print(f"  Stato Distinte: {g.lineup_status}\n")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today_str = now.strftime("%Y-%m-%d")
    out_file = OUT_DIR / f"gems_board_{today_str}.json"

    data_out = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M CEST"),
        "total_gems_detected": len(all_gems),
        "selected_gems_count": len(top_slate),
        "gems": [
            {
                "match": g.match_name,
                "kickoff_time": g.kickoff_time,
                "category": g.category,
                "market": g.market,
                "selection": g.selection,
                "book_odd": g.book_odd,
                "probability": g.probability,
                "fair_odd": g.fair_odd,
                "edge": g.edge,
                "safety_clause": g.safety_clause,
                "lineup_status": g.lineup_status,
                "rationale": g.rationale,
                "tier": g.tier,
                "player_name": g.player_name,
                "xg_home": g.xg_home,
                "xg_away": g.xg_away,
            }
            for g in top_slate
        ],
    }

    out_file.write_text(json.dumps(data_out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gems Board salvato in {out_file}")


if __name__ == "__main__":
    main()
