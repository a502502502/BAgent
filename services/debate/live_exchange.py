"""
Confronto sul bus tra Cursor e Antigravity.

Cursor misura la selezione (motore, DNA, coerenza delle quote, validatore) e pubblica
le obiezioni. Antigravity replica. Una frase non cancella un'obiezione: solo CONCEDE
ritira la selezione, solo REPLACE la rimisura. Il voto non dice mai che la schedina
è prenotabile su Netwin.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from services.mcp.agent_bus_store import AgentBusStore

SWEET_MIN = 0.72
SWEET_MAX = 0.88
MIN_EDGE = 0.04
TRAP_ODD = 1.22
DRIFT = 0.05
STOCK_SIXTH_SENSE = (
    "avvio diesel",
    "corto muso palmeiras",
    "dixon-coles calibrato",
    "profilo conforme al dna",
)

_LEG_LINE = re.compile(r"LEG\s*(\d+)\s*:\s*(CONCEDE|HOLD|REPLACE)\b(.*)$", re.IGNORECASE)
_MARKET = re.compile(r'market\s*=\s*"([^"]+)"', re.IGNORECASE)
_ODD = re.compile(r"odd\s*=\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
_SENSE = re.compile(r'sixth_sense\s*=\s*"([^"]*)"', re.IGNORECASE)
_PERIOD = re.compile(r"tempo|\b1\s*°?\s*t\b|primo tempo", re.IGNORECASE)
_CEILING = re.compile(r"multigol\s*0\s*-\s*[12]", re.IGNORECASE)
_SIDE = re.compile(r"\b(?:casa|ospite|home|away)\b", re.IGNORECASE)


def iso_kickoff(raw: str) -> str:
    """`20261009 00:30:00` diventa `2026-10-09`. Gli altri formati restano così come sono."""
    text = (raw or "").strip()
    matched = re.match(r"(\d{4})(\d{2})(\d{2})", text)
    if matched:
        return f"{matched.group(1)}-{matched.group(2)}-{matched.group(3)}"
    return text[:10]


def blocking_objections(measurement: Dict[str, Any]) -> List[Dict[str, str]]:
    """Obiezioni che una replica in prosa non può cancellare."""
    market = str(measurement.get("market") or "")
    blocks: List[Dict[str, str]] = []

    def add(code: str, detail: str) -> None:
        blocks.append({"code": code, "detail": detail})

    # Regola 45' rimossa: i mercati 1° Tempo (MultiGol 0-1 1°T, Under 1.5 1°T, ecc.)
    # sono pienamente ammessi e prezzati matematicamente via Poisson (xG * 0.45).
    engine_p = measurement.get("engine_probability")
    if engine_p is None:
        add(
            "ENGINE_UNMAPPED",
            "Il motore Dixon-Coles del validatore non assegna una probabilità a questo mercato.",
        )
    claimed = measurement.get("claimed_probability")
    if engine_p is not None and claimed is not None and abs(float(engine_p) - float(claimed)) > DRIFT:
        add(
            "PROBABILITY_DRIFT",
            f"Probabilità dichiarata {float(claimed):.1%} contro {float(engine_p):.1%} del motore sullo storico.",
        )
    if engine_p is not None and not (SWEET_MIN <= float(engine_p) <= SWEET_MAX):
        add(
            "OUTSIDE_SWEET_SPOT",
            f"Probabilità del motore {float(engine_p):.1%} fuori dalla fascia {SWEET_MIN:.0%}-{SWEET_MAX:.0%}.",
        )
    odd = measurement.get("book_odd")
    if engine_p is not None and odd is not None:
        edge = float(engine_p) * float(odd) - 1.0
        if edge < MIN_EDGE:
            add("EDGE_BELOW_4", f"Edge del motore {edge:+.1%} sotto +4% a quota {float(odd):.2f}.")
    if odd is not None and float(odd) < TRAP_ODD:
        add("TRAP_ODD", f"Quota {float(odd):.2f} sotto 1.22.")
    if measurement.get("dna_prohibited"):
        add("DNA_RED", measurement.get("dna_reason") or "Semaforo rosso del DNA.")
    archetype = str(measurement.get("dna_archetype") or "")
    if archetype == "ASYMMETRIC_DOMINANCE" and _CEILING.search(market) and _SIDE.search(market):
        add(
            "CEILING_ON_DOMINANT",
            "Tetto di gol sulla squadra dominante: il DNA chiede un mercato aperto.",
        )
    straight = measurement.get("straight_result_odd")
    if straight is not None and market.strip().casefold() in {"x2", "1x"}:
        if float(odd or 0) >= float(straight) - 0.08:
            add(
                "INCOHERENT_DOUBLE_CHANCE",
                f"La doppia chance @{float(odd):.2f} è a ridosso del secco @{float(straight):.2f}.",
            )
    sense = str(measurement.get("sixth_sense") or "").strip()
    if len(sense) < 15 or any(token in sense.casefold() for token in STOCK_SIXTH_SENSE):
        add("STOCK_SIXTH_SENSE", "Manca una rassegna stampa: la formula fissa non è il Sesto Senso.")
    if measurement.get("validator_passed") is False:
        add(
            "VALIDATOR_BLOCK",
            measurement.get("validator_reason") or "strict_validator non ha firmato la selezione.",
        )
    return blocks


def parse_rebuttal(text: str) -> Dict[int, Dict[str, Any]]:
    """Legge le righe `LEG n: CONCEDE|HOLD|REPLACE`. Senza righe, nessuna modifica."""
    actions: Dict[int, Dict[str, Any]] = {}
    for line in (text or "").splitlines():
        matched = _LEG_LINE.search(line.strip())
        if not matched:
            continue
        index = int(matched.group(1))
        operation = matched.group(2).upper()
        tail = matched.group(3) or ""
        action: Dict[str, Any] = {"op": operation}
        market = _MARKET.search(tail)
        odd = _ODD.search(tail)
        sense = _SENSE.search(tail)
        if market:
            action["market"] = market.group(1)
        if odd:
            action["odd"] = float(odd.group(1))
        if sense:
            action["sixth_sense"] = sense.group(1)
        actions[index] = action
    return actions


def apply_rebuttal(
    legs: List[Dict[str, Any]],
    actions: Dict[int, Dict[str, Any]],
    remeasure: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Applica la replica. HOLD e la prosa lasciano le obiezioni dove stanno."""
    updated: List[Dict[str, Any]] = []
    for leg in legs:
        index = int(leg["index"])
        action = actions.get(index, {"op": "HOLD"})
        operation = action.get("op", "HOLD")
        if operation == "CONCEDE":
            updated.append({**leg, "status": "WITHDRAWN", "objections": []})
            continue
        if operation == "REPLACE":
            proposal = {
                **leg,
                "market": action.get("market", leg.get("market")),
                "book_odd": action.get("odd", leg.get("book_odd")),
                "sixth_sense": action.get("sixth_sense", leg.get("sixth_sense") or ""),
                "claimed_probability": None,
                "claimed_edge": None,
            }
            measured = remeasure(proposal)
            measured["index"] = index
            measured["objections"] = blocking_objections(measured)
            measured["status"] = _status_of(measured)
            updated.append(measured)
            continue
        kept = dict(leg)
        kept["objections"] = list(kept.get("objections") or blocking_objections(kept))
        kept["status"] = "BLOCKED" if kept["objections"] else _status_of(kept)
        updated.append(kept)
    return updated


