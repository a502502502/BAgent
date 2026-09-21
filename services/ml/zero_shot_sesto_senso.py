"""
ZeroShotSestoSenso — Classificatore Zero-Shot locale per l'audit delle notizie di Sesto Senso.
Utilizza DeBERTa/BART tramite Hugging Face Transformers per categorizzare news, tweet e rassegne
stampa locali in etichette di rischio operativo per il betting senza costi API.
"""

from __future__ import annotations
import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

DEFAULT_LABELS_MAP = {
    "infortunio, forfait o problema fisico": "INJURY_OR_ABSENCE",
    "turnover, rotazione o riposo precauzionale": "ROTATION_OR_TURNOVER",
    "tensione spogliatoio, stipendi non pagati o lite": "LOCKER_ROOM_OR_DISCIPLINE",
    "condizioni campo impraticabile, pioggia o vento": "TACTICAL_OR_SURFACE",
    "entusiasmo, recupero titolari o forma eccezionale": "POSITIVE_MOMENTUM",
}


class ZeroShotSestoSenso:
    """
    Classificatore Zero-Shot per il Sesto Senso sportivo.
    Classifica snippet testuali in categorie operative di rischio.
    """

    def __init__(
        self,
        model_name: str = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.device = device
        self._pipeline = None
        self._is_available = False
        self._init_pipeline()

    def _init_pipeline(self):
        try:
            from transformers import pipeline
            device_id = 0 if self.device == "cuda" else -1
            self._pipeline = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                device=device_id,
            )
            self._is_available = True
            logger.info(f"ZeroShot pipeline ({self.model_name}) inizializzata con successo.")
        except ImportError:
            logger.warning("Libreria 'transformers' non installata. Utilizzo fallback euristico su parole chiave.")
            self._is_available = False
        except Exception as e:
            logger.warning(f"Inizializzazione ZeroShot pipeline fallita ({e}). Utilizzo fallback euristico.")
            self._is_available = False

    @property
    def is_available(self) -> bool:
        return self._is_available

    def classify_snippet(self, text: str) -> Dict[str, Any]:
        """
        Classifica un singolo snippet informativo.
        Ritorna la categoria di rischio prevalente, la confidenza e l'impatto stimato.
        Utilizza un approccio ibrido: pattern matching sportivo ad alta precisione
        combinato con inferenza zero-shot DeBERTa per testi sfumati.
        """
        if not text or not text.strip():
            return {
                "top_category": "NEUTRAL",
                "confidence": 1.0,
                "is_risk": False,
                "impact_factor": 0.0,
                "scores": {},
                "model": "rule_based",
            }

        domain_res = self._fallback_classify(text)

        # Se abbiamo un chiaro segnale da pattern sportivo di dominio (es. 'risentimento', 'forfait', 'turnover', 'rientro')
        if domain_res["top_category"] != "NEUTRAL" and domain_res["confidence"] >= 0.65:
            domain_res["model"] = "Hybrid-SportsDomain"
            return domain_res

        candidate_labels = list(DEFAULT_LABELS_MAP.keys())

        if self.is_available and self._pipeline is not None:
            try:
                res = self._pipeline(text, candidate_labels=candidate_labels, multi_label=False)
                top_label = res["labels"][0]
                top_score = float(res["scores"][0])
                top_category = DEFAULT_LABELS_MAP.get(top_label, "UNKNOWN")
                scores = {DEFAULT_LABELS_MAP.get(lbl, lbl): round(float(sc), 4) for lbl, sc in zip(res["labels"], res["scores"])}
                impact_factor, is_risk = self._compute_impact(top_category, top_score)
                return {
                    "text": text,
                    "top_category": top_category,
                    "confidence": round(top_score, 4),
                    "is_risk": is_risk,
                    "impact_factor": impact_factor,
                    "scores": scores,
                    "model": "ZeroShot-DeBERTa",
                }
            except Exception as e:
                logger.warning(f"Errore inferenza pipeline ({e}), attivazione fallback.")
                return domain_res
        else:
            return domain_res

    def audit_news(self, snippets: List[str]) -> List[Dict[str, Any]]:
        """
        Processa una lista di rassegne stampa o snippet informativi.
        """
        return [self.classify_snippet(s) for s in snippets if s.strip()]

    @staticmethod
    def _compute_impact(category: str, score: float) -> tuple[float, bool]:
        """Determina il fattore di impatto moltiplicativo sul team/giocatore."""
        if score < 0.35:
            return 0.0, False

        impact_map = {
            "INJURY_OR_ABSENCE": (-0.25 * score, True),
            "ROTATION_OR_TURNOVER": (-0.20 * score, True),
            "LOCKER_ROOM_OR_DISCIPLINE": (-0.15 * score, True),
            "TACTICAL_OR_SURFACE": (-0.10 * score, True),
            "POSITIVE_MOMENTUM": (+0.12 * score, False),
        }
        return impact_map.get(category, (0.0, False))

    @staticmethod
    def _fallback_classify(text: str) -> Dict[str, Any]:
        """Classificazione euristica di fallback basata su regex e parole chiave."""
        t_low = text.lower()

        patterns = {
            "INJURY_OR_ABSENCE": [
                r"infortun", r"lesion", r"risentiment", r"stirament", r"forfait",
                r"out", r"indisponibil", r"distorsion", r"operat", r"stop", r"assent"
            ],
            "ROTATION_OR_TURNOVER": [
                r"turnover", r"ripos", r"panchina", r"rotazion", r"preservat",
                r"fatic", r"stanchezz", r"infrasettiman", r"coppa"
            ],
            "LOCKER_ROOM_OR_DISCIPLINE": [
                r"stipend", r"litig", r"societ", r"contestaz", r"crisi", r"esoner",
                r"multa", r"squalific", r"dissidi"
            ],
            "TACTICAL_OR_SURFACE": [
                r"fango", r"pioggia", r"maltempo", r"erba", r"terra", r"vento",
                r"campo pesante", r"impraticabil"
            ],
            "POSITIVE_MOMENTUM": [
                r"rientr", r"recuperat", r"titolare", r"entusiasmo", r"striscia",
                r"vittori", r"carico", r"in forma"
            ],
        }

        matched_scores = {}
        for cat, kw_list in patterns.items():
            count = sum(1 for kw in kw_list if re.search(kw, t_low))
            matched_scores[cat] = count

        best_cat = max(matched_scores, key=matched_scores.get)
        best_count = matched_scores[best_cat]

        if best_count > 0:
            confidence = min(0.90, 0.50 + 0.15 * best_count)
            top_category = best_cat
        else:
            confidence = 0.50
            top_category = "NEUTRAL"

        impact, is_risk = ZeroShotSestoSenso._compute_impact(top_category, confidence)

        return {
            "text": text,
            "top_category": top_category,
            "confidence": round(confidence, 2),
            "is_risk": is_risk,
            "impact_factor": round(impact, 2),
            "scores": {k: 1.0 if k == top_category else 0.0 for k in patterns},
            "model": "RuleBasedFallback",
        }
