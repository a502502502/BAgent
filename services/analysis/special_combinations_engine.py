"""
services/analysis/special_combinations_engine.py — Special Combinations & High-Resilience Engine.

Modulo quantitativo specializzato nell'ingegnerizzazione di mercati ad altissima probabilità congiunta:
1. Chance Mix a Matrice Unione (P(A ∪ B) >= 88%-94%, es. '1X o Over 1.5', 'X2 o Over 1.5', 'Gol o Over 2.5');
2. MultiGol Asimmetrico per Tempi ('MG 0-2 1°T + MG 1-3 2°T');
3. Dutching Asimmetrico a Paracadute (Twin-Ticket Goleada Lock con copertura 100% dello stake);
4. Disaccoppiamento Balistico Ortogonale (Corner + MultiGol 1-4 + Cartellini).
"""

from __future__ import annotations
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("SpecialCombinationsEngine")

def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def _price_or_fair(
    odds: Dict[str, float],
    key: str,
    probability: float,
    fair_odd: float,
) -> Tuple[float, float]:
    """Senza quota vera l'edge è zero: la fair odd non è un prezzo del banco."""
    quoted = odds.get(key)
    if quoted is None or quoted <= 1.0:
        return fair_odd, 0.0
    return quoted, (probability * quoted) - 1.0


def build_bivariate_matrix(xg_home: float, xg_away: float, max_goals: int = 8) -> List[List[float]]:
    """Costruisce la matrice di probabilità P(Home=i, Away=j)."""
    home_pmf = [_poisson_pmf(i, xg_home) for i in range(max_goals + 1)]
    away_pmf = [_poisson_pmf(j, xg_away) for j in range(max_goals + 1)]
    return [[home_pmf[i] * away_pmf[j] for j in range(max_goals + 1)] for i in range(max_goals + 1)]

@dataclass
class SpecialSelection:
    market_family: str        # 'CHANCE_MIX', 'ASYMMETRIC_HALVES', 'DUTCHING_LOCK', 'ORTHOGONAL_BALISTIC'
    selection_name: str       # es. "1X o Over 1.5"
    netwin_market_label: str  # Dicitura per ricerca su Netwin
    real_probability: float   # Probabilità reale calcolata (0.0 - 1.0)
    fair_odd: float           # 1.0 / probabilità
    estimated_bookmaker_odd: float
    mathematical_edge: float  # (P * Odd) - 1.0
    resilience_rating: str    # "QUASI_INFALLIBILE" (>92%), "ACCIAIO" (>88%), "SOLIDO" (>82%)
    single_losing_scenario: str  # L'unico risultato che fa perdere (es. "Solo lo 0-1")
    tactical_rationale: str
    dutching_stake_split: Optional[Dict[str, float]] = None # Per dutching a paracadute

