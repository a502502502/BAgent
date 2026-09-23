"""
TabPFNSportsPredictor — Modello Fondazionale per Dati Tabellari basato su Transformer.
Utilizza TabPFN (Prior-Data Fitted Networks) per calcolare probabilità bayesiane calibrate
su leghe minori o campionati con storico ridotto, senza bisogno di retraining.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TabPFNSportsPredictor:
    """
    Predittore basato su TabPFN per il calcio.
    Esegue inferenza in-context su un set di match recenti della lega.
    """

    DEFAULT_FEATURES = [
        "home_elo",
        "away_elo",
        "elo_diff",
        "home_form_5",
        "away_form_5",
        "home_gd_5",
        "away_gd_5",
        "home_advantage",
    ]

    def __init__(self, device: str = "cpu", n_estimators: int = 4):
        self.device = device
        self.n_estimators = n_estimators
        self._classifier = None
        self._is_available = False
        self._init_model()

    def _init_model(self):
        try:
            from tabpfn import TabPFNClassifier
            self._classifier = TabPFNClassifier(
                device=self.device,
                n_estimators=self.n_estimators,
            )
            self._is_available = True
            logger.info("TabPFNClassifier inizializzato con successo.")
        except ImportError:
            logger.warning("Libreria 'tabpfn' non installata. TabPFNSportsPredictor utilizzerà il fallback euristico.")
            self._is_available = False
        except Exception as e:
            logger.warning(f"Inizializzazione TabPFN fallita ({e}). Utilizzo fallback euristico.")
            self._is_available = False

    @property
    def is_available(self) -> bool:
        return self._is_available

    def _generate_synthetic_prior_football(self) -> pd.DataFrame:
        """
        Genera un dataset di riferimento a priori (30 match calibrati)
        per leghe minori dove mancano dati storici granulari.
        Classi target: 0 = Away (2), 1 = Draw (X), 2 = Home (1).
        """
        records = []
        # Campioni bilanciati distribuiti secondo ELO diff
        diffs = [-300, -200, -100, -50, 0, 50, 100, 200, 300]
        for diff in diffs:
            h_elo = 1500 + diff / 2
            a_elo = 1500 - diff / 2
            # 3 scenari per ciascun diff: Home win, Draw, Away win pesati
            if diff > 150:
                results = [2, 2, 2, 1, 0] # Favorita netta casa
            elif diff > 0:
                results = [2, 2, 1, 1, 0] # Leggera favorita casa
            elif diff > -150:
                results = [2, 1, 1, 0, 0] # Equilibrata
            else:
                results = [1, 0, 0, 0, 2] # Favorita ospite

            for r in results:
                h_form = 8.0 + (diff / 50.0)
                a_form = 8.0 - (diff / 50.0)
                records.append({
                    "home_elo": h_elo,
                    "away_elo": a_elo,
                    "elo_diff": diff,
                    "home_form_5": max(1.0, min(15.0, h_form)),
                    "away_form_5": max(1.0, min(15.0, a_form)),
                    "home_gd_5": (diff / 100.0) * 2.0,
                    "away_gd_5": -(diff / 100.0) * 2.0,
                    "home_advantage": 1.0,
                    "result": r,
                })
        return pd.DataFrame(records)

    def predict_football(
        self,
        home_team: str,
        away_team: str,
        home_elo: float = 1500.0,
        away_elo: float = 1500.0,
        home_form_5: float = 7.0,
        away_form_5: float = 7.0,
        home_gd_5: float = 0.0,
        away_gd_5: float = 0.0,
        league_history: Optional[pd.DataFrame] = None,
        market_odds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calcola probabilità 1X2 bayesiane con TabPFN in-context learning.
        """
        elo_diff = home_elo - away_elo
        query_row = {
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_diff": elo_diff,
            "home_form_5": home_form_5,
            "away_form_5": away_form_5,
            "home_gd_5": home_gd_5,
            "away_gd_5": away_gd_5,
            "home_advantage": 1.0,
        }
        query_df = pd.DataFrame([query_row])[self.DEFAULT_FEATURES]

        if self.is_available and self._classifier is not None:
            try:
                # Utilizza lo storico della lega se fornito (almeno 15 match), altrimenti prior sintetico
                if league_history is not None and len(league_history) >= 15:
                    train_df = league_history.copy()
                else:
                    train_df = self._generate_synthetic_prior_football()

                X_train = train_df[self.DEFAULT_FEATURES]
                y_train = train_df["result"].astype(int)

                self._classifier.fit(X_train, y_train)
                probs = self._classifier.predict_proba(query_df)[0]
                classes = list(self._classifier.classes_)

                # Mappa le classi [0: Away, 1: Draw, 2: Home]
                prob_map = {c: float(p) for c, p in zip(classes, probs)}
                p_away = prob_map.get(0, 0.25)
                p_draw = prob_map.get(1, 0.28)
                p_home = prob_map.get(2, 0.47)
            except Exception as e:
                logger.warning(f"Errore inferenza TabPFN ({e}), attivazione fallback.")
                p_home, p_draw, p_away = self._fallback_probs(elo_diff)
        else:
            p_home, p_draw, p_away = self._fallback_probs(elo_diff)

        # Normalizzazione
        total = p_home + p_draw + p_away
        p_home = round(p_home / total, 4)
        p_draw = round(p_draw / total, 4)
        p_away = round(p_away / total, 4)
        p_1x = round(p_home + p_draw, 4)
        p_x2 = round(p_draw + p_away, 4)

        fair_1 = round(1.0 / p_home, 2) if p_home > 0 else 99.0
        fair_x = round(1.0 / p_draw, 2) if p_draw > 0 else 99.0
        fair_2 = round(1.0 / p_away, 2) if p_away > 0 else 99.0
        fair_1x = round(1.0 / p_1x, 2) if p_1x > 0 else 99.0
        fair_x2 = round(1.0 / p_x2, 2) if p_x2 > 0 else 99.0

        result = {
            "model": "TabPFN" if self.is_available else "HeuristicFallback",
            "home_team": home_team,
            "away_team": away_team,
            "prob_1": p_home,
            "prob_x": p_draw,
            "prob_2": p_away,
            "prob_1x": p_1x,
            "prob_x2": p_x2,
            "fair_odds": {
                "1": fair_1,
                "X": fair_x,
                "2": fair_2,
                "1X": fair_1x,
                "X2": fair_x2,
            },
            "value_bets": [],
        }

        if market_odds:
            for mkt, fair_o in result["fair_odds"].items():
                if mkt in market_odds:
                    odd = market_odds[mkt]
                    prob = 1.0 / fair_o
                    edge = round((prob * odd - 1.0) * 100, 2)
                    if edge > 3.0:
                        result["value_bets"].append({
                            "selection": mkt,
                            "odds": odd,
                            "fair_odds": fair_o,
                            "edge_pct": edge
                        })

        return result

    @staticmethod
    def _fallback_probs(elo_diff: float) -> tuple[float, float, float]:
        """Fallback logistico calibrato su diff ELO."""
        import math
        # Modello logistico con vantaggio campo (+65 ELO)
        effective_diff = elo_diff + 65.0
        p_home = 1.0 / (1.0 + math.exp(-effective_diff / 220.0))
        p_draw = 0.28 * math.exp(-abs(effective_diff) / 600.0)
        p_away = max(0.05, 1.0 - p_home - p_draw)
        p_home = max(0.05, p_home)
        return p_home, p_draw, p_away
