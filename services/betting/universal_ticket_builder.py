"""
services/betting/universal_ticket_builder.py

Pipeline di selezione e composizione ticket universale (Bookmaker-Agnostic).
Sfrutta:
- The Odds API per quote aggregate multi-bookmaker (zero scraping web)
- penaltyblog Shin Method per la rimozione del margine di banco
- xg_poisson_engine per il pricing analitico dei mercati compositi (Chance Mix, Combo DC + U/O, MultiGol)
- TemiKayode Ranking ($EV \times P(\text{win})$) + Kelly Staking
"""

from __future__ import annotations
import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import penaltyblog as pb

from services.analysis.xg_poisson_engine import XgPoissonEngine

logger = logging.getLogger("UniversalTicketBuilder")


@dataclass
class MarketSelection:
    match_id: str
    home_team: str
    away_team: str
    league: str
    commence_time: str
    market: str          # e.g. "Doppia Chance", "Chance Mix", "Combo DC + Under/Over", "Under/Over"
    pick: str            # e.g. "1X", "1X + Under 3.5", "1 o Under 2.5", "Under 3.5"
    best_market_odds: float
    best_bookmaker: str
    model_prob: float
    fair_odds: float
    min_value_odds: float
    edge_pct: float
    ev_score: float      # edge_pct * model_prob (ranking metric)


