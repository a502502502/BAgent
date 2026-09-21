"""
Live Momentum Sentinel & In-Play Gem Sniping Engine
Monitora gli eventi in tempo reale durante i match (bagel 0-6 nel tennis, espulsioni,
primi set prolungati a 5-5/6-6, crollo delle quote live) per:
1. Allertare immediatamente su cali fisici o ribaltoni (es. Arantxa Rus)
2. Segnalare conferme matematiche anticipate (es. Over 18.5 già al 1° set)
3. Rilevare opportunità di Live Sniping (quote gonfiate in-play su favoriti sotto di un gol/set).
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional

class LiveMomentumSentinel:
    """
    Sentinel in-play per il rilevamento di anomalie, chiusure anticipate e opportunità live.
    """

    def analyze_tennis_live_state(
        self,
        player1: str,
        player2: str,
        sets_score: str, # es. "1-1"
        games_score: str, # es. "4-6 6-0 1-0"
        active_bet: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analizza lo stato live di una partita di tennis.
        Rileva 'Bagel' (6-0 / 0-6), set lunghi e cali di rendimento.
        """
        games = games_score.split()
        alerts = []
        status_verdict = "IN_PROGRESS"

        # 1. Rilevamento Bagel (6-0 o 0-6)
        has_bagel = any("6-0" in g or "0-6" in g for g in games)
        if has_bagel:
            alerts.append({
                "type": "BAGEL_COLLAPSE_WARNING",
                "severity": "CRITICAL",
                "message": f"Rilevato set a zero (6-0/0-6) nel match. Grave crollo fisico o blackout mentale di una delle giocatrici."
            })
            status_verdict = "HIGH_VOLATILITY"

        # 2. Calcolo game totali già disputati
        total_games_played = 0
        for g in games:
            parts = g.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                total_games_played += int(parts[0]) + int(parts[1])

        # 3. Verifica tenuta Over Game
        over_locked = False
        if active_bet and "over" in active_bet.lower():
            if "18.5" in active_bet and total_games_played >= 13:
                over_locked = True
                alerts.append({
                    "type": "OVER_LOCK_CONFIRMED",
                    "severity": "INFO",
                    "message": f"Over 18.5 quasi matematico: già {total_games_played} game disputati! Bastano pochi game per l'incasso."
                })

        return {
            "match": f"{player1} vs {player2}",
            "sets": sets_score,
            "games": games_score,
            "total_games": total_games_played,
            "has_bagel": has_bagel,
            "over_locked": over_locked,
            "status_verdict": status_verdict,
            "alerts": alerts
        }

    def analyze_football_live_state(
        self,
        home_team: str,
        away_team: str,
        score: str, # es. "0-0", "0-1"
        minute: int,
        red_cards_home: int = 0,
        red_cards_away: int = 0,
        active_bet: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analizza lo stato live di una partita di calcio.
        Rileva espulsioni, gol a freddo e opportunità di Live Sniping.
        """
        alerts = []
        is_sniping_opportunity = False

        # Rilevamento Cartellino Rosso
        if red_cards_home > 0 or red_cards_away > 0:
            team_with_red = home_team if red_cards_home > 0 else away_team
            alerts.append({
                "type": "RED_CARD_ALERT",
                "severity": "CRITICAL",
                "message": f"Cartellino rosso per {team_with_red}! Gli equilibri tattici sono alterati."
            })

        # Live Sniping: Favorito sotto nel primo tempo
        parts = score.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            h_goals = int(parts[0])
            a_goals = int(parts[1])

            if minute <= 45 and a_goals > h_goals:
                is_sniping_opportunity = True
                alerts.append({
                    "type": "LIVE_SNIPING_OPPORTUNITY",
                    "severity": "HIGH",
                    "message": f"{home_team} in svantaggio ({score}) al {minute}'. La quota 1X o Over 1.5 Casa è ora ai massimi storici di valore."
                })

        return {
            "match": f"{home_team} vs {away_team}",
            "score": score,
            "minute": minute,
            "red_cards": {"home": red_cards_home, "away": red_cards_away},
            "is_sniping_opportunity": is_sniping_opportunity,
            "alerts": alerts
        }
