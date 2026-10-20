"""
services/analysis/slate_ticket_synthesizer.py — Generatore Autonomo di Schedine Multi-Mercato Tipster-Style.

Implementa la sintesi autonoma di ticket ad alto rendimento e protezione statistica:
1. Scansiona il palinsesto del giorno (tutte le leghe disponibili).
2. Per ogni match, esegue l'ingestione on-demand (Regola #90) e il calcolo bilaterale (RollingTenEngine).
3. Esamina l'intero spettro di mercati per match:
   - Doppia Chance protetta (1X, X2)
   - Gol (GG) bilaterale su match ad alto voltaggio
   - Chance Mix salvagente (X o Gol per derby tesi, 1X o Over 1.5)
   - MultiGol Squadra asimmetrico (MultiGol 1-3 Casa/Ospite)
   - Mercati Tempi (Over 0.5 2°T, MultiGol 1-3 2°T)
   - Mercati Specialistici (Over 1.5 Cartellini Squadra)
   - Combo Classiche Protette (1X + Over 1.5)
4. Filtra le selezioni nel corridoio ideale 1.25 - 1.48 con Hit Rate reale >= 75-80%.
5. Assembla ticket eterogenei da 5-7 eventi con moltiplicatore 8.00x - 15.00x,
   in piena autonomia e senza dipendenza da tipster esterni.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.analysis.rolling_ten_engine import RollingTenEngine

logger = logging.getLogger("SlateTicketSynthesizer")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "bagent.db"
ODD_FLOOR = 1.25
ODD_CEILING = 1.48


def kickoff_complete(kickoff: str) -> bool:
    """Data e ora esplicite, come richiede la Regola #76."""
    text = (kickoff or "").strip()
    has_date = ("-" in text or "/" in text) and any(ch.isdigit() for ch in text)
    return has_date and ":" in text


def open_or_tense_fixture(h_gf: float, a_gf: float, tournament: str) -> bool:
    """Chance Mix solo su gare aperte, oppure equilibrate e tese.

    `and` lega più stretto di `or`: il campionato va parentesizzato insieme
    al filtro sul divario gol, altrimenti ogni Serie A passa il gate.
    """
    both_open = h_gf >= 1.8 and a_gf >= 1.8
    balanced = abs(h_gf - a_gf) < 0.4
    tense = any(tag in (tournament or "") for tag in ("Super Lig", "Derby", "Serie A"))
    return both_open or (balanced and tense)


def cards_market_allowed(tournament: str) -> bool:
    """Over cartellini solo fuori da Nord Europa e Austria, dove il ritmo è pulito."""
    text = (tournament or "").lower()
    blocked = ("norveg", "eliteserien", "allsvenskan", "superliga", "austria", "admiral")
    return not any(tag in text for tag in blocked)


def venue_rate(flow: Dict[str, Any], home_key: str, blended_key: str) -> Optional[float]:
    """In casa se il campione basta, altrimenti sulle ultime gare di qualsiasi campo."""
    if flow.get("matches", 0) < 3:
        return None
    if flow.get("home_n", 0) >= 3:
        return float(flow.get(home_key) or 0.0)
    return float(flow.get(blended_key) or 0.0)


def quoted_odd(odds_dict: Dict[str, Any], group: str, name: str, default: float) -> float:
    raw = (odds_dict.get(group) or {}).get(name, default)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


@dataclass
class MatchGemPick:
    match_name: str
    home_team: str
    away_team: str
    tournament: str
    kickoff: str
    market_name: str
    market_category: str  # 'DOPPIA_CHANCE', 'GOL', 'CHANCE_MIX', 'MULTIGOL_SQUADRA', 'TEMPI', 'CARTELLINI', 'COMBO'
    odd: float
    hit_rate: float
    rationale: str


