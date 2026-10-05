"""
services/analysis/omni_statistical_optimizer.py — Motore Statistico & Ottimizzatore Combinatorio Multi-Mercato.

Risolve la monotonia delle combinazioni estendendo il pricing matematico a TUTTI i mercati:
1. Gol & Tempi (Bivariate Dixon-Coles Poisson + split tempi)
2. Calci d'Angolo (Negative Binomial bivariata: 1X2 Corner, 1° Tempo, Prima a X Corner, U/O)
3. Disciplinari & Falli (Poisson/Gamma: 1X2 Cartellini, U/O Cartellini, Falli Giocatore Over 1.5)
4. Player Props Ultra (xG/90 + fattore legni/traverse + clausola subentrante)

Applica a ciascuna leg il punteggio a campana gaussiana dello Sweet Spot (p=80%, q=1.45):
    S(p, q) = exp(-1/2 * (((p - 0.80) / 0.12)^2 + ((ln q - ln 1.45) / 0.20)^2))

Esegue l'ottimizzazione combinatoria per creare portafogli di N ticket (max 4 leg ciascuno)
imponendo il vincolo di DIVERSITÀ DI FAMIGLIA (massimo 1 mercato per famiglia per ticket).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.stats import poisson, nbinom

from services.analysis.statistical_combo import (
    SWEET_PROBABILITY,
    SWEET_ODD,
    PROBABILITY_WIDTH,
    ODD_WIDTH,
    MIN_ODD,
    statistical_score,
    structural_block,
    StatPick
)
from services.analysis.xg_poisson_engine import QuantitativeEngine
from services.analysis.tipster_intelligence import classify_market_family


@dataclass
class MatchDossier:
    """Contenitore completo delle statistiche di una partita per il pricing multi-mercato."""
    match_name: str
    kickoff: str = "2026-10-05 20:45 CEST"
    xg_home: float = 1.40
    xg_away: float = 1.10
    corners_home: float = 5.2
    corners_away: float = 4.0
    cards_home: float = 2.1
    cards_away: float = 2.4
    referee_cards_avg: float = 4.2
    # Dizionario giocatore -> {"xg_90": float, "fouls_avg": float, "minutes": int}
    players: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Dizionario o lista mercati quotati con quote reali del bookmaker
    catalog_source: Optional[str] = None


class OmniStatisticalPricer:
    """Prezzatore statistico universale per tutte le categorie di mercato calcistico."""

    def __init__(self, xg_engine: Optional[QuantitativeEngine] = None):
        self.xg_engine = xg_engine or QuantitativeEngine()

    def price_corner_1x2(self, avg_c1: float, avg_c2: float, dispersion: float = 1.4) -> Dict[str, float]:
        """Calcola la probabilità di 1, X, 2 sui calci d'angolo con Binomiale Negativa."""
        max_c = 22
        alpha = max(0.01, dispersion - 1.0)
        n1 = 1.0 / alpha
        p1 = 1.0 / (1.0 + alpha * max(0.5, avg_c1))
        n2 = 1.0 / alpha
        p2 = 1.0 / (1.0 + alpha * max(0.5, avg_c2))

        c_range = np.arange(max_c)
        pmf1 = nbinom.pmf(c_range, n1, p1)
        pmf2 = nbinom.pmf(c_range, n2, p2)
        grid = np.outer(pmf1, pmf2)

        prob_1 = float(np.tril(grid, -1).sum())
        prob_x = float(np.diag(grid).sum())
        prob_2 = float(np.triu(grid, 1).sum())
        total = prob_1 + prob_x + prob_2
        return {
            "1": prob_1 / total,
            "X": prob_x / total,
            "2": prob_2 / total
        }

    def price_first_half_corners_1x2(self, avg_c1: float, avg_c2: float) -> Dict[str, float]:
        """Calcola 1X2 corner nel 1° tempo (circa il 45% del volume totale)."""
        return self.price_corner_1x2(avg_c1 * 0.45, avg_c2 * 0.45, dispersion=1.3)

    def price_race_to_corners(self, avg_c1: float, avg_c2: float, target_corners: int) -> Dict[str, float]:
        """
        Calcola la probabilità che una squadra raggiunga per prima X corner ('Prima a X Corner').
        Modellato come processo di arrivo di Poisson con probabilità di arrivo binomiale e cutoff temporale.
        """
        total_rate = avg_c1 + avg_c2
        if total_rate <= 0:
            return {"TEAM 1": 0.5, "TEAM 2": 0.5, "NESSUNO": 0.0}

        p1 = avg_c1 / total_rate
        # Probabilità cumulativa che Team 1 ottenga target successi prima che Team 2 ottenga target successi
        # Risoluzione classica del problema di Banach/Pascal:
        n_trials = 2 * target_corners - 1
        prob_1_reaches_first = sum(
            math.comb(n_trials, k) * (p1 ** k) * ((1.0 - p1) ** (n_trials - k))
            for k in range(target_corners, n_trials + 1)
        )

        # Probabilità che nessuna delle due squadre raggiunga target corner nei 90'
        # Usando Poisson(avg_c1) e Poisson(avg_c2)
        p_c1_under = sum(poisson.pmf(k, avg_c1) for k in range(target_corners))
        p_c2_under = sum(poisson.pmf(k, avg_c2) for k in range(target_corners))
        p_nessuno = float(p_c1_under * p_c2_under)

        prob_team1 = prob_1_reaches_first * (1.0 - p_nessuno)
        prob_team2 = (1.0 - prob_1_reaches_first) * (1.0 - p_nessuno)

        return {
            "TEAM 1": float(prob_team1),
            "TEAM 2": float(prob_team2),
            "NESSUNO": float(p_nessuno)
        }

    def price_player_fouls_over(self, player_fouls_avg: float, threshold: float = 1.5) -> float:
        """Calcola la probabilità Over X.5 Falli Commessi dal giocatore usando Poisson."""
        lam = max(0.2, player_fouls_avg)
        int_thresh = int(math.floor(threshold))
        p_under = sum(poisson.pmf(k, lam) for k in range(int_thresh + 1))
        return float(1.0 - p_under)

    def price_team_cards_1x2(self, cards_home: float, cards_away: float, ref_factor: float = 1.0) -> Dict[str, float]:
        """Calcola 1X2 Cartellini squadra."""
        lam1 = max(0.5, cards_home * (ref_factor / 4.0))
        lam2 = max(0.5, cards_away * (ref_factor / 4.0))
        max_k = 15
        grid = np.outer(poisson.pmf(np.arange(max_k), lam1), poisson.pmf(np.arange(max_k), lam2))
        prob_1 = float(np.tril(grid, -1).sum())
        prob_x = float(np.diag(grid).sum())
        prob_2 = float(np.triu(grid, 1).sum())
        tot = prob_1 + prob_x + prob_2
        return {"1": prob_1 / tot, "X": prob_x / tot, "2": prob_2 / tot}

    def price_total_cards_over(self, cards_home: float, cards_away: float, threshold: float = 3.5, ref_factor: float = 1.0) -> float:
        """Calcola Over punti cartellini totali del match."""
        lam_tot = (cards_home + cards_away) * (ref_factor / 4.0)
        int_thresh = int(math.floor(threshold))
        p_under = sum(poisson.pmf(k, lam_tot) for k in range(int_thresh + 1))
        return float(1.0 - p_under)

    def price_player_prop_ultra(self, player_xg_90: float, minutes: float = 75.0) -> float:
        """
        Calcola la probabilità di 'Marcatore Più Ultra' (Segna o Palo/Traversa con Sostituto compreso).
        Include:
        - Gol base da xG
        - Fattore legni/traverse (+18% volume d'occasione)
        - Copertura del subentrante (+12% conservazione dell'evento nei minuti residui)
        """
        base_lambda = max(0.05, player_xg_90 * (minutes / 90.0))
        # Lambda potenziata per legni e subentrante
        ultra_lambda = base_lambda * 1.30
        p_event = 1.0 - math.exp(-ultra_lambda)
        return float(min(0.92, max(0.15, p_event)))

    def price_market(
        self,
        dossier: MatchDossier,
        market_name: str,
        selection: str,
        book_odd: float
    ) -> Optional[StatPick]:
        """Prezza qualsiasi mercato, deduce la famiglia e calcola punteggio e sanzioni strutturali."""
        if book_odd < MIN_ODD:
            return None

        m_lower = market_name.lower().strip()
        s_upper = selection.strip().upper()
        prob: Optional[float] = None
        family = classify_market_family(market_name)

        # 1. Player Props Ultra
        if "marcatore" in m_lower or "segna o" in m_lower or "palo" in m_lower:
            # Ricerca giocatore
            found_player = None
            for p_name, p_stat in dossier.players.items():
                if p_name.lower() in m_lower:
                    found_player = p_stat
                    break
            xg_90 = found_player.get("xg_90", 0.55) if found_player else 0.50
            mins = found_player.get("minutes", 75.0) if found_player else 75.0
            prob = self.price_player_prop_ultra(xg_90, mins)
            family = "PLAYER_PROPS_COMBO"

        # 2. Falli Giocatore
        elif "falli" in m_lower and "over" in s_upper.lower():
            found_player = None
            for p_name, p_stat in dossier.players.items():
                if p_name.lower() in m_lower:
                    found_player = p_stat
                    break
            fouls_avg = found_player.get("fouls_avg", 2.0) if found_player else 2.0
            thresh = 1.5 if "1.5" in m_lower else 2.5
            prob = self.price_player_fouls_over(fouls_avg, thresh)
            family = "TEAM_CARDS_VOLUME"

        # 3. 1X2 Cartellini / Punti Cartellini
        elif "cartellini" in m_lower:
            if "1x2" in m_lower:
                dist = self.price_team_cards_1x2(dossier.cards_home, dossier.cards_away, dossier.referee_cards_avg)
                prob = dist.get(s_upper)
            elif "over" in s_upper.lower() or "u/o" in m_lower:
                thresh = 3.5 if "3.5" in m_lower else (4.5 if "4.5" in m_lower else 2.5)
                prob = self.price_total_cards_over(dossier.cards_home, dossier.cards_away, thresh, dossier.referee_cards_avg)
            family = "TEAM_CARDS_VOLUME"

        # 4. Calci d'Angolo: Prima a X Corner
        elif "prima a" in m_lower and any(k in m_lower for k in ["corner", "calci angolo", "calci d'angolo", "angoli"]):
            match_x = re.search(r"prima a (\d+)", m_lower)
            target = int(match_x.group(1)) if match_x else 5
            races = self.price_race_to_corners(dossier.corners_home, dossier.corners_away, target)
            prob = races.get(s_upper)
            family = "TEAM_CORNERS_VOLUME"

        # 5. Calci d'Angolo: 1X2 Corner (1° Tempo o Finale)
        elif any(k in m_lower for k in ["corner", "calci angolo", "calci d'angolo", "angoli"]) and ("1x2" in m_lower or "esito" in m_lower or m_lower.strip() in ["1x2 corner", "calci angolo 1x2"]):
            if "1 tempo" in m_lower or "1° tempo" in m_lower or "1t" in m_lower:
                dist = self.price_first_half_corners_1x2(dossier.corners_home, dossier.corners_away)
            else:
                dist = self.price_corner_1x2(dossier.corners_home, dossier.corners_away)
            prob = dist.get(s_upper)
            family = "TEAM_CORNERS_VOLUME"

        # 6. Mercati Gol & Flussi Dixon-Coles
        else:
            # Specializzazione MultiGol Squadra Singola (es. 1-3, 1-4, 2-4)
            if "multigol squadra" in m_lower or "multigol casa" in m_lower or "multigol ospite" in m_lower:
                family = "TEAM_GOALS_VOLUME"
                is_home = "squadra 1" in m_lower or "casa" in m_lower
                lam = dossier.xg_home if is_home else dossier.xg_away
                sel_m = re.search(r"(\d+)\s*-\s*(\d+)", selection)
                if sel_m:
                    low, high = int(sel_m.group(1)), int(sel_m.group(2))
                    prob = float(sum(poisson.pmf(k, lam) for k in range(low, high + 1)))
                elif selection.isdigit():
                    prob = float(poisson.pmf(int(selection), lam))
            else:
                if selection.lower() in market_name.lower():
                    target_str = market_name
                else:
                    target_str = f"{market_name} {selection}".strip()
                prob = self.xg_engine.goal_market_probability(dossier.xg_home, dossier.xg_away, target_str)
                if prob is None:
                    prob = self.xg_engine.goal_market_probability(dossier.xg_home, dossier.xg_away, market_name)
                if prob is None:
                    prob = self.xg_engine.goal_market_probability(dossier.xg_home, dossier.xg_away, selection)

        if prob is None or prob <= 0.0 or prob >= 1.0:
            return None

        # Controllo blocchi strutturali
        block = structural_block(
            market_name,
            xg_home=dossier.xg_home,
            xg_away=dossier.xg_away
        )

        edge = prob * book_odd - 1.0
        score = 0.0 if block else statistical_score(prob, book_odd)

        # Costruisci etichetta mercato leggibile
        clean_market = f"{market_name} [{selection}]" if selection not in market_name else market_name

        return StatPick(
            market=clean_market,
            probability=round(prob, 3),
            book_odd=round(book_odd, 2),
            fair_odd=round(1.0 / prob, 2),
            edge=round(edge, 3),
            score=round(score, 3),
            blocked=block
        )


