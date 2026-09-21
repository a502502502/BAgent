"""
services/ml/hf_sports_intelligence.py — Hugging Face Sports Intelligence & News Sentinel.

Analizza news, dichiarazioni pre-match, report infortuni e tweet di insider
usando modelli Hugging Face (NLP Sentiment & Zero-Shot Classification) combinati
con un motore di regole dominio sportivo (Italiano ed Inglese).

Impatto pratico sul Betting:
- Se il capocannoniere o il portiere titolare è out -> ricalibra xG (Dixon-Coles) prima del calcio d'inizio.
- Se un tennista lamenta problemi muscolari o ha fasciature -> applica penalità Elo e Stamina (Markov Engine).
- Rileva opportunità di valore prima che i bookmaker commerciali recepiscano le news (Steam Move anticipato).
"""

from __future__ import annotations
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("HFSportsIntelligence")


class HFSportsIntelligence:
    """
    Motore di Intelligence Sportiva basato su modelli Hugging Face e pattern matching avanzato.
    """

    # Dizionari di segnali critici sportivi (Italiano ed Inglese)
    INJURY_KEYWORDS = [
        "infortunio", "infortunato", "lesione", "problema muscolare", "risentimento",
        "distorsione", "stiramento", "operazione", "forfait", "salta la partita",
        "non convocato", "indisponibile", "positivo al test", "squalificato",
        "injury", "injured", "out of the match", "ruled out", "hamstring",
        "muscle problem", "knock", "doubtful", "suspended", "withdrawn"
    ]

    TURNOVER_KEYWORDS = [
        "turnover", "rotazione", "riserve", "seconda linea", "a riposo",
        "panchina", "ampio turnover", "in vista della coppa", "priorità champions",
        "rested", "benched", "rotation", "second-string", "prioritizing"
    ]

    CRISIS_KEYWORDS = [
        "crisi", "esonero", "contestazione", "spogliatoio spaccato", "sfiducia",
        "dimissioni", "ritiro punitivo", "ultimatum", "crisi societaria",
        "crisis", "sacking", "under pressure", "dressing room unrest", "ultimatum"
    ]

    HIGH_MORALE_KEYWORDS = [
        "entusiasmo", "vittoria nel derby", "striscia vincente", "imbattuti",
        "ritorno del capitano", "rinnovo", "clima euforico", "pieno recupero",
        "winning streak", "boost", "unbeaten", "high morale", "full recovery"
    ]

    # Keyword specifiche Tennis
    TENNIS_PHYSICAL_KEYWORDS = [
        "medical timeout", "mto", "fasciatura", "problema alla spalla", "gomito",
        "affaticamento", "crampi", "zoppica", "ha vomitato", "condizioni precarie",
        "strappo", "strapped", "shoulder issue", "elbow", "cramping", "limping"
    ]

    def __init__(self, use_hf_pipeline: bool = False, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.use_hf_pipeline = use_hf_pipeline
        self.model_name = model_name
        self._classifier = None

        if self.use_hf_pipeline:
            self._init_pipeline()

    def _init_pipeline(self):
        """Inizializza la pipeline Hugging Face in lazy mode per non rallentare l'avvio."""
        try:
            from transformers import pipeline
            logger.info(f"Caricamento pipeline Hugging Face ({self.model_name})...")
            self._classifier = pipeline("sentiment-analysis", model=self.model_name)
            logger.info("Pipeline Hugging Face caricata con successo.")
        except Exception as e:
            logger.warning(f"Impossibile caricare la pipeline Hugging Face ({e}). Uso motore euristico ad alte prestazioni.")
            self._classifier = None

    def analyze_football_team_news(self, team_name: str, news_snippets: List[str]) -> Dict[str, Any]:
        """
        Analizza le notizie relative a una squadra di calcio.
        Restituisce moltiplicatori correttivi per xG Attacco e xG Difesa.
        """
        text_corpus = " ".join(news_snippets).lower()
        
        detected_injuries = [kw for kw in self.INJURY_KEYWORDS if kw in text_corpus]
        detected_turnover = [kw for kw in self.TURNOVER_KEYWORDS if kw in text_corpus]
        detected_crisis = [kw for kw in self.CRISIS_KEYWORDS if kw in text_corpus]
        detected_morale = [kw for kw in self.HIGH_MORALE_KEYWORDS if kw in text_corpus]

        # Calcolo moltiplicatori xG
        # Default: 1.0 (nessuna variazione)
        xg_att_multiplier = 1.0
        xg_def_multiplier = 1.0 # > 1.0 significa difesa più debole (concede più gol attesi)
        morale_score = 0.0 # da -1.0 a +1.0

        # Impatto infortuni/assenze
        if detected_injuries:
            # Penalità attacco dal -10% al -22% a seconda della frequenza
            att_penalty = min(0.22, 0.10 + len(detected_injuries) * 0.04)
            xg_att_multiplier -= att_penalty
            morale_score -= 0.35

        # Impatto turnover
        if detected_turnover:
            xg_att_multiplier -= 0.12
            xg_def_multiplier += 0.10 # Difesa meno affiatata
            morale_score -= 0.20

        # Impatto crisi / esonero
        if detected_crisis:
            xg_def_multiplier += 0.18 # Spogliatoio fragile, concede di più
            morale_score -= 0.45

        # Impatto entusiasmo / morale alto
        if detected_morale and not detected_crisis:
            xg_att_multiplier += 0.10
            morale_score += 0.40

        # Hugging Face sentiment score se disponibile
        hf_sentiment = "NEUTRAL"
        if self._classifier and news_snippets:
            try:
                # Eseguiamo il sentiment sul primo snippet più lungo
                longest_snippet = max(news_snippets, key=len)[:512]
                res = self._classifier(longest_snippet)[0]
                hf_sentiment = f"{res['label']} ({res['score']:.2f})"
                if res["label"] == "NEGATIVE" and res["score"] > 0.85:
                    morale_score -= 0.20
                elif res["label"] == "POSITIVE" and res["score"] > 0.85:
                    morale_score += 0.20
            except Exception as e:
                logger.debug(f"Errore inferenza HF: {e}")

        # Clamp finale
        xg_att_multiplier = max(0.65, min(1.30, xg_att_multiplier))
        xg_def_multiplier = max(0.70, min(1.40, xg_def_multiplier))
        morale_score = max(-1.0, min(1.0, morale_score))

        return {
            "team": team_name,
            "xg_att_multiplier": round(xg_att_multiplier, 3),
            "xg_def_multiplier": round(xg_def_multiplier, 3),
            "morale_score": round(morale_score, 2),
            "hf_sentiment": hf_sentiment,
            "detected_signals": {
                "injuries": detected_injuries,
                "turnover": detected_turnover,
                "crisis": detected_crisis,
                "high_morale": detected_morale
            }
        }

    def analyze_tennis_player_news(self, player_name: str, news_snippets: List[str]) -> Dict[str, Any]:
        """
        Analizza le notizie relative a un tennista prima del match.
        Rileva infortuni, fasciature o affaticamento per correggere Elo e Stamina.
        """
        text_corpus = " ".join(news_snippets).lower()

        physical_issues = [kw for kw in self.TENNIS_PHYSICAL_KEYWORDS if kw in text_corpus]
        general_injuries = [kw for kw in self.INJURY_KEYWORDS if kw in text_corpus]
        high_morale = [kw for kw in self.HIGH_MORALE_KEYWORDS if kw in text_corpus]

        elo_adjustment = 0.0 # Variazione punti Elo (-100 a +60)
        stamina_penalty = 0.0 # Penalità da sottrarre al parametro stamina (0.0 a 0.35)
        physical_warning = False

        if physical_issues or general_injuries:
            physical_warning = True
            count = len(physical_issues) + len(general_injuries)
            # Penalità Elo da -35 a -80 punti
            elo_adjustment -= min(80.0, 35.0 + count * 15.0)
            # Penalità stamina (rischio altissimo di crollo dal 2° set o bagel)
            stamina_penalty = min(0.35, 0.15 + count * 0.05)

        if high_morale and not physical_warning:
            elo_adjustment += 25.0

        return {
            "player": player_name,
            "elo_adjustment": round(elo_adjustment, 1),
            "stamina_penalty": round(stamina_penalty, 2),
            "physical_warning": physical_warning,
            "detected_signals": {
                "physical_issues": physical_issues,
                "general_injuries": general_injuries,
                "high_morale": high_morale
            }
        }

    def adjust_match_xg(
        self,
        xg_home_pre: float,
        xg_away_pre: float,
        home_news: List[str],
        away_news: List[str],
        home_team: str = "Home",
        away_team: str = "Away"
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Applica i moltiplicatori di intelligence notizie agli xG pre-match
        prima di passarli a XgPoissonEngine (Dixon-Coles).
        """
        home_intel = self.analyze_football_team_news(home_team, home_news)
        away_intel = self.analyze_football_team_news(away_team, away_news)

        # L'xG finale della squadra di casa è il suo attacco moltiplicato per la vulnerabilità difensiva dell'avversario
        adj_xg_home = xg_home_pre * home_intel["xg_att_multiplier"] * away_intel["xg_def_multiplier"]
        adj_xg_away = xg_away_pre * away_intel["xg_att_multiplier"] * home_intel["xg_def_multiplier"]

        audit = {
            "home_intel": home_intel,
            "away_intel": away_intel,
            "raw_xg": {"home": xg_home_pre, "away": xg_away_pre},
            "adjusted_xg": {"home": round(adj_xg_home, 3), "away": round(adj_xg_away, 3)}
        }

        return adj_xg_home, adj_xg_away, audit

    def adjust_tennis_elo(
        self,
        p1_elo_pre: float,
        p2_elo_pre: float,
        p1_news: List[str],
        p2_news: List[str],
        p1_stamina_pre: float = 0.80,
        p2_stamina_pre: float = 0.80,
        p1_name: str = "Player 1",
        p2_name: str = "Player 2"
    ) -> Tuple[float, float, float, float, Dict[str, Any]]:
        """
        Applica le correzioni di intelligence notizie all'Elo e alla Stamina dei tennisti
        prima di passarli a SurfaceEloEngine (Markov Engine).
        """
        p1_intel = self.analyze_tennis_player_news(p1_name, p1_news)
        p2_intel = self.analyze_tennis_player_news(p2_name, p2_news)

        adj_elo1 = p1_elo_pre + p1_intel["elo_adjustment"]
        adj_elo2 = p2_elo_pre + p2_intel["elo_adjustment"]

        adj_stamina1 = max(0.40, p1_stamina_pre - p1_intel["stamina_penalty"])
        adj_stamina2 = max(0.40, p2_stamina_pre - p2_intel["stamina_penalty"])

        audit = {
            "p1_intel": p1_intel,
            "p2_intel": p2_intel,
            "raw_elo": {p1_name: p1_elo_pre, p2_name: p2_elo_pre},
            "adjusted_elo": {p1_name: round(adj_elo1, 1), p2_name: round(adj_elo2, 1)},
            "adjusted_stamina": {p1_name: round(adj_stamina1, 2), p2_name: round(adj_stamina2, 2)}
        }

        return adj_elo1, adj_elo2, adj_stamina1, adj_stamina2, audit
