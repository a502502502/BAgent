#!/usr/bin/env python3
"""
services/analysis/behavioral_market_rules.py
Motore di Regole Comportamentali Tattiche & Selezione Intelligente dei Mercati.

Collega le risposte a domande tattiche chiave ai mercati avanzati di Netwin:
1. "Le squadre segnano sempre nel primo tempo?" (Frequenza Gol 1° Tempo)
2. "Segnano più nel primo o nel secondo tempo?" (Distribuzione Temporale 1T vs 2T)
3. "Dopo che hanno segnato si chiudono o continuano ad attaccare?" (Reattività al Vantaggio / Game State)
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class TeamBehavioralProfile:
    team_name: str
    is_home: bool
    pct_matches_scoring_1h: float     # % gare in cui segna nel 1° Tempo
    pct_matches_scoring_2h: float     # % gare in cui segna nel 2° Tempo
    goal_share_1h: float              # % dei suoi gol totali che cadono nel 1° Tempo
    goal_share_2h: float              # % dei suoi gol totali che cadono nel 2° Tempo (es. 46-90')
    late_goal_rate: float             # % dei suoi gol che cadono dopo il 75' (martello finale)
    failed_to_score_pct: float        # % partite a secco
    clean_sheet_pct: float            # % partite senza subire gol
    post_lead_behavior: str           # 'RULLO_COMPRESSORE', 'GESTORE_DIFENSIVO', 'EQUILIBRATO'
    avg_goals_scored: float           # media gol fatti a partita
    avg_goals_conceded: float         # media gol subiti a partita

class BehavioralMarketRulesEngine:
    """
    Valuta l'accoppiamento tattico-statistico tra due squadre e identifica
    i mercati flessibili ad altissima probabilità (Regola #39).
    """

    @staticmethod
    def classify_post_lead_behavior(late_goal_rate: float, avg_goals_scored: float, goal_diff: float) -> str:
        """
        Determina se una squadra dopo il vantaggio continua ad attaccare (Rullo)
        o se si chiude a gestire il risultato (Gestore).
        """
        if avg_goals_scored >= 2.1 and late_goal_rate >= 0.24:
            return "RULLO_COMPRESSORE"  # Non si ferma all'1-0, segna anche nel finale (es. Bayern, Man Utd, Barça)
        elif avg_goals_scored <= 1.4 or (late_goal_rate <= 0.15 and goal_diff >= 0):
            return "GESTORE_DIFENSIVO"  # Passa in vantaggio e congela il match (es. Palmeiras, Atletico Madrid)
        else:
            return "EQUILIBRATO"

    def evaluate_match_markets(
        self,
        home_profile: TeamBehavioralProfile,
        away_profile: TeamBehavioralProfile,
        h2h_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Applica le regole comportamentali e seleziona i mercati ottimali.
        """
        recommended_markets = []

        # -------------------------------------------------------------
        # REGOLA 1: "CASA SEGNA IN ENTRAMBI I TEMPI: SI"
        # Domanda: La squadra di casa è un rullo compressore che segna con regolarità sia nel 1° che nel 2° tempo?
        # -------------------------------------------------------------
        if (
            home_profile.pct_matches_scoring_1h >= 0.70 and
            home_profile.pct_matches_scoring_2h >= 0.75 and
            home_profile.post_lead_behavior == "RULLO_COMPRESSORE" and
            away_profile.clean_sheet_pct <= 0.25
        ):
            recommended_markets.append({
                "market": "Casa Segna in Entrambi i Tempi: SI",
                "trigger_reason": (
                    f"{home_profile.team_name} segna nel 1°T nel {int(home_profile.pct_matches_scoring_1h*100)}% "
                    f"e nel 2°T nel {int(home_profile.pct_matches_scoring_2h*100)}% dei casi. "
                    f"Profilo Rullo Compressore (non rallenta dopo il vantaggio)."
                ),
                "tactical_logic": "Basta 1 gol per tempo; nessun vincolo sul totale gol complessivi o sull'ospite.",
                "confidence": "HIGH"
            })

        # -------------------------------------------------------------
        # REGOLA 2: "MULTIGOL 1-3 OSPITE (o CASA): SI"
        # Domanda: La squadra ospite è affidabile (segna quasi sempre) ma in trasferta è pragmatica (non fa goleada)?
        # -------------------------------------------------------------
        if (
            away_profile.failed_to_score_pct <= 0.20 and  # va a secco in meno del 20% delle gare
            away_profile.avg_goals_scored >= 1.0 and
            away_profile.avg_goals_scored <= 2.2          # difficilmente fa 4+ gol fuori casa
        ):
            recommended_markets.append({
                "market": f"MultiGol 1-3 Ospite ({away_profile.team_name}): SI",
                "trigger_reason": (
                    f"{away_profile.team_name} va a secco solo nel {int(away_profile.failed_to_score_pct*100)}% "
                    f"delle trasferte e segna tra 1 e 3 gol nel 90%+ dei casi."
                ),
                "tactical_logic": (
                    "Protegge dal risultato bloccato (0-1, 1-1, 0-2, 1-2). "
                    "Indipendente da quanti gol subisce o se vince/pareggia."
                ),
                "confidence": "VERY_HIGH"
            })

        # -------------------------------------------------------------
        # REGOLA 3: "1X + MULTIGOL 1-5: SI" (Protezione Totale Anti-Beffa)
        # Domanda: La squadra di casa è favorita ma ha la tendenza a vincere di misura (1-0 / 2-0 / 2-1)?
        # -------------------------------------------------------------
        if (
            home_profile.clean_sheet_pct >= 0.40 and
            home_profile.post_lead_behavior in ["GESTORE_DIFENSIVO", "EQUILIBRATO"]
        ):
            recommended_markets.append({
                "market": "1X + MultiGol 1-5: SI",
                "trigger_reason": (
                    f"{home_profile.team_name} è favorita e solida ma con profilo Gestore: "
                    f"tende a controllare dopo l'1-0 (evitare assolutamente il rigido '1 + Over 1.5')."
                ),
                "tactical_logic": "Copre l'1-0, 2-0, 1-1, 2-1, 3-0, 3-1, 4-1. Nessun rischio su match a basso punteggio.",
                "confidence": "VERY_HIGH"
            })

        # -------------------------------------------------------------
        # REGOLA 4: "OV 1°T 0.5 + OV 2°T 1.5: SI"
        # Domanda: Segnano più nel 1° o nel 2° tempo?
        # Risposta: 1°T di studio (basta 1 gol), 2°T le difese crollano e fioccano i gol (almeno 2 gol).
        # -------------------------------------------------------------
        combined_1h_over05 = 1.0 - (home_profile.failed_to_score_pct * away_profile.clean_sheet_pct)
        if (
            home_profile.goal_share_2h >= 0.55 and
            (home_profile.avg_goals_scored + away_profile.avg_goals_scored) >= 2.8 and
            home_profile.late_goal_rate >= 0.22
        ):
            recommended_markets.append({
                "market": "OV 1°T 0.5 + OV 2°T 1.5: SI",
                "trigger_reason": (
                    f"Il {int(home_profile.goal_share_2h*100)}% dei gol di {home_profile.team_name} "
                    f"cade nella ripresa con forte accelerazione nel finale ({int(home_profile.late_goal_rate*100)}% dopo il 75')."
                ),
                "tactical_logic": "Sfrutta l'apertura delle difese stanche nella ripresa senza forzare un 1° tempo a valanga.",
                "confidence": "HIGH"
            })

        # -------------------------------------------------------------
        # REGOLA 5: "DOPPIA CHANCE + GG: 1X + GG: SI"
        # Domanda: La squadra di casa non perde ma entrambe hanno difese permeabili e attacchi caldi?
        # -------------------------------------------------------------
        if (
            home_profile.clean_sheet_pct <= 0.35 and
            away_profile.failed_to_score_pct <= 0.25 and
            home_profile.avg_goals_scored >= 1.5 and
            away_profile.avg_goals_scored >= 1.2
        ):
            recommended_markets.append({
                "market": "Doppia Chance + GG: 1X + GG: SI",
                "trigger_reason": (
                    f"Fattore campo forte per {home_profile.team_name}, ma clean sheet rari ({int(home_profile.clean_sheet_pct*100)}%). "
                    f"{away_profile.team_name} segna quasi sempre ({int((1-away_profile.failed_to_score_pct)*100)}% gare a segno)."
                ),
                "tactical_logic": "Intercetta 1-1, 2-1, 3-1, 2-2 a quote eccezionali (spesso vicine a 2.00x).",
                "confidence": "HIGH"
            })

        return recommended_markets
