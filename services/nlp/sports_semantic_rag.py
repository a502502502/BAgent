#!/usr/bin/env python3
"""
services/nlp/sports_semantic_rag.py
Hugging Face SportsBERT-based Semantic Analysis & Tactical RAG Engine (Regole #43 & #49).

Utilizza il modello Hugging Face 'NeuML/sportsbert-small-embeddings' (384-d dense embeddings)
per analizzare semanticamente testi giornalistici, dichiarazioni e motivazioni di Sesto Senso,
calcolando affinità con bandiere di rischio:
- ROTATION_RISK (turnover, coppe infrasettimanali, titolari a riposo)
- SLOW_START (ritmi lenti, campo pesante, studio tattico nel 1° tempo)
- LOW_MOTIVATION (squadra già qualificata, salvezza acquisita, match scarico)
- INJURY_ALARM (infortuni, risentimenti, assenze dell'ultimo minuto)
- DEFENSIVE_WALL (blocco basso, catenaccio, pullman davanti alla porta)
- HIGH_INTENSITY_OFFENSE (pressing alto, tiro continuo, assedio offensivo)
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


class SportsSemanticRAG:
    """
    Motore RAG e di Audit Semantico basato su SportsBERT per la rassegna stampa e il Sesto Senso.
    """

    MODEL_NAME = "NeuML/sportsbert-small-embeddings"

    # Profili semantici di riferimento per ciascuna dimensione tattica
    REFERENCE_ANCHORS = {
        "ROTATION_RISK": (
            "ampio turnover, titolari a riposo, formazione stravolta per la coppa infrasettimanale, "
            "rotazione della rosa, seconde linee in campo, risparmiare energie per la Champions"
        ),
        "SLOW_START": (
            "partita molto bloccata e chiusa, ritmi lenti e spezzettati, avvio diesel, fase di studio prolungata, "
            "primo tempo privo di occasioni e senza tiri nello specchio, grande prudenza tattica"
        ),
        "LOW_MOTIVATION": (
            "squadra già aritmeticamente qualificata, salvezza raggiunta con largo anticipo, nessun obiettivo di classifica, "
            "match senza stimoli agonistici, clima amichevole di fine stagione, deconcentrazione"
        ),
        "INJURY_ALARM": (
            "infortunio muscolare, risentimento fisico, assente alla rifinitura, non convocato, "
            "problemi al ginocchio, affaticamento e condizioni precarie, forfait dell'ultimo minuto"
        ),
        "DEFENSIVE_WALL": (
            "catenaccio a oltranza, blocco bassissimo sulla propria trequarti, tutti i giocatori dietro la linea della palla, "
            "linea a cinque ultra-difensiva, protezione ermetica dell'area di rigore, pullman davanti alla porta"
        ),
        "HIGH_INTENSITY_OFFENSE": (
            "pressing asfissiante ultra-offensivo, attacco devastante, assedio totale nella metacampo avversaria, "
            "pioggia di tiri verso la porta avversaria, ritmi vertiginosi e verticalizzazioni continue"
        )
    }

    def __init__(self, device: Optional[str] = None):
        self._initialized = False
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu") if HF_AVAILABLE else "cpu"
        self.tokenizer = None
        self.model = None
        self._anchor_embeddings: Dict[str, np.ndarray] = {}

    def _lazy_init(self):
        if self._initialized or not HF_AVAILABLE:
            return
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self.model = AutoModel.from_pretrained(self.MODEL_NAME).to(self.device)
            self._initialized = True
            self._precompute_anchors()
        except Exception as e:
            print(f"[SportsSemanticRAG] Errore inizializzazione modello: {e}", file=sys.stderr)

    def encode(self, texts: List[str]) -> np.ndarray:
        """Calcola embeddings normalizzati a 384 dimensioni con mean-pooling."""
        self._lazy_init()
        if not self._initialized:
            # Fallback euristico se modello non disponibile
            return np.zeros((len(texts), 384), dtype=np.float32)

        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            # Mean pooling con attention mask
            attention_mask = inputs["attention_mask"].unsqueeze(-1)
            token_embeddings = outputs.last_hidden_state
            sum_embeddings = torch.sum(token_embeddings * attention_mask, dim=1)
            sum_mask = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
            embeddings = sum_embeddings / sum_mask
            # Normalizzazione L2
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        return embeddings.cpu().numpy()

    def _precompute_anchors(self):
        """Pre-calcola gli embeddings dei vettori di ancoraggio tattico."""
        anchor_keys = list(self.REFERENCE_ANCHORS.keys())
        anchor_texts = [self.REFERENCE_ANCHORS[k] for k in anchor_keys]
        embs = self.encode(anchor_texts)
        for idx, k in enumerate(anchor_keys):
            self._anchor_embeddings[k] = embs[idx]

    def audit_text_semantics(
        self,
        text: str,
        threshold: float = 0.55
    ) -> Dict[str, Any]:
        """
        Audita una motivazione di Sesto Senso o un testo giornalistico:
        calcola la somiglianza coseno con tutti i profili tattici e restituisce le bandiere attivate.
        """
        if not text or len(text.strip()) < 5:
            return {
                "passed": True,
                "scores": {},
                "flags": [],
                "dominant_cluster": "NEUTRAL"
            }

        self._lazy_init()
        if not self._initialized:
            # Fallback deterministico a parole chiave
            return self._keyword_fallback(text)

        text_emb = self.encode([text])[0]
        scores: Dict[str, float] = {}
        detected_flags: List[str] = []

        for flag_name, anchor_emb in self._anchor_embeddings.items():
            # Cosine similarity tra vettori già normalizzati L2 è il prodotto scalare
            sim = float(np.dot(text_emb, anchor_emb))
            scores[flag_name] = round(sim, 3)
            if sim >= threshold:
                detected_flags.append(flag_name)

        dominant = max(scores.items(), key=lambda x: x[1])

        return {
            "passed": True,
            "scores": scores,
            "flags": detected_flags,
            "dominant_cluster": dominant[0] if dominant[1] >= 0.40 else "NEUTRAL",
            "dominant_score": dominant[1]
        }

    def _keyword_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback rapido basato su regole lessicali se HF non è caricato."""
        t_low = text.lower()
        flags = []
        scores = {}
        if any(w in t_low for w in ["turnover", "riposo", "champions", "rotazioni"]):
            flags.append("ROTATION_RISK")
            scores["ROTATION_RISK"] = 0.70
        if any(w in t_low for w in ["diesel", "bloccata", "ritmi bassi", "studio"]):
            flags.append("SLOW_START")
            scores["SLOW_START"] = 0.70
        if any(w in t_low for w in ["qualificata", "salvezza raggiunta", "senza stimoli"]):
            flags.append("LOW_MOTIVATION")
            scores["LOW_MOTIVATION"] = 0.70
        if any(w in t_low for w in ["blocco basso", "catenaccio", "ermetic"]):
            flags.append("DEFENSIVE_WALL")
            scores["DEFENSIVE_WALL"] = 0.75
        return {
            "passed": True,
            "scores": scores,
            "flags": flags,
            "dominant_cluster": flags[0] if flags else "NEUTRAL",
            "dominant_score": 0.70 if flags else 0.0
        }


# Istanza singleton globale per riutilizzo veloce
_global_sports_rag: Optional[SportsSemanticRAG] = None

def get_sports_semantic_rag() -> SportsSemanticRAG:
    global _global_sports_rag
    if _global_sports_rag is None:
        _global_sports_rag = SportsSemanticRAG()
    return _global_sports_rag


if __name__ == "__main__":
    print("Test SportsSemanticRAG con Hugging Face NeuML/sportsbert-small-embeddings...")
    rag = get_sports_semantic_rag()
    
    test_cases = [
        "L'allenatore fa massiccio turnover tenendo a riposo i titolari per la sfida di Champions League.",
        "Lanús imposta un catenaccio ermetico con blocco bassissimo a protezione del pareggio.",
        "Primo tempo che si preannuncia diesel, ritmi lenti e grande fase di studio.",
        "Scontro ad alta intensità con assedio continuo nell'area di rigore e raffica di tiri."
    ]

    for t in test_cases:
        res = rag.audit_text_semantics(t)
        print("\nTesto:", t)
        print("Dominant Cluster:", res["dominant_cluster"], f"({res.get('dominant_score', 0):.2f})")
        print("Flags attivati:", res["flags"])
        print("Scores:", res["scores"])
