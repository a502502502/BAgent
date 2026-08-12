"""
PredictionLogger — registro locale delle previsioni BAgent.

Salva ogni analisi in data/predictions/log.json.
Permette di aggiungere il risultato reale e calcolare le performance.

Utilizzo:
    logger = PredictionLogger()
    pid = logger.save(result)           # ritorna l'ID della previsione
    logger.add_result(pid, "H", 2, 1)  # aggiunge risultato reale
    stats = logger.stats()             # calcola metriche aggregate
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


LOG_PATH = Path("data/predictions/log.json")


class PredictionLogger:
    """
    Gestisce il registro locale delle previsioni.

    Ogni entry contiene:
      - id:             identificatore univoco
      - created_at:     timestamp analisi
      - home / away:    nomi squadre
      - match_date:     data partita
      - base_probs:     probabilità dal modello statistico
      - adjusted_probs: probabilità dopo Sesto Senso
      - goal_markets:   Over/Under, BTTS da Poisson
      - market_odds:    quote inserite dall'utente
      - value_signals:  value bet identificate
      - result:         'H' | 'D' | 'A' | None (da inserire dopo)
      - home_goals:     gol casa (da inserire dopo)
      - away_goals:     gol ospite (da inserire dopo)
      - settled_at:     timestamp quando è stato inserito il risultato
    """

    def __init__(self, log_path: Path = LOG_PATH):
        self.log_path = Path(log_path)
        self._ensure_file()

    # ------------------------------------------------------------------
    # Lettura / scrittura
    # ------------------------------------------------------------------

    def _ensure_file(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text(
                json.dumps({"predictions": []}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _load(self) -> dict:
        return json.loads(self.log_path.read_text(encoding="utf-8"))

    def _save(self, data: dict):
        self.log_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Salva previsione
    # ------------------------------------------------------------------

    def save(self, result) -> str:
        """
        Salva un MatchAnalysisResult nel log.
        Ritorna l'ID della previsione.
        """
        pid = str(uuid.uuid4())[:8]

        adj = result.adjusted_probs
        ss = result.sixth_sense

        entry = {
            "id":          pid,
            "created_at":  result.analyzed_at,
            "home":        result.home,
            "away":        result.away,
            "match_date":  result.match_date,
            "base_probs":  result.base_probs,
            "adjusted_probs": adj.to_dict(),
            "goal_markets":   result.goal_markets,
            "market_odds":    result.market_odds,
            "value_signals":  result.value_signals,
            "sixth_sense_status":     ss.status,
            "sixth_sense_confidence": ss.overall_confidence,
            "sixth_sense_summary":    ss.summary,
            # Da compilare dopo la partita
            "result":      None,   # 'H' | 'D' | 'A'
            "home_goals":  None,
            "away_goals":  None,
            "settled_at":  None,
        }

        data = self._load()
        data["predictions"].append(entry)
        self._save(data)

        return pid

    # ------------------------------------------------------------------
    # Aggiunge risultato reale
    # ------------------------------------------------------------------

    def add_result(
        self,
        prediction_id: str,
        result: str,           # 'H' | 'D' | 'A'
        home_goals: Optional[int] = None,
        away_goals: Optional[int] = None,
    ) -> bool:
        """
        Aggiunge il risultato reale a una previsione esistente.

        result: 'H' (casa vince) | 'D' (pareggio) | 'A' (ospite vince)
        Ritorna True se trovata e aggiornata.
        """
        result = result.upper()
        if result not in ("H", "D", "A"):
            raise ValueError("result deve essere 'H', 'D' o 'A'")

        data = self._load()
        for entry in data["predictions"]:
            if entry["id"] == prediction_id:
                entry["result"]     = result
                entry["home_goals"] = home_goals
                entry["away_goals"] = away_goals
                entry["settled_at"] = datetime.now(timezone.utc).isoformat()
                self._save(data)
                return True

        return False

    # ------------------------------------------------------------------
    # Lista previsioni
    # ------------------------------------------------------------------

    def pending(self) -> list[dict]:
        """Previsioni senza risultato."""
        data = self._load()
        return [p for p in data["predictions"] if p["result"] is None]

    def settled(self) -> list[dict]:
        """Previsioni con risultato."""
        data = self._load()
        return [p for p in data["predictions"] if p["result"] is not None]

    def all(self) -> list[dict]:
        return self._load()["predictions"]

    # ------------------------------------------------------------------
    # Statistiche di performance
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """
        Calcola metriche di performance sulle previsioni con risultato.

        Ritorna:
          total:        numero previsioni valutate
          accuracy:     % previsioni corrette (esito più probabile)
          brier_score:  Brier score (più basso = meglio, <0.22 buono)
          roi_value_bets: ROI simulato se si puntasse 1 unità su ogni value bet
          value_bet_accuracy: % value bet vinte
          calibration:  tabella probabilità previste vs frequenza reale
        """
        records = self.settled()

        if not records:
            return {"total": 0, "message": "Nessuna previsione con risultato."}

        total = len(records)
        correct = 0
        brier_sum = 0.0

        # Value bet tracking
        vb_profit = 0.0
        vb_bets = 0
        vb_wins = 0

        for rec in records:
            adj = rec.get("adjusted_probs", {})
            ph = adj.get("home_win", 0.33)
            pd_ = adj.get("draw", 0.33)
            pa = adj.get("away_win", 0.34)
            actual = rec["result"]

            # Accuracy
            pred = max(("H", ph), ("D", pd_), ("A", pa), key=lambda x: x[1])[0]
            if pred == actual:
                correct += 1

            # Brier score
            ah = 1 if actual == "H" else 0
            ad = 1 if actual == "D" else 0
            aa = 1 if actual == "A" else 0
            brier_sum += (ph - ah) ** 2 + (pd_ - ad) ** 2 + (pa - aa) ** 2

            # Value bets
            for vs in rec.get("value_signals", []):
                market = vs["market"]
                odd    = vs.get("market_odd", 0)

                won = False
                if market == "home_win"  and actual == "H": won = True
                elif market == "draw"    and actual == "D": won = True
                elif market == "away_win" and actual == "A": won = True
                # mercati gol (solo se abbiamo i gol)
                elif rec.get("home_goals") is not None:
                    hg = rec["home_goals"]
                    ag = rec["away_goals"]
                    total_goals = hg + ag
                    btts = hg > 0 and ag > 0
                    if market == "over_2_5"  and total_goals > 2: won = True
                    elif market == "under_2_5" and total_goals <= 2: won = True
                    elif market == "over_1_5"  and total_goals > 1: won = True
                    elif market == "under_1_5" and total_goals <= 1: won = True
                    elif market == "over_3_5"  and total_goals > 3: won = True
                    elif market == "under_3_5" and total_goals <= 3: won = True
                    elif market == "btts_yes" and btts: won = True
                    elif market == "btts_no"  and not btts: won = True

                vb_bets += 1
                if won:
                    vb_profit += odd - 1
                    vb_wins += 1
                else:
                    vb_profit -= 1

        return {
            "total":          total,
            "accuracy":       round(correct / total, 3),
            "brier_score":    round(brier_sum / (total * 3), 4),
            "value_bets_placed":   vb_bets,
            "value_bets_won":      vb_wins,
            "value_bet_accuracy":  round(vb_wins / vb_bets, 3) if vb_bets > 0 else None,
            "roi_value_bets":      round(vb_profit / vb_bets, 3) if vb_bets > 0 else None,
        }
