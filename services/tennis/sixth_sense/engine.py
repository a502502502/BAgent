"""
TennisSixthSense — Sesto Senso per il tennis.

Cerca notizie su infortuni, ritiri, forma recente, problemi fisici
dei giocatori prima di una partita.

Utilizzo:
    from services.tennis.sixth_sense.engine import TennisSixthSense
    ss = TennisSixthSense()
    events = ss.analyze("Carlos Alcaraz", "Jannik Sinner", surface="clay")
    print(events.summary)
    print(events.p1_factor)   # moltiplicatore forza P1 (es. 0.88 se infortunato)
    print(events.p2_factor)   # moltiplicatore forza P2
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone

from services.football.external.sources.news import SixthSenseNewsCollector


@dataclass
class TennisEvent:
    player: str
    event_type: str       # injury | fatigue | withdrawal_risk | morale | form
    impact: float         # -3..+3 (negativo = svantaggia il giocatore)
    confidence: float     # 0.0..1.0
    description: str


@dataclass
class TennisSixthSenseResult:
    player1: str
    player2: str
    status: str           # OK | NO_NEWS | ERROR
    events: list[TennisEvent] = field(default_factory=list)
    summary: str = ""
    overall_confidence: float = 0.0

    # Fattori moltiplicativi per il modello (1.0 = neutro)
    p1_factor: float = 1.0
    p2_factor: float = 1.0

    def to_dict(self) -> dict:
        return {
            "player1":            self.player1,
            "player2":            self.player2,
            "status":             self.status,
            "summary":            self.summary,
            "overall_confidence": self.overall_confidence,
            "p1_factor":          self.p1_factor,
            "p2_factor":          self.p2_factor,
            "events":             [vars(e) for e in self.events],
        }


# ── Parsing risposta LLM ──────────────────────────────────────────────────────

def _parse_llm_events(text: str, player1: str, player2: str) -> list[TennisEvent]:
    """
    Estrae eventi strutturati dal testo LLM in formato JSON-like.
    Cerca pattern: player, event_type, impact, confidence, description.
    """
    import json, re

    events: list[TennisEvent] = []

    # Prova parsing JSON se il modello ha risposto in JSON
    json_match = re.search(r"\[.*?\]", text, re.DOTALL)
    if json_match:
        try:
            raw = json.loads(json_match.group())
            for item in raw:
                if isinstance(item, dict):
                    events.append(TennisEvent(
                        player=item.get("player", ""),
                        event_type=item.get("event_type", "other"),
                        impact=float(item.get("impact", 0)),
                        confidence=float(item.get("confidence", 0.5)),
                        description=item.get("description", ""),
                    ))
            return events
        except Exception:
            pass

    # Fallback: parsing riga per riga
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("="):
            continue
        # Cerca menzione di giocatori + keyword
        p = None
        if player1.split()[-1].lower() in line.lower():
            p = player1
        elif player2.split()[-1].lower() in line.lower():
            p = player2
        if not p:
            continue

        etype = "other"
        impact = 0.0
        if any(w in line.lower() for w in ["infort", "injur", "hurt", "retire", "forfait", "bless"]):
            etype = "injury"
            impact = -2.0
        elif any(w in line.lower() for w in ["fatig", "stanc", "tante partite", "days rest"]):
            etype = "fatigue"
            impact = -1.0
        elif any(w in line.lower() for w in ["form", "winning", "confidence", "vittori"]):
            etype = "form"
            impact = 1.0

        if impact != 0.0:
            events.append(TennisEvent(
                player=p,
                event_type=etype,
                impact=impact,
                confidence=0.5,
                description=line[:200],
            ))

    return events


def _impact_to_factor(events: list[TennisEvent], player: str) -> float:
    """
    Converte gli eventi in un fattore moltiplicativo [0.7, 1.3].
    -3 → 0.70 (fortemente svantaggiato)
     0 → 1.00 (neutro)
    +3 → 1.30 (fortemente avvantaggiato)
    """
    total_impact = sum(
        e.impact * e.confidence
        for e in events
        if player.split()[-1].lower() in e.player.lower() or e.player == player
    )
    # Scala: ±3 impact → ±30% factor
    factor = 1.0 + (total_impact / 10.0)
    return round(max(0.70, min(1.30, factor)), 3)


# ── Engine principale ─────────────────────────────────────────────────────────

class TennisSixthSense:
    """
    Sesto Senso per il tennis.
    Usa lo stesso news collector del calcio, ma con query ottimizzate per tennis.
    """

    TENNIS_QUERIES = [
        "{player} infortunio OR ritiro OR forfait OR injury OR withdrawal",
        "{player} tennis news form",
    ]

    def __init__(
        self,
        anthropic_key: Optional[str] = None,
        newsapi_key: Optional[str] = None,
        llm_model: str = "claude-haiku-4-5-20251001",
    ):
        self._anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY")
        self._newsapi_key = newsapi_key or os.getenv("NEWSAPI_KEY")
        self._model = llm_model
        self._collector = SixthSenseNewsCollector(newsapi_key=self._newsapi_key)

    def analyze(
        self,
        player1: str,
        player2: str,
        surface: str = "hard",
        tournament: str = "",
        match_date: Optional[str] = None,
        verbose: bool = False,
    ) -> TennisSixthSenseResult:
        """
        Analizza notizie su entrambi i giocatori.

        Ritorna TennisSixthSenseResult con:
        - events: lista eventi trovati
        - p1_factor / p2_factor: moltiplicatori per il modello (usati in TennisEngine)
        - summary: sintesi testuale
        """

        if verbose:
            print(f"[TennisSS] Ricerca notizie: {player1} vs {player2}")

        # Raccolta notizie (sfruttiamo il collector del calcio con home/away = p1/p2)
        try:
            bundle = self._collector.collect(
                home=player1,
                away=player2,
                match_date=match_date,
                max_per_team=6,
            )
        except Exception as e:
            return TennisSixthSenseResult(
                player1=player1, player2=player2,
                status="ERROR", summary=str(e),
            )

        total = bundle.get("total_articles", 0)
        if verbose:
            print(f"[TennisSS] {total} articoli raccolti")

        if total == 0:
            return TennisSixthSenseResult(
                player1=player1, player2=player2,
                status="NO_NEWS", summary="Nessuna notizia trovata.",
            )

        # Prepara prompt
        news_text = self._collector.format_for_llm(bundle)
        prompt = self._build_prompt(player1, player2, surface, tournament, news_text)

        # Analisi LLM
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._anthropic_key)
            msg = client.messages.create(
                model=self._model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            llm_text = msg.content[0].text if msg.content else ""
        except Exception as e:
            # Se LLM non disponibile, usa parsing euristico diretto
            llm_text = news_text
            if verbose:
                print(f"[TennisSS] LLM non disponibile ({e}), parsing euristico")

        events = _parse_llm_events(llm_text, player1, player2)

        p1_factor = _impact_to_factor(events, player1)
        p2_factor = _impact_to_factor(events, player2)

        # Summary
        if events:
            summary_parts = []
            for ev in events:
                sign = "+" if ev.impact > 0 else ""
                summary_parts.append(f"{ev.player} [{ev.event_type}: {sign}{ev.impact:.0f}]")
            summary = " | ".join(summary_parts)
        else:
            summary = "Nessun evento rilevante trovato."

        overall_conf = (
            sum(e.confidence for e in events) / len(events)
            if events else 0.0
        )

        return TennisSixthSenseResult(
            player1=player1,
            player2=player2,
            status="OK",
            events=events,
            summary=summary,
            overall_confidence=round(overall_conf, 2),
            p1_factor=p1_factor,
            p2_factor=p2_factor,
        )

    def _build_prompt(
        self, p1: str, p2: str, surface: str, tournament: str, news_text: str
    ) -> str:
        ctx = f"Torneo: {tournament} | Superficie: {surface}" if tournament else f"Superficie: {surface}"
        return f"""Sei un analista tennis. Analizza le notizie e identifica fattori rilevanti per la partita {p1} vs {p2}.
{ctx}

{news_text}

Identifica eventi che influenzano la partita. Rispondi SOLO con un array JSON:
[
  {{
    "player": "nome giocatore",
    "event_type": "injury|fatigue|withdrawal_risk|morale|form",
    "impact": numero da -3 a +3,
    "confidence": numero da 0.0 a 1.0,
    "description": "breve spiegazione in italiano"
  }}
]

Se non trovi nulla di rilevante, rispondi con [].
Non aggiungere testo fuori dal JSON."""
