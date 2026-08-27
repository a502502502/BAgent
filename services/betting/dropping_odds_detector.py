"""
BAgent - Dropping Odds & Closing Line Value (CLV) Engine
Modulo per il tracciamento in tempo reale delle variazioni di quota (Dropping Odds),
rilevamento dello Smart Money, Steam Moves e calcolo del Closing Line Value (CLV).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any

@dataclass
class OddsMovement:
    event_id: str
    match_name: str
    tournament: str
    market: str
    selection: str
    opening_odds: float
    current_odds: float
    closing_odds: Optional[float] = None
    drop_pct: float = 0.0
    clv_pct: Optional[float] = None
    bookmakers_count: int = 1
    is_smart_money: bool = False
    is_steam_move: bool = False
    signal_strength: str = "NEUTRAL"
    detected_at: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""

class DroppingOddsDetector:
    """
    Rileva crolli di quota anomali e calcola il Closing Line Value.
    
    Soglie di Rilevamento:
    - Drop >= 6%: Segnale Moderato (Attenzione)
    - Drop >= 10%: 🔥 Smart Money / Sharp Action (Forte Convinzione)
    - Drop >= 15%: 🚨 Steam Move / Notizia Bomba (Formazione / Infortunio Chiave)
    """

    SMART_MONEY_THRESHOLD = 10.0 # 10% di calo quota
    STEAM_MOVE_THRESHOLD = 15.0  # 15% di crollo improvviso
    MODERATE_DROP_THRESHOLD = 6.0

    def __init__(self):
        self.tracked_events: Dict[str, OddsMovement] = {}

    def calculate_drop(self, opening_odds: float, current_odds: float) -> float:
        """Calcola la percentuale di calo quota."""
        if opening_odds <= 1.0 or current_odds <= 1.0:
            return 0.0
        return ((opening_odds - current_odds) / opening_odds) * 100.0

    def calculate_clv(self, bet_odds: float, closing_odds: float) -> float:
        """
        Calcola il Closing Line Value (CLV).
        CLV % = (bet_odds / closing_odds - 1) * 100
        Se CLV > 0: La scommessa ha battuto la linea di chiusura del mercato (Value Bet a lungo termine).
        """
        if closing_odds <= 1.0 or bet_odds <= 1.0:
            return 0.0
        return ((bet_odds / closing_odds) - 1.0) * 100.0

    def analyze_movement(
        self,
        event_id: str,
        match_name: str,
        tournament: str,
        market: str,
        selection: str,
        opening_odds: float,
        current_odds: float,
        bookmakers_count: int = 1,
        closing_odds: Optional[float] = None
    ) -> OddsMovement:
        """
        Analizza il movimento di quota ed emette un verdetto quantitativo.
        """
        drop_pct = self.calculate_drop(opening_odds, current_odds)
        clv_pct = self.calculate_clv(current_odds, closing_odds) if closing_odds else None

        is_smart_money = drop_pct >= self.SMART_MONEY_THRESHOLD
        is_steam_move = drop_pct >= self.STEAM_MOVE_THRESHOLD and bookmakers_count >= 3

        if is_steam_move:
            signal = "🚨 STEAM MOVE (Crollo Massiccio Multi-Bookmaker: Notizia Improvvisa)"
            notes = "Il mercato internazionale sta riversando volumi eccezionali su questo esito. Scommettere subito prima dell'ulteriore crollo!"
        elif is_smart_money:
            signal = "🔥 SMART MONEY (Flusso Professionale Rilevato: Sharp Action)"
            notes = "Gli scommettitori istituzionali stanno comprando questa selezione. Elevata probabilità di chiusura a quota molto inferiore."
        elif drop_pct >= self.MODERATE_DROP_THRESHOLD:
            signal = "👀 MODERATE DROP (Leggero Favore del Mercato)"
            notes = "Trend di quota positivo ma non ancora determinante."
        elif drop_pct <= -5.0:
            signal = "⚠️ DRIFTING ODDS (Quota in Salita / Mercato Sfavorevole)"
            notes = "La quota sta salendo. Possibile calo di fiducia o notizie negative dell'ultima ora."
        else:
            signal = "⚖️ STABLE ODDS (Quota Stabile / Mercato Bilanciato)"
            notes = "Flussi regolari senza anomalie di volume."

        movement = OddsMovement(
            event_id=event_id,
            match_name=match_name,
            tournament=tournament,
            market=market,
            selection=selection,
            opening_odds=opening_odds,
            current_odds=current_odds,
            closing_odds=closing_odds,
            drop_pct=round(drop_pct, 2),
            clv_pct=round(clv_pct, 2) if clv_pct is not None else None,
            bookmakers_count=bookmakers_count,
            is_smart_money=is_smart_money,
            is_steam_move=is_steam_move,
            signal_strength=signal,
            notes=notes
        )

        key = f"{event_id}_{market}_{selection}"
        self.tracked_events[key] = movement
        return movement

    def format_telegram_alert(self, movement: OddsMovement) -> Optional[str]:
        """Formatta un alert Telegram immediato se il movimento è rilevante."""
        if not (movement.is_smart_money or movement.is_steam_move):
            return None

        icon = "🚨" if movement.is_steam_move else "🔥"
        msg = (
            f"{icon} *BAGENT MARKET ALERT: DROPPING ODDS DETECTED*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚽ *Partita:* {movement.match_name}\n"
            f"🏆 *Torneo:* {movement.tournament}\n"
            f"🎯 *Mercato:* {movement.market} ➔ `{movement.selection}`\n\n"
            f"📉 *Variazione Quota:*\n"
            f"• Quota Apertura: `{movement.opening_odds:.2f}`\n"
            f"• Quota Attuale: `{movement.current_odds:.2f}`\n"
            f"• Crollo (Drop): *{movement.drop_pct:.2f}%*\n"
            f"• Bookmaker Coinvolti: {movement.bookmakers_count}\n\n"
            f"🧠 *Segnale:* {movement.signal_strength}\n"
            f"💡 *Nota Operativa:* {movement.notes}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        return msg