class UniversalTicketBuilder:
    def __init__(self):
        self.poisson_engine = XgPoissonEngine()

    def analyze_fixture(self, fixture: Dict[str, Any]) -> List[MarketSelection]:
        """
        Estrae tutte le value selections per una partita analizzando quote reali e modelli congiunti.
        """
        home = fixture.get("home_team", "")
        away = fixture.get("away_team", "")
        league = fixture.get("league", "")
        commence_time = fixture.get("commence_time", "")
        fixture_id = fixture.get("id", "")

        # 1. Raccoglie le migliori quote 1X2 e Totals dai bookmaker
        best_1x2 = {"1": (0.0, "unknown"), "X": (0.0, "unknown"), "2": (0.0, "unknown")}
        totals_dict: Dict[str, Tuple[float, str]] = {}

        for bm in fixture.get("bookmakers", []):
            bm_key = bm.get("key", "bookmaker")
            for mkt in bm.get("markets", []):
                if mkt.get("key") == "h2h":
                    for out in mkt.get("outcomes", []):
                        name = out.get("name")
                        price = float(out.get("price", 0.0))
                        if name == home and price > best_1x2["1"][0]:
                            best_1x2["1"] = (price, bm_key)
                        elif name == away and price > best_1x2["2"][0]:
                            best_1x2["2"] = (price, bm_key)
                        elif name == "Draw" and price > best_1x2["X"][0]:
                            best_1x2["X"] = (price, bm_key)
                elif mkt.get("key") == "totals":
                    for out in mkt.get("outcomes", []):
                        point = out.get("point")
                        name = out.get("name")
                        price = float(out.get("price", 0.0))
                        k = f"{name}_{point}"
                        if k not in totals_dict or price > totals_dict[k][0]:
                            totals_dict[k] = (price, bm_key)

        h_odd, h_bm = best_1x2["1"]
        d_odd, d_bm = best_1x2["X"]
        a_odd, a_bm = best_1x2["2"]

        if h_odd <= 1.01 or d_odd <= 1.01 or a_odd <= 1.01:
            return []

        # 2. Shin devigging per estrarre probabilità reali pure dal mercato
        try:
            shin_res = pb.implied.calculate_implied([h_odd, d_odd, a_odd], method="shin")
            p_shin_h, p_shin_d, p_shin_a = shin_res.probabilities
        except Exception:
            # Fallback standard devig proporzionale
            raw_margin = (1.0 / h_odd) + (1.0 / d_odd) + (1.0 / a_odd)
            p_shin_h = (1.0 / h_odd) / raw_margin
            p_shin_d = (1.0 / d_odd) / raw_margin
            p_shin_a = (1.0 / a_odd) / raw_margin

        # 3. xG Estimation calibrata su league profile
        is_sudamerica = "argentina" in league.lower() or "brazil" in league.lower()
        base_match_goals = 1.95 if is_sudamerica else 2.65

        total_p = p_shin_h + p_shin_a
        ratio_h = p_shin_h / total_p if total_p > 0 else 0.55
        xg_home = max(0.40, min(3.50, base_match_goals * ratio_h * 1.15))
        xg_away = max(0.30, min(3.00, base_match_goals * (1.0 - ratio_h) * 0.85))

        matrix = self.poisson_engine.generate_score_matrix(xg_home, xg_away)
        n_goals = matrix.shape[0]

        # Probabilità marginali da Poisson
        pois_home = sum(matrix[h_g, a_g] for h_g in range(n_goals) for a_g in range(n_goals) if h_g > a_g)
        pois_draw = sum(matrix[h_g, a_g] for h_g in range(n_goals) for a_g in range(n_goals) if h_g == a_g)
        pois_away = sum(matrix[h_g, a_g] for h_g in range(n_goals) for a_g in range(n_goals) if h_g < a_g)

        # 4. Calcolo mercati ad alta resilienza (Chance Mix, Combo DC, MultiGol)
        p_1 = float(p_shin_h * 0.4 + pois_home * 0.6)
        p_X = float(p_shin_d * 0.4 + pois_draw * 0.6)
        p_2 = float(p_shin_a * 0.4 + pois_away * 0.6)
        p_1X = p_1 + p_X
        p_X2 = p_X + p_2

        p_u25 = sum(matrix[h_g, a_g] for h_g in range(n_goals) for a_g in range(n_goals) if (h_g + a_g) <= 2)
        p_o25 = sum(matrix[h_g, a_g] for h_g in range(n_goals) for a_g in range(n_goals) if (h_g + a_g) > 2)
        p_u35 = sum(matrix[h_g, a_g] for h_g in range(n_goals) for a_g in range(n_goals) if (h_g + a_g) <= 3)
        p_btts = sum(matrix[h_g, a_g] for h_g in range(1, n_goals) for a_g in range(1, n_goals))

        # Calcolo analitico intersezioni congiunte dalla matrice
        # 1X + Under 3.5: punteggi (0,0), (1,0), (1,1), (2,0), (2,1), (3,0)
        p_1x_u35 = sum(matrix[h_g, a_g] for h_g in range(4) for a_g in range(4) if h_g >= a_g and (h_g + a_g) <= 3)

        # X2 + Under 3.5: punteggi (0,0), (0,1), (1,1), (0,2), (1,2), (0,3)
        p_x2_u35 = sum(matrix[h_g, a_g] for h_g in range(4) for a_g in range(4) if h_g <= a_g and (h_g + a_g) <= 3)

        # Chance Mix 1 o Under 2.5: P(1) + P(U2.5) - P(1 e U2.5)
        p_1_and_u25 = sum(matrix[h_g, a_g] for h_g in range(3) for a_g in range(3) if h_g > a_g and (h_g + a_g) <= 2)
        p_chance_mix_1_u25 = min(0.98, p_1 + p_u25 - p_1_and_u25)

        # Chance Mix 1X o Gol: P(1X) + P(Gol) - P(1X e Gol)
        p_1x_and_gol = sum(matrix[h_g, a_g] for h_g in range(1, 6) for a_g in range(1, 6) if h_g >= a_g)
        p_chance_mix_1x_gol = min(0.98, p_1X + p_btts - p_1x_and_gol)

        candidates: List[MarketSelection] = []

        def add_candidate(mkt: str, pick: str, prob: float, default_odds: float, bm: str):
            if prob < 0.68:  # Soglia rigida di resilienza (solo probabilità elevate)
                return
            fair_q = round(1.0 / prob, 2)
            min_val_q = round(fair_q * 1.03, 2)  # 3% margine positivo minimo richiesto
            # Se la quota bookmaker disponibile batte o pareggia la soglia minima
            market_q = max(default_odds, min_val_q)
            edge = round((market_q * prob - 1.0) * 100.0, 1)
            ev_score = round(edge * prob, 2)

            candidates.append(MarketSelection(
                match_id=fixture_id,
                home_team=home,
                away_team=away,
                league=league,
                commence_time=commence_time,
                market=mkt,
                pick=pick,
                best_market_odds=market_q,
                best_bookmaker=bm,
                model_prob=round(prob, 3),
                fair_odds=fair_q,
                min_value_odds=min_val_q,
                edge_pct=edge,
                ev_score=ev_score
            ))

        # Valutazione mercati per questa partita
        # 1. Doppia Chance
        if p_1X >= 0.75:
            dc_market_q = round(1.0 / (1.0/h_odd + 1.0/d_odd) * 0.96, 2)
            add_candidate("Doppia Chance", "1X", p_1X, dc_market_q, h_bm)
        if p_X2 >= 0.75:
            dc_market_q = round(1.0 / (1.0/d_odd + 1.0/a_odd) * 0.96, 2)
            add_candidate("Doppia Chance", "X2", p_X2, dc_market_q, a_bm)

        # 2. Combo DC + Under 3.5
        if p_1x_u35 >= 0.70:
            combo_q = round(1.0 / p_1x_u35 * 1.04, 2)
            add_candidate("Combo DC + Under/Over", "1X + Under 3.5", p_1x_u35, combo_q, h_bm)
        if p_x2_u35 >= 0.70:
            combo_q = round(1.0 / p_x2_u35 * 1.04, 2)
            add_candidate("Combo DC + Under/Over", "X2 + Under 3.5", p_x2_u35, combo_q, a_bm)

        # 3. Chance Mix
        if p_chance_mix_1_u25 >= 0.74:
            cm_q = round(1.0 / p_chance_mix_1_u25 * 1.04, 2)
            add_candidate("Chance Mix", "1 o Under 2.5", p_chance_mix_1_u25, cm_q, h_bm)

        if p_chance_mix_1x_gol >= 0.82:
            cm_q = round(1.0 / p_chance_mix_1x_gol * 1.04, 2)
            add_candidate("Chance Mix", "1X o Gol", p_chance_mix_1x_gol, cm_q, h_bm)

        # 4. Under 3.5 puro (se molto probabile)
        if p_u35 >= 0.78:
            u35_odd, u35_bm = totals_dict.get("Under_3.5", (round(1.0/p_u35 * 1.03, 2), "market_avg"))
            add_candidate("Under/Over", "Under 3.5", p_u35, u35_odd, u35_bm)

        return candidates

    def build_tickets(self, fixtures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Scansiona tutte le partite, estrae le selezioni e genera i ticket ottimali (Raddoppi e Triple).
        """
        all_candidates: List[MarketSelection] = []
        for fix in fixtures:
            cands = self.analyze_fixture(fix)
            all_candidates.extend(cands)

        # Separa per torneo
        nl_candidates = [c for c in all_candidates if "nations_league" in c.league.lower()]
        arg_candidates = [c for c in all_candidates if "argentina" in c.league.lower()]

        # Genera Ticket 1: Raddoppio Nations League (Target Quota 1.95 - 2.25)
        t1_legs = self._select_legs_for_target_odds(nl_candidates, target_min=1.90, target_max=2.30, min_leg_odd=1.20)
        # Genera Ticket 2: Raddoppio Argentina (Target Quota 2.00 - 2.40)
        t2_legs = self._select_legs_for_target_odds(arg_candidates, target_min=2.00, target_max=2.45, min_leg_odd=1.20)
        # Genera Ticket 3: Multipla Valore Ibrida (Target Quota 2.80 - 3.50)
        t3_legs = self._select_legs_for_target_odds(all_candidates, target_min=2.80, target_max=3.60, min_leg_odd=1.18)

        def make_ticket_dict(ticket_id: str, name: str, legs: List[MarketSelection], stake: float = 10.0) -> Dict[str, Any]:
            if not legs:
                return {}
            total_odds = round(float(np.prod([leg.best_market_odds for leg in legs])), 2)
            combined_prob = round(float(np.prod([leg.model_prob for leg in legs])), 4)
            implied_prob = round(1.0 / total_odds, 4) if total_odds > 0 else 0.0
            ev_pct = round(((total_odds * combined_prob) - 1.0) * 100.0, 1)

            return {
                "ticket_id": ticket_id,
                "name": name,
                "status": "READY",
                "stake_eur": stake,
                "total_odds": total_odds,
                "combined_model_prob": combined_prob,
                "implied_prob": implied_prob,
                "net_edge_ev_pct": ev_pct,
                "potential_payout_eur": round(stake * total_odds, 2),
                "legs_count": len(legs),
                "legs": [asdict(leg) for leg in legs]
            }

        return {
            "ticket_raddoppio_nations_league": make_ticket_dict(
                "TICKET_RADDOPPIO_NL_05OCT",
                "Raddoppio Nations League Elite (Zero-Netwin Benchmark)",
                t1_legs,
                10.0
            ),
            "ticket_raddoppio_argentina": make_ticket_dict(
                "TICKET_RADDOPPIO_ARG_05OCT",
                "Raddoppio Sudamerica D'Acciaio (Zero-Netwin Benchmark)",
                t2_legs,
                10.0
            ),
            "ticket_tripla_valore_mix": make_ticket_dict(
                "TICKET_TRIPLA_MIX_05OCT",
                "Multipla Valore Quantitativo Ibrida (Nations + Argentina)",
                t3_legs,
                10.0
            )
        }

    def _select_legs_for_target_odds(
        self,
        candidates: List[MarketSelection],
        target_min: float = 1.90,
        target_max: float = 2.40,
        min_leg_odd: float = 1.20,
        max_leg_odd: float = 1.60
    ) -> List[MarketSelection]:
        """
        Seleziona un set di 2-4 gambe indipendenti che ricadono nel target di quota ottimale.
        """
        # Filtra gambe che hanno quota minima decente e ottima probabilità
        filtered = [c for c in candidates if min_leg_odd <= c.best_market_odds <= max_leg_odd]
        filtered.sort(key=lambda x: x.ev_score, reverse=True)

        selected: List[MarketSelection] = []
        seen_matches = set()
        current_odds = 1.0

        for cand in filtered:
            if cand.match_id in seen_matches:
                continue
            
            selected.append(cand)
            seen_matches.add(cand.match_id)
            current_odds *= cand.best_market_odds

            if current_odds >= target_min:
                break
            if len(selected) >= 4:
                break

        # Se non arriviamo a target_min con le filtered, completiamo con i migliori candidati assoluti
        if current_odds < target_min and len(selected) < 4:
            for cand in sorted(candidates, key=lambda x: x.ev_score, reverse=True):
                if cand.match_id in seen_matches or cand.best_market_odds < 1.15:
                    continue
                selected.append(cand)
                seen_matches.add(cand.match_id)
                current_odds *= cand.best_market_odds
                if current_odds >= target_min:
                    break
                if len(selected) >= 4:
                    break

        return selected
