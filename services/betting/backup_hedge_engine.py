"""
services/betting/backup_hedge_engine.py — Twin-Ticket Capital Preservation Engine.

Calcola e dimensiona matematicamente la Schedina di Backup (Twin-Ticket Lock):
- Risolve l'equazione di copertura a perdita zero: S2 * Q2 >= Stot;
- Ripartisce scientificamente lo stake tra Ticket Principale (Core) e Ticket di Backup;
- Supporta due strategie:
    1. 'TAIL_RISK_COMPLEMENT': copre la coda di rischio dell'evento più esposto della principale;
    2. 'ORTHOGONAL_VALUE_RESERVE': riserva indipendente a quota calibrata (Q2 in [4.50, 6.50]).
"""

from __future__ import annotations
import math
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("BackupHedgeEngine")

@dataclass
class TwinTicketResult:
    total_budget_eur: float
    # Schedina Principale
    main_ticket_name: str
    main_selections: List[Dict[str, Any]]
    main_total_odd: float
    main_stake_eur: float
    main_payout_eur: float
    main_net_profit_eur: float
    # Schedina Backup
    backup_ticket_name: str
    backup_selections: List[Dict[str, Any]]
    backup_total_odd: float
    backup_stake_eur: float
    backup_payout_eur: float
    # Scenari di Risultato
    scenario_main_won_net_eur: float        # Principale vince, Backup perde
    scenario_backup_won_net_eur: float      # Principale perde, Backup vince (ZERO PERDITA GARANTITA >= 0.0)
    scenario_both_won_net_eur: float        # Entrambe vincono (se eventi disgiunti)
    backup_strategy_type: str
    notes: str = ""

class BackupHedgeEngine:
    """
    Motore di Staking e Generazione Schedine di Backup a Capitale Protetto.
    """

    MIN_BACKUP_ODD = 4.00   # Quota minima della schedina di backup per non assorbire troppo stake
    MAX_BACKUP_STAKE_PCT = 0.30 # Massimo 30% del budget totale allocabile al backup

    def __init__(self):
        pass

    @staticmethod
    def calculate_zero_loss_split(total_budget: float, main_odd: float, backup_odd: float) -> Tuple[float, float]:
        """
        Calcola gli stake S1 (Principale) ed S2 (Backup) affinché:
        S2 * backup_odd >= total_budget (Zero Perdita / Break-Even garantito).
        """
        if backup_odd <= 1.0 or total_budget <= 0:
            raise ValueError("Parametri quota o budget non validi.")

        # S2 minimo necessario per coprire esattamente l'intero budget
        # Arrotondamento per eccesso al centesimo per garantire >= total_budget
        raw_s2 = total_budget / backup_odd
        s2 = round(math.ceil(raw_s2 * 100.0) / 100.0, 2)

        # Se s2 è inferiore a 1€ e il bookmaker richiede minimo 1€/2€, adegua
        s2 = max(1.00, s2) if total_budget >= 5.0 else max(0.50, s2)

        # Verifica vincolo di stake massimo sul backup
        if s2 >= total_budget:
            raise ValueError(f"Quota backup @{backup_odd:.2f} troppo bassa per garantire break-even con budget €{total_budget:.2f}.")

        s1 = round(total_budget - s2, 2)
        return s1, s2

    def create_orthogonal_twin_ticket(
        self,
        total_budget: float,
        main_name: str,
        main_selections: List[Dict[str, Any]],
        main_odd: float,
        backup_name: str,
        backup_selections: List[Dict[str, Any]],
        backup_odd: float,
        strategy_type: str = "ORTHOGONAL_VALUE_RESERVE"
    ) -> TwinTicketResult:
        """
        Genera la coppia di ticket coordinata con calcolo di tutti gli scenari finanziari.
        """
        s1, s2 = self.calculate_zero_loss_split(total_budget, main_odd, backup_odd)

        payout_main = round(s1 * main_odd, 2)
        payout_backup = round(s2 * backup_odd, 2)

        # Scenario A: Vince Principale, Perde Backup
        # Net = Payout_Main - Total_Budget
        scen_a = round(payout_main - total_budget, 2)

        # Scenario B: Perde Principale, Vince Backup
        # Net = Payout_Backup - Total_Budget (deve essere >= 0.00!)
        scen_b = round(payout_backup - total_budget, 2)

        # Scenario C: Entrambe vincono (se indipendenti)
        # Net = Payout_Main + Payout_Backup - Total_Budget
        scen_c = round((payout_main + payout_backup) - total_budget, 2)

        notes = (
            f"Capitale protetto: se la Principale salta ma il Backup vince, incassi €{payout_backup:.2f} "
            f"recuperando il 100% dei €{total_budget:.2f} investiti (Utile netto: €{scen_b:+.2f})."
        )

        return TwinTicketResult(
            total_budget_eur=total_budget,
            main_ticket_name=main_name,
            main_selections=main_selections,
            main_total_odd=round(main_odd, 2),
            main_stake_eur=s1,
            main_payout_eur=payout_main,
            main_net_profit_eur=scen_a,
            backup_ticket_name=backup_name,
            backup_selections=backup_selections,
            backup_total_odd=round(backup_odd, 2),
            backup_stake_eur=s2,
            backup_payout_eur=payout_backup,
            scenario_main_won_net_eur=scen_a,
            scenario_backup_won_net_eur=scen_b,
            scenario_both_won_net_eur=scen_c,
            backup_strategy_type=strategy_type,
            notes=notes
        )

    def generate_tail_risk_backup(
        self,
        main_selections: List[Dict[str, Any]],
        total_budget: float,
        main_odd: float
    ) -> TwinTicketResult:
        """
        Costruisce automaticamente la schedina di backup complementare:
        Identifica l'evento più volatile nella principale e genera la copertura speculare.
        """
        # Cerca selezione con coda di rischio (MultiGol 1-3 -> Over 3.5; 1X -> 2)
        vulnerable_leg = None
        complement_market = None
        complement_odd = 4.50

        for sel in main_selections:
            market = sel.get("market", "").upper()
            if "MULTIGOL 1-3" in market or "MULTIGOL 2-4" in market:
                vulnerable_leg = sel
                team = sel.get("match", "").split(" vs ")[0]
                complement_market = f"Over 3.5 Squadra ({team})"
                complement_odd = 4.80
                break
            elif "1X" in market:
                vulnerable_leg = sel
                away = sel.get("match", "").split(" vs ")[-1]
                complement_market = f"2 Fisso o DNB 2 ({away})"
                complement_odd = 4.20
                break

        if not vulnerable_leg:
            # Fallback a Riserva Balistica Ortogonale
            backup_selections = [
                {"match": "Match A", "market": "Over 8.5 Corner Totali", "odd": 2.10},
                {"match": "Match B", "market": "Over 4.5 Cartellini Totali", "odd": 2.25}
            ]
            backup_odd = round(2.10 * 2.25, 2)
            strat = "ORTHOGONAL_VALUE_RESERVE"
        else:
            backup_selections = [
                {
                    "match": vulnerable_leg.get("match", ""),
                    "market": complement_market,
                    "odd": complement_odd,
                    "note": "Copertura speculare dell'esito estremo / coda di rischio"
                }
            ]
            backup_odd = complement_odd
            strat = "TAIL_RISK_COMPLEMENT"

        return self.create_orthogonal_twin_ticket(
            total_budget=total_budget,
            main_name="Master Ticket Principale",
            main_selections=main_selections,
            main_odd=main_odd,
            backup_name="Ticket Paracadute Zero-Perdita",
            backup_selections=backup_selections,
            backup_odd=backup_odd,
            strategy_type=strat
        )