class SpecialCombinationsEngine:
    """
    Motore quantitativo per combinazioni speciali e mercati a prova di bomba.
    """

    MIN_PROBABILITY_THRESHOLD = 0.82 # Minimo 82% per mercati speciali
    MIN_EDGE_THRESHOLD = 0.04        # Minimo +4% di valore atteso

    def __init__(self):
        pass

    def evaluate_chance_mixes(
        self,
        match_name: str,
        xg_home: float,
        xg_away: float,
        bookmaker_odds_map: Optional[Dict[str, float]] = None
    ) -> List[SpecialSelection]:
        """
        Calcola tutte le Chance Mix a Matrice Unione (P(A ∪ B)).
        """
        matrix = build_bivariate_matrix(xg_home, xg_away, max_goals=8)
        odds = bookmaker_odds_map or {}
        selections: List[SpecialSelection] = []

        # -------------------------------------------------------------
        # 1. '1X o Over 1.5': Perde SOLO sullo 0-1 esatto!
        # P = 1.0 - P(Home=0, Away=1)
        # -------------------------------------------------------------
        p_0_1 = matrix[0][1]
        p_1x_or_o15 = round(1.0 - p_0_1, 4)
        fair_odd_1 = round(1.0 / max(0.001, p_1x_or_o15), 2)
        odd_1, edge_1 = _price_or_fair(odds, "1X o Over 1.5", p_1x_or_o15, fair_odd_1)

        selections.append(SpecialSelection(
            market_family="CHANCE_MIX",
            selection_name="1X o Over 1.5",
            netwin_market_label="Chance Mix: 1X o Over 1.5",
            real_probability=p_1x_or_o15,
            fair_odd=fair_odd_1,
            estimated_bookmaker_odd=odd_1,
            mathematical_edge=round(edge_1, 4),
            resilience_rating="QUASI_INFALLIBILE" if p_1x_or_o15 >= 0.92 else "ACCIAIO",
            single_losing_scenario="Perde unicamente sul risultato esatto di 0-1",
            tactical_rationale=(
                f"Copre l'intera gamma degli esiti: vittorie interne (1-0, 2-0, 2-1), tutti i pareggi (0-0, 1-1, 2-2) "
                f"e qualsiasi vittoria ospite con almeno 2 gol (0-2, 1-2, 0-3). L'unica sconfitta possibile è il solitario 0-1."
            )
        ))

        # -------------------------------------------------------------
        # 2. 'X2 o Over 1.5': Perde SOLO sull'1-0 esatto della squadra di casa!
        # P = 1.0 - P(Home=1, Away=0)
        # -------------------------------------------------------------
        p_1_0 = matrix[1][0]
        p_x2_or_o15 = round(1.0 - p_1_0, 4)
        fair_odd_2 = round(1.0 / max(0.001, p_x2_or_o15), 2)
        odd_2, edge_2 = _price_or_fair(odds, "X2 o Over 1.5", p_x2_or_o15, fair_odd_2)

        selections.append(SpecialSelection(
            market_family="CHANCE_MIX",
            selection_name="X2 o Over 1.5",
            netwin_market_label="Chance Mix: X2 o Over 1.5",
            real_probability=p_x2_or_o15,
            fair_odd=fair_odd_2,
            estimated_bookmaker_odd=odd_2,
            mathematical_edge=round(edge_2, 4),
            resilience_rating="QUASI_INFALLIBILE" if p_x2_or_o15 >= 0.92 else "ACCIAIO",
            single_losing_scenario="Perde unicamente sul risultato esatto di 1-0",
            tactical_rationale=(
                f"Ideale per trasferte delle favorite: incassa su vittoria ospite, pareggi (0-0, 1-1) e qualsiasi vittoria casalinga con 2+ reti (2-0, 2-1). "
                f"Si perde solo in caso di 'corto muso' 1-0 della squadra casalinga."
            )
        ))

        # -------------------------------------------------------------
        # 3. 'Gol o Over 2.5': Perde solo su 0-0, 1-0, 2-0, 0-1, 0-2 (5 esiti chiusi)
        # -------------------------------------------------------------
        p_under_and_nogol = matrix[0][0] + matrix[1][0] + matrix[0][1] + matrix[2][0] + matrix[0][2]
        p_gg_or_o25 = round(1.0 - p_under_and_nogol, 4)
        fair_odd_3 = round(1.0 / max(0.001, p_gg_or_o25), 2)
        odd_3, edge_3 = _price_or_fair(odds, "Gol o Over 2.5", p_gg_or_o25, fair_odd_3)

        selections.append(SpecialSelection(
            market_family="CHANCE_MIX",
            selection_name="Gol o Over 2.5",
            netwin_market_label="Chance Mix: Entrambe Segnano o Over 2.5",
            real_probability=p_gg_or_o25,
            fair_odd=fair_odd_3,
            estimated_bookmaker_odd=odd_3,
            mathematical_edge=round(edge_3, 4),
            resilience_rating="ACCIAIO" if p_gg_or_o25 >= 0.88 else "SOLIDO",
            single_losing_scenario="Perde solo su pareggio a secco (0-0) o vittorie a clean sheet strette (1-0, 2-0, 0-1, 0-2)",
            tactical_rationale=(
                f"Perfetto per gare aperte e coppe europee: incassa su qualsiasi pareggio con gol (1-1, 2-2) e su qualsiasi goleada anche a senso unico (3-0, 4-0)."
            )
        ))

        # -------------------------------------------------------------
        # 4. '1X o Gol': Perde solo se la squadra ospite vince a zero (0-1, 0-2, 0-3...)
        # P = 1.0 - Sum(j=1..8) P(Home=0, Away=j)
        # -------------------------------------------------------------
        p_away_clean_win = sum(matrix[0][j] for j in range(1, 9))
        p_1x_or_gg = round(1.0 - p_away_clean_win, 4)
        fair_odd_4 = round(1.0 / max(0.001, p_1x_or_gg), 2)
        odd_4, edge_4 = _price_or_fair(odds, "1X o Gol", p_1x_or_gg, fair_odd_4)

        selections.append(SpecialSelection(
            market_family="CHANCE_MIX",
            selection_name="1X o Gol",
            netwin_market_label="Chance Mix: 1X o Gol",
            real_probability=p_1x_or_gg,
            fair_odd=fair_odd_4,
            estimated_bookmaker_odd=odd_4,
            mathematical_edge=round(edge_4, 4),
            resilience_rating="QUASI_INFALLIBILE" if p_1x_or_o15 >= 0.92 else "ACCIAIO",
            single_losing_scenario="Perde solo se la squadra in trasferta vince senza subire gol",
            tactical_rationale=(
                f"Basta che la squadra di casa non perda (1X) oppure che segni almeno un gol nella partita per incassare."
            )
        ))

        return selections

    def evaluate_asymmetric_halves(
        self,
        match_name: str,
        xg_total: float,
        bookmaker_odd: float = 1.45
    ) -> SpecialSelection:
        """
        MultiGol Asimmetrico per Tempi: MG 0-2 1°T + MG 1-3 2°T.
        Fisiologia: 43% xG nel primo tempo, 57% xG nel secondo.
        """
        xg_1t = xg_total * 0.43
        xg_2t = xg_total * 0.57

        p_1t_0_2 = sum(_poisson_pmf(k, xg_1t) for k in range(0, 3))
        p_2t_1_3 = sum(_poisson_pmf(k, xg_2t) for k in range(1, 4))

        p_joint = round(p_1t_0_2 * p_2t_1_3, 4)
        fair_odd = round(1.0 / max(0.001, p_joint), 2)
        edge = (p_joint * bookmaker_odd) - 1.0

        return SpecialSelection(
            market_family="ASYMMETRIC_HALVES",
            selection_name="MultiGol 0-2 1°T + 1-3 2°T",
            netwin_market_label="MultiGol Tempi: 0-2 1°T & 1-3 2°T",
            real_probability=p_joint,
            fair_odd=fair_odd,
            estimated_bookmaker_odd=bookmaker_odd,
            mathematical_edge=round(edge, 4),
            resilience_rating="ACCIAIO" if p_joint >= 0.85 else "SOLIDO",
            single_losing_scenario="Perde se nel 1°T ci sono 3+ gol o se il 2°T resta inchiodato sullo 0-0",
            tactical_rationale=(
                f"Sfrutta la dinamica fisiologica del match: fase di studio controllata nei primi 45' (P={p_1t_0_2:.1%}) "
                f"e ripresa con spazi aperti e difese stanche dove basta 1 gol per incassare (P={p_2t_1_3:.1%})."
            )
        )

    def evaluate_dutching_lock(
        self,
        team_name: str,
        xg_team: float,
        odd_core_mg13: float = 1.40,
        odd_goleada_ov35: float = 4.80,
        total_stake_eur: float = 10.0
    ) -> SpecialSelection:
        """
        Dutching Asimmetrico a Paracadute (Twin-Ticket Lock per Attacchi Dominanti):
        - Schedina Core (80% stake): MultiGol 1-3 Squadra
        - Schedina Paracadute (20% stake): Over 3.5 Squadra
        L'unica sconfitta possibile: 0 gol della squadra favorita!
        """
        p_0_goals = _poisson_pmf(0, xg_team)
        p_lock = round(1.0 - p_0_goals, 4)
        fair_odd = round(1.0 / max(0.001, p_lock), 2)

        # Calcolo Staking Paracadute
        # w_para * odd_goleada = 1.0 (garantisce rimborso 100% o utile minimo)
        stake_para = round(total_stake_eur / odd_goleada_ov35, 2)
        stake_core = round(total_stake_eur - stake_para, 2)

        # Rendimento medio ponderato
        p_1_3 = sum(_poisson_pmf(k, xg_team) for k in range(1, 4))
        p_4_plus = sum(_poisson_pmf(k, xg_team) for k in range(4, 9))

        ret_core = stake_core * odd_core_mg13
        ret_para = stake_para * odd_goleada_ov35

        effective_combined_odd = round((ret_core * p_1_3 + ret_para * p_4_plus) / max(0.01, (p_1_3 + p_4_plus)) / total_stake_eur, 2)
        edge = (p_lock * effective_combined_odd) - 1.0

        return SpecialSelection(
            market_family="DUTCHING_LOCK",
            selection_name=f"Dutching Paracadute Goleada: {team_name}",
            netwin_market_label=f"Twin-Ticket: {team_name} MultiGol 1-3 + Over 3.5",
            real_probability=p_lock,
            fair_odd=fair_odd,
            estimated_bookmaker_odd=effective_combined_odd,
            mathematical_edge=round(edge, 4),
            resilience_rating="QUASI_INFALLIBILE" if p_lock >= 0.94 else "ACCIAIO",
            single_losing_scenario=f"Perde unicamente se {team_name} resta a secco con zero gol segnati",
            tactical_rationale=(
                f"Elimina la Ceiling Trap (Regola #48): lo stake (€{total_stake_eur:.2f}) è ripartito con €{stake_core:.2f} su MG 1-3 "
                f"ed €{stake_para:.2f} su Over 3.5. Se {team_name} segna 1, 2 o 3 gol incassi €{ret_core:.2f}; se dilaga a 4+ gol incassi €{ret_para:.2f}."
            ),
            dutching_stake_split={
                "core_stake_eur": stake_core,
                "parachute_stake_eur": stake_para,
                "payout_core_eur": round(ret_core, 2),
                "payout_parachute_eur": round(ret_para, 2)
            }
        )

    def scan_best_specials_for_match(
        self,
        match_name: str,
        xg_home: float,
        xg_away: float,
        bookmaker_odds: Optional[Dict[str, float]] = None
    ) -> List[SpecialSelection]:
        """Scansiona tutte le combinazioni speciali e restituisce quelle con valore reale ed Edge >= +5.0%."""
        all_specials: List[SpecialSelection] = []

        # 1. Chance Mixes
        cm_list = self.evaluate_chance_mixes(match_name, xg_home, xg_away, bookmaker_odds)
        all_specials.extend(cm_list)

        odds = bookmaker_odds or {}

        # 2. MultiGol Asimmetrico Tempi — solo con quota reale
        halves_key = "MultiGol 0-2 1°T + 1-3 2°T"
        if halves_key in odds and odds[halves_key] > 1.0:
            xg_tot = xg_home + xg_away
            all_specials.append(
                self.evaluate_asymmetric_halves(match_name, xg_tot, odds[halves_key])
            )

        # 3. Dutching Paracadute — solo se entrambe le quote sono presenti
        fav_name = match_name.split(" vs ")[0] if xg_home >= xg_away else match_name.split(" vs ")[-1]
        fav_xg = max(xg_home, xg_away)
        core_key = "MultiGol 1-3 Squadra"
        para_key = "Over 3.5 Squadra"
        if (
            fav_xg >= 1.70
            and odds.get(core_key, 0) > 1.0
            and odds.get(para_key, 0) > 1.0
        ):
            all_specials.append(
                self.evaluate_dutching_lock(fav_name, fav_xg, odds[core_key], odds[para_key])
            )

        # Filtra per alta resilienza ed Edge positivo
        filtered = [s for s in all_specials if s.real_probability >= self.MIN_PROBABILITY_THRESHOLD and s.mathematical_edge >= self.MIN_EDGE_THRESHOLD]
        filtered.sort(key=lambda s: s.real_probability, reverse=True)
        return filtered