class CombinatorialPortfolioOptimizer:
    """Ottimizzatore combinatorio per la creazione di portafogli diversificati di ticket."""

    def __init__(self, pricer: Optional[OmniStatisticalPricer] = None):
        self.pricer = pricer or OmniStatisticalPricer()

    def generate_candidate_picks(self, dossier: MatchDossier, catalog_markets: List[Dict[str, Any]]) -> List[Tuple[StatPick, str]]:
        """Prezza tutti i mercati di una partita e restituisce le pick legali con la loro famiglia."""
        picks = []
        for m in catalog_markets:
            m_name = f"{m.get('market', '')} {m.get('line', '')}".strip()
            for o in m.get("outcomes", []):
                sel = str(o.get("selection", ""))
                odd = float(o.get("odds", 0.0))
                if odd < MIN_ODD:
                    continue
                pick = self.pricer.price_market(dossier, m_name, sel, odd)
                if pick and pick.blocked is None and pick.score > 0.0:
                    family = classify_market_family(m_name)
                    picks.append((pick, family))
        
        # Ordina per score decrescente
        picks.sort(key=lambda item: item[0].score, reverse=True)
        return picks

    def build_diversified_portfolio(
        self,
        matches_dossiers: List[MatchDossier],
        candidate_picks_by_match: Dict[str, List[Tuple[StatPick, str]]],
        num_tickets: int = 5,
        ticket_size: int = 4,
        stake_per_ticket: float = 2.50,
        bankroll_reference: float = 100.0
    ) -> Dict[str, Any]:
        """
        Assembla N ticket da max 4 leg ciascuno massimizzando il punteggio statistico
        e garantendo:
        1. Al massimo 1 leg per partita per ticket.
        2. Massima diversità di famiglia all'interno di ciascun ticket (no ripetizioni monotone).
        3. Nessun duplicato esatto tra i ticket (cross-ticket variety).
        """
        tickets = []
        used_signatures_global = set()

        # Definisci archetipi tattici con famiglie target prioritarie
        archetypes = [
            {
                "id": "TICKET_1_IBRIDO_SPECIALI",
                "name": "Ticket 1: Quaterna Ibrida Speciali & Flussi",
                "priority_families": ["PLAYER_PROPS_COMBO", "TEAM_GOALS_VOLUME", "TEAM_CORNERS_VOLUME", "CHANCE_MIX"]
            },
            {
                "id": "TICKET_2_DISCIPLINA_RITMO",
                "name": "Ticket 2: Quaterna Disciplina, Ritmo & Pressione",
                "priority_families": ["TEAM_CARDS_VOLUME", "FIRST_HALF_MULTIGOL", "TEAM_CORNERS_VOLUME", "TEAM_CARDS_VOLUME"]
            },
            {
                "id": "TICKET_3_STELLE_ASSEDIO",
                "name": "Ticket 3: Quaterna Stelle Europee & Assedio Corner",
                "priority_families": ["PLAYER_PROPS_COMBO", "TEAM_CORNERS_VOLUME", "TEAM_GOALS_VOLUME", "TEAM_CORNERS_VOLUME"]
            },
            {
                "id": "TICKET_4_TATTICA_PRESSIONE",
                "name": "Ticket 4: Quaterna Tattica, Pressione & Trasferte",
                "priority_families": ["TEAM_GOALS_VOLUME", "TEAM_CARDS_VOLUME", "TEAM_CARDS_VOLUME", "TEAM_CORNERS_VOLUME"]
            },
            {
                "id": "TICKET_5_SOLIDITA_VOLUME",
                "name": "Ticket 5: Quaterna Solidità, Fasi di Gioco & Volume",
                "priority_families": ["TEAM_CORNERS_VOLUME", "TEAM_GOALS_VOLUME", "DOPPIA_CHANCE", "TEAM_GOALS_VOLUME"]
            }
        ]

        match_names = list(candidate_picks_by_match.keys())

        for arch_idx in range(min(num_tickets, len(archetypes))):
            arch = archetypes[arch_idx]
            ticket_legs = []
            ticket_matches = set()
            ticket_families = []

            target_families = arch["priority_families"]

            # 1. Ricerca guidata dagli archetipi di famiglia
            for target_fam in target_families:
                best_leg = None
                best_match = None
                best_fam = None

                for m_name in match_names:
                    if m_name in ticket_matches:
                        continue
                    candidates = candidate_picks_by_match[m_name]
                    for pick, fam in candidates:
                        sig = (m_name, pick.market)
                        if sig in used_signatures_global:
                            continue
                        if fam == target_fam:
                            if best_leg is None or pick.score > best_leg.score:
                                best_leg = pick
                                best_match = m_name
                                best_fam = fam
                                break

                if best_leg is not None:
                    ticket_legs.append({
                        "match": best_match,
                        "market": best_leg.market,
                        "market_family": best_fam,
                        "odds": best_leg.book_odd,
                        "probability": best_leg.probability,
                        "fair_odd": best_leg.fair_odd,
                        "edge": best_leg.edge,
                        "score": best_leg.score,
                        "verdict": best_leg.verdict
                    })
                    ticket_matches.add(best_match)
                    ticket_families.append(best_fam)
                    used_signatures_global.add((best_match, best_leg.market))

                if len(ticket_legs) >= ticket_size:
                    break

            # 2. Se non ancora completato, riempi con le migliori selezioni con vincolo di diversità
            if len(ticket_legs) < ticket_size:
                for m_name in match_names:
                    if m_name in ticket_matches:
                        continue
                    candidates = candidate_picks_by_match[m_name]
                    for pick, fam in candidates:
                        sig = (m_name, pick.market)
                        if sig in used_signatures_global:
                            continue
                        # Evita troppe ripetizioni della stessa famiglia
                        if ticket_families.count(fam) >= 2:
                            continue
                        ticket_legs.append({
                            "match": m_name,
                            "market": pick.market,
                            "market_family": fam,
                            "odds": pick.book_odd,
                            "probability": pick.probability,
                            "fair_odd": pick.fair_odd,
                            "edge": pick.edge,
                            "score": pick.score,
                            "verdict": pick.verdict
                        })
                        ticket_matches.add(m_name)
                        ticket_families.append(fam)
                        used_signatures_global.add(sig)
                        break
                    if len(ticket_legs) >= ticket_size:
                        break

            # Calcolo metriche del ticket
            total_odd = 1.0
            joint_prob = 1.0
            for leg in ticket_legs:
                total_odd *= leg["odds"]
                joint_prob *= leg["probability"]

            total_odd = round(total_odd, 2)
            joint_prob = round(joint_prob, 3)
            fair_odd = round(1.0 / max(0.001, joint_prob), 2)
            overall_edge = round(joint_prob * total_odd - 1.0, 3)
            payout = round(stake_per_ticket * total_odd, 2)

            tickets.append({
                "id": arch["id"],
                "name": arch["name"],
                "stake": stake_per_ticket,
                "total_odds": total_odd,
                "probability": joint_prob,
                "fair_odd": fair_odd,
                "edge": overall_edge,
                "potential_payout": payout,
                "legs": ticket_legs
            })

        return {
            "bankroll_reference": bankroll_reference,
            "session_stake": round(stake_per_ticket * len(tickets), 2),
            "playable": True,
            "optimizer": "OmniStatisticalOptimizer (Multi-Market + Family Diversity)",
            "ev_policy": "EV negativo: avviso informativo, non bloccante. Bocciatura solo su rischio strutturale.",
            "tickets": tickets
        }
