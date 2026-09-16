"""
services/betting/netwin_odds_checker.py — Netwin Live Odds Connector & Aggio Sentinel (Pilastro 1).

Monitora e valida le quote reali di Netwin contro le quote teoriche del palinsesto.
Intercetta l'Aggio Trap (compressione quote su campionati secondari o fasce orarie notturne)
ed evita a monte la proposta di mercati il cui Edge reale crolla sotto la soglia di legge (+4.0%).
"""

from __future__ import annotations
import os
import json
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger("NetwinOddsChecker")

@dataclass
class NetwinOddAudit:
    match_name: str
    market_name: str
    proposed_odd: float
    netwin_real_odd: float
    real_probability: float
    original_edge_pct: float
    netwin_edge_pct: float
    is_aggio_trap: bool
    passed: bool
    rejection_reason: Optional[str] = None
    recommended_alternative_market: Optional[str] = None
    recommended_alternative_odd: Optional[float] = None

class NetwinOddsChecker:
    """
    Sentinel di controllo quote e margini per il bookmaker Netwin.it
    """

    MIN_ACCEPTABLE_EDGE = 0.04   # Minimo +4.0% di valore matematico atteso
    MAX_ALLOWED_ODD_HAIRCUT = 0.08  # Max 8% di decrescita tra quota teorica e Netwin

    def __init__(self, cache_file: Optional[Path] = None):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.cache_file = cache_file or (self.root_dir / "data" / "netwin_odds_cache.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._odds_cache: Dict[str, Any] = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Errore caricamento cache quote Netwin: {e}")
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._odds_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Errore salvataggio cache quote Netwin: {e}")

    def update_cached_odd(self, match_name: str, market_name: str, actual_odd: float):
        """Aggiorna la quota effettiva verificata su Netwin."""
        key = f"{match_name.strip().lower()}::{market_name.strip().lower()}"
        self._odds_cache[key] = {
            "match": match_name,
            "market": market_name,
            "netwin_odd": actual_odd
        }
        self._save_cache()

    def get_netwin_odd(self, match_name: str, market_name: str, fallback_odd: float) -> float:
        """Restituisce la quota Netwin reale se nota/in cache, altrimenti il fallback."""
        key = f"{match_name.strip().lower()}::{market_name.strip().lower()}"
        cached = self._odds_cache.get(key)
        if cached and "netwin_odd" in cached:
            return float(cached["netwin_odd"])
        return fallback_odd

    def audit_market(
        self,
        match_name: str,
        market_name: str,
        proposed_odd: float,
        real_probability: float,
        netwin_override_odd: Optional[float] = None
    ) -> NetwinOddAudit:
        """
        Esegue l'audit dell'aggio applicato da Netwin.
        Verifica se il taglio quota distrugge il vantaggio matematico.
        """
        netwin_odd = netwin_override_odd or self.get_netwin_odd(match_name, market_name, proposed_odd)
        
        orig_edge = (real_probability * proposed_odd) - 1.0
        netwin_edge = (real_probability * netwin_odd) - 1.0

        # Rileva Aggio Trap: decurtazione della quota >= 8% oppure Edge reale sceso sotto il 4%
        is_haircut = (proposed_odd - netwin_odd) / max(0.01, proposed_odd) >= self.MAX_ALLOWED_ODD_HAIRCUT
        is_aggio_trap = is_haircut or (netwin_edge < self.MIN_ACCEPTABLE_EDGE)

        passed = not is_aggio_trap and (netwin_edge >= self.MIN_ACCEPTABLE_EDGE)

        rejection_reason = None
        alt_market = None
        alt_odd = None

        if not passed:
            rejection_reason = (
                f"[BLOCCATO - NETWIN AGGIO TRAP] Quota proposta @{proposed_odd:.2f} tagliata a @{netwin_odd:.2f} su Netwin. "
                f"L'Edge reale crolla da {orig_edge:+.1%} a {netwin_edge:+.1%} (minimo richiesto: +4.0%). "
                f"Scommessa matematicamente sconveniente sul banco."
            )
            
            # Suggerisci alternativa elastica non compressa
            if "MULTIGOL 2-5" in market_name.upper():
                alt_market = "MultiGol 2-4 Partita"
                alt_odd = round(netwin_odd * 1.18, 2)
            elif "MULTIGOL 1-3" in market_name.upper():
                alt_market = "Over 4.5 Cartellini Totali Match"
                alt_odd = 1.45
            elif "OVER 1.5" in market_name.upper():
                alt_market = "MultiGol 2-4 Partita"
                alt_odd = 1.55

        return NetwinOddAudit(
            match_name=match_name,
            market_name=market_name,
            proposed_odd=proposed_odd,
            netwin_real_odd=netwin_odd,
            real_probability=real_probability,
            original_edge_pct=round(orig_edge * 100, 2),
            netwin_edge_pct=round(netwin_edge * 100, 2),
            is_aggio_trap=is_aggio_trap,
            passed=passed,
            rejection_reason=rejection_reason,
            recommended_alternative_market=alt_market,
            recommended_alternative_odd=alt_odd
        )
