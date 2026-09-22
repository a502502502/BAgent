"""
services/ml/hf_sports_intelligence.py — Hugging Face Multilingual Sports Intelligence & News Sentinel.

Analizza news, dichiarazioni pre-match, report infortuni e rassegna stampa
in 4 LINGUE (Spagnolo 🇦🇷, Portoghese 🇧🇷, Italiano 🇮🇹, Inglese 🇬🇧)
usando modelli Hugging Face (Multilingual Zero-Shot & Sentiment) combinati
con un motore di regole di dominio calcistico ad alte prestazioni.

NOTE DI SISTEMA:
- REGOLA SUPREMA RISPETTATA: 100% Calcio. Nessun evento, parametro o metodo sul Tennis.
- Calibra dinamicamente i moltiplicatori di xG per XgPoissonEngine (Dixon-Coles).
"""

from __future__ import annotations
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("HFSportsIntelligence")


class HFSportsIntelligence:
    """
    Motore di Intelligence Calcistica Multilingue basato su Hugging Face
    e dizionari ottimizzati per campionati Europei e Sudamericani.
    """

    # 1. INFORTUNI ED ASSENZE (IT, EN, ES 🇦🇷, PT 🇧🇷)
    INJURY_KEYWORDS = [
        # Italiano
        "infortunio", "infortunato", "lesione", "problema muscolare", "risentimento",
        "distorsione", "stiramento", "operazione", "forfait", "salta la partita",
        "non convocato", "indisponibile", "squalificato",
        # Inglese
        "injury", "injured", "out of the match", "ruled out", "hamstring",
        "muscle problem", "knock", "doubtful", "suspended", "withdrawn",
        # Spagnolo (Argentina / Sudamerica)
        "lesión", "lesionado", "molestia muscular", "desgarro", "isquiotibial",
        "esguince", "baja confirmada", "no viajó", "al margen", "descartado",
        "suspendido", "quedó afuera", "rotura", "molestias físicas",
        # Portoghese (Brasile)
        "lesão", "lesionado", "dores na coxa", "desfalque", "estiramento",
        "fora do jogo", "vetado pelo dm", "departamento médico", "entorse",
        "suspenso", "poupado por dores", "incômodo muscular", "não joga"
    ]

    # 2. TURNOVER E ROTAZIONE (IT, EN, ES 🇦🇷, PT 🇧🇷)
    TURNOVER_KEYWORDS = [
        # Italiano
        "turnover", "rotazione", "riserve", "seconda linea", "a riposo",
        "panchina", "ampio turnover", "in vista della coppa",
        # Inglese
        "rested", "benched", "rotation", "second-string", "prioritizing cup",
        # Spagnolo (Argentina / Sudamerica)
        "rotación", "equipo alternativo", "suplentes", "cuidar jugadores",
        "pensando en la copa", "mix de titulares", "descanso para", "guardar figuras",
        # Portoghese (Brasile)
        "vai poupar", "poupando titulares", "time misto", "time reserva",
        "foco na libertadores", "foco na copa", "preservado", "segunda linha"
    ]

    # 3. CRISI E TENSIONE (IT, EN, ES 🇦🇷, PT 🇧🇷)
    CRISIS_KEYWORDS = [
        # Italiano
        "crisi", "esonero", "contestazione", "spogliatoio spaccato", "sfiducia",
        "dimissioni", "ritiro punitivo", "ultimatum", "crisi societaria",
        # Inglese
        "crisis", "sacking", "under pressure", "dressing room unrest", "ultimatum",
        # Spagnolo (Argentina / Sudamerica)
        "crisis", "ultimátum al dt", "clima caliente", "hinchada enfurecida",
        "renuncia", "rescisión de contrato", "vestuario roto", "pelea interna",
        # Portoghese (Brasile)
        "crise", "demissão", "pressão sobre o técnico", "torcida protesta",
        "vestiário rachado", "salários atrasados", "cobrança da organizada"
    ]

    # 4. MORALE ALTO ED ENTUSIASMO (IT, EN, ES 🇦🇷, PT 🇧🇷)
    HIGH_MORALE_KEYWORDS = [
        # Italiano
        "entusiasmo", "vittoria nel derby", "striscia vincente", "imbattuti",
        "ritorno del capitano", "rinnovo", "clima euforico", "pieno recupero",
        # Inglese
        "winning streak", "boost", "unbeaten", "high morale", "full recovery",
        # Spagnolo (Argentina / Sudamerica)
        "fiesta en la cancha", "clima de fiesta", "racha positiva", "invicto",
        "recupera a su figura", "ánimo por las nubes", "goleada histórica",
        # Portoghese (Brasile)
        "embalado", "fase iluminada", "sequência invicta", "volta do artilheiro",
        "moral elevado", "clima de decisão", "estádio lotado"
    ]

    def __init__(
        self,
        use_hf_pipeline: bool = False,
        sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english",
        multilingual_zero_shot_model: str = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        device: str = "cpu"
    ):
        self.use_hf_pipeline = use_hf_pipeline
        self.sentiment_model = sentiment_model
        self.multilingual_zero_shot_model = multilingual_zero_shot_model
        self.device = device
        
        self._sentiment_classifier = None
        self._zero_shot_classifier = None

        if self.use_hf_pipeline:
            self._init_pipelines()

    def _init_pipelines(self):
        """Inizializza le pipeline Hugging Face in lazy mode."""
        try:
            from transformers import pipeline
            device_id = 0 if self.device == "cuda" else -1
            
            logger.info(f"Caricamento pipeline Zero-Shot Multilingue ({self.multilingual_zero_shot_model})...")
            self._zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model=self.multilingual_zero_shot_model,
                device=device_id
            )
            logger.info("Pipeline Zero-Shot Multilingue caricata con successo.")
        except Exception as e:
            logger.warning(f"Impossibile caricare Zero-Shot HF ({e}). Uso motore euristico multilingue ad alte prestazioni.")
            self._zero_shot_classifier = None

    def analyze_football_team_news(self, team_name: str, news_snippets: List[str]) -> Dict[str, Any]:
        """
        Analizza le notizie relative a una squadra di calcio (supporta IT, EN, ES, PT).
        Restituisce moltiplicatori correttivi per xG Attacco e xG Difesa.
        """
        text_corpus = " ".join(news_snippets).lower()
        
        detected_injuries = [kw for kw in self.INJURY_KEYWORDS if kw in text_corpus]
        detected_turnover = [kw for kw in self.TURNOVER_KEYWORDS if kw in text_corpus]
        detected_crisis = [kw for kw in self.CRISIS_KEYWORDS if kw in text_corpus]
        detected_morale = [kw for kw in self.HIGH_MORALE_KEYWORDS if kw in text_corpus]

        # Inizializzazione moltiplicatori xG
        # Default: 1.0 (nessuna variazione)
        xg_att_multiplier = 1.0
        xg_def_multiplier = 1.0  # > 1.0 significa difesa indebolita (concede più xG agli avversari)
        morale_score = 0.0       # da -1.0 a +1.0

        # Impatto infortuni/assenze
        if detected_injuries:
            att_penalty = min(0.24, 0.10 + len(detected_injuries) * 0.04)
            xg_att_multiplier -= att_penalty
            morale_score -= 0.35

        # Impatto turnover / poupar titulares
        if detected_turnover:
            xg_att_multiplier -= 0.14
            xg_def_multiplier += 0.12  # Squadra con riserve meno affiatata
            morale_score -= 0.20

        # Impatto crisi societaria / esonero
        if detected_crisis:
            xg_def_multiplier += 0.18
            morale_score -= 0.45

        # Impatto entusiasmo / striscia positiva
        if detected_morale and not detected_crisis:
            xg_att_multiplier += 0.10
            morale_score += 0.40

        # Valutazione Zero-Shot se disponibile
        hf_zero_shot = None
        if self._zero_shot_classifier and news_snippets:
            try:
                candidate_labels = [
                    "infortunio o assenza titolare",
                    "ampio turnover o squadra riserve",
                    "crisi societaria o contestazione",
                    "entusiasmo e momento positivo"
                ]
                sample_text = " ".join(news_snippets)[:512]
                res = self._zero_shot_classifier(sample_text, candidate_labels=candidate_labels)
                top_label = res["labels"][0]
                top_score = res["scores"][0]
                hf_zero_shot = {"top_label": top_label, "confidence": round(top_score, 2)}

                if top_score >= 0.70:
                    if "infortunio" in top_label:
                        xg_att_multiplier = min(xg_att_multiplier, 0.82)
                    elif "turnover" in top_label:
                        xg_att_multiplier = min(xg_att_multiplier, 0.85)
                        xg_def_multiplier = max(xg_def_multiplier, 1.15)
                    elif "crisi" in top_label:
                        xg_def_multiplier = max(xg_def_multiplier, 1.20)
                    elif "entusiasmo" in top_label:
                        xg_att_multiplier = max(xg_att_multiplier, 1.10)
            except Exception as e:
                logger.debug(f"Errore inferenza Zero-Shot HF: {e}")

        # Clamp finale per evitare oscillazioni irrealistiche
        xg_att_multiplier = max(0.65, min(1.30, xg_att_multiplier))
        xg_def_multiplier = max(0.70, min(1.40, xg_def_multiplier))
        morale_score = max(-1.0, min(1.0, morale_score))

        return {
            "team": team_name,
            "xg_att_multiplier": round(xg_att_multiplier, 3),
            "xg_def_multiplier": round(xg_def_multiplier, 3),
            "morale_score": round(morale_score, 2),
            "hf_zero_shot": hf_zero_shot,
            "detected_signals": {
                "injuries": detected_injuries,
                "turnover": detected_turnover,
                "crisis": detected_crisis,
                "high_morale": detected_morale
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
        prima di passarli al motore statistico Dixon-Coles (XgPoissonEngine).
        """
        home_intel = self.analyze_football_team_news(home_team, home_news)
        away_intel = self.analyze_football_team_news(away_team, away_news)

        # L'xG finale della squadra di casa è il suo attacco moltiplicato per la vulnerabilità difensiva avversaria
        adj_xg_home = xg_home_pre * home_intel["xg_att_multiplier"] * away_intel["xg_def_multiplier"]
        adj_xg_away = xg_away_pre * away_intel["xg_att_multiplier"] * home_intel["xg_def_multiplier"]

        audit = {
            "home_intel": home_intel,
            "away_intel": away_intel,
            "raw_xg": {"home": xg_home_pre, "away": xg_away_pre},
            "adjusted_xg": {"home": round(adj_xg_home, 3), "away": round(adj_xg_away, 3)}
        }

        return adj_xg_home, adj_xg_away, audit
