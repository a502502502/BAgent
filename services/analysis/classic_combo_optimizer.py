"""
ClassicComboOptimizer — Motore Quantitativo per Combinazioni Pre-Compilate Classiche.

Analizza e calcola quote potenziate (target Valore / Raddoppio 1.80 – 2.25+)
da mercati combo reali forniti da API-Football (Bet365, Marathonbet, William Hill, ecc.):
  - 1X2 + Over/Under (1.5, 2.5, 3.5, 4.5) [Bet ID 25]
  - 1X2 + Gol/No Gol (Yes/No) [Bet ID 24]
  - Doppia Chance + Over/Under (1.5, 2.5, 3.5) [Bet ID 38]
  - Doppia Chance + Gol/No Gol [Bet ID 37]
  - Totale Squadra Casa/Ospite (Over/Under 1.5) [Bet ID 16, 17]
  - Gol/No Gol + Over/Under [Bet ID 49]

Utilizza una distribuzione bivariata congiunta di Poisson su xG stimato
per calcolare la vera probabilità congiunta P(A ∩ B), l'Expected Value (EV)
e scartare combinazioni a trappola (es. Under 2.5 + Gol).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _poisson_pmf(k: int, lam: float) -> float:
    """Calcola P(X = k) per X ~ Poisson(lam)."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def build_joint_poisson(xg_home: float, xg_away: float, max_goals: int = 8) -> List[List[float]]:
    """
    Costruisce la matrice joint[i][j] = P(Home=i, Away=j)
    assumendo indipendenza condizionata tra le due distribuzioni Poisson.
    """
    home_pmf = [_poisson_pmf(k, xg_home) for k in range(max_goals + 1)]
    away_pmf = [_poisson_pmf(k, xg_away) for k in range(max_goals + 1)]
    return [[home_pmf[i] * away_pmf[j] for j in range(max_goals + 1)] for i in range(max_goals + 1)]


@dataclass
class ComboSelection:
    market_name: str         # es. "1X2 + Under/Over 3.5"
    selection: str           # es. "1 & Under 3.5"
    netwin_label: str        # nome leggibile per palinsesto italiano
    odd: float               # Quota reale bookmaker
    bookmaker: str           # es. "Bet365"
    model_prob: float        # Probabilità teorica calcolata (0.0 - 1.0)
    edge: float              # EV = (model_prob * odd) - 1.0
    risk_level: str          # "BASSO", "MEDIO", "ALTO"
    tactical_rationale: str  # Spiegazione logico-statistica

    @property
    def edge_pct(self) -> str:
        sign = "+" if self.edge >= 0 else ""
        return f"{sign}{self.edge * 100:.1f}%"

    @property
    def prob_pct(self) -> str:
        return f"{self.model_prob * 100:.1f}%"

    @property
    def score(self) -> float:
        """
        Punteggio composito per il ranking:
        Score = (model_prob ^ 0.6) * (1 + max(-0.2, edge))
        """
        ev_factor = 1.0 + max(-0.2, self.edge)
        return (self.model_prob ** 0.6) * ev_factor


