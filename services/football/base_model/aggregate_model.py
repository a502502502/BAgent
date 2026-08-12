"""
AggregateModel — gestione partite di ritorno (doppia sfida).

Calcola:
1. Probabilità base del match di ritorno calibrate sull'andata
2. Probabilità di qualificazione per ogni squadra (via simulazione Poisson)
3. Contesto testuale per il Sesto Senso

Convenzione nomi:
    "home" / "away" si riferiscono sempre al match di RITORNO.
    first_leg_home_goals = gol fatti dalla squadra HOME del ritorno, nella gara di andata.
    first_leg_away_goals = gol fatti dalla squadra AWAY del ritorno, nella gara di andata.

Esempio — Copenhagen (H) vs Debreceni (A) ritorno, andata 0-3 a Debrecen:
    AggregateModel(first_leg_home_goals=3, first_leg_away_goals=0)
    → Copenhagen (home ritorno) ha segnato 3 nell'andata
    → Debreceni (away ritorno) ha segnato 0 nell'andata
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.football.base_model.goal_model import GoalModel


class AggregateModel:

    def __init__(self, first_leg_home_goals: int, first_leg_away_goals: int):
        self.fl_home = int(first_leg_home_goals)
        self.fl_away = int(first_leg_away_goals)

    # ------------------------------------------------------------------
    # Proprietà aggregate
    # ------------------------------------------------------------------

    @property
    def home_aggregate_lead(self) -> int:
        """Vantaggio aggregato della squadra in casa nel ritorno. Negativo = svantaggio."""
        return self.fl_home - self.fl_away

    @property
    def home_ahead(self) -> bool:
        return self.home_aggregate_lead > 0

    @property
    def away_ahead(self) -> bool:
        return self.home_aggregate_lead < 0

    @property
    def level(self) -> bool:
        return self.home_aggregate_lead == 0

    # ------------------------------------------------------------------
    # Probabilità base del ritorno
    # ------------------------------------------------------------------

    def base_return_probs(self, home_field_advantage: float = 0.08) -> dict:
        """
        Stima probabilità 1X2 del ritorno con modello smorzato.

        Logica:
        - Punto di partenza: probabilità neutre di campionato con vantaggio campo
          (home ~44%, draw 28%, away ~28%)
        - Il risultato dell'andata è solo una correzione: ogni gol di differenza
          vale SHIFT_PER_GOAL, cappato a MAX_SHIFT
        - Questo evita di trattare un singolo risultato come prova definitiva
          di forza relativa

        Esempi:
          agg. 0-2 (away avanti 2) → home -16%, away +16% → ~28/28/44
          agg. 4-1 (home avanti 3) → home +24% (cap) → ~68/28/4
          agg. 0-0              → solo vantaggio campo → ~44/28/28
        """
        SHIFT_PER_GOAL = 0.08   # ogni gol di differenza vale 8%
        MAX_SHIFT      = 0.24   # massimo spostamento (equivale a 3 gol)

        # Base neutra con vantaggio campo
        base_home = 0.40 + home_field_advantage * 0.5  # ~0.44
        base_draw = 0.28
        base_away = 1.0 - base_home - base_draw         # ~0.28

        # Vantaggio della squadra in trasferta nel ritorno (= chi ha segnato di più all'andata come ospite)
        away_advantage = self.fl_away - self.fl_home
        shift = max(-MAX_SHIFT, min(MAX_SHIFT, away_advantage * SHIFT_PER_GOAL))

        home_win = base_home - shift
        away_win = base_away + shift
        draw     = base_draw

        # Normalizza e clippa valori minimi
        total = home_win + draw + away_win
        return {
            "home_win": round(max(0.05, home_win / total), 4),
            "draw":     round(draw / total, 4),
            "away_win": round(max(0.05, away_win / total), 4),
        }

    # ------------------------------------------------------------------
    # Probabilità di qualificazione (simulazione Poisson)
    # ------------------------------------------------------------------

    def qualification_probs(
        self,
        goal_model: "GoalModel",
        max_goals: int = 8,
    ) -> dict:
        """
        Usa la score_matrix del GoalModel per simulare tutti i possibili
        risultati del ritorno e calcola chi si qualifica sull'aggregato.

        Note:
        - In caso di parità aggregata si va ai supplementari (ET)
        - Modellizziamo ET come 50/50 (semplificazione conservativa)

        Ritorna dict con:
            home_qualifies: P(home si qualifica)
            away_qualifies: P(away si qualifica)
            goes_to_et:     P(parità aggregata → supplementari)
        """
        matrix = goal_model.score_matrix(max_goals=max_goals)

        p_home = 0.0
        p_away = 0.0
        p_et   = 0.0

        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                p = matrix[h][a]

                home_agg = self.fl_home + h
                away_agg = self.fl_away + a

                if home_agg > away_agg:
                    p_home += p
                elif away_agg > home_agg:
                    p_away += p
                else:
                    p_et += p  # supplementari

        # ET distribuito 50/50
        p_home += p_et * 0.5
        p_away += p_et * 0.5

        return {
            "home_qualifies": round(p_home, 4),
            "away_qualifies": round(p_away, 4),
            "goes_to_et":     round(p_et, 4),
        }

    # ------------------------------------------------------------------
    # Testo di contesto per il Sesto Senso
    # ------------------------------------------------------------------

    def context_description(self, home: str, away: str) -> str:
        """
        Genera una descrizione testuale del contesto aggregato
        da iniettare nel prompt del Sesto Senso.
        """
        lead = self.home_aggregate_lead

        lines = [
            f"PARTITA DI RITORNO (doppia sfida)",
            f"Punteggio andata: {home} {self.fl_home} - {self.fl_away} {away}",
            f"Aggregato attuale: {home} avanti {self.fl_home}-{self.fl_away}" if lead > 0
            else (f"Aggregato attuale: {away} avanti {self.fl_away}-{self.fl_home}" if lead < 0
                  else f"Aggregato in parità: {self.fl_home}-{self.fl_away}"),
        ]

        if lead > 0:
            if lead >= 3:
                lines.append(f"{home} si qualifica anche perdendo fino a {lead-1} gol di scarto.")
            elif lead == 2:
                lines.append(f"{home} si qualifica anche perdendo di 1. {away} deve vincere con 3+ gol di scarto.")
            elif lead == 1:
                lines.append(f"{home} si qualifica anche con il pareggio. {away} deve vincere per forza.")
        elif lead < 0:
            deficit = -lead
            if deficit >= 3:
                lines.append(f"{home} deve ribaltare {deficit} gol di svantaggio. Impresa difficile.")
            elif deficit == 2:
                lines.append(f"{home} deve vincere con almeno 3 gol di scarto o 2 gol per andare ai supplementari.")
            elif deficit == 1:
                lines.append(f"{home} deve vincere di almeno 1 gol. Un pareggio porta ai supplementari.")
        else:
            lines.append("Pareggio aggregato. Chi vince il ritorno passa, altrimenti supplementari.")

        lines.append(
            "ATTENZIONE: queste dinamiche cambiano radicalmente le motivazioni e le strategie "
            "delle squadre rispetto a una partita singola normale. Tienilo in conto nell'analisi."
        )

        return "\n".join(lines)
