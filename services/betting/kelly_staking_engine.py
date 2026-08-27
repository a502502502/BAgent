"""
BAgent - Kelly Staking Engine (Fractional Kelly Criterion)
Modulo per il calcolo scientifico e dinamico dello stake (importo in €)
per scommesse singole, multiple e sistemi.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class StakeRecommendation:
    bankroll: float
    odds: float
    estimated_prob: float
    edge_pct: float
    full_kelly_pct: float
    fractional_kelly_pct: float
    recommended_stake: float
    min_stake: float
    max_stake: float
    expected_growth_rate: float
    verdict: str
    risk_level: str

class KellyStakingEngine:
    """
    Motore quantitativo basato sul Criterio di Kelly Frazionario.
    Fornisce la dimensione ottimale della puntata massimizzando la crescita geometrica
    del capitale ed eliminando il rischio di rovina (Risk of Ruin = 0).
    """

    DEFAULT_FRACTION = 0.25      # Quarter-Kelly (1/4): Standard aureo del quant betting
    CONSERVATIVE_FRACTION = 0.15 # 15% Kelly per mercati ad alta volatilità
    AGGRESSIVE_FRACTION = 0.40   # 40% Kelly per selezioni a bassissima varianza (es. Over 1.5 / DC)
    
    HARD_CAP_SINGLE_TICKET_PCT = 0.08  # Max 8% del bankroll su singolo ticket
    HARD_CAP_DAILY_TOTAL_PCT = 0.25    # Max 25% del bankroll impegnato contemporaneamente
    MINIMUM_STAKE_EUR = 2.00           # Limite minimo di puntata bookmaker (Netwin / ADM)

    def __init__(self, current_bankroll: float = 116.45):
        self.bankroll = max(current_bankroll, 1.0)

    def set_bankroll(self, new_bankroll: float):
        self.bankroll = max(new_bankroll, 1.0)

    def calculate_stake(
        self,
        odds: float,
        estimated_prob: float,
        market_type: str = "general",
        custom_fraction: Optional[float] = None
    ) -> StakeRecommendation:
        """
        Calcola lo stake ideale per un evento o multipla.
        
        Parametri:
        - odds: Quota decimale (es. 2.25)
        - estimated_prob: Probabilità stimata dal modello Poisson / Sesto Senso (0.0 - 1.0)
        - market_type: Tipologia di mercato per calibrazione della frazione
        """
        if odds <= 1.0:
            raise ValueError("Le quote devono essere maggiori di 1.00")
        
        # Edge = (prob * odds) - 1
        edge = (estimated_prob * odds) - 1.0
        edge_pct = edge * 100.0

        b = odds - 1.0 # Quote nette
        p = max(min(estimated_prob, 1.0), 0.0)
        q = 1.0 - p

        # Formula di Kelly Standard: f* = (b*p - q) / b = (p * odds - 1) / (odds - 1)
        if b <= 0 or edge <= 0:
            full_kelly = 0.0
        else:
            full_kelly = (b * p - q) / b

        # Selezione frazione di Kelly in base alla varianza del mercato
        if custom_fraction is not None:
            fraction = custom_fraction
        elif market_type in ["corner_totali", "doppia_chance_gol", "multigol"]:
            fraction = self.AGGRESSIVE_FRACTION # Varianza bassa
        elif market_type in ["falli_giocatore", "player_props", "cartellini"]:
            fraction = self.CONSERVATIVE_FRACTION # Varianza alta dei singoli
        else:
            fraction = self.DEFAULT_FRACTION # 25% Kelly standard

        fractional_kelly_pct = full_kelly * fraction
        
        # Applicazione Hard Cap di sicurezza (Max 8% bankroll)
        capped_pct = min(fractional_kelly_pct, self.HARD_CAP_SINGLE_TICKET_PCT)
        
        raw_stake = self.bankroll * capped_pct
        
        # Arrotondamento ai 50 centesimi / euro più vicino per usabilità
        if raw_stake < self.MINIMUM_STAKE_EUR and edge > 0:
            # Se c'è edge positivo ma lo stake è sotto 2€, impostiamo il minimo sindacale
            recommended_stake = self.MINIMUM_STAKE_EUR if self.bankroll >= 20.0 else 1.00
        else:
            recommended_stake = round(raw_stake * 2) / 2 # Arrotondato a 0.50€

        # Calcolo tasso di crescita geometrico atteso g = p * ln(1 + f*b) + q * ln(1 - f)
        import math
        f = capped_pct
        if f > 0 and (1 + f * b) > 0 and (1 - f) > 0:
            expected_growth = p * math.log(1 + f * b) + q * math.log(1 - f)
        else:
            expected_growth = 0.0

        # Verdetto
        if edge_pct <= 0:
            verdict = "❌ NO BET (Edge negativo o nullo, il bookmaker ha il vantaggio)"
            risk_level = "ELEVATO"
            recommended_stake = 0.00
        elif edge_pct < 5.0:
            verdict = "👀 MICRO VALUE (Edge positivo < 5%, stake ridotto)"
            risk_level = "MEDIO"
        elif edge_pct < 15.0:
            verdict = "⭐ HIGH VALUE (Edge solido tra 5% e 15%, stake ottimale)"
            risk_level = "OTTIMALE"
        else:
            verdict = "💎 MEGA VALUE (Edge eccezionale > 15%, massima efficienza)"
            risk_level = "ALTA CONVINZIONE"

        return StakeRecommendation(
            bankroll=self.bankroll,
            odds=odds,
            estimated_prob=estimated_prob,
            edge_pct=round(edge_pct, 2),
            full_kelly_pct=round(full_kelly * 100, 2),
            fractional_kelly_pct=round(fractional_kelly_pct * 100, 2),
            recommended_stake=recommended_stake,
            min_stake=self.MINIMUM_STAKE_EUR,
            max_stake=round(self.bankroll * self.HARD_CAP_SINGLE_TICKET_PCT, 2),
            expected_growth_rate=round(expected_growth * 100, 4),
            verdict=verdict,
            risk_level=risk_level
        )

    def allocate_daily_tickets(self, tickets: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Alloca il budget tra più ticket contemporanei garantendo che
        la somma degli stake non superi il limite giornaliero (25% Bankroll).
        """
        results = []
        total_allocated = 0.0
        max_daily_budget = self.bankroll * self.HARD_CAP_DAILY_TOTAL_PCT

        for t in tickets:
            rec = self.calculate_stake(
                odds=t["odds"],
                estimated_prob=t["prob"],
                market_type=t.get("market_type", "general"),
                custom_fraction=t.get("fraction")
            )
            t_res = dict(t)
            t_res["recommendation"] = rec
            t_res["calculated_stake"] = rec.recommended_stake
            total_allocated += rec.recommended_stake
            results.append(t_res)

        # Se il totale supera il tetto giornaliero, normalizziamo proporzionalmente
        if total_allocated > max_daily_budget and total_allocated > 0:
            scale = max_daily_budget / total_allocated
            for r in results:
                scaled_stake = round((r["calculated_stake"] * scale) * 2) / 2
                r["calculated_stake"] = max(scaled_stake, self.MINIMUM_STAKE_EUR)

        return results
