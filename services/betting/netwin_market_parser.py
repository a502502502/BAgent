"""Parse BAgent pick strings into Netwin UI actions (no browser)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


class UnsupportedNetwinMarket(ValueError):
    """Pick/market string cannot be mapped onto a Netwin click sequence."""


@dataclass(frozen=True)
class NetwinMarketAction:
    family: str
    pick: str
    ou_line: Optional[float] = None
    combo_result: Optional[str] = None
    combo_ou_side: Optional[str] = None
    combo_ou_line: Optional[float] = None
    combo_type: Optional[str] = None  # OU, MULTIGOL, BTTS
    combo_multigol_range: Optional[str] = None  # "1-4", "2-5"
    combo_multigol_scope: Optional[str] = "MATCH"  # MATCH, HOME, AWAY
    multigol_range: Optional[str] = None
    multigol_scope: Optional[str] = None
    specialty_side: Optional[str] = None  # 1/X/2 or OVER/UNDER for corner/cards
    specialty_line: Optional[float] = None
    specialty_scope: Optional[str] = None  # HOME, AWAY, TOTAL for corner lines
    chance_mix: Optional[str] = None  # e.g. "X o GG"
    raw: str = ""

    def column_hint(self) -> Optional[int]:
        """Index into the home-row .contenitoreSingolaQuota strip, if applicable."""
        if self.family == "1X2":
            return {"1": 0, "X": 1, "2": 2}[self.pick]
        if self.family == "DC":
            return {"1X": 3, "12": 4, "X2": 5}[self.pick]
        if self.family == "OU" and self.ou_line == 2.5:
            return 6 if self.pick == "UNDER" else 7
        if self.family == "BTTS":
            return 8 if self.pick == "GOL" else 9
        return None


def parse_netwin_selection(market: str = "", pick: str = "") -> NetwinMarketAction:
    raw = " ".join(part.strip() for part in (market, pick) if part and str(part).strip())
    text = _normalize(raw)
    if not text:
        raise UnsupportedNetwinMarket("Empty market/pick")

    pick_n = _normalize(pick)
    market_n = _normalize(market)

    folded = text.replace("MULTI GOL", "MULTIGOL")
    if "MULTIGOL" in folded and "+" not in folded:
        return _parse_multigol(folded, raw)

    chance = _parse_chance_mix(text)
    if chance is not None:
        return chance

    corner = _parse_specialty(text, market_n, family="CORNER", keywords=("CORNER", "CALCI D'ANGOLO", "ANGOLI"))
    if corner is not None:
        return corner

    cards = _parse_specialty(
        text,
        market_n,
        family="CARDS",
        keywords=("CARTELLIN", "SANZION", "AMMONIZ", "CARDS", "YELLOW"),
    )
    if cards is not None:
        return cards

    if "+" in text:
        return _parse_combo(text, raw)

    btts = _parse_btts(pick_n) or _parse_btts(text)
    if btts is not None and "UNDER" not in text and "OVER" not in text:
        return NetwinMarketAction(family="BTTS", pick=btts, raw=raw)

    ou = _parse_ou(pick_n) or _parse_ou(text)
    if ou is not None:
        side, line = ou
        return NetwinMarketAction(family="OU", pick=side, ou_line=line, raw=raw)

    dc = _parse_dc(pick_n) or (
        _parse_dc(text) if "1X2" not in market_n else _parse_dc(pick_n)
    )
    if dc is not None:
        return NetwinMarketAction(family="DC", pick=dc, raw=raw)

    fx = _parse_1x2(pick_n) or _parse_1x2_from_market(market_n, pick_n, text)
    if fx is not None:
        return NetwinMarketAction(family="1X2", pick=fx, raw=raw)

    raise UnsupportedNetwinMarket(f"Cannot map Netwin market: {raw!r}")


def _normalize(value: str) -> str:
    text = str(value or "").strip().upper()
    text = text.replace("U/O", "UNDER/OVER")
    text = text.replace("G/NG", "GOL")
    text = re.sub(r"\s+", " ", text)
    return text


def _parse_btts(text: str) -> Optional[str]:
    if not text:
        return None
    compact = text.replace(" ", "")
    no_tokens = ("NOGOL", "NO-GOL", "BTTSNO", "BTTS:NO")
    if any(tok in compact for tok in no_tokens) or re.search(r"\bNG\b", text):
        return "NOGOL"
    yes_exact = {"GOL", "GG", "BTTS", "BTTS SI", "BTTS YES", "GOL SI"}
    if text in yes_exact or compact in ("BTTSSI", "GOLS"):
        return "GOL"
    if re.fullmatch(r"GOL", text):
        return "GOL"
    return None


def _parse_ou(text: str) -> Optional[tuple[str, float]]:
    if "UNDER" not in text and "OVER" not in text:
        return None
    side_m = re.search(r"\b(UNDER|OVER)\b", text)
    if not side_m:
        return None
    line_m = re.search(r"(\d+\.\d+)", text)
    line = float(line_m.group(1)) if line_m else 2.5
    return side_m.group(1), line


def _parse_dc(text: str) -> Optional[str]:
    if not text or "UNDER" in text or "OVER" in text:
        return None
    for token in ("1X", "X2", "12"):
        if re.search(rf"(?<![0-9A-Z]){token}(?![0-9A-Z])", text):
            return token
    return None


def _parse_1x2(text: str) -> Optional[str]:
    if text in ("1", "X", "2"):
        return text
    return None


def _parse_1x2_from_market(market_n: str, pick_n: str, text: str) -> Optional[str]:
    if pick_n in ("1", "X", "2"):
        return pick_n
    if "1X2" in market_n or "ESITO" in market_n:
        m = re.search(r"(?<![0-9A-Z])([1X2])(?![0-9A-Z])", pick_n or text)
        if m:
            return m.group(1)
    if text in ("1", "X", "2"):
        return text
    return None


def _parse_combo(text: str, raw: str) -> NetwinMarketAction:
    """1/X/2/1X/X2/12 plus MultiGol, Gol/NoGol, or Under/Over. The right-hand side decides the branch."""
    folded = text.replace("MULTI GOL", "MULTIGOL")
    left, _, right = folded.partition("+")
    result = _parse_dc(left)
    if result is None:
        m = re.search(r"(?<![0-9A-Z])([12X])(?![0-9A-Z])", left.strip())
        if m and m.group(1) in ("1", "2", "X"):
            result = m.group(1)
    if result is None:
        raise UnsupportedNetwinMarket(f"Cannot map combo result in {raw!r}")

    multigol = re.search(r"MULTIGOL\s*(\d+\s*-\s*\d+)", right)
    if multigol:
        rng = re.sub(r"\s+", "", multigol.group(1))
        scope = "MATCH"
        if re.search(r"\b(?:CASA|HOME)\b", right):
            scope = "HOME"
        elif re.search(r"\b(?:OSPITE|AWAY)\b", right):
            scope = "AWAY"
        return NetwinMarketAction(
            family="COMBO",
            pick=folded,
            combo_result=result,
            combo_type="MULTIGOL",
            combo_multigol_range=rng,
            combo_multigol_scope=scope,
            raw=raw,
        )

    btts = _parse_btts(right.strip())
    if btts is not None and "UNDER" not in right and "OVER" not in right:
        return NetwinMarketAction(
            family="COMBO",
            pick=folded,
            combo_result=result,
            combo_type="BTTS",
            combo_ou_side=btts,
            raw=raw,
        )

    ou = _parse_ou(folded)
    if ou is None:
        raise UnsupportedNetwinMarket(
            f"Cannot map combo (neither MultiGol, Gol/NoGol nor Under/Over): {raw!r}"
        )
    side, line = ou
    return NetwinMarketAction(
        family="COMBO",
        pick=folded,
        combo_result=result,
        combo_type="OU",
        combo_ou_side=side,
        combo_ou_line=line,
        raw=raw,
    )


def _parse_chance_mix(text: str) -> Optional[NetwinMarketAction]:
    if "CHANCE MIX" not in text and not re.search(r"\bO\b.*(GG|GOL|OVER)", text):
        # Require explicit Chance Mix or "X o GG" / "1X o Over" pattern
        if not re.search(r"\b(1X|X2|12|X|1|2)\s+O\s+(GG|GOL|OVER|UNDER)", text):
            return None
    m = re.search(
        r"(?:CHANCE\s*MIX[:\s]*)?(1X|X2|12|X|1|2)\s+O\s+(GG|GOL|OVER\s*\d+(?:\.\d+)?|UNDER\s*\d+(?:\.\d+)?)",
        text,
    )
    if not m:
        return None
    left, right = m.group(1), m.group(2).replace(" ", "")
    if right in ("GG", "GOL"):
        right = "GG"
    mix = f"{left} o {right}"
    return NetwinMarketAction(
        family="CHANCE_MIX",
        pick=mix,
        chance_mix=mix,
        raw=text,
    )


def _parse_specialty(
    text: str,
    market_n: str,
    *,
    family: str,
    keywords: tuple[str, ...],
) -> Optional[NetwinMarketAction]:
    hay = f"{market_n} {text}"
    if not any(k in hay for k in keywords):
        return None
    ou = _parse_ou(text)
    if ou is not None:
        side, line = ou
        scope = _corner_scope(text) if family == "CORNER" else None
        return NetwinMarketAction(
            family=family,
            pick=f"{side} {line:g}",
            specialty_side=side,
            specialty_line=line,
            specialty_scope=scope,
            raw=text,
        )
    for token in ("1X", "X2", "12", "1", "X", "2"):
        if re.search(rf"(?<![0-9A-Z]){token}(?![0-9A-Z])", text):
            return NetwinMarketAction(
                family=family,
                pick=token,
                specialty_side=token,
                raw=text,
            )
    return NetwinMarketAction(family=family, pick=text, raw=text)


def _corner_scope(text: str) -> str:
    """HOME/AWAY when the corner line belongs to one side, otherwise the match total."""
    if re.search(r"\b(?:CASA|HOME)\b", text):
        return "HOME"
    if re.search(r"\b(?:OSPITE|AWAY)\b", text):
        return "AWAY"
    return "TOTAL"


def _parse_multigol(text: str, raw: str) -> NetwinMarketAction:
    m = re.search(
        r"MULTIGOL\s+(\d+\s*-\s*\d+)(?:\s+(CASA|OSPITE|HOME|AWAY|TOTALE|MATCH|PARTITA))?",
        text,
    )
    rng = m.group(1).replace(" ", "") if m else None
    if not rng:
        loose = re.search(r"(\d+\s*-\s*\d+)", text)
        rng = loose.group(1).replace(" ", "") if loose else None
    if not rng:
        raise UnsupportedNetwinMarket(f"MultiGol without range: {raw!r}")
    scope = "MATCH"
    token = (m.group(2) if m else None) or ""
    if token in ("CASA", "HOME") or "CASA" in text or "HOME" in text:
        scope = "HOME"
    elif token in ("OSPITE", "AWAY") or "OSPITE" in text or "AWAY" in text:
        scope = "AWAY"
    return NetwinMarketAction(
        family="MULTIGOL",
        pick=f"MULTIGOL {rng}",
        multigol_range=rng,
        multigol_scope=scope,
        raw=raw,
    )


_VS_SPLIT = re.compile(r"\s+vs\.?\s+|\s+v\s+", re.IGNORECASE)
_STOP_TOKENS = {
    "fc", "cf", "sc", "ac", "as", "the", "de", "del", "la", "el",
    "club", "calcio", "united", "city", "sporting", "ss", "ud",
}


def split_home_away(match_info: dict) -> tuple[str, str]:
    home = str(match_info.get("home") or "").strip()
    away = str(match_info.get("away") or "").strip()
    match = str(match_info.get("match") or "").strip()
    if match:
        parts = _VS_SPLIT.split(match, maxsplit=1)
        if len(parts) == 2:
            home = home or parts[0].strip()
            away = away or parts[1].strip()
        elif not home:
            home = match
    return home, away


def significant_tokens(name: str) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9]+", (name or "").lower())
    kept = [w for w in words if w not in _STOP_TOKENS and len(w) >= 3]
    return kept or words[:1]


def row_matches_teams(row_text: str, home: str, away: str = "") -> bool:
    blob = (row_text or "").lower()
    home_ok = any(tok in blob for tok in significant_tokens(home))
    if not away:
        return home_ok
    away_ok = any(tok in blob for tok in significant_tokens(away))
    return home_ok and away_ok


def is_real_netwin_booking_code(code: Optional[str]) -> bool:
    return bool(code) and re.fullmatch(r"\d{6}", str(code)) is not None


def extract_booking_code(scoped_text: str) -> Optional[str]:
    """Extract a 6-digit booking code only from a prenotazione-scoped snippet."""
    if not scoped_text:
        return None
    if not re.search(r"prenotazion|codice", scoped_text, re.IGNORECASE):
        return None
    labeled = re.search(
        r"codice(?:\s+prenotazione)?[^\d]{0,24}(\d{6})",
        scoped_text,
        re.IGNORECASE,
    )
    if labeled:
        return labeled.group(1)
    if re.search(r"prenotazion", scoped_text, re.IGNORECASE):
        found = re.findall(r"\b(\d{6})\b", scoped_text)
        if len(found) == 1:
            return found[0]
    return None


def market_tab_labels(action: NetwinMarketAction) -> list[str]:
    if action.family == "COMBO":
        if action.combo_type == "MULTIGOL":
            if action.combo_result in ("1X", "X2", "12"):
                return ["Doppia Chance + MultiGol", "DC + MultiGol", "COMBO", "MultiGol"]
            return ["1X2 + MultiGol", "Esito + MultiGol", "COMBO", "MultiGol"]
        if action.combo_type == "BTTS":
            if action.combo_result in ("1X", "X2", "12"):
                return ["Doppia Chance + Gol/NoGol", "DC + G/NG", "COMBO"]
            return ["1X2 + Gol/NoGol", "1X2 + Gol", "COMBO"]
        if action.combo_result in ("1X", "X2", "12"):
            return [
                "Doppia Chance + U/O",
                "Doppia Chance + Under/Over",
                "DC + U/O",
                "1X2 + U/O",
            ]
        return ["1X2 + U/O", "1X2 + Under/Over", "1X2 + Over/Under"]
    if action.family == "OU":
        return ["Under/Over", "U/O", "Over/Under"]
    if action.family == "MULTIGOL":
        return ["MultiGol", "Multigol", "Multi Gol"]
    if action.family == "BTTS":
        return ["Gol/NoGol", "Gol / No Gol", "G/NG"]
    if action.family == "CORNER":
        return [
            "Corner",
            "Angoli",
            "Calci d'angolo",
            "1X2 Corner",
            "Under/Over Corner",
            "U/O Corner",
        ]
    if action.family == "CARDS":
        return [
            "Cartellini",
            "Sanzioni",
            "Ammonizioni",
            "Under/Over Cartellini",
            "1X2 Cartellini",
        ]
    if action.family == "CHANCE_MIX":
        return ["Chance Mix", "Combinazioni speciali", "Mix"]
    return []


def outcome_search_texts(action: NetwinMarketAction) -> list[str]:
    texts: list[str] = []
    if action.family == "COMBO" and action.combo_result and action.combo_type == "MULTIGOL":
        res = action.combo_result
        rng = action.combo_multigol_range or ""
        texts.extend(
            [
                f"{res} + MultiGol {rng}",
                f"{res}+MultiGol {rng}",
                f"MultiGol {rng}",
                rng,
            ]
        )
    elif action.family == "COMBO" and action.combo_result and action.combo_type == "BTTS":
        res = action.combo_result
        label = "NoGol" if action.combo_ou_side == "NOGOL" else "Gol"
        texts.extend([f"{res} + {label}", f"{res}+{label}", label])
    elif action.family == "COMBO" and action.combo_result and action.combo_ou_side:
        side = "Under" if action.combo_ou_side == "UNDER" else "Over"
        line = action.combo_ou_line or 1.5
        line_s = f"{line:g}"
        res = action.combo_result
        texts.extend(
            [
                f"{res} + {side} {line_s}",
                f"{res}+{side} {line_s}",
                f"{res} {side} {line_s}",
                f"{side} {line_s}",
            ]
        )
    if action.family == "OU" and action.ou_line is not None:
        side = "Under" if action.pick == "UNDER" else "Over"
        line_s = f"{action.ou_line:g}"
        texts.extend([f"{side} {line_s}", line_s])
    if action.family == "MULTIGOL" and action.multigol_range:
        texts.extend(
            [
                action.multigol_range,
                f"MultiGol {action.multigol_range}",
                action.multigol_range.replace("-", " - "),
            ]
        )
        if action.multigol_scope == "HOME":
            texts.append(f"MultiGol {action.multigol_range} Casa")
        elif action.multigol_scope == "AWAY":
            texts.append(f"MultiGol {action.multigol_range} Ospite")
    if action.family in ("CORNER", "CARDS"):
        if action.specialty_side in ("OVER", "UNDER") and action.specialty_line is not None:
            side = "Over" if action.specialty_side == "OVER" else "Under"
            line_s = f"{action.specialty_line:g}"
            texts.extend([f"{side} {line_s}", line_s, f"{side} {line_s} Totale"])
            if action.specialty_scope == "HOME":
                texts.append(f"{side} {line_s} Casa")
            elif action.specialty_scope == "AWAY":
                texts.append(f"{side} {line_s} Ospite")
        elif action.specialty_side:
            texts.append(action.specialty_side)
    if action.family == "CHANCE_MIX" and action.chance_mix:
        mix = action.chance_mix
        texts.extend(
            [
                mix,
                mix.replace(" o ", " O "),
                mix.replace("GG", "Gol"),
                mix.replace(" o ", "+"),
            ]
        )
    return texts