def _status_of(measurement: Dict[str, Any]) -> str:
    if measurement.get("objections"):
        return "BLOCKED"
    if measurement.get("validator_passed") is True:
        return "PASSED_VALIDATOR"
    return "UNRESOLVED"


def format_critique(title: str, legs: List[Dict[str, Any]]) -> str:
    """Testo che Cursor pubblica sul bus. Chiede una replica con le righe LEG."""
    lines = [
        f"CRITICA DI CURSOR — {title}",
        "Le obiezioni qui sotto restano finché la replica non ritira la selezione o non la sostituisce.",
        "Formato: LEG <n>: CONCEDE   oppure   LEG <n>: REPLACE market=\"...\" odd=1.40",
        "Una difesa in prosa non cambia il voto.",
        "",
    ]
    for leg in legs:
        lines.append(
            f"LEG {leg['index']}: {leg.get('match_name')} — {leg.get('market')} @{float(leg.get('book_odd') or 0):.2f}"
        )
        engine_p = leg.get("engine_probability")
        if engine_p is None:
            lines.append("  Motore: probabilità non assegnata.")
        else:
            lines.append(f"  Motore: P {float(engine_p):.1%} | DNA {leg.get('dna_status')} / {leg.get('dna_archetype')}")
        claimed = leg.get("claimed_probability")
        if claimed is not None:
            lines.append(f"  Dichiarata: P {float(claimed):.1%}")
        for objection in leg.get("objections") or []:
            lines.append(f"  - {objection['code']}: {objection['detail']}")
        lines.append("")
    return "\n".join(lines).strip()