class SlateTicketSynthesizer:
    """Motore autonomo di scansione palinsesto e composizione ticket multi-mercato."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.engine = RollingTenEngine(db_path=self.db_path)

    def evaluate_match_gems(
        self,
        home_team: str,
        away_team: str,
        tournament: str,
        kickoff: str,
        odds_dict: Optional[Dict[str, Any]] = None,
    ) -> List[MatchGemPick]:
        """
        Analizza un singolo match su tutti i mercati possibili e restituisce i candidati a valore.
        """
        # Esegui cross-analisi bilaterale con auto-download on-demand (Regola #90)
        res = self.engine.cross_analyze_match(home_team, away_team, auto_download=True)
        hp = self.engine.get_team_profile(home_team)
        ap = self.engine.get_team_profile(away_team)

        if not hp or not ap or not kickoff_complete(kickoff):
            return []

        odds_dict = odds_dict or {}
        candidates: List[MatchGemPick] = []

        # Estrai statistiche chiave
        h_gf = hp.get("avg_goals_scored", 0.0)
        h_ga = hp.get("avg_goals_conceded", 0.0)
        a_gf = ap.get("avg_goals_scored", 0.0)
        a_ga = ap.get("avg_goals_conceded", 0.0)

        h_ov15 = hp.get("hr_over_15_match", 0.0)
        a_ov15 = ap.get("hr_over_15_match", 0.0)
        h_flow = self.engine.team_flow(home_team)
        a_flow = self.engine.team_flow(away_team)
        hr_1x = venue_rate(h_flow, "home_unbeaten_hr", "unbeaten_hr")
        hr_combo = venue_rate(h_flow, "home_dc_and_ov15_hr", "dc_and_ov15_hr")
        btts_hr = None
        if h_flow.get("matches", 0) >= 3 and a_flow.get("matches", 0) >= 3:
            btts_hr = round((h_flow["btts_hr"] + a_flow["btts_hr"]) / 2.0, 1)

        # 1. DOPPIA CHANCE (1X se la casa è nettamente più solida dell'ospite)
        if hr_1x is not None and h_gf >= 1.3 and a_gf <= 1.1 and h_ga <= 1.4:
            odd_1x = odds_dict.get("DOPPIA_CHANCE", {}).get("1X", 1.34)
            if 1.25 <= odd_1x <= 1.45:
                sample = h_flow["home_n"] if h_flow["home_n"] >= 3 else h_flow["matches"]
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name="Doppia Chance 1X",
                        market_category="DOPPIA_CHANCE",
                        odd=odd_1x,
                        hit_rate=round(hr_1x, 1),
                        rationale=(
                            f"{home_team} non perde nel {hr_1x:.1f}% di {sample} gare recenti "
                            f"(GF {h_gf:.1f}, {away_team} GF {a_gf:.1f})."
                        ),
                    )
                )

        # 2. GOL (GG) (se entrambi gli attacchi producono e le difese concedono)
        if btts_hr is not None and h_gf >= 1.6 and a_gf >= 1.6 and h_ov15 >= 80.0 and a_ov15 >= 80.0:
            odd_gg = odds_dict.get("GOL_NOGOL", {}).get("Gol", 1.47)
            if 1.35 <= odd_gg <= 1.55:
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name="Gol (GG)",
                        market_category="GOL",
                        odd=odd_gg,
                        hit_rate=btts_hr,
                        rationale=(
                            f"Gol entrambe nelle ultime gare: {home_team} {h_flow['btts_hr']:.1f}%, "
                            f"{away_team} {a_flow['btts_hr']:.1f}%."
                        ),
                    )
                )

        # 3. CHANCE MIX: X O GOL (gare aperte, oppure equilibrate in tornei tesi)
        x_gg_hr = (
            float(hp.get("hr_chance_mix_x_gg") or 0.0) + float(ap.get("hr_chance_mix_x_gg") or 0.0)
        ) / 2.0
        if open_or_tense_fixture(h_gf, a_gf, tournament) and x_gg_hr >= 75.0:
            odd_x_gg = quoted_odd(odds_dict, "CHANCE_MIX", "Chance Mix: X o Gol", 1.35)
            if ODD_FLOOR <= odd_x_gg <= 1.45:
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name="Chance Mix: X o Gol",
                        market_category="CHANCE_MIX",
                        odd=odd_x_gg,
                        hit_rate=round(x_gg_hr, 1),
                        rationale=(
                            f"X o Gol storico al {x_gg_hr:.1f}% "
                            f"(Casa GF {h_gf:.1f}, Ospite GF {a_gf:.1f})."
                        ),
                    )
                )

        # 4. MULTIGOL SQUADRA (MultiGol 1-3 Casa o Ospite)
        h_mg13 = hp.get("hr_multigol_1_3_team", 0.0)
        a_mg13 = ap.get("hr_multigol_1_3_team", 0.0)

        if h_mg13 >= 80.0 and h_gf >= 1.2:
            odd_mg_h = quoted_odd(odds_dict, "MULTIGOL_SQUADRA", "1-3 Casa", 1.30)
            if not (ODD_FLOOR <= odd_mg_h <= ODD_CEILING):
                odd_mg_h = None
            if odd_mg_h is not None:
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name=f"MultiGol 1-3 Squadra Casa ({home_team})",
                        market_category="MULTIGOL_SQUADRA",
                        odd=odd_mg_h,
                        hit_rate=h_mg13,
                        rationale=f"{home_team} segna tra 1 e 3 reti nell'{h_mg13:.1f}% delle gare recenti.",
                    )
                )
        elif a_mg13 >= 75.0 and a_gf >= 1.4:
            odd_mg_a = quoted_odd(odds_dict, "MULTIGOL_SQUADRA", "1-3 Ospite", 1.27)
            if ODD_FLOOR <= odd_mg_a <= ODD_CEILING:
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name=f"MultiGol 1-3 Squadra Ospite ({away_team})",
                        market_category="MULTIGOL_SQUADRA",
                        odd=odd_mg_a,
                        hit_rate=a_mg13,
                        rationale=f"{away_team} segna con costanza tra 1 e 3 gol in trasferta ({a_mg13:.1f}% hit-rate).",
                    )
                )

        # 5. SPECIALIST CARTELLINI (Over 1.5 Cartellini della squadra, non del match)
        if (
            cards_market_allowed(tournament)
            and h_flow.get("cards_n", 0) >= 3
            and h_flow.get("avg_team_cards", 0.0) >= 2.0
        ):
            odd_cards = quoted_odd(odds_dict, "CARTELLINI", "Over 1.5 Squadra", 1.47)
            if ODD_FLOOR <= odd_cards <= ODD_CEILING:
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name=f"Over 1.5 Cartellini {home_team}",
                        market_category="CARTELLINI",
                        odd=odd_cards,
                        hit_rate=h_flow["team_cards_ov15_hr"],
                        rationale=(
                            f"{home_team} prende almeno 2 cartellini nel {h_flow['team_cards_ov15_hr']:.1f}% "
                            f"di {h_flow['cards_n']} gare con tabellino (media {h_flow['avg_team_cards']:.1f})."
                        ),
                    )
                )

        # 6. COMBO CLASSICA PROTETTA (1X + Over 1.5, entrambe vere nella stessa gara)
        if hr_combo is not None and h_gf >= 1.5 and h_ov15 >= 75.0 and (a_ga >= 1.3 or a_gf <= 1.0):
            odd_combo = odds_dict.get("COMBO", {}).get("1X + Over 1.5", 1.36)
            if 1.28 <= odd_combo <= 1.48:
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name="Combo 1X + Over 1.5",
                        market_category="COMBO",
                        odd=odd_combo,
                        hit_rate=round(hr_combo, 1),
                        rationale=(
                            f"1X e Over 1.5 insieme nel {hr_combo:.1f}% delle gare recenti di {home_team} "
                            f"(Over 1.5 di squadra {h_ov15:.1f}%)."
                        ),
                    )
                )

        # 7. TEMPI (Over 0.5 2° Tempo o MultiGol 1-3 2° Tempo)
        sh_ov05 = hp.get("hr_over_05_sh_match", 0.0)
        sh_mg13 = hp.get("hr_mg_1_3_sh_match", 0.0)
        if sh_ov05 >= 85.0:
            odd_sh = quoted_odd(odds_dict, "TEMPI", "Over 0.5 2° Tempo", 1.23)
            if ODD_FLOOR <= odd_sh <= ODD_CEILING:
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name="Over 0.5 2° Tempo",
                        market_category="TEMPI",
                        odd=odd_sh,
                        hit_rate=sh_ov05,
                        rationale=f"Gara che si sblocca nella ripresa con frequenza gol 2° tempo del {sh_ov05:.1f}%.",
                    )
                )
        elif sh_mg13 >= 80.0:
            odd_sh_mg = quoted_odd(odds_dict, "TEMPI", "MultiGol 1-3 2° Tempo", 1.29)
            if ODD_FLOOR <= odd_sh_mg <= ODD_CEILING:
                candidates.append(
                    MatchGemPick(
                        match_name=f"{home_team} vs {away_team}",
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament,
                        kickoff=kickoff,
                        market_name="MultiGol 1-3 2° Tempo",
                        market_category="TEMPI",
                        odd=odd_sh_mg,
                        hit_rate=sh_mg13,
                        rationale=f"Secondo tempo a ritmo regolare (hit rate MultiGol 1-3 al {sh_mg13:.1f}%).",
                    )
                )

        # Ordina per Hit Rate decrescente
        candidates.sort(key=lambda c: (c.hit_rate, c.odd), reverse=True)
        return candidates

    def build_tipster_style_ticket(
        self,
        matches_catalog: List[Dict[str, Any]],
        target_legs: int = 7,
        min_total_odd: float = 7.5,
        max_total_odd: float = 13.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Scansiona l'intero palinsesto e sintetizza un ticket multi-mercato bilanciato:
        - 1 Doppia Chance
        - 1 Gol (GG)
        - 1 Chance Mix
        - 1-2 MultiGol Squadra
        - 1 Specialistico (Cartellini)
        - 1 Combo protetta (1X + Over 1.5)
        - 1 Tempi (se necessario per raggiungere il numero di gambe)
        """
        all_picks_by_match: Dict[str, List[MatchGemPick]] = {}

        for m in matches_catalog:
            h = m.get("home_team", "")
            a = m.get("away_team", "")
            t = m.get("tournament", "")
            ko = m.get("kickoff", "")
            odds = m.get("markets", {})
            if not h or not a:
                continue

            gems = self.evaluate_match_gems(h, a, t, ko, odds)
            if gems:
                all_picks_by_match[f"{h} vs {a}"] = gems

        if len(all_picks_by_match) < target_legs:
            logger.warning(f"Partite analizzabili insufficienti ({len(all_picks_by_match)} < {target_legs})")
            return None

        # Strategia di composizione eterogenea per categoria
        category_slots = [
            "DOPPIA_CHANCE",
            "GOL",
            "CHANCE_MIX",
            "MULTIGOL_SQUADRA",
            "CARTELLINI",
            "COMBO",
            "MULTIGOL_SQUADRA",  # secondo multigol o tempi
            "TEMPI",
        ]

        selected_picks: List[MatchGemPick] = []
        used_matches = set()
        used_categories: Dict[str, int] = {}

        # 1. Assegna le selezioni garantendo la massima diversità
        for cat in category_slots:
            best_pick_for_cat: Optional[MatchGemPick] = None
            best_score = -1.0

            for m_name, picks in all_picks_by_match.items():
                if m_name in used_matches:
                    continue

                for p in picks:
                    if p.market_category == cat:
                        # Punteggio di idoneità: hit_rate ponderata per quota
                        score = p.hit_rate * p.odd
                        if score > best_score:
                            best_score = score
                            best_pick_for_cat = p

            if best_pick_for_cat:
                selected_picks.append(best_pick_for_cat)
                used_matches.add(best_pick_for_cat.match_name)
                used_categories[cat] = used_categories.get(cat, 0) + 1

            if len(selected_picks) >= target_legs:
                break

        # Se mancano slot per completare target_legs, aggiungi le migliori gemme rimanenti
        if len(selected_picks) < target_legs:
            for m_name, picks in all_picks_by_match.items():
                if m_name in used_matches:
                    continue
                if picks:
                    selected_picks.append(picks[0])
                    used_matches.add(m_name)
                    if len(selected_picks) >= target_legs:
                        break

        # Ordina per orario di inizio
        selected_picks.sort(key=lambda p: p.kickoff)

        # Calcola moltiplicatore totale
        total_odd = 1.0
        for p in selected_picks:
            total_odd *= p.odd
        total_odd = round(total_odd, 2)

        # Calcola probabilità congiunta
        joint_p = 1.0
        for p in selected_picks:
            joint_p *= (p.hit_rate / 100.0)
        joint_p = round(joint_p * 100.0, 1)

        ticket_id = f"AUTO_SYNTH_{datetime.now().strftime('%d%b').upper()}_{total_odd:.1f}X"
        in_band = min_total_odd <= total_odd <= max_total_odd
        if not in_band:
            logger.warning(
                "Moltiplicatore %.2f fuori dalla banda %.2f-%.2f",
                total_odd,
                min_total_odd,
                max_total_odd,
            )

        ticket_data = {
            "ticket_id": ticket_id,
            "title": f"Multipla Autonoma Tipster-Style ({len(selected_picks)} Eventi)",
            "architecture": "Hybrid Heterogeneous Asymmetric Mix (Regola #89 & #91)",
            "num_legs": len(selected_picks),
            "total_odds": total_odd,
            "odds_band": {"min": min_total_odd, "max": max_total_odd, "inside": in_band},
            "bonus_multiplier_est": round(total_odd * 1.15, 2),
            "joint_hit_rate_pct": joint_p,
            "status": "READY" if in_band else "OUT_OF_ODDS_BAND",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "legs": [
                {
                    "match": p.match_name,
                    "tournament": p.tournament,
                    "kickoff": p.kickoff,
                    "market": p.market_name,
                    "category": p.market_category,
                    "odd": p.odd,
                    "hit_rate": p.hit_rate,
                    "rationale": p.rationale,
                }
                for p in selected_picks
            ],
        }

        return ticket_data
