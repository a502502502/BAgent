#!/usr/bin/env python3
"""
services/live/siege_engine.py
Protocollo Assedio Live & Trigger Asimmetrico (Regola #50).

Rileva in tempo reale quando una squadra sfavorita ("piccola") passa in vantaggio
su una favorita ("grande") e attiva istantaneamente il paniere di mercati asimmetrici:
1. Corner Boom Favorita (proiezione 1.2 - 1.5 corner ogni 10 min di assedio);
2. Cartellini Ostruzionismo Piccola (perdite di tempo, falli tattici);
3. Volume Balistico Tiri Favorita (tiri continui da fuori area e ribattuti);
4. Doppia Chance di Rimonta Live (1X / X2 a quota gonfiata con Edge > 15-25%).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple


@dataclass
class SiegeOpportunity:
    match_name: str
    minute: int
    favorite_name: str
    underdog_name: str
    favorite_is_home: bool
    current_score: str
    pre_match_fav_odd: float
    projected_additional_corners_fav: float
    recommended_corner_line: str
    projected_additional_cards_underdog: float
    recommended_card_line: str
    projected_additional_shots_fav: float
    recommended_shot_line: str
    recommended_comeback_market: str
    estimated_comeback_odd: float
    estimated_comeback_edge: float
    rationale: str
    telegram_alert_html: str = ""


class LiveSiegeEngine:
    """
    Motore analitico per l'attivazione dei mercati di assedio in-play.
    """

    # Parametri quantitativi vincolanti
    MAX_PRE_MATCH_FAV_ODD = 1.60       # La favorita deve avere una quota pre-gara <= 1.60
    MIN_MINUTE = 12                     # Troppo presto prima del 12'
    MAX_MINUTE = 78                     # Oltre il 78' il tempo utile di assedio scema

    # Coefficienti balistici medi per minuto di assedio
    CORNER_RATE_PER_MIN = 0.135        # ~1.35 corner ogni 10 minuti di assedio
    SHOT_RATE_PER_MIN = 0.28           # ~2.8 tiri ogni 10 minuti di assedio
    CARD_RATE_PER_MIN_LATE = 0.045     # ~1 cartellino ogni 22 minuti per la piccola

    def __init__(self):
        pass

    def evaluate_in_play(
        self,
        match_name: str,
        minute: int,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        pre_match_odd_home: float,
        pre_match_odd_away: float,
        current_corners_home: int = 0,
        current_corners_away: int = 0,
        current_cards_home: int = 0,
        current_cards_away: int = 0,
        current_shots_home: int = 0,
        current_shots_away: int = 0
    ) -> Optional[SiegeOpportunity]:
        """
        Valuta se la partita si trova in stato di 'Assedio Asimmetrico'.
        Ritorna un oggetto SiegeOpportunity con le raccomandazioni operative se il trigger scatta.
        """
        if minute < self.MIN_MINUTE or minute > self.MAX_MINUTE:
            return None

        # 1. Identifica la favorita pre-match
        is_home_fav = pre_match_odd_home <= self.MAX_PRE_MATCH_FAV_ODD and pre_match_odd_home < pre_match_odd_away
        is_away_fav = pre_match_odd_away <= self.MAX_PRE_MATCH_FAV_ODD and pre_match_odd_away < pre_match_odd_home

        if not is_home_fav and not is_away_fav:
            return None

        # 2. Verifica se la sfavorita è in vantaggio
        underdog_is_leading = False
        fav_name = ""
        und_name = ""
        fav_is_home = False
        fav_odd = 0.0
        cur_fav_corners = 0
        cur_und_cards = 0
        cur_fav_shots = 0

        if is_home_fav and away_score > home_score:
            underdog_is_leading = True
            fav_name = home_team
            und_name = away_team
            fav_is_home = True
            fav_odd = pre_match_odd_home
            cur_fav_corners = current_corners_home
            cur_und_cards = current_cards_away
            cur_fav_shots = current_shots_home
        elif is_away_fav and home_score > away_score:
            underdog_is_leading = True
            fav_name = away_team
            und_name = home_team
            fav_is_home = False
            fav_odd = pre_match_odd_away
            cur_fav_corners = current_corners_away
            cur_und_cards = current_cards_home
            cur_fav_shots = current_shots_away

        if not underdog_is_leading:
            return None

        # 3. Calcolo proiezioni balistiche sui minuti rimanenti
        rem_minutes = max(10, 90 - minute)

        # Proiezione Corner Favorita
        add_corners = rem_minutes * self.CORNER_RATE_PER_MIN
        tot_proj_corners = cur_fav_corners + add_corners
        rec_corner_line = f"Over {math.floor(tot_proj_corners - 0.5) + 0.5} Corner {fav_name} Live"

        # Proiezione Cartellini Piccola
        # Se siamo nel 2° tempo (dopo il 45'), il tasso di cartellini sale per time-wasting
        card_rate = self.CARD_RATE_PER_MIN_LATE if minute >= 45 else (self.CARD_RATE_PER_MIN_LATE * 0.75)
        add_cards = rem_minutes * card_rate
        tot_proj_cards = cur_und_cards + add_cards
        rec_card_line = f"Over {max(1.5, math.floor(tot_proj_cards - 0.5) + 0.5)} Cartellini {und_name} Live"

        # Proiezione Tiri
        add_shots = rem_minutes * self.SHOT_RATE_PER_MIN
        tot_proj_shots = cur_fav_shots + add_shots
        rec_shot_line = f"Over {math.floor(tot_proj_shots - 1.5) + 0.5} Tiri Totali {fav_name} Live"

        # Stima Valore Doppia Chance Rimonta Live
        # Probabilità decrescente col passare dei minuti, ma quota di mercato sale più rapidamente
        base_p = 0.80 if fav_is_home else 0.74
        time_factor = rem_minutes / 75.0  # da 1.0 (min 15) a ~0.16 (min 78)
        p_comeback = round(max(0.48, min(0.85, base_p * (0.60 + 0.40 * time_factor))), 2)
        comeback_market = f"1X Live ({fav_name})" if fav_is_home else f"X2 Live ({fav_name})"
        
        # Quota tipica live con svantaggio: dai 1.35-1.55 del primo tempo ai 1.80-2.35 della ripresa
        est_live_odd = round(1.28 + (1.0 - min(1.0, time_factor)) * 0.95, 2)
        edge_comeback = (p_comeback * est_live_odd) - 1.0

        score_str = f"{home_score} - {away_score}"

        rationale = (
            f"La sfavorita '{und_name}' è in vantaggio per {score_str} al {minute}'. "
            f"La favorita '{fav_name}' (quota pre @{fav_odd:.2f}) è costretta all'assedio totale nella trequarti avversaria per i restanti {rem_minutes} minuti. "
            f"La difesa a blocco basso di '{und_name}' genererà deviazioni continue sul fondo (+{add_corners:.1f} corner attesi), "
            f"falli tattici/ostruzionismo (+{add_cards:.1f} cartellini attesi) e raffiche di tiri (+{add_shots:.1f} conclusioni)."
        )

        # Formattazione HTML per Telegram
        tg_html = (
            f"🚨 <b>ALLERTA ASSEDIO LIVE: PICCOLA IN VANTAGGIO SULLA BIG!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏟️ <b>{match_name}</b> ({minute}')\n"
            f"⚡ Punteggio Live: <b>{und_name} {score_str} {fav_name}</b>\n"
            f"👑 Favorita in Svantaggio: <b>{fav_name}</b> (Pre-Match: @{fav_odd:.2f})\n\n"
            f"🎯 <b>MERCATI ASIMMETRICI ATTIVATI (Regola #50):</b>\n"
            f"• 🚩 <b>CORNER BOOM</b>: <code>{rec_corner_line}</code>\n"
            f"   └ <i>Attesi +{add_corners:.1f} corner della big nei restanti {rem_minutes}'</i>\n"
            f"• 🟨 <b>CARTELLINI OSTRUZIONISMO</b>: <code>{rec_card_line}</code>\n"
            f"   └ <i>Piccola costretta a falli tattici e perdite di tempo</i>\n"
            f"• 🎯 <b>VOLUME BALISTICO</b>: <code>{rec_shot_line}</code>\n"
            f"• 🔄 <b>VALUE RIMONTA</b>: <code>{comeback_market} @ ~{est_live_odd:.2f}</code> (Edge stimato: {edge_comeback*100:+.1f}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>Mercati disponibili subito su Netwin / Live In-Play!</i>"
        )

        return SiegeOpportunity(
            match_name=match_name,
            minute=minute,
            favorite_name=fav_name,
            underdog_name=und_name,
            favorite_is_home=fav_is_home,
            current_score=score_str,
            pre_match_fav_odd=fav_odd,
            projected_additional_corners_fav=round(add_corners, 1),
            recommended_corner_line=rec_corner_line,
            projected_additional_cards_underdog=round(add_cards, 1),
            recommended_card_line=rec_card_line,
            projected_additional_shots_fav=round(add_shots, 1),
            recommended_shot_line=rec_shot_line,
            recommended_comeback_market=comeback_market,
            estimated_comeback_odd=est_live_odd,
            estimated_comeback_edge=round(edge_comeback, 3),
            rationale=rationale,
            telegram_alert_html=tg_html
        )
