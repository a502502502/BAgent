#!/usr/bin/env python3
"""Prenota su Netwin la Tripla Combo Opzione 1 (09/10/2026).

Selezioni:
  1) PSV vs Heerenveen — prova 1 + Til Marcatore (fallback: GIOCATORI/Til)
  2) Dortmund vs Werder — 1X + Over 2.5
  3) Braga vs Sporting — X2 + Over 1.5
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.betting.netwin_automator import NetwinAutomator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("book_opzione1")

OUT = ROOT / "reports" / "tickets" / "ticket_netwin_opzione1_09ott.json"
STAKE = 5.0

SELECTIONS = [
    {
        "match": "PSV Eindhoven vs SC Heerenveen",
        "home": "PSV",
        "away": "Heerenveen",
        "market": "COMBO",
        "pick": "1 + Over 1.5",
        "netwin_odds": 1.95,
        "note": "Fallback bookable: 1+O1.5 se Til non selezionabile; tentativo Til via UI sotto.",
        "try_til": True,
        "kickoff_time": "2026-10-09 20:00 CEST",
    },
    {
        "match": "Borussia Dortmund vs Werder Brema",
        "home": "Dortmund",
        "away": "Werder",
        "market": "COMBO",
        "pick": "1X + Over 2.5",
        "netwin_odds": 1.42,
        "kickoff_time": "2026-10-09 20:30 CEST",
    },
    {
        "match": "Sporting Braga vs Sporting CP",
        "home": "Braga",
        "away": "Sporting",
        "market": "COMBO",
        "pick": "X2 + Over 1.5",
        "netwin_odds": 1.57,
        "kickoff_time": "2026-10-09 21:15 CEST",
    },
]


def try_click_til(auto: NetwinAutomator) -> bool:
    """Apre tab Giocatori/Marcatori e clicca Guus Til se presente."""
    page = auto.page
    if page is None:
        return False
    for tab in ("GIOCATORI", "MARCATORI", "SPECIALI MATCH", "COMBO"):
        try:
            loc = page.get_by_text(tab, exact=True)
            if loc.count():
                loc.first.click(timeout=2000)
                page.wait_for_timeout(1200)
        except Exception:
            continue
    for label in ("Til", "G. Til", "Guus Til", "TIL"):
        try:
            nodes = page.get_by_text(label, exact=False)
            for i in range(min(nodes.count(), 12)):
                node = nodes.nth(i)
                if not node.is_visible():
                    continue
                txt = " ".join(node.inner_text().split())
                if "til" not in txt.casefold():
                    continue
                # Prefer quota vicino al nome
                try:
                    node.click(timeout=2000)
                    page.wait_for_timeout(800)
                    logger.info("Cliccato esito Til: %s", txt[:80])
                    return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def main() -> int:
    auto = NetwinAutomator(headless=False)
    if not auto.open_sportsbook():
        print(json.dumps({"success": False, "error": "Impossibile aprire Netwin"}, ensure_ascii=False))
        return 1
    auto.clear_betslip()

    added = 0
    legs_ok = []
    for sel in SELECTIONS:
        ok = False
        if sel.get("try_til"):
            # Prima cerca Til; se fallisce usa combo 1+Over 1.5 bookable
            logger.info("Tentativo PSV + Til Marcatore...")
            if auto.search_match(sel["home"]):
                auto._row_team = sel["home"]
                auto._row_opponent = sel.get("away", "")
                auto.click_match_row(sel["home"])
                ok = try_click_til(auto)
            if not ok:
                logger.warning("Til non trovato: fallback COMBO 1 + Over 1.5")
                ok = auto.add_match_selection({
                    **sel,
                    "pick": "1 + Over 1.5",
                    "market": "COMBO",
                })
                sel = {**sel, "pick": "1 + Over 1.5", "fallback_used": True}
        else:
            ok = auto.add_match_selection(sel)
        if ok:
            added += 1
            legs_ok.append(sel)
        else:
            logger.error("Selezione fallita: %s", sel["match"])
        auto.page.wait_for_timeout(1000)

    result = {
        "success": False,
        "events_added": added,
        "total_events": len(SELECTIONS),
        "legs": legs_ok,
        "stake": STAKE,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M CEST"),
    }

    if added != len(SELECTIONS):
        auto.clear_betslip()
        auto.close()
        result["error"] = f"Aggiunte {added}/{len(SELECTIONS)} selezioni. Prenotazione non emessa."
        OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2

    book = auto.generate_booking_code(stake=STAKE)
    result.update(book)
    if result.get("booking_code") and auto.page is not None:
        shot = ROOT / "reports" / "receipts" / f"prenotazione_opzione1_{result['booking_code']}.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        auto.page.screenshot(path=str(shot), full_page=True)
        result["screenshot"] = str(shot)
    auto.close()
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "raw_html"}, indent=2, ensure_ascii=False, default=str))
    return 0 if result.get("success") and result.get("booking_code") else 3


if __name__ == "__main__":
    raise SystemExit(main())
