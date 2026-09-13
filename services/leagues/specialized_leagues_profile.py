#!/usr/bin/env python3
"""
services/leagues/specialized_leagues_profile.py
Specializzazione nei 4 Circuiti Satellite di BAgent (Regola #52):
1. Brasile (Brasileirao Serie A - bra.1)
2. Argentina (Liga Profesional - arg.1)
3. Olanda (Eredivisie - ned.1)
4. Norvegia (Eliteserien - nor.1)

Modella il DNA statistico, balistico e tattico di ciascuna lega,
indirizzando automaticamente la scelta dei mercati ottimali e bloccando
le giocate contro-natura (es. Over Cartellini in Norvegia o Under 2.5 in Olanda).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class LeagueProfile:
    name: str
    country: str
    code: str  # bra.1, arg.1, ned.1, nor.1
    tactical_archetype: str
    avg_goals: float
    over_25_pct: float
    btts_pct: float
    avg_fouls: float
    avg_cards: float
    avg_corners: float
    home_advantage_bias: float  # Moltiplicatore fattore campo (1.0 = standard, 1.25 = altissimo)
    optimal_markets: List[str]
    prohibited_markets: List[str]
    betting_directives: str
    key_powerhouses: List[str]


LEAGUE_PROFILES: Dict[str, LeagueProfile] = {
    "bra.1": LeagueProfile(
        name="Brasileirão Serie A",
        country="Brasile",
        code="bra.1",
        tactical_archetype="Fortino Casalingo, Usura da Trasferta & Fisicità Sudamericana",
        avg_goals=2.42,
        over_25_pct=46.5,
        btts_pct=48.0,
        avg_fouls=28.5,
        avg_cards=5.1,
        avg_corners=9.8,
        home_advantage_bias=1.28,  # Fattore campo mostruoso per viaggi continentali
        optimal_markets=[
            "1X + MultiGol 1-5",
            "1X + Under 3.5",
            "1 Fisso Big in Casa",
            "MultiGol 1-3 Casa",
            "Over Cartellini 2° Tempo (tempo effettivo basso)"
        ],
        prohibited_markets=[
            "2 Fisso Ospite a quota compressa (< 1.85)",
            "Over 3.5 Totali indiscriminati",
            "MultiGol con tetto a 2 su big lanciate"
        ],
        betting_directives=(
            "In Brasile il fattore campo al Maracanã, Allianz Parque o Morumbi è sovrano. "
            "Le trasferte di 3000+ km spossano le squadre ospiti. "
            "Privilegiare sempre mercati protetti sulla favorita casalinga (1X + Under 3.5 o MultiGol 1-5). "
            "Evitare 2 fissi esterni a meno di quote espansive con edge certo."
        ),
        key_powerhouses=["Flamengo", "Palmeiras", "Botafogo", "Atlético-MG", "São Paulo", "Internacional"]
    ),

    "arg.1": LeagueProfile(
        name="Liga Profesional Argentina",
        country="Argentina",
        code="arg.1",
        tactical_archetype="Guerra Tattica, Catenaccio Intenso & Bassa Conversione Realizzativa",
        avg_goals=2.05,
        over_25_pct=38.2,
        btts_pct=41.0,
        avg_fouls=30.8,
        avg_cards=5.8,
        avg_corners=8.6,
        home_advantage_bias=1.22,
        optimal_markets=[
            "Under 2.5 Partita",
            "Under 3.5 Partita",
            "Over 4.5 / Over 5.5 Cartellini Totali",
            "1X + Under 3.5",
            "X2 + Under 3.5",
            "MultiGol 1-3 Partita"
        ],
        prohibited_markets=[
            "Over 2.5 a quota compressa",
            "Goal / BTTS (Entrambe segnano) sistematico",
            "Handicap asiatici larghi (-1.5 / -2.5)"
        ],
        betting_directives=(
            "In Argentina il calcio è bloccato, aggressivo e molto falloso. "
            "Oltre il 60% dei match finisce Under 2.5. Gli arbitri hanno il cartellino facilissimo. "
            "Regno indiscusso per Over Cartellini e mercati Under combinati a Doppia Chance."
        ),
        key_powerhouses=["River Plate", "Boca Juniors", "Racing Club", "Independiente", "Estudiantes", "San Lorenzo"]
    ),

    "ned.1": LeagueProfile(
        name="Eredivisie",
        country="Olanda",
        code="ned.1",
        tactical_archetype="Total Football, Verticalità Offensiva & Heavy Right-Tail",
        avg_goals=3.28,
        over_25_pct=68.5,
        btts_pct=62.0,
        avg_fouls=21.2,
        avg_cards=3.4,
        avg_corners=11.2,
        home_advantage_bias=1.10,
        optimal_markets=[
            "1/2 + Over 1.5",
            "1/2 + Over 2.5",
            "Over 1.5 / Over 2.5 Gol Squadra Big (PSV, Feyenoord, Ajax)",
            "MultiGol 2-5 Partita",
            "Over 9.5 / Over 10.5 Corner Totali",
            "1X2 Corner Dominante"
        ],
        prohibited_markets=[
            "MultiGol 1-3 su PSV o Feyenoord (Regola #48 Anti-Ceiling: rischio 4-0, 5-1)",
            "Under 2.5 Partita a quote basse",
            "No Gol sulle sfide di vertice"
        ],
        betting_directives=(
            "In Olanda le difese lasciano praterie e gli attacchi non si fermano mai sull'1-0. "
            "Mercati aperti verso l'alto (Uncapped: 2+Over 1.5, MultiGol 2-5). "
            "Volume balistico di tiri elevatissimo: ideale per mercati sui Corner."
        ),
        key_powerhouses=["PSV Eindhoven", "Feyenoord", "Ajax", "AZ Alkmaar", "FC Twente", "FC Utrecht"]
    ),

    "nor.1": LeagueProfile(
        name="Eliteserien",
        country="Norvegia",
        code="nor.1",
        tactical_archetype="Erba Sintetica Rapida, Ritmi Alti & Arbitraggio Pulito (Fair Play)",
        avg_goals=3.04,
        over_25_pct=64.0,
        btts_pct=59.5,
        avg_fouls=19.4,
        avg_cards=2.9,
        avg_corners=11.6,
        home_advantage_bias=1.18,
        optimal_markets=[
            "Over 2.5 Gol Partita",
            "Gol / BTTS (Entrambe le Squadre Segnano)",
            "1X2 Corner Bodø/Glimt o Brann (Volume > 19 tiri)",
            "Over 1.5 Gol Squadra Ospite/Casa Big",
            "MultiGol 2-5 Partita"
        ],
        prohibited_markets=[
            "Over Cartellini (Partite pulitissime, metro all'inglese: grave errore!)",
            "Under 1.5 Partita",
            "MultiGol a tetto basso (1-2 o 1-3 su Bodø/Glimt)"
        ],
        betting_directives=(
            "La Norvegia vive sul sintetico: la palla viaggia al doppio della velocità, "
            "generando decine di tiri dal limite e corner a valanga. "
            "Il fair play scandinavo e gli arbitri permissivi azzerano i cartellini: "
            "MAI giocare Over Cartellini in Eliteserien. Giocare Over gol e Corner!"
        ),
        key_powerhouses=["FK Bodø/Glimt", "SK Brann", "Molde FK", "Rosenborg BK", "Viking FK", "Tromsø IL"]
    )
}


class SpecializedLeagueEngine:
    """
    Motore analitico per l'applicazione delle direttive specifiche per i 4 campionati.
    """

    @staticmethod
    def resolve_code(query: str) -> Optional[str]:
        q = query.lower()
        if "bra" in q or "brasil" in q:
            return "bra.1"
        if "arg" in q:
            return "arg.1"
        if "ned" in q or "oland" in q or "eredivisie" in q:
            return "ned.1"
        if "nor" in q or "eliteserien" in q or "norve" in q:
            return "nor.1"
        return None

    @classmethod
    def get_profile(cls, query: str) -> Optional[LeagueProfile]:
        code = cls.resolve_code(query)
        return LEAGUE_PROFILES.get(code) if code else None

    @classmethod
    def audit_market_for_league(cls, league_query: str, market_name: str) -> Tuple[bool, str]:
        profile = cls.get_profile(league_query)
        if not profile:
            return True, "Lega standard non soggetta a profilo satellite."

        m_upper = market_name.upper()

        # Audit Norvegia: Cartellini vietati!
        if profile.code == "nor.1":
            if "CARTELLIN" in m_upper or "CARD" in m_upper:
                return False, (
                    f"[BLOCCO REGOLA #52 - SPECIALIZZAZIONE NORVEGIA] Rifiutato mercato cartellini '{market_name}'. "
                    f"In Eliteserien la media sanzioni è di appena 2.9 a match (arbitraggio all'inglese e fair play). "
                    f"I cartellini sono vietati in Norvegia: optare per Over Gol o Corner!"
                )

        # Audit Olanda: Divieto Under o tetti bassi su Big
        if profile.code == "ned.1":
            if "UNDER 2.5" in m_upper or "UN 2.5" in m_upper:
                return False, (
                    f"[BLOCCO REGOLA #52 - SPECIALIZZAZIONE OLANDA] Rifiutato Under 2.5 in Eredivisie. "
                    f"Media gol di 3.28 a match e Over 2.5 al 68.5%. Optare per mercati Over o MultiGol 2-5."
                )

        # Audit Argentina: Divieto Over compressi
        if profile.code == "arg.1":
            if "OVER 2.5" in m_upper and "UNDER" not in m_upper and "1X" not in m_upper:
                return False, (
                    f"[AVVISO REGOLA #52 - SPECIALIZZAZIONE ARGENTINA] Attenzione su Over 2.5 in Argentina (Under 2.5 al 62%). "
                    f"Consigliato privilegiare Under 2.5/3.5 o Over Cartellini!"
                )

        return True, f"Mercato coerente con il DNA tattico di {profile.name}."
