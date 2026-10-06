"""Quote gol di un catalogo SNAI compatto, nel nome che il motore sa prezzare.

Le probabilità non si scrivono a mano. Se il nome del mercato non è mappato,
la riga non entra.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from services.analysis.statistical_combo import StatPick, best_combination, rank_statistical_combos

CEST = timezone(timedelta(hours=2))
MAX_AGE_HOURS = 12.0

_RANGE = re.compile(r"(\d+)\s*-\s*(\d+)")
_LINE = re.compile(r"(\d+(?:[.,]\d+)?)")


def catalog_age_hours(catalog: dict, now: datetime | None = None) -> float | None:
    raw = catalog.get("fetched_at") or ""
    moment = now or datetime.now(CEST)
    if raw:
        try:
            fetched = datetime.strptime(raw, "%Y-%m-%d %H:%M CEST").replace(tzinfo=CEST)
            return (moment - fetched).total_seconds() / 3600.0
        except ValueError:
            pass
    path_str = catalog.get("_path")
    if path_str:
        p = Path(path_str)
        if p.exists():
            fetched = datetime.fromtimestamp(p.stat().st_mtime, tz=CEST)
            return (moment - fetched).total_seconds() / 3600.0
    return None


def goal_odds_from_catalog(catalog: dict) -> dict[str, float]:
    """Traduce i mercati gol aperti in nomi canonici. Il 1X2 entra anche sotto 1.20."""
    odds: dict[str, float] = {}
    for market in catalog.get("markets") or []:
        name = str(market.get("market") or "").strip().upper()
        line = str(market.get("line") or "").strip().upper()
        if any(token in name for token in ("GIOCATORE", "MARCATORE", "CARTOLIN", "CORNER", "ANGOL", "FALLO")):
            continue
        for outcome in market.get("outcomes") or []:
            if not outcome.get("open"):
                continue
            selection = str(outcome.get("selection") or "").strip().upper()
            odd = float(outcome.get("odds") or 0.0)
            if odd <= 1.0:
                continue
            canonical = _canonical(name, line, selection)
            if canonical is None:
                continue
            if odd < 1.20 and canonical not in {"1", "X", "2"}:
                continue
            odds.setdefault(canonical, odd)
    return odds


def best_goal_pick(xg_home: float, xg_away: float, catalog: dict) -> StatPick | None:
    return best_combination(rank_statistical_combos(xg_home, xg_away, goal_odds_from_catalog(catalog)))


def _canonical(name: str, line: str, selection: str) -> str | None:
    if "TEMPO" in name or "TEMPO" in line:
        return None
    if name == "1X2 ESITO FINALE" and selection in {"1", "X", "2"}:
        return selection
    if name == "DOPPIA CHANCE" and selection in {"1X", "X2", "12"}:
        return selection
    if name == "UNDER/OVER" and "SQUADRA" not in name:
        parsed = _LINE.search(line)
        if parsed and selection in {"OVER", "UNDER"}:
            number = parsed.group(1).replace(",", ".")
            return f"{selection.title()} {number}"
    if name.startswith("MULTIGOL") and "SQUADRA" not in name:
        band = _RANGE.search(selection)
        if band:
            return f"MultiGol {band.group(1)}-{band.group(2)}"
    if "SQUADRA" in name and "MULTIGOL" in name:
        band = _RANGE.search(selection) or _RANGE.search(line)
        if not band:
            return None
        side = "Casa" if "SQUADRA 1" in name else "Ospite" if "SQUADRA 2" in name else ""
        if not side:
            return None
        return f"MultiGol {band.group(1)}-{band.group(2)} {side}"
    if "COMBO CHANCE" in name and "GOAL" in selection and "NOGOAL" not in selection:
        side = selection.split(" O ")[0].strip()
        if side in {"1", "X", "2"}:
            return f"Chance Mix: {side} o Gol"
    if name.startswith("COMBO: DC + MULTIGOAL") and "ALTRO" not in selection:
        band = _RANGE.search(line)
        side = selection.split(" + ")[0].strip()
        if band and side in {"1X", "X2", "12"}:
            return f"{side} + MultiGol {band.group(1)}-{band.group(2)}"
    if name.startswith("COMBO: DC + U/O"):
        parsed = _LINE.search(line)
        parts = selection.split(" + ")
        if parsed and len(parts) == 2 and parts[0] in {"1X", "X2", "12"} and parts[1] in {"OVER", "UNDER"}:
            number = parsed.group(1).replace(",", ".")
            return f"{parts[0]} + {parts[1].title()} {number}"
    return None