def verdict_text(title: str, legs: List[Dict[str, Any]]) -> str:
    """Sintesi del voto. Non usa la formula di consenso dell'arena euristica."""
    passed = [leg for leg in legs if leg.get("status") == "PASSED_VALIDATOR"]
    withdrawn = [leg for leg in legs if leg.get("status") == "WITHDRAWN"]
    blocked = [leg for leg in legs if leg.get("status") not in {"PASSED_VALIDATOR", "WITHDRAWN"}]
    lines = [f"VOTO DI CURSOR — {title}"]
    if passed and not blocked:
        lines.append(
            f"{len(passed)} selezioni hanno passato il validatore. {len(withdrawn)} ritirate. "
            "Questo voto non è una prenotazione Netwin."
        )
    else:
        lines.append(
            f"Schedina non giocabile. Bloccate: {len(blocked)}. "
            f"Passate dal validatore: {len(passed)}. Ritirate: {len(withdrawn)}."
        )
    for leg in legs:
        lines.append(f"LEG {leg['index']}: {leg.get('status')} — {leg.get('match_name')} / {leg.get('market')}")
        for objection in leg.get("objections") or []:
            lines.append(f"  - {objection['code']}: {objection['detail']}")
    return "\n".join(lines)


class LiveTicketDebate:
    """Apre il dibattito, pubblica la critica e giudica la replica arrivata sul bus."""

    def __init__(
        self,
        store: Optional[AgentBusStore] = None,
        measurer: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ):
        self.store = store or AgentBusStore()
        self.measurer = measurer or measure_leg

    def open(self, title: str, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Misura le selezioni e lascia il dibattito in attesa della replica."""
        legs = []
        for index, proposal in enumerate(proposals, start=1):
            measured = self.measurer(proposal)
            measured["index"] = index
            measured["objections"] = blocking_objections(measured)
            measured["status"] = "BLOCKED" if measured["objections"] else _status_of(measured)
            legs.append(measured)
        debate_id = f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        critique = format_critique(title, legs)
        debate = {
            "debate_id": debate_id,
            "title": title,
            "status": "AWAITING_REBUTTAL",
            "legs": legs,
            "turns": [
                {"role": "Cursor", "kind": "CRITIQUE", "content": critique},
            ],
        }
        self.store.upsert_debate(debate)
        self.store.post_message(
            sender="Cursor",
            recipient="Antigravity",
            message_type="DEBATE_CRITIQUE",
            content=critique,
            metadata={"debate_id": debate_id},
        )
        return self.store.get_debate(debate_id) or debate

    def rebut(self, debate_id: str, text: str, sender: str = "Antigravity") -> Dict[str, Any]:
        """Registra la replica. Non vota."""
        debate = self._require(debate_id)
        debate.setdefault("turns", []).append(
            {"role": sender, "kind": "REBUTTAL", "content": text.strip()}
        )
        debate["status"] = "AWAITING_VERDICT"
        self.store.upsert_debate(debate)
        self.store.post_message(
            sender=sender,
            recipient="Cursor",
            message_type="DEBATE_REBUTTAL",
            content=text.strip(),
            metadata={"debate_id": debate_id},
        )
        return self.store.get_debate(debate_id) or debate

    def judge(self, debate_id: str) -> Dict[str, Any]:
        """Rimisura dopo l'ultima replica e pubblica il voto."""
        debate = self._require(debate_id)
        rebuttals = [turn for turn in debate.get("turns", []) if turn.get("kind") == "REBUTTAL"]
        text = rebuttals[-1]["content"] if rebuttals else ""
        legs = apply_rebuttal(debate.get("legs", []), parse_rebuttal(text), self.measurer)
        passed = [leg for leg in legs if leg.get("status") == "PASSED_VALIDATOR"]
        blocked = [leg for leg in legs if leg.get("status") not in {"PASSED_VALIDATOR", "WITHDRAWN"}]
        approved = bool(passed) and not blocked
        summary = verdict_text(debate.get("title") or debate_id, legs)
        debate["legs"] = legs
        debate["status"] = "PASSED_VALIDATOR" if approved else "REJECTED"
        debate["approved"] = approved
        debate.setdefault("turns", []).append(
            {"role": "Cursor", "kind": "VERDICT", "content": summary}
        )
        self.store.upsert_debate(debate)
        self.store.post_message(
            sender="Cursor",
            recipient="Antigravity",
            message_type="DEBATE_VERDICT",
            content=summary,
            metadata={"debate_id": debate_id, "approved": approved},
        )
        return self.store.get_debate(debate_id) or debate

    def wait_rebuttal(self, debate_id: str, timeout: float = 120, interval: float = 2.0) -> Optional[Dict[str, Any]]:
        """Attende DEBATE_REBUTTAL e poi vota. None se Antigravity non replica in tempo."""
        current = self.store.get_debate(debate_id)
        if current and current.get("status") == "AWAITING_VERDICT":
            return self.judge(debate_id)
        message = self.store.wait_for_debate_message(
            debate_id,
            "DEBATE_REBUTTAL",
            timeout=timeout,
            interval=interval,
        )
        if message is None:
            return None
        current = self.store.get_debate(debate_id)
        if not current or current.get("status") != "AWAITING_VERDICT":
            self.rebut(
                debate_id,
                message.get("content") or "",
                sender=message.get("sender") or "Antigravity",
            )
        return self.judge(debate_id)

    def _require(self, debate_id: str) -> Dict[str, Any]:
        debate = self.store.get_debate(debate_id)
        if debate is None:
            raise KeyError(f"Dibattito {debate_id} assente sul bus")
        return debate


def measure_leg(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Misura una selezione contro cache Netwin, motore, DNA e strict_validator."""
    match_name = str(proposal.get("match_name") or "")
    tournament = str(proposal.get("tournament") or "")
    market = str(proposal.get("market") or "")
    odd = float(proposal.get("book_odd") or 0)
    sense = str(proposal.get("sixth_sense") or "")
    measurement: Dict[str, Any] = {
        "match_name": match_name,
        "tournament": tournament,
        "market": market,
        "book_odd": odd,
        "claimed_probability": proposal.get("claimed_probability"),
        "claimed_edge": proposal.get("claimed_edge"),
        "sixth_sense": sense,
        "is_period": bool(_PERIOD.search(market)),
        "engine_probability": None,
        "dna_status": "",
        "dna_archetype": "",
        "dna_prohibited": False,
        "dna_reason": "",
        "straight_result_odd": None,
        "validator_passed": None,
        "validator_reason": "",
    }
    cached = _cached_match(match_name)
    xg_home = xg_away = None
    if cached is not None:
        tournament = tournament or cached.tournament
        measurement["tournament"] = tournament
        from services.betting.netwin_cache_reader import estimate_xg

        xg_home, xg_away = estimate_xg(cached)
        cache_odd = cached.odds_dict.get(market)
        if cache_odd is not None:
            measurement["book_odd"] = float(cache_odd)
            odd = float(cache_odd)
        key = "2" if market.strip().casefold() == "x2" else "1" if market.strip().casefold() == "1x" else ""
        if key and key in cached.odds_dict:
            measurement["straight_result_odd"] = float(cached.odds_dict[key])
        kickoff = iso_kickoff(cached.kickoff)
    else:
        kickoff = iso_kickoff(str(proposal.get("kickoff") or ""))

    if xg_home and xg_away and not measurement["is_period"]:
        from services.analysis.xg_poisson_engine import QuantitativeEngine

        measurement["engine_probability"] = QuantitativeEngine().goal_market_probability(
            xg_home, xg_away, market
        )

    try:
        from services.analysis.league_dna_market_matcher import LeagueDNAMarketMatcher

        dna = LeagueDNAMarketMatcher().check_market_suitability(
            tournament,
            _side(match_name, 0),
            _side(match_name, 1),
            market,
            "",
            odd,
        )
        measurement["dna_status"] = dna.status
        measurement["dna_archetype"] = dna.team_archetype
        measurement["dna_prohibited"] = bool(dna.is_prohibited)
        measurement["dna_reason"] = dna.rejection_reason or dna.tactical_rationale or ""
    except Exception as error:
        measurement["dna_reason"] = f"DNA non calcolato: {error}"

    measurement["validator_passed"], measurement["validator_reason"] = _run_validator(
        measurement,
        xg_home,
        xg_away,
        kickoff,
    )
    return measurement


def _side(match_name: str, index: int) -> str:
    parts = re.split(r"\s+vs\s+", match_name, flags=re.IGNORECASE)
    if len(parts) != 2:
        return ""
    return parts[index].strip()


def _cached_match(match_name: str):
    try:
        from services.betting.netwin_cache_reader import load_cached_matches
    except Exception:
        return None
    wanted = match_name.casefold().strip()
    for match in load_cached_matches():
        if match.match_name.casefold().strip() == wanted:
            return match
    return None


def _run_validator(measurement: Dict[str, Any], xg_home, xg_away, kickoff: str):
    try:
        from services.betting.strict_ticket_pipeline import MarketCandidate, StrictTicketPipeline
    except Exception as error:
        return False, f"Validatore non caricato: {error}"
    home_played, away_played = _played_counts(measurement["match_name"])
    candidate = MarketCandidate(
        match_name=measurement["match_name"],
        tournament=measurement.get("tournament") or "",
        market_name=measurement["market"],
        bookmaker_odd=float(measurement["book_odd"]),
        xg_home=xg_home,
        xg_away=xg_away,
        kickoff_time=kickoff,
        is_first_half_only=bool(measurement.get("is_period")),
        is_intermediate_deadline=bool(measurement.get("is_period")),
        sixth_sense_analysis=str(measurement.get("sixth_sense") or ""),
        verified_sources_checked=bool(
            home_played is not None and away_played is not None and home_played >= 3 and away_played >= 3
        ),
        home_matches_played=home_played,
        away_matches_played=away_played,
    )
    try:
        report = StrictTicketPipeline().validate_candidate(candidate)
    except Exception as error:
        return False, f"Validatore in errore: {error}"
    return bool(report.passed), report.rejection_reason or ""


def _played_counts(match_name: str):
    home, away = _side(match_name, 0), _side(match_name, 1)
    if not home or not away:
        return None, None
    try:
        import sqlite3

        from services.betting.netwin_cache_reader import _find_matching_team
        from services.database.schema import DB_PATH
    except Exception:
        return None, None
    if not DB_PATH.exists():
        return None, None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    except sqlite3.Error:
        return None, None
    try:
        home_name = _find_matching_team(conn, home, home_side=True)
        away_name = _find_matching_team(conn, away, home_side=False)

        def _count(name: str) -> Optional[int]:
            if not name:
                return None
            row = conn.execute(
                """
                SELECT COUNT(league) FROM matches
                WHERE status='FT' AND season='2026' AND (home_team=? OR away_team=?)
                """,
                (name, name),
            ).fetchone()
            if row is None or row[0] is None:
                return None
            return int(row[0])

        return _count(home_name), _count(away_name)
    except sqlite3.Error:
        return None, None
    finally:
        conn.close()