class ClassicComboOptimizer:
    """
    Estrae e analizza le combo classiche pre-compilate per una partita,
    selezionando quelle con massimo valore nella fascia di quota desiderata.
    """

    def __init__(
        self,
        xg_home: float,
        xg_away: float,
        home_team: str = "Casa",
        away_team: str = "Ospite",
        min_quota: float = 1.75,
        max_quota: float = 2.40,
        min_prob: float = 0.40,
    ):
        self.xg_home = max(0.2, xg_home)
        self.xg_away = max(0.2, xg_away)
        self.home_team = home_team
        self.away_team = away_team
        self.min_quota = min_quota
        self.max_quota = max_quota
        self.min_prob = min_prob

        # Calcola distribuzione congiunta
        self.max_goals = 8
        self.joint = build_joint_poisson(self.xg_home, self.xg_away, max_goals=self.max_goals)

    # -------------------------------------------------------------------------
    # Calcolo Probabilità Modello per ogni mercato combo
    # -------------------------------------------------------------------------

    def calc_prob_result_total(self, outcome: str, line: float, is_over: bool) -> float:
        """
        Calcola P(Esito 1X2 ∩ Totale Gol Over/Under Line).
        outcome: 'Home', 'Draw', 'Away'
        line: 1.5, 2.5, 3.5, 4.5
        is_over: True per Over, False per Under
        """
        prob = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                res_match = (
                    (outcome == "Home" and i > j) or
                    (outcome == "Draw" and i == j) or
                    (outcome == "Away" and i < j)
                )
                if not res_match:
                    continue

                tot = i + j
                tot_match = (tot > line) if is_over else (tot < line)
                if tot_match:
                    prob += self.joint[i][j]
        return prob

    def calc_prob_result_btts(self, outcome: str, btts_yes: bool) -> float:
        """
        Calcola P(Esito 1X2 ∩ Gol/No Gol).
        outcome: 'Home', 'Draw', 'Away'
        btts_yes: True per Gol (GG), False per No Gol (NG)
        """
        prob = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                res_match = (
                    (outcome == "Home" and i > j) or
                    (outcome == "Draw" and i == j) or
                    (outcome == "Away" and i < j)
                )
                if not res_match:
                    continue

                btts_match = (i >= 1 and j >= 1) if btts_yes else (i == 0 or j == 0)
                if btts_match:
                    prob += self.joint[i][j]
        return prob

    def calc_prob_dc_total(self, dc: str, line: float, is_over: bool) -> float:
        """
        Calcola P(Doppia Chance ∩ Totale Gol Over/Under Line).
        dc: '1X', 'X2', '12'
        """
        prob = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                dc_match = (
                    (dc == "1X" and i >= j) or
                    (dc == "X2" and i <= j) or
                    (dc == "12" and i != j)
                )
                if not dc_match:
                    continue

                tot = i + j
                tot_match = (tot > line) if is_over else (tot < line)
                if tot_match:
                    prob += self.joint[i][j]
        return prob

    def calc_prob_dc_btts(self, dc: str, btts_yes: bool) -> float:
        """
        Calcola P(Doppia Chance ∩ Gol/No Gol).
        """
        prob = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                dc_match = (
                    (dc == "1X" and i >= j) or
                    (dc == "X2" and i <= j) or
                    (dc == "12" and i != j)
                )
                if not dc_match:
                    continue

                btts_match = (i >= 1 and j >= 1) if btts_yes else (i == 0 or j == 0)
                if btts_match:
                    prob += self.joint[i][j]
        return prob

    def calc_prob_team_total(self, team: str, line: float, is_over: bool) -> float:
        """
        Calcola P(Gol Squadra Casa/Ospite Over/Under).
        team: 'Home' o 'Away'
        """
        prob = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                val = i if team == "Home" else j
                match = (val > line) if is_over else (val < line)
                if match:
                    prob += self.joint[i][j]
        return prob

    def calc_prob_btts_total(self, btts_yes: bool, line: float, is_over: bool) -> float:
        """
        Calcola P(Gol/No Gol ∩ Over/Under Totale).
        """
        prob = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                btts_match = (i >= 1 and j >= 1) if btts_yes else (i == 0 or j == 0)
                if not btts_match:
                    continue
                tot = i + j
                tot_match = (tot > line) if is_over else (tot < line)
                if tot_match:
                    prob += self.joint[i][j]
        return prob

    # -------------------------------------------------------------------------
    # Parsing ed elaborazione quote grezze API-Football
    # -------------------------------------------------------------------------

    def extract_and_evaluate_combos(self, odds_response: dict) -> List[ComboSelection]:
        """
        Prende la risposta grezza di API-Football /odds?fixture={id},
        analizza tutti i bookmaker disponibili e restituisce le migliori combo.
        """
        resp = odds_response.get("response", [])
        if not resp:
            return []

        bookmakers = resp[0].get("bookmakers", [])
        if not bookmakers:
            return []

        evaluated: List[ComboSelection] = []

        # Itera su TUTTI i bookmaker per massimizzare la copertura quote
        for bm in bookmakers:
            bm_name = bm.get("name", "Bookmaker")
            bets = bm.get("bets", [])

            for b in bets:
                bet_id = b.get("id")
                bet_name = b.get("name", "")
                values = b.get("values", [])

                # --- BET ID 25: Result/Total Goals ---
                if bet_id == 25 or "result/total goals" in bet_name.lower():
                    for v in values:
                        val_str = str(v.get("value", ""))
                        try:
                            odd = float(v.get("odd", 0.0))
                        except (ValueError, TypeError):
                            continue

                        if "/" in val_str:
                            parts = val_str.split("/")
                            res_part = parts[0].strip()
                            tot_part = parts[1].strip()

                            is_over = "over" in tot_part.lower()
                            is_under = "under" in tot_part.lower()
                            if not (is_over or is_under):
                                continue

                            try:
                                line_str = "".join([c for c in tot_part if c.isdigit() or c == "."])
                                line = float(line_str)
                            except ValueError:
                                continue

                            res_code = "Home" if "home" in res_part.lower() else ("Away" if "away" in res_part.lower() else "Draw")
                            res_symbol = "1" if res_code == "Home" else ("2" if res_code == "Away" else "X")
                            uo_symbol = f"Over {line}" if is_over else f"Under {line}"

                            prob = self.calc_prob_result_total(res_code, line, is_over)
                            edge = (prob * odd) - 1.0

                            team_label = self.home_team if res_code == "Home" else (self.away_team if res_code == "Away" else "Pareggio")
                            if is_over:
                                rationale = f"{team_label} vince con spinta offensiva (linea {uo_symbol})"
                            else:
                                rationale = f"{team_label} vince gestendo il ritmo (linea {uo_symbol} protettiva)"

                            risk = "BASSO" if prob >= 0.55 else ("MEDIO" if prob >= 0.45 else "ALTO")

                            evaluated.append(ComboSelection(
                                market_name="1X2 + Totale Gol",
                                selection=f"{res_symbol} & {uo_symbol}",
                                netwin_label=f"{res_symbol} + {uo_symbol}",
                                odd=odd,
                                bookmaker=bm_name,
                                model_prob=prob,
                                edge=edge,
                                risk_level=risk,
                                tactical_rationale=rationale
                            ))

                # --- BET ID 24: Results/Both Teams Score ---
                elif bet_id == 24 or "results/both teams score" in bet_name.lower():
                    for v in values:
                        val_str = str(v.get("value", ""))
                        try:
                            odd = float(v.get("odd", 0.0))
                        except (ValueError, TypeError):
                            continue

                        if "/" in val_str:
                            parts = val_str.split("/")
                            res_part = parts[0].strip()
                            btts_part = parts[1].strip()
                            btts_yes = "yes" in btts_part.lower()

                            res_code = "Home" if "home" in res_part.lower() else ("Away" if "away" in res_part.lower() else "Draw")
                            res_symbol = "1" if res_code == "Home" else ("2" if res_code == "Away" else "X")
                            btts_symbol = "Gol" if btts_yes else "No Gol"

                            prob = self.calc_prob_result_btts(res_code, btts_yes)
                            edge = (prob * odd) - 1.0

                            team_label = self.home_team if res_code == "Home" else (self.away_team if res_code == "Away" else "Pareggio")
                            rationale = f"{team_label} con esito {btts_symbol}"
                            risk = "BASSO" if prob >= 0.55 else ("MEDIO" if prob >= 0.45 else "ALTO")

                            evaluated.append(ComboSelection(
                                market_name="1X2 + Gol/No Gol",
                                selection=f"{res_symbol} & {btts_symbol}",
                                netwin_label=f"{res_symbol} + {btts_symbol}",
                                odd=odd,
                                bookmaker=bm_name,
                                model_prob=prob,
                                edge=edge,
                                risk_level=risk,
                                tactical_rationale=rationale
                            ))

                # --- BET ID 38: Double Chance / Total Goals ---
                elif bet_id == 38 or "double chance / total goals" in bet_name.lower() or "double chance + total" in bet_name.lower():
                    for v in values:
                        val_str = str(v.get("value", ""))
                        try:
                            odd = float(v.get("odd", 0.0))
                        except (ValueError, TypeError):
                            continue

                        is_over = "over" in val_str.lower()
                        is_under = "under" in val_str.lower()
                        if not (is_over or is_under):
                            continue

                        dc = "1X" if "1x" in val_str.lower() or "home/draw" in val_str.lower() else (
                            "X2" if "x2" in val_str.lower() or "draw/away" in val_str.lower() else "12"
                        )

                        try:
                            line_str = "".join([c for c in val_str if c.isdigit() or c == "."])
                            line = float(line_str)
                        except ValueError:
                            continue

                        uo_symbol = f"Over {line}" if is_over else f"Under {line}"
                        prob = self.calc_prob_dc_total(dc, line, is_over)
                        edge = (prob * odd) - 1.0

                        rationale = f"Doppia chance {dc} corazzata con linea {uo_symbol}"
                        risk = "BASSO" if prob >= 0.60 else ("MEDIO" if prob >= 0.48 else "ALTO")

                        evaluated.append(ComboSelection(
                            market_name="Doppia Chance + Totale Gol",
                            selection=f"{dc} & {uo_symbol}",
                            netwin_label=f"{dc} + {uo_symbol}",
                            odd=odd,
                            bookmaker=bm_name,
                            model_prob=prob,
                            edge=edge,
                            risk_level=risk,
                            tactical_rationale=rationale
                        ))

                # --- BET ID 16 & 17: Team Totals (Over 1.5 Squadra) ---
                elif bet_id in [16, 17] or "total - home" in bet_name.lower() or "total - away" in bet_name.lower():
                    team_type = "Home" if bet_id == 16 or "home" in bet_name.lower() else "Away"
                    t_name = self.home_team if team_type == "Home" else self.away_team
                    for v in values:
                        val_str = str(v.get("value", ""))
                        try:
                            odd = float(v.get("odd", 0.0))
                        except (ValueError, TypeError):
                            continue

                        if "over 1.5" in val_str.lower():
                            prob = self.calc_prob_team_total(team_type, 1.5, True)
                            edge = (prob * odd) - 1.0
                            xg_team = self.xg_home if team_type == "Home" else self.xg_away
                            rationale = f"{t_name} segna 2+ gol (xG individuale: {xg_team:.2f})"
                            risk = "BASSO" if prob >= 0.55 else ("MEDIO" if prob >= 0.45 else "ALTO")

                            evaluated.append(ComboSelection(
                                market_name=f"Totale Gol {t_name}",
                                selection=f"{t_name} Over 1.5",
                                netwin_label=f"{t_name} Over 1.5",
                                odd=odd,
                                bookmaker=bm_name,
                                model_prob=prob,
                                edge=edge,
                                risk_level=risk,
                                tactical_rationale=rationale
                            ))

                # --- BET ID 49: Total Goals / Both Teams To Score ---
                elif bet_id == 49 or "total goals/both teams to score" in bet_name.lower():
                    for v in values:
                        val_str = str(v.get("value", "")).lower()
                        try:
                            odd = float(v.get("odd", 0.0))
                        except (ValueError, TypeError):
                            continue

                        # Gestisce sia 'o/yes 2.5' che 'over 2.5/yes'
                        is_over = val_str.startswith("o/") or "over" in val_str
                        is_under = val_str.startswith("u/") or "under" in val_str
                        btts_yes = "yes" in val_str
                        btts_no = "no" in val_str

                        if not (is_over or is_under) or not (btts_yes or btts_no):
                            continue

                        # Guardrail: Ban Under 2.5 + Yes (trappola microscopica esatta 1-1)
                        if is_under and "2.5" in val_str and btts_yes:
                            continue

                        try:
                            line_str = "".join([c for c in val_str if c.isdigit() or c == "."])
                            line = float(line_str)
                        except ValueError:
                            continue

                        uo_str = f"Over {line}" if is_over else f"Under {line}"
                        btts_str = "Gol" if btts_yes else "No Gol"

                        prob = self.calc_prob_btts_total(btts_yes, line, is_over)
                        edge = (prob * odd) - 1.0

                        rationale = f"Combinazione {btts_str} associato a {uo_str}"
                        risk = "BASSO" if prob >= 0.55 else ("MEDIO" if prob >= 0.45 else "ALTO")

                        evaluated.append(ComboSelection(
                            market_name="Gol/No Gol + Totale Gol",
                            selection=f"{btts_str} & {uo_str}",
                            netwin_label=f"{btts_str} + {uo_str}",
                            odd=odd,
                            bookmaker=bm_name,
                            model_prob=prob,
                            edge=edge,
                            risk_level=risk,
                            tactical_rationale=rationale
                        ))

        # Rimuove duplicati esatti tenendo la quota migliore tra tutti i bookmaker
        unique_dict: Dict[str, ComboSelection] = {}
        for c in evaluated:
            if c.selection not in unique_dict or c.odd > unique_dict[c.selection].odd:
                unique_dict[c.selection] = c

        all_combos = list(unique_dict.values())

        # Filtra per i requisiti:
        # 1. Quota nel target [min_quota, max_quota]
        # 2. Probabilità minima model_prob >= min_prob
        # 3. Edge tollerato (EV >= -0.06 per non scartare quote vicine al fair value)
        filtered = [
            c for c in all_combos
            if self.min_quota <= c.odd <= self.max_quota and c.model_prob >= self.min_prob and c.edge >= -0.06
        ]

        # Ordina per score composito decrescente
        filtered.sort(key=lambda c: c.score, reverse=True)
        return filtered
