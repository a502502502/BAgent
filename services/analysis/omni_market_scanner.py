#!/usr/bin/env python3
"""
services/analysis/omni_market_scanner.py
Omni-Market Scanner & Balanced Safety Score Engine (Regola #33, #39, #40, #41).

Scansiona TUTTI i mercati offerti dai bookmaker (1X2, DC, DNB, Over/Under, GG/NG, 
MultiGol, Corner, Cartellini, Tiri, Tempi, Combo Protette) e calcola:
1. P_reale (Poisson bivariata + modelli distribuiti)
2. Fair Odd (1 / P_reale)
3. Mathematical Edge ((P_reale * Quota) - 1)
4. Balanced Safety Score (BSS): il punto di equilibrio perfetto tra Probabilità, Quota ed Edge.
"""

from __future__ import annotations
import math
import os
import requests
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Carica .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_HOST = "v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def build_bivariate_matrix(lam_h: float, lam_a: float, max_g: int = 7) -> List[List[float]]:
    matrix = []
    for i in range(max_g + 1):
        row = []
        p_i = poisson_pmf(i, lam_h)
        for j in range(max_g + 1):
            p_j = poisson_pmf(j, lam_a)
            row.append(p_i * p_j)
        matrix.append(row)
    return matrix


@dataclass
class ScannedMarketPick:
    market_category: str     # es. "Combo Protetta", "MultiGol Squadra", "Doppia Chance", "Corner", "Over/Under"
    market_name: str         # es. "1X + Over 1.5", "MultiGol 1-3 Casa", "Home Corners Over 3.5"
    selection: str
    bookmaker_odd: float
    real_probability: float
    fair_odd: float
    mathematical_edge: float
    balanced_safety_score: float
    resilience_type: str     # "90_MIN_ELASTIC", "INTERMEDIATE_45_TRAP", "RIGID_OUTRIGHT"
    is_approved: bool
    rejection_reason: Optional[str] = None
    audit_notes: str = ""


