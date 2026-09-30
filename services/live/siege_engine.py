from utils.logger import logger
from domain.models import MarketData

class SiegeEngine:
    """Regola #50: Protocollo Assedio Live & Trigger Asimmetrico."""
    
    def check_siege_trigger(self, home_team: str, away_team: str, pre_match_odds_home: float, current_score: tuple, minute: int) -> list[MarketData]:
        """
        Attiva l'allerta se la sfavorita (quota > 2.50 implicita o favorita < 1.60) passa in vantaggio.
        """
        is_underdog_leading = False
        leading_team = ""
        
        # Logica semplificata per demo: se la favorita aveva quota < 1.60 e ora sta perdendo
        if pre_match_odds_home < 1.60 and current_score[0] < current_score[1] and minute > 15:
            is_underdog_leading = True
            leading_team = away_team
        elif pre_match_odds_home > 2.50 and current_score[0] > current_score[1] and minute > 15:
            is_underdog_leading = True
            leading_team = home_team

        if not is_underdog_leading:
            return []

        logger.critical(f"🚨 ALLERTA ASSEDIO LIVE: {leading_team} in vantaggio sulla Big! Minuto: {minute}'")
        
        # Genera automaticamente le 4 selezioni asimmetriche
        opportunities = [
            MarketData(market_name=f"Over Corner {leading_team} (Assedio)", quota=1.65, probabilita_reale=0.75),
            MarketData(market_name=f"Cartellini Ostruzionismo {leading_team}", quota=1.80, probabilita_reale=0.65),
            MarketData(market_name=f"Value Bet Rimonta Live (1X/X2)", quota=1.90, probabilita_reale=0.60)
        ]
        
        for opp in opportunities:
            logger.success(f"💰 OPPORTUNITÀ GENERATA: {opp.market_name} @ {opp.quota} (Edge: {opp.edge:.2%})")
            
        return opportunities
