"""
services/ml/chronos_odds_forecaster.py — Time-Series Odds & Steam Move Forecaster.

Ispirato ad Amazon Chronos (amazon/chronos-t5-tiny) per il forecasting probabilistico
delle serie temporali di quote (Pinnacle, Betfair Exchange, Netwin).

Obiettivi sul Betting:
- Prevedere la quota di chiusura (Closing Line Value - CLV) a partire dai tick storici pre-match.
- Rilevare se un calo di quota è un vero "Steam Move" dei sindacati sharp o semplice rumore di mercato.
- Fornire stime probabilistiche (quantili 10%, 50%, 90%) sull'andamento della quota.
"""

from __future__ import annotations
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("ChronosOddsForecaster")


class ChronosOddsForecaster:
    """
    Forecaster di quote con architettura a doppio livello (Dual-Layer):
    1. Chronos Pipeline (se installato 'chronos-forecasting' o tramite Hugging Face Transformers).
    2. Fallback Autoregressivo & Smoothing Esponenziale Adattivo (zero dipendenze esterne).
    """

    def __init__(
        self,
        model_name: str = "amazon/chronos-t5-tiny",
        use_hf_chronos: bool = False,
        device: str = "cpu"
    ):
        self.model_name = model_name
        self.use_hf_chronos = use_hf_chronos
        self.device = device
        self._pipeline = None
        self._is_chronos_available = False

        if self.use_hf_chronos:
            self._init_chronos()

    def _init_chronos(self):
        """Inizializza la pipeline Chronos se disponibile."""
        try:
            # Chronos può essere usato tramite la libreria chronos o transformers
            from chronos import ChronosPipeline
            import torch
            device_str = "cuda" if (self.device == "cuda" and torch.cuda.is_available()) else "cpu"
            self._pipeline = ChronosPipeline.from_pretrained(
                self.model_name,
                device_map=device_str,
                torch_dtype=torch.bfloat16 if device_str == "cuda" else torch.float32,
            )
            self._is_chronos_available = True
            logger.info(f"Chronos Pipeline ({self.model_name}) inizializzata con successo.")
        except ImportError:
            logger.info("Libreria 'chronos-forecasting' non presente. Utilizzo motore statistico autoregressivo ad alta precisione.")
            self._is_chronos_available = False
        except Exception as e:
            logger.warning(f"Inizializzazione Chronos fallita ({e}). Utilizzo fallback statistico.")
            self._is_chronos_available = False

    @property
    def is_chronos_available(self) -> bool:
        return self._is_chronos_available

    def forecast_odds_movement(
        self,
        odds_series: List[float],
        prediction_horizon: int = 3,
        market_name: str = "Match Odds"
    ) -> Dict[str, Any]:
        """
        Prevede l'andamento futuro della quota data una serie cronologica di rilevazioni.
        
        Args:
            odds_series: Lista di quote in ordine cronologico (es. [2.10, 2.05, 1.98, 1.90]).
            prediction_horizon: Quanti step futuri prevedere (default 3 step).
            market_name: Nome del mercato analizzato.
        """
        if not odds_series or len(odds_series) < 2:
            return {
                "error": "Serie quote insufficiente (minimo 2 rilevazioni richieste)",
                "signal": "NO_DATA",
                "predicted_closing_odds": odds_series[-1] if odds_series else 1.0,
                "steam_probability": 0.0
            }

        series = np.array(odds_series, dtype=float)
        current_odds = float(series[-1])
        opening_odds = float(series[0])

        # Se Chronos HF è disponibile, esegue inferenza con il modello linguistico per time-series
        if self._is_chronos_available and self._pipeline is not None:
            try:
                import torch
                context = torch.tensor(series, dtype=torch.float32)
                forecast = self._pipeline.predict(
                    context,
                    prediction_length=prediction_horizon,
                    num_samples=20,
                    temperature=0.7,
                    top_k=50,
                    top_p=0.9
                )
                # forecast shape: [1, num_samples, prediction_length]
                low_q, median_q, high_q = np.quantile(forecast[0].numpy(), [0.1, 0.5, 0.9], axis=0)
                pred_closing = float(median_q[-1])
                pred_low = float(low_q[-1])
                pred_high = float(high_q[-1])
                engine_used = "HuggingFace_Chronos"
            except Exception as e:
                logger.warning(f"Errore durante inferenza Chronos ({e}), passo al fallback statistico.")
                pred_closing, pred_low, pred_high = self._statistical_forecast(series, prediction_horizon)
                engine_used = "Statistical_AR_Fallback"
        else:
            pred_closing, pred_low, pred_high = self._statistical_forecast(series, prediction_horizon)
            engine_used = "Statistical_AR_Fallback"

        # Analisi cinematica delle quote (Velocità, Accelerazione e Pressione Sharp)
        delta_total = current_odds - opening_odds
        pct_change = (delta_total / opening_odds) * 100.0
        
        # Velocità recente (ultimi step)
        recent_delta = series[-1] - series[-2]
        acceleration = 0.0
        if len(series) >= 3:
            prev_delta = series[-2] - series[-3]
            acceleration = recent_delta - prev_delta

        # Rilevamento Steam Move & Calcolo Probabilità
        # Uno steam move autentico presenta:
        # 1. Calo percentuale marcato (<= -4.0%)
        # 2. Accelerazione negativa (il calo aumenta di velocità o è costante)
        # 3. Quota prevista inferiore alla quota attuale
        steam_prob = 0.0
        if pct_change < -2.0:
            steam_prob += min(0.40, abs(pct_change) * 0.04)
        if recent_delta < 0:
            steam_prob += 0.25
        if acceleration <= 0:
            steam_prob += 0.20
        if pred_closing < current_odds:
            steam_prob += 0.15
        steam_prob = max(0.0, min(0.99, steam_prob))

        # Classificazione del segnale operativo
        if pct_change <= -5.0 and steam_prob >= 0.70:
            signal = "STRONG_STEAM_DROP"
            recommendation = "Valore immediato: la quota sul mercato commerciale è destinata a crollare ulteriormente."
        elif pct_change <= -2.5 and steam_prob >= 0.50:
            signal = "MODERATE_STEAM_DROP"
            recommendation = "Pressione ribassista in corso: quota interessante con vantaggio sul CLV."
        elif pct_change >= 4.0:
            signal = "DRIFTING_UP"
            recommendation = "Quota in forte salita (sconsigliata): il mercato sta scartando questa selezione."
        else:
            signal = "STABLE"
            recommendation = "Quota stabile: oscillazioni fisiologiche nel range di tolleranza."

        return {
            "market": market_name,
            "engine": engine_used,
            "opening_odds": round(opening_odds, 3),
            "current_odds": round(current_odds, 3),
            "predicted_closing_odds": round(max(1.01, pred_closing), 3),
            "confidence_band_90": {
                "low": round(max(1.01, pred_low), 3),
                "high": round(max(1.01, pred_high), 3)
            },
            "metrics": {
                "total_delta": round(delta_total, 3),
                "pct_change": round(pct_change, 2),
                "recent_velocity": round(recent_delta, 3),
                "acceleration": round(acceleration, 3),
                "steam_probability": round(steam_prob, 3)
            },
            "signal": signal,
            "recommendation": recommendation,
            "clv_advantage": round(current_odds - pred_closing, 3) if current_odds > pred_closing else 0.0
        }

    def _statistical_forecast(self, series: np.ndarray, horizon: int) -> Tuple[float, float, float]:
        """
        Modello predittivo autoregressivo con Holt-Winters Linear Trend e decay dinamico.
        Garantisce robustezza estrema e nessun overshoot irrealistico delle quote.
        """
        n = len(series)
        alpha = 0.45  # Peso per il livello attuale
        beta = 0.25   # Peso per il trend

        # Inizializzazione Holt
        level = series[0]
        trend = series[1] - series[0] if n > 1 else 0.0

        for i in range(1, n):
            prev_level = level
            level = alpha * series[i] + (1.0 - alpha) * (prev_level + trend)
            trend = beta * (level - prev_level) + (1.0 - beta) * trend

        # Previsione a termine con damping (il trend rallenta col passare del tempo)
        damping_factor = 0.85
        future_trend = sum(trend * (damping_factor ** k) for k in range(1, horizon + 1))
        forecast_median = level + future_trend

        # Stima della volatilità residua
        residuals = []
        for i in range(1, n):
            residuals.append(series[i] - series[i - 1])
        volatility = np.std(residuals) if len(residuals) > 1 else 0.02
        volatility = max(0.015, volatility)

        band_width = 1.645 * volatility * math.sqrt(horizon) # 90% confidence interval
        forecast_low = forecast_median - band_width
        forecast_high = forecast_median + band_width

        return forecast_median, forecast_low, forecast_high