class OmniMarketScanner:
    """
    Scanner universale di tutti i mercati disponibili con classificazione di sicurezza bilanciata.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY", "")
        self.headers = {"x-apisports-key": self.api_key}

    def fetch_all_odds(self, fixture_id: int) -> Dict[str, Any]:
        """Scarica tutti i mercati disponibili da API-Football (Bet365 / Bookmaker primari)."""
        url = f"https://{API_HOST}/odds?fixture={fixture_id}"
        try:
            r = requests.get(url, headers=self.headers, timeout=12)
            if r.status_code == 200:
                res = r.json().get("response", [])
                if res:
                    return res[0]
        except Exception as e:
            print(f"[OmniMarketScanner] Errore API Odds: {e}")
        return {}

    def fetch_fixture_info(self, fixture_id: int) -> Dict[str, Any]:
        url = f"https://{API_HOST}/fixtures?id={fixture_id}"
        try:
            r = requests.get(url, headers=self.headers, timeout=12)
            if r.status_code == 200:
                res = r.json().get("response", [])
                if res:
                    return res[0]
        except Exception as e:
            print(f"[OmniMarketScanner] Errore API Fixture: {e}")
        return {}

    @staticmethod
    def calculate_balanced_safety_score(
        p_real: float,
        odd: float,
        edge: float,
        resilience_type: str
    ) -> float:
        """
        Calcola il Balanced Safety Score (BSS):
        Trova il sweet spot tra Alta Probabilità + Quota Efficace + Edge Reale + Respiro a 90'.
        """
        if edge < 0.03 or p_real < 0.65:
            return 0.0

        if resilience_type == "INTERMEDIATE_45_TRAP" and odd < 1.55:
            return 0.0

        # Quota Utility Factor (premio range ideale 1.28 - 1.65)
        if 1.28 <= odd <= 1.65:
            q_factor = 1.15
        elif 1.22 <= odd < 1.28:
            q_factor = 0.90
        elif odd < 1.22:
            q_factor = 0.45
        elif 1.65 < odd <= 1.95:
            q_factor = 1.00
        elif 1.95 < odd <= 2.30:
            q_factor = 0.80
        else:
            q_factor = 0.55

        # Resilience Multiplier
        if resilience_type == "90_MIN_ELASTIC":
            res_factor = 1.20
        elif resilience_type == "RIGID_OUTRIGHT":
            res_factor = 0.85
        else:
            res_factor = 0.70

        # BSS formula
        bss = (p_real ** 1.6) * (1.0 + edge) * q_factor * res_factor * 100.0
        return round(bss, 2)

    def scan_fixture(
        self,
        fixture_id: int,
        xg_home: float = 1.70,
        xg_away: float = 1.10,
        xc_home: float = 6.0,
        xc_away: float = 3.5,
        xk_home: float = 2.0,
        xk_away: float = 2.8,
    ) -> List[ScannedMarketPick]:
        odds_data = self.fetch_all_odds(fixture_id)
        fix_info = self.fetch_fixture_info(fixture_id)

        home_team = fix_info.get("teams", {}).get("home", {}).get("name", "Casa")
        away_team = fix_info.get("teams", {}).get("away", {}).get("name", "Ospite")

        # 1. Matrice Poisson Gol
        joint_g = build_bivariate_matrix(xg_home, xg_away, max_g=7)
        p_home_win = sum(joint_g[i][j] for i in range(8) for j in range(8) if i > j)
        p_draw = sum(joint_g[i][i] for i in range(8))
        p_away_win = sum(joint_g[i][j] for i in range(8) for j in range(8) if i < j)

        p_1x = p_home_win + p_draw
        p_x2 = p_away_win + p_draw
        p_12 = p_home_win + p_away_win

        p_over_15 = sum(joint_g[i][j] for i in range(8) for j in range(8) if (i + j) > 1.5)
        p_under_15 = 1.0 - p_over_15
        p_over_25 = sum(joint_g[i][j] for i in range(8) for j in range(8) if (i + j) > 2.5)
        p_under_25 = 1.0 - p_over_25
        p_under_35 = sum(joint_g[i][j] for i in range(8) for j in range(8) if (i + j) < 3.5)
        p_over_35 = 1.0 - p_under_35

        p_gg = (1.0 - poisson_pmf(0, xg_home)) * (1.0 - poisson_pmf(0, xg_away))
        p_ng = 1.0 - p_gg

        # MultiGol
        p_home_mg_1_3 = sum(poisson_pmf(k, xg_home) for k in [1, 2, 3])
        p_away_mg_1_3 = sum(poisson_pmf(k, xg_away) for k in [1, 2, 3])
        p_tot_mg_1_4 = sum(joint_g[i][j] for i in range(8) for j in range(8) if 1 <= (i + j) <= 4)
        p_tot_mg_1_5 = sum(joint_g[i][j] for i in range(8) for j in range(8) if 1 <= (i + j) <= 5)

        # Combo Protette
        p_1x_over_15 = sum(joint_g[i][j] for i in range(8) for j in range(8) if i >= j and (i + j) > 1.5)
        p_1x_under_35 = sum(joint_g[i][j] for i in range(8) for j in range(8) if i >= j and (i + j) < 3.5)
        p_x2_over_15 = sum(joint_g[i][j] for i in range(8) for j in range(8) if j >= i and (i + j) > 1.5)
        p_x2_under_35 = sum(joint_g[i][j] for i in range(8) for j in range(8) if j >= i and (i + j) < 3.5)
        p_1x_gg = sum(joint_g[i][j] for i in range(8) for j in range(8) if i >= j and i >= 1 and j >= 1)

        # Corner (Poisson)
        p_c_home_ov_35 = 1.0 - sum(poisson_pmf(k, xc_home) for k in range(4))
        p_c_home_ov_45 = 1.0 - sum(poisson_pmf(k, xc_home) for k in range(5))
        p_c_away_ov_35 = 1.0 - sum(poisson_pmf(k, xc_away) for k in range(4))
        p_c_away_ov_45 = 1.0 - sum(poisson_pmf(k, xc_away) for k in range(5))
        p_c_tot_ov_85 = 1.0 - sum(poisson_pmf(k, xc_home + xc_away) for k in range(9))

        # Cartellini
        p_k_tot_ov_35 = 1.0 - sum(poisson_pmf(k, xk_home + xk_away) for k in range(4))
        p_k_tot_ov_45 = 1.0 - sum(poisson_pmf(k, xk_home + xk_away) for k in range(5))

        # Tempi
        p_home_1t = 1.0 - poisson_pmf(0, xg_home * 0.45)
        p_home_2t = 1.0 - poisson_pmf(0, xg_home * 0.55)
        p_home_both_halves = p_home_1t * p_home_2t

        # Regola #47: MultiGol Asimmetrico per Tempi (0-2 1°T + 1-3 2°T)
        # 1°T (0-2 gol) assorbe lo 0-0 all'intervallo; 2°T (1-3 gol) sfrutta le difese stanche
        lam_tot_1t = (xg_home + xg_away) * 0.45
        lam_tot_2t = (xg_home + xg_away) * 0.55
        p_1t_0_2 = sum(poisson_pmf(k, lam_tot_1t) for k in [0, 1, 2])
        p_2t_1_3 = sum(poisson_pmf(k, lam_tot_2t) for k in [1, 2, 3])
        p_asym_mg_halves = p_1t_0_2 * p_2t_1_3

        # Regola #47: Tiri Totali Partita (Volume Balistico Indipendente)
        # Stima tiri complessivi da xG e ritmo (media 13.5 tiri per gol atteso)
        exp_shots_tot = (xg_home * 8.5 + 4.5) + (xg_away * 7.5 + 4.0)
        p_shots_ov_215 = 1.0 - sum(poisson_pmf(k, exp_shots_tot) for k in range(22))
        p_shots_ov_235 = 1.0 - sum(poisson_pmf(k, exp_shots_tot) for k in range(24))

        theoretical_probs: Dict[Tuple[str, str], Tuple[float, str]] = {
            ("1X2", "Home"): (p_home_win, "RIGID_OUTRIGHT"),
            ("1X2", "Draw"): (p_draw, "RIGID_OUTRIGHT"),
            ("1X2", "Away"): (p_away_win, "RIGID_OUTRIGHT"),
            ("Double Chance", "Home/Draw"): (p_1x, "90_MIN_ELASTIC"),
            ("Double Chance", "Home/Away"): (p_12, "90_MIN_ELASTIC"),
            ("Double Chance", "Draw/Away"): (p_x2, "90_MIN_ELASTIC"),
            ("Goals Over/Under", "Over 1.5"): (p_over_15, "90_MIN_ELASTIC"),
            ("Goals Over/Under", "Under 1.5"): (p_under_15, "90_MIN_ELASTIC"),
            ("Goals Over/Under", "Over 2.5"): (p_over_25, "90_MIN_ELASTIC"),
            ("Goals Over/Under", "Under 2.5"): (p_under_25, "90_MIN_ELASTIC"),
            ("Goals Over/Under", "Under 3.5"): (p_under_35, "90_MIN_ELASTIC"),
            ("Goals Over/Under", "Over 3.5"): (p_over_35, "90_MIN_ELASTIC"),
            ("Both Teams Score", "Yes"): (p_gg, "90_MIN_ELASTIC"),
            ("Both Teams Score", "No"): (p_ng, "90_MIN_ELASTIC"),
            ("MultiGol Squadra", f"MultiGol 1-3 {home_team}"): (p_home_mg_1_3, "90_MIN_ELASTIC"),
            ("MultiGol Squadra", f"MultiGol 1-3 {away_team}"): (p_away_mg_1_3, "90_MIN_ELASTIC"),
            ("MultiGol Totale", "MultiGol 1-4"): (p_tot_mg_1_4, "90_MIN_ELASTIC"),
            ("MultiGol Totale", "MultiGol 1-5"): (p_tot_mg_1_5, "90_MIN_ELASTIC"),
            ("MultiGol Tempi", "MG 0-2 1°T + 1-3 2°T"): (p_asym_mg_halves, "90_MIN_ELASTIC"),
            ("Tiri Totali", "Over 21.5 Tiri Totali"): (p_shots_ov_215, "90_MIN_ELASTIC"),
            ("Tiri Totali", "Over 23.5 Tiri Totali"): (p_shots_ov_235, "90_MIN_ELASTIC"),
            ("Combo Protetta", "1X + Over 1.5"): (p_1x_over_15, "90_MIN_ELASTIC"),
            ("Combo Protetta", "1X + Under 3.5"): (p_1x_under_35, "90_MIN_ELASTIC"),
            ("Combo Protetta", "X2 + Over 1.5"): (p_x2_over_15, "90_MIN_ELASTIC"),
            ("Combo Protetta", "X2 + Under 3.5"): (p_x2_under_35, "90_MIN_ELASTIC"),
            ("Combo Protetta", "1X + GG"): (p_1x_gg, "90_MIN_ELASTIC"),
            ("Corner Squadra", f"{home_team} Corner Over 4.5"): (p_c_home_ov_45, "90_MIN_ELASTIC"),
            ("Corner Squadra", f"{away_team} Corner Over 3.5"): (p_c_away_ov_35, "90_MIN_ELASTIC"),
            ("Corner Totali", "Corner Over 8.5"): (p_c_tot_ov_85, "90_MIN_ELASTIC"),
            ("Cartellini Totali", "Cartellini Over 3.5"): (p_k_tot_ov_35, "90_MIN_ELASTIC"),
            ("Cartellini Totali", "Cartellini Over 4.5"): (p_k_tot_ov_45, "90_MIN_ELASTIC"),
            ("Tempi", f"{home_team} Segna in Entrambi i Tempi"): (p_home_both_halves, "INTERMEDIATE_45_TRAP"),
        }

        # Estrai quote da API-Football
        bookmakers = odds_data.get("bookmakers", [])
        extracted_odds: Dict[Tuple[str, str], float] = {}

        for b in bookmakers:
            for bet in b.get("bets", []):
                b_name = bet.get("name")
                for val in bet.get("values", []):
                    v_val = str(val.get("value"))
                    odd_f = float(val.get("odd", 0.0))

                    if b_name == "Match Winner":
                        extracted_odds[("1X2", v_val)] = max(extracted_odds.get(("1X2", v_val), 0.0), odd_f)
                    elif b_name == "Double Chance":
                        extracted_odds[("Double Chance", v_val)] = max(extracted_odds.get(("Double Chance", v_val), 0.0), odd_f)
                    elif b_name == "Goals Over/Under":
                        extracted_odds[("Goals Over/Under", v_val)] = max(extracted_odds.get(("Goals Over/Under", v_val), 0.0), odd_f)
                    elif b_name == "Both Teams Score":
                        extracted_odds[("Both Teams Score", v_val)] = max(extracted_odds.get(("Both Teams Score", v_val), 0.0), odd_f)
                    elif b_name == "Home Corners Over/Under" and "4.5" in v_val and "Over" in v_val:
                        extracted_odds[("Corner Squadra", f"{home_team} Corner Over 4.5")] = odd_f
                    elif b_name == "Away Corners Over/Under" and "3.5" in v_val and "Over" in v_val:
                        extracted_odds[("Corner Squadra", f"{away_team} Corner Over 3.5")] = odd_f
                    elif b_name == "Corners Over Under" and "8.5" in v_val and "Over" in v_val:
                        extracted_odds[("Corner Totali", "Corner Over 8.5")] = odd_f
                    elif b_name == "Cards Over/Under":
                        if "3.5" in v_val and "Over" in v_val:
                            extracted_odds[("Cartellini Totali", "Cartellini Over 3.5")] = odd_f
                        elif "4.5" in v_val and "Over" in v_val:
                            extracted_odds[("Cartellini Totali", "Cartellini Over 4.5")] = odd_f
                    elif b_name == "To Score In Both Halves By Teams":
                        if home_team.lower() in v_val.lower() or "home" in v_val.lower():
                            extracted_odds[("Tempi", f"{home_team} Segna in Entrambi i Tempi")] = odd_f

        # Fallback intelligenti mercati combo e multigol su Netwin
        odd_1x = extracted_odds.get(("Double Chance", "Home/Draw"), 1.30)
        odd_x2 = extracted_odds.get(("Double Chance", "Draw/Away"), 1.30)

        if ("Combo Protetta", "1X + Over 1.5") not in extracted_odds:
            extracted_odds[("Combo Protetta", "1X + Over 1.5")] = round(max(1.32, odd_1x * 1.08), 2)
        if ("Combo Protetta", "1X + Under 3.5") not in extracted_odds:
            extracted_odds[("Combo Protetta", "1X + Under 3.5")] = round(max(1.35, odd_1x * 1.12), 2)
        if ("Combo Protetta", "X2 + Over 1.5") not in extracted_odds:
            extracted_odds[("Combo Protetta", "X2 + Over 1.5")] = round(max(1.32, odd_x2 * 1.08), 2)
        if ("Combo Protetta", "X2 + Under 3.5") not in extracted_odds:
            extracted_odds[("Combo Protetta", "X2 + Under 3.5")] = round(max(1.35, odd_x2 * 1.12), 2)
        if ("Combo Protetta", "1X + GG") not in extracted_odds:
            extracted_odds[("Combo Protetta", "1X + GG")] = round(max(1.85, odd_1x * 1.45), 2)

        if ("MultiGol Squadra", f"MultiGol 1-3 {home_team}") not in extracted_odds:
            extracted_odds[("MultiGol Squadra", f"MultiGol 1-3 {home_team}")] = 1.32
        if ("MultiGol Squadra", f"MultiGol 1-3 {away_team}") not in extracted_odds:
            extracted_odds[("MultiGol Squadra", f"MultiGol 1-3 {away_team}")] = 1.30
        if ("MultiGol Totale", "MultiGol 1-4") not in extracted_odds:
            extracted_odds[("MultiGol Totale", "MultiGol 1-4")] = 1.25
        if ("MultiGol Totale", "MultiGol 1-5") not in extracted_odds:
            extracted_odds[("MultiGol Totale", "MultiGol 1-5")] = 1.18

        if ("Corner Squadra", f"{home_team} Corner Over 4.5") not in extracted_odds:
            extracted_odds[("Corner Squadra", f"{home_team} Corner Over 4.5")] = 1.55
        if ("Cartellini Totali", "Cartellini Over 3.5") not in extracted_odds:
            extracted_odds[("Cartellini Totali", "Cartellini Over 3.5")] = 1.45

        scanned_picks: List[ScannedMarketPick] = []

        for (m_cat, sel_name), (p_real, res_type) in theoretical_probs.items():
            odd = extracted_odds.get((m_cat, sel_name))
            if not odd or odd < 1.10:
                continue

            fair_odd = 1.0 / max(0.001, p_real)
            edge = (p_real * odd) - 1.0

            bss = self.calculate_balanced_safety_score(
                p_real=p_real,
                odd=odd,
                edge=edge,
                resilience_type=res_type
            )

            is_appr = True
            rej = None
            if edge < 0.04:
                is_appr = False
                rej = f"Edge insufficiente o negativo ({edge*100:+.1f}%)"
            elif res_type == "INTERMEDIATE_45_TRAP" and odd < 1.55:
                is_appr = False
                rej = f"Trappola 45' a quota compressa (@{odd:.2f} < 1.55)"
            elif p_real < 0.70:
                is_appr = False
                rej = f"Probabilità reale troppo bassa per mercato sicuro ({p_real*100:.1f}% < 70%)"

            notes = (
                f"P_real: {p_real*100:.1f}% | Fair Odd: @{fair_odd:.2f} | "
                f"Quota Bookie: @{odd:.2f} | Edge: {edge*100:+.1f}% | BSS: {bss:.1f}"
            )

            scanned_picks.append(
                ScannedMarketPick(
                    market_category=m_cat,
                    market_name=sel_name,
                    selection=sel_name,
                    bookmaker_odd=odd,
                    real_probability=p_real,
                    fair_odd=fair_odd,
                    mathematical_edge=edge,
                    balanced_safety_score=bss,
                    resilience_type=res_type,
                    is_approved=is_appr,
                    rejection_reason=rej,
                    audit_notes=notes
                )
            )

        scanned_picks.sort(key=lambda x: (x.is_approved, x.balanced_safety_score), reverse=True)
        return scanned_picks
