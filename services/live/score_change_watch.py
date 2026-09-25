"""Avvisa solo quando il punteggio o la fase di una selezione cambiano."""

from __future__ import annotations

import re
from typing import Iterable

_YOUTH = re.compile(r"\bU\d{2}\b", re.IGNORECASE)
_ALIASES = {
    "georgia": ("georgia",),
    "irlanda del nord": ("northern ireland", "irlanda del nord"),
    "armenia": ("armenia",),
    "lettonia": ("latvia", "lettonia"),
    "svezia": ("sweden", "svezia"),
    "romania": ("romania",),
    "montenegro": ("montenegro",),
    "cipro": ("cyprus", "cipro"),
    "ungheria": ("hungary", "ungheria"),
    "ucraina": ("ukraine", "ucraina"),
    "italia": ("italy", "italia"),
    "belgio": ("belgium", "belgio"),
    "turchia": ("turkey", "turkiye", "turchia"),
    "francia": ("france", "francia"),
    "polonia": ("poland", "polonia"),
    "bosnia erzegovina": ("bosnia",),
}


def is_youth(name: str) -> bool:
    return _YOUTH.search(name or "") is not None


def same_team(feed_name: str, ticket_name: str) -> bool:
    """Il nome del feed corrisponde alla squadra del ticket, senza le Under."""
    if is_youth(feed_name):
        return False
    key = " ".join((ticket_name or "").lower().split())
    aliases = _ALIASES.get(key, (key,))
    folded = (feed_name or "").lower()
    return any(alias in folded for alias in aliases)


def coarse_phase(status_code: str) -> str:
    if status_code == "3":
        return "ft"
    if status_code == "11":
        return "ht"
    if status_code in {"2", "4", "5", "12", "13"}:
        return "live"
    return "scheduled"


def fingerprint(row: dict) -> str:
    return f"{row.get('score') or '-'}|{coarse_phase(str(row.get('status_code') or ''))}"


def find_row(feed: Iterable[dict], home: str, away: str) -> dict | None:
    for row in feed:
        if same_team(str(row.get("home") or ""), home) and same_team(str(row.get("away") or ""), away):
            return row
    return None


def selection_note(pick: str, score: str, phase: str) -> str:
    """Dice se la selezione è già chiusa o ancora aperta. Senza punteggio resta in attesa."""
    if phase == "scheduled" or score in {"", "-"}:
        return "in attesa"
    try:
        home_goals, away_goals = (int(part) for part in score.split("-", 1))
    except ValueError:
        return "in attesa"
    total = home_goals + away_goals
    text = pick.lower()
    finished = phase == "ft"
    if text.startswith("over"):
        line = _line(text)
        if total > line:
            return "chiusa vinta"
        return "chiusa persa" if finished else "in corso"
    if text.startswith("under"):
        line = _line(text)
        if total > line:
            return "chiusa persa"
        return "chiusa vinta" if finished else "in corso"
    if text == "gol":
        if home_goals > 0 and away_goals > 0:
            return "chiusa vinta"
        return "chiusa persa" if finished else "in corso"
    if text == "x2":
        if finished:
            return "chiusa vinta" if home_goals <= away_goals else "chiusa persa"
        return "sotto" if home_goals > away_goals else "in corso"
    return "in corso" if not finished else "finita"


def changed_rows(previous: dict[str, str], legs: list[dict], feed: Iterable[dict]) -> tuple[list[dict], dict[str, str]]:
    """Ritorna gli avvisi nuovi e lo stato aggiornato. Il primo avvistamento non è un cambio."""
    alerts = []
    state = dict(previous)
    rows = list(feed)
    for leg in legs:
        home, away = _split_match(str(leg.get("match") or ""))
        row = find_row(rows, home, away)
        if row is None:
            continue
        key = f"{home}|{away}"
        current = fingerprint(row)
        seen = state.get(key)
        state[key] = current
        if seen is None or seen == current:
            continue
        score, phase = current.split("|", 1)
        alerts.append(
            {
                "match": f"{row.get('home')} - {row.get('away')}",
                "score": score,
                "phase": phase,
                "minute": str(row.get("period") or ""),
                "pick": str(leg.get("pick") or ""),
                "note": selection_note(str(leg.get("pick") or ""), score, phase),
            }
        )
    return alerts, state


def _split_match(match: str) -> tuple[str, str]:
    home, away = match.split(" vs ", 1)
    return home.strip(), away.strip()


def _line(text: str) -> float:
    found = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(found.group(1)) if found else 0.0
