"""
SixthSenseAnalyzer — usa un LLM per analizzare le notizie di una partita
e restituire eventi strutturati con impatti sulle probabilità.

Il modello legge articoli su squadre/giocatori e produce:
  - lista di eventi rilevanti (infortuni, cambi allenatore, morale, ecc.)
  - impatto stimato su home/draw/away (-3 molto negativo ... +3 molto positivo)
  - confidenza per ogni evento

Richiede: ANTHROPIC_API_KEY nell'environment.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

import anthropic


# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------

@dataclass
class SixthSenseEvent:
    team: str                  # 'home' | 'away' | 'both'
    event_type: str            # injury | coach_change | morale | fatigue | suspension | other
    description: str           # spiegazione breve
    impact: float              # -3.0 ... +3.0 (negativo = penalizza quella squadra)
    confidence: float          # 0.0 ... 1.0
    source_hint: str = ""      # titolo articolo di riferimento

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SixthSenseAnalysis:
    home: str
    away: str
    events: list[SixthSenseEvent] = field(default_factory=list)
    home_adjustment: float = 0.0   # aggiustamento netto sulle prob home
    draw_adjustment: float = 0.0
    away_adjustment: float = 0.0
    overall_confidence: float = 0.0
    summary: str = ""
    raw_response: str = ""
    status: str = "OK"             # OK | NO_NEWS | ERROR | NO_EVENTS

    def to_dict(self) -> dict:
        return {
            "home": self.home,
            "away": self.away,
            "events": [e.to_dict() for e in self.events],
            "home_adjustment": self.home_adjustment,
            "draw_adjustment": self.draw_adjustment,
            "away_adjustment": self.away_adjustment,
            "overall_confidence": self.overall_confidence,
            "summary": self.summary,
            "status": self.status,
        }


# ------------------------------------------------------------------
# System prompt
# ------------------------------------------------------------------

SYSTEM_PROMPT = """Sei un analista di scommesse sportive esperto. Il tuo compito è leggere notizie su una partita di calcio e identificare fattori contestuali che potrebbero influenzare il risultato in modo diverso da quanto già incorporato nelle quote dei bookmaker.

Rispondi SEMPRE e SOLO con un oggetto JSON valido. Nessun testo prima o dopo il JSON.

Schema di risposta:
{
  "events": [
    {
      "team": "home" | "away" | "both",
      "event_type": "injury" | "coach_change" | "morale" | "fatigue" | "suspension" | "motivation" | "other",
      "description": "spiegazione concisa in italiano",
      "impact": <numero da -3.0 a +3.0>,
      "confidence": <numero da 0.0 a 1.0>,
      "source_hint": "titolo o fonte dell'articolo"
    }
  ],
  "summary": "sintesi complessiva in 2-3 frasi",
  "overall_confidence": <numero da 0.0 a 1.0>
}

Scala impatto:
  +3 = fortissimo vantaggio per quella squadra (es. avversario con 5 assenze chiave)
  +2 = vantaggio significativo (es. ritrovata forma mentale dopo cambio allenatore positivo)
  +1 = lieve vantaggio (es. un giocatore importante in dubbio)
   0 = nessun impatto rilevante
  -1 = lieve svantaggio
  -2 = svantaggio significativo (es. infortunio titolare importante)
  -3 = svantaggio gravissimo (es. scandalo, disfunzione totale dello spogliatoio)

Regole importanti:
- L'impatto è relativo alla squadra indicata in "team" (positivo = bene per quella squadra)
- Se non trovi notizie rilevanti, restituisci events: [] e overall_confidence: 0.0
- Non inventare eventi non supportati dalle notizie fornite
- Considera solo notizie recenti (ultime 72 ore sono più rilevanti)
- Sii conservativo: preferisci impatti più bassi se non sei sicuro"""


# ------------------------------------------------------------------
# Analyzer
# ------------------------------------------------------------------

class SixthSenseAnalyzer:
    """
    Invia le notizie raccolte a Claude e riceve un'analisi strutturata.

    Utilizzo:
        analyzer = SixthSenseAnalyzer()
        analysis = analyzer.analyze(news_prompt, home="Juventus", away="Inter")
        print(analysis.to_dict())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-haiku-4-5-20251001",  # veloce ed economico per questa task
    ):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = model

    def analyze(
        self,
        news_prompt: str,
        home: str,
        away: str,
        base_probs: Optional[dict] = None,
    ) -> SixthSenseAnalysis:
        """
        Analizza le notizie e restituisce un'analisi strutturata.

        news_prompt: testo formattato da SixthSenseNewsCollector.format_for_llm()
        base_probs:  probabilità base {home_win, draw, away_win} per contesto aggiuntivo
        """
        if not news_prompt or not news_prompt.strip():
            return SixthSenseAnalysis(
                home=home,
                away=away,
                status="NO_NEWS",
                summary="Nessuna notizia disponibile per l'analisi.",
            )

        # Aggiungi contesto probabilità base se disponibile
        context = news_prompt
        if base_probs:
            context += (
                f"\n\n=== PROBABILITÀ BASE DEL MODELLO STATISTICO ===\n"
                f"Home Win: {base_probs.get('home_win', 'N/A'):.1%}\n"
                f"Draw:     {base_probs.get('draw', 'N/A'):.1%}\n"
                f"Away Win: {base_probs.get('away_win', 'N/A'):.1%}\n"
                f"Il tuo compito è identificare fattori che il modello statistico non vede."
            )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": context}],
            )

            raw = message.content[0].text
            data = self._parse_response(raw)

            events = [
                SixthSenseEvent(
                    team=e.get("team", "both"),
                    event_type=e.get("event_type", "other"),
                    description=e.get("description", ""),
                    impact=float(e.get("impact", 0.0)),
                    confidence=float(e.get("confidence", 0.5)),
                    source_hint=e.get("source_hint", ""),
                )
                for e in data.get("events", [])
            ]

            analysis = SixthSenseAnalysis(
                home=home,
                away=away,
                events=events,
                overall_confidence=float(data.get("overall_confidence", 0.0)),
                summary=data.get("summary", ""),
                raw_response=raw,
                status="OK" if events else "NO_EVENTS",
            )

            return analysis

        except Exception as e:
            return SixthSenseAnalysis(
                home=home,
                away=away,
                status="ERROR",
                summary=f"Errore durante l'analisi: {e}",
            )

    def _parse_response(self, raw: str) -> dict:
        """Estrae JSON dalla risposta del modello, gestendo testo extra."""
        # Cerca blocco JSON esplicito
        match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        # Cerca oggetto JSON diretto
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))

        return {}
