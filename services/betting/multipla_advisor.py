"""
MultiplaAdvisor — filtri e regole per costruire multipla di valore.

Lezioni integrate da partite perse (12/08/2026):
  1. Quote < 1.40 in multipla: aggiungono poco valore, niente protezione
  2. BTTS con probabilità < 62%: troppo vicino al 50/50, rischio alto
  3. Partite di coppa (secondo turno): puntare sulla qualificazione, non sul 1X2
  4. Edge minimo su ogni selezione: almeno +5% rispetto al mercato

Utilizzo:
    advisor = MultiplaAdvisor()
    selezioni = [
        Selection("Copenhagen", "Debrecen", "over_0_5_ht", 0.92, 1.21, cup_leg=2),
        Selection("Rapid Vienna", "Paide", "btts_yes", 0.55, 1.92),
        Selection("GKS Katowice", "Hapoel Tel Aviv", "away_win", 0.65, 3.15, cup_leg=2),
    ]
    report = advisor.analyze(selezioni)
    print(report)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ------------------------------------------------------------------
# Soglie e regole
# ------------------------------------------------------------------

MIN_ODDS          = 1.40    # Quota minima per inserire in multipla
MIN_BTTS_PROB     = 0.62    # Probabilità minima per selezione BTTS
MIN_EDGE          = 0.05    # Edge minimo (nostra prob - prob mercato)
BTTS_MARKETS      = {"btts_yes", "gg", "both_teams_score"}
CUP_1X2_MARKETS   = {"home_win", "away_win", "draw", "1", "x", "2"}


# ------------------------------------------------------------------
# Struttura selezione
# ------------------------------------------------------------------

@dataclass
class Selection:
    """
    Una singola selezione per la multipla.

    Parametri:
        home:           nome squadra casa
        away:           nome squadra ospite
        market:         mercato (es. 'away_win', 'btts_yes', 'over_2_5', 'qualify_away')
        our_prob:       probabilità stimata dal modello (0-1)
        market_odd:     quota offerta dal bookmaker
        cup_leg:        numero del turno di coppa (1 o 2); None se gara secca
        label:          etichetta leggibile (opzionale)
    """
    home:       str
    away:       str
    market:     str
    our_prob:   float
    market_odd: float
    cup_leg:    Optional[int] = None
    label:      Optional[str] = None

    @property
    def market_prob(self) -> float:
        return 1.0 / self.market_odd if self.market_odd > 0 else 1.0

    @property
    def edge(self) -> float:
        return self.our_prob - self.market_prob

    @property
    def display_name(self) -> str:
        return self.label or f"{self.home} vs {self.away} [{self.market}]"


# ------------------------------------------------------------------
# Risultato analisi singola selezione
# ------------------------------------------------------------------

@dataclass
class SelectionVerdict:
    selection:   Selection
    approved:    bool
    warnings:    list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    score:       int = 0    # 0-100

    def summary(self) -> str:
        icon = "✅" if self.approved else "❌"
        lines = [
            f"{icon}  {self.selection.display_name}",
            f"     Quota: {self.selection.market_odd:.2f}  |  "
            f"Nostra prob: {self.selection.our_prob:.1%}  |  "
            f"Mercato: {self.selection.market_prob:.1%}  |  "
            f"Edge: {self.selection.edge:+.1%}  |  "
            f"Score: {self.score}/100",
        ]
        for w in self.warnings:
            lines.append(f"     ⚠️  {w}")
        for s in self.suggestions:
            lines.append(f"     💡 {s}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Advisor principale
# ------------------------------------------------------------------

class MultiplaAdvisor:
    """
    Valuta ogni selezione e decide se includerla in una multipla.

    Regole:
      R1 — Quota minima >= 1.40
      R2 — BTTS: probabilità >= 62%
      R3 — Coppa 2° turno + 1X2: sconsigliato, suggerisci qualificazione
      R4 — Edge minimo >= 5%
      R5 — Probabilità modello >= 55%
    """

    def __init__(
        self,
        min_odds:      float = MIN_ODDS,
        min_btts_prob: float = MIN_BTTS_PROB,
        min_edge:      float = MIN_EDGE,
        min_our_prob:  float = 0.55,
    ):
        self.min_odds      = min_odds
        self.min_btts_prob = min_btts_prob
        self.min_edge      = min_edge
        self.min_our_prob  = min_our_prob

    def evaluate(self, sel: Selection) -> SelectionVerdict:
        warnings:    list[str] = []
        suggestions: list[str] = []
        score = 100
        approved = True

        market_lower = sel.market.lower()

        # R1 — Quota minima
        if sel.market_odd < self.min_odds:
            warnings.append(
                f"Quota {sel.market_odd:.2f} troppo bassa (minimo {self.min_odds:.2f}). "
                "In multipla non protegge dal rischio."
            )
            score -= 40
            approved = False

        # R2 — BTTS
        if market_lower in BTTS_MARKETS:
            if sel.our_prob < self.min_btts_prob:
                warnings.append(
                    f"BTTS con prob {sel.our_prob:.1%} troppo bassa "
                    f"(minimo {self.min_btts_prob:.1%}). Troppo vicino al 50/50."
                )
                score -= 35
                approved = False

        # R3 — Coppa 2° turno + 1X2
        if sel.cup_leg == 2 and market_lower in CUP_1X2_MARKETS:
            warnings.append(
                "Coppa 2° turno: il 1X2 è rischioso. "
                "La squadra in svantaggio gioca in modo atipico."
            )
            suggestions.append(
                "Usa 'qualify_home' o 'qualify_away' invece del 1X2."
            )
            score -= 25
            if sel.our_prob < 0.70:
                approved = False
                score -= 10

        # R4 — Edge minimo
        if sel.edge < self.min_edge:
            warnings.append(
                f"Edge {sel.edge:+.1%} insufficiente (minimo +{self.min_edge:.0%}). "
                "Nessun vantaggio reale sul mercato."
            )
            score -= 20
            if sel.edge < 0:
                approved = False
                score -= 15

        # R5 — Probabilità modello minima
        if sel.our_prob < self.min_our_prob:
            warnings.append(
                f"Prob modello {sel.our_prob:.1%} troppo bassa "
                f"(minimo {self.min_our_prob:.1%}). Selezione coin-flip."
            )
            score -= 25
            approved = False

        score = max(0, min(100, score))
        return SelectionVerdict(
            selection=sel,
            approved=approved,
            warnings=warnings,
            suggestions=suggestions,
            score=score,
        )

    def analyze(self, selections: list[Selection]) -> str:
        verdicts = [self.evaluate(s) for s in selections]
        approved = [v for v in verdicts if v.approved]

        lines = [
            "=" * 65,
            "  MULTIPLA ADVISOR — Analisi selezioni",
            "=" * 65,
            "",
        ]

        for v in verdicts:
            lines.append(v.summary())
            lines.append("")

        lines += ["─" * 65, "  RIEPILOGO", "─" * 65]
        lines.append(f"  Selezioni totali:   {len(selections)}")
        lines.append(f"  Approvate:          {len(approved)}")
        lines.append(f"  Scartate:           {len(selections) - len(approved)}")
        lines.append("")

        if approved:
            multipla_odd  = 1.0
            combined_prob = 1.0
            for v in approved:
                multipla_odd  *= v.selection.market_odd
                combined_prob *= v.selection.our_prob

            lines.append("  Multipla consigliata (solo selezioni approvate):")
            for v in approved:
                lines.append(f"    • {v.selection.display_name}  @{v.selection.market_odd:.2f}")
            lines.append(f"  Quota totale:       {multipla_odd:.2f}")
            lines.append(f"  Prob. combinata:    {combined_prob:.1%}")
            lines.append(f"  EV per €10:         €{10 * combined_prob * multipla_odd - 10:+.2f}")
        else:
            lines.append("  ⛔ Nessuna selezione approvata — non giocare oggi.")

        avg_score = sum(v.score for v in verdicts) / len(verdicts) if verdicts else 0
        lines += ["", f"  Score medio ticket: {avg_score:.0f}/100", "=" * 65]
        return "\n".join(lines)

    def filter_selections(self, selections: list[Selection]) -> list[Selection]:
        """Ritorna solo le selezioni approvate."""
        return [s for s in selections if self.evaluate(s).approved]
