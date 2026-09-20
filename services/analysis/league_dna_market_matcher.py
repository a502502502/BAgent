#!/usr/bin/env python3
"""
services/analysis/league_dna_market_matcher.py
League & Team Tactical DNA Profiler & Market Matching Engine (Regola #71).

Determina, certifica e audita i mercati ottimali e più sicuri (P >= 88-96%) in base al "DNA Tattico"
del campionato e delle squadre in campo:

1. DEFENSIVE_ATTRITION (Argentina, Brasile, Colombia, Uruguay, Serie B):
   - Profilo: Ritmo spezzettato da falli, xG basso (<= 2.15), baricentri bassi, 0-0 frequente (18%+).
   - Semaforo Verde: ASIAN_UNDER (3.0, 3.25), UNDER 3.5 / 4.5, GG_BOTH_HALVES_NO, DNB / AH 0.0.
   - Semaforo Rosso (VIETATI): OVER 0.5 (trappola mortale dello 0-0!), OVER CORNER ALTI (> 7.5), OVER 2.5.

2. OPEN_BALLISTIC_TRANSITION (MLS, Bundesliga, Eredivisie, Scandinavia, Austria):
   - Profilo: Campi larghi, difese alte e allegre, transizioni rapide coast-to-coast, xG alto (>= 3.0).
   - Semaforo Verde: OVER CORNER TOTALI (6.5, 7.5), CHANCE MIX (X2 o Over 1.5), DRAW NO BET (DNB), OVER 1.5 GOL.
   - Semaforo Rosso (VIETATI): UNDER STRETTI (Under 2.5 / 3.0), NO GOL, 1X2 SECCO IN TRASFERTA.

3. ASYMMETRIC_DOMINANCE (City, Barca, Real, Sporting CP, Bayern, PSG vs blocco basso):
   - Profilo: 65%+ possesso territoriale, 18-22 tiri verso lo specchio, assedio prolungato.
   - Semaforo Verde: CORNER SQUADRA (Over 3.5 / 4.5), CHANCE MIX (1X o Over 1.5), PARATE PORTIERE SFAVORITA (Over 2.5/3.5), FUORIGIOCO SFAVORITA (Flick trap).
   - Semaforo Rosso (VIETATI): 1X2 SECCO A QUOTA COMPRESSA (< 1.65), OVER 1°T A 45', TETTO BASSO A 3 GOL (Anti-Ceiling).

4. PRAGMATIC_MANAGEMENT / CORTO MUSO (Napoli con Allegri, Atletico Madrid con Simeone, Huracán, Corinthians):
   - Profilo: Gestione del minimo scarto, abbassamento del baricentro dopo l'1-0, clean sheet prioritario.
   - Semaforo Verde: 1X + MULTIGOL 1-5, UNDER 3.5, DNB, MULTIGOL 1-3 SQUADRA.
   - Semaforo Rosso (VIETATI): COMBO RIGIDE CON OVER 1.5 (es. 1X + Over 1.5, 1 + Over 1.5), OVER 2.5.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class MarketSuitabilityResult:
    market_name: str
    is_recommended: bool
    is_prohibited: bool
    suitability_score: float         # 0.0 - 100.0
    status: str                      # "GREEN" (Ottimale), "YELLOW" (Neutro/Accettabile), "RED" (VIETATO)
    tactical_rationale: str
    league_cluster: str
    team_archetype: str
    rejection_reason: Optional[str] = None
    recommended_alternatives: List[str] = field(default_factory=list)


@dataclass
class DNAMarketRecommendation:
    league_name: str
    home_team: str
    away_team: str
    league_cluster: str              # "DEFENSIVE_ATTRITION", "OPEN_BALLISTIC", "TACTICAL_HYBRID"
    match_archetype: str             # "ASYMMETRIC_DOMINANCE", "PRAGMATIC_MANAGEMENT", "OPEN_BALLISTIC", "DEFENSIVE_ATTRITION", "BALANCED_COMPETITIVE"
    cluster_description: str
    league_stats: Dict[str, Any]
    recommended_archetypes: List[Dict[str, Any]]
    prohibited_archetypes: List[Dict[str, Any]]
    key_insights: List[str]


class LeagueDNAMarketMatcher:
    """
    Motore analitico per abbinare scientificamente i mercati alle caratteristiche
    statistiche e tattiche di ciascun campionato e delle squadre.
    """

    # 1. Database Campionati per Cluster
    LEAGUE_PROFILES = {
        "DEFENSIVE_ATTRITION": {
            "keywords": [
                "argentina", "liga profesional", "primera division argentina", "copa de la liga",
                "brasile", "serie a brasiliana", "brasileirao", "serie b brasiliana",
                "colombia", "primera a colombia", "uruguay", "paraguay", "venezuela",
                "serie b", "serie b italia", "ligue 2"
            ],
            "description": "Campionato a logoramento difensivo, ritmi spezzettati da falli, baricentri bassi e 0-0 frequente.",
            "stats": {
                "avg_goals": 2.10,
                "avg_corners": 8.5,
                "avg_cards": 5.5,
                "zero_zero_rate_pct": 18.2,
                "under_25_pct": 61.5,
                "under_35_pct": 88.0,
            }
        },
        "OPEN_BALLISTIC": {
            "keywords": [
                "mls", "major league soccer", "stati uniti", "usa mls",
                "bundesliga", "germania", "2. bundesliga", "2.bundesliga",
                "eredivisie", "olanda", "eerste divisie",
                "allsvenskan", "svezia", "eliteserien", "norvegia",
                "austria", "bundesliga austriaca", "svizzera", "super league svizzera"
            ],
            "description": "Campionato aperto con campo largo, difese alte e allegre, transizioni rapide e altissima produzione balistica.",
            "stats": {
                "avg_goals": 3.18,
                "avg_corners": 10.8,
                "avg_cards": 3.8,
                "zero_zero_rate_pct": 6.0,
                "under_25_pct": 41.0,
                "over_15_pct": 84.5,
            }
        },
        "TACTICAL_HYBRID": {
            "keywords": [
                "serie a", "italia", "premier league", "inghilterra",
                "laliga", "la liga", "spagna", "liga portugal", "portogallo",
                "ligue 1", "francia"
            ],
            "description": "Campionato d'élite europeo con forte asimmetria tra top club e squadre di medio-bassa classifica.",
            "stats": {
                "avg_goals": 2.65,
                "avg_corners": 9.8,
                "avg_cards": 4.5,
                "zero_zero_rate_pct": 8.5,
                "under_25_pct": 51.0,
                "under_35_pct": 77.5,
            }
        }
    }

    # 2. Database Squadre per Archetipo Tattico
    DOMINANT_ATTACKING_CLUBS = {
        "manchester city", "barcelona", "barcellona", "real madrid",
        "bayern munich", "bayern monaco", "sporting cp", "sporting lisbona",
        "inter", "milan", "villarreal", "paris saint germain", "psg", "arsenal", "liverpool",
        "flamengo", "palmeiras", "river plate", "boca juniors"
    }

    HIGH_WING_CORNER_CLUBS = {
        "sporting cp", "sporting lisbona", "manchester city", "bayern munich",
        "bayern monaco", "liverpool", "psg", "lafc", "columbus crew", "inter"
    }

    OFFSIDE_TRAP_CLUBS = {
        "barcelona", "barcellona", "aston villa", "tottenham"
    }

    PRAGMATIC_LOW_PACE_CLUBS = {
        "napoli", "atletico madrid", "juventus", "huracan", "huracán",
        "corinthians", "gremio", "grêmio", "getafe", "mallorca"
    }

    LEAKY_DEFENSE_CLUBS = {
        "san jose", "san jose earthquakes", "southampton", "werder bremen", "werder brema",
        "heerenveen", "st. louis", "chicago fire", "monza"
    }

    def __init__(self):
        pass

    def identify_league_cluster(self, league: str) -> Tuple[str, Dict[str, Any]]:
        """Identifica il cluster statistico del campionato."""
        l_norm = league.lower().strip()
        for cluster, data in self.LEAGUE_PROFILES.items():
            for kw in data["keywords"]:
                if kw in l_norm:
                    return cluster, data
        return "TACTICAL_HYBRID", self.LEAGUE_PROFILES["TACTICAL_HYBRID"]

    def identify_team_archetype(self, home: str, away: str) -> str:
        """Determina l'archetipo tattico dominante dell'incontro."""
        h_norm = home.lower().strip()
        a_norm = away.lower().strip()

        # Verifica Pragmatismo / Corto Muso
        is_pragmatic = any(c in h_norm or c in a_norm for c in self.PRAGMATIC_LOW_PACE_CLUBS)
        # Verifica Dominanza Asimmetrica
        is_dominant = any(c in h_norm or c in a_norm for c in self.DOMINANT_ATTACKING_CLUBS)

        if is_dominant:
            return "ASYMMETRIC_DOMINANCE"
        if is_pragmatic:
            return "PRAGMATIC_MANAGEMENT"
        return "STANDARD"

    def get_market_recommendations(
        self,
        league: str,
        home_team: str,
        away_team: str
    ) -> DNAMarketRecommendation:
        """
        Genera la matrice completa di mercati consigliati e vietati per il match
        in base alla combinazione di Campionato + Squadre.
        """
        league_cluster, league_data = self.identify_league_cluster(league)
        team_archetype = self.identify_team_archetype(home_team, away_team)
        h_norm = home_team.lower().strip()
        a_norm = away_team.lower().strip()

        # Determina il match archetype finale
        if team_archetype == "ASYMMETRIC_DOMINANCE":
            match_archetype = "ASYMMETRIC_DOMINANCE"
        elif team_archetype == "PRAGMATIC_MANAGEMENT":
            match_archetype = "PRAGMATIC_MANAGEMENT"
        elif league_cluster == "OPEN_BALLISTIC":
            match_archetype = "OPEN_BALLISTIC"
        elif league_cluster == "DEFENSIVE_ATTRITION":
            match_archetype = "DEFENSIVE_ATTRITION"
        else:
            match_archetype = "BALANCED_COMPETITIVE"

        recommended = []
        prohibited = []
        insights = []

        # -------------------------------------------------------------
        # 1. CASO MLS & CAMPIONATI APERTI BALISTICI
        # -------------------------------------------------------------
        if match_archetype == "OPEN_BALLISTIC" or league_cluster == "OPEN_BALLISTIC":
            recommended.extend([
                {
                    "name": "Over 6.5 / Over 7.5 Corner Totali Incontro",
                    "category": "CORNER_OVER",
                    "priority": "MASSIMA",
                    "why": (
                        f"In {league} il gioco sulle fasce, i campi ampi e i ribaltamenti continui producono "
                        f"in media {league_data['stats'].get('avg_corners', 10.8):.1f} corner per gara. "
                        f"La soglia 6.5 ha una probabilità reale > 91% (bastano 7 corner in due squadre!)."
                    )
                },
                {
                    "name": "Chance Mix: X2 o Over 1.5 (o 1X o Over 1.5)",
                    "category": "CHANCE_MIX",
                    "priority": "MASSIMA",
                    "why": "Disgiunzione logica ad altissima resilienza (P >= 94-96%): incassa se la favorita non perde OPPURE se ci sono 2 gol."
                },
                {
                    "name": "Draw No Bet (DNB / AH 0.0) su Favorita Esterna",
                    "category": "DNB",
                    "priority": "ALTA",
                    "why": "In MLS le trasferte sono lunghe e i pareggi spettacolari frequenti (2-2): il DNB rimborsa il pareggio a quote eccellenti (@1.55-1.68)."
                },
                {
                    "name": "Over 1.5 Gol Totali Partita",
                    "category": "GOALS_OVER",
                    "priority": "ALTA",
                    "why": f"Oltre l'84% dei match in {league} produce 2 o più reti. Lo 0-0 si registra in appena il 6% dei casi."
                },
                {
                    "name": "MultiGol 2-5 Partita",
                    "category": "MULTIGOL",
                    "priority": "ALTA",
                    "why": "Copre i risultati tipici ad alto punteggio (2-0, 2-1, 3-1, 2-2, 3-2) proteggendo da crolli offensivi."
                }
            ])

            prohibited.extend([
                {
                    "name": "Corner Squadra Ospite Monosquadra (Over 2.5 / 3.5 Corner Ospite)",
                    "risk": "Regola #72: In MLS i padroni di casa spingono furiosamente sulle fasce (San Jose ha battuto 16 corner da sola!). La squadra ospite, pur favorita, rischia di essere schiacciata e fermarsi a 2-3 corner (LAFC a 3). Usare SOLO Corner Totali Partita!"
                },
                {
                    "name": "Under Stretti (Under 2.5 / Under 3.0)",
                    "risk": f"Incompatibile col DNA di {league}! Le difese concedono spazi larghi e l'xG medio è di {league_data['stats'].get('avg_goals', 3.18):.2f}. Alto rischio di 2-2 o 3-1."
                },
                {
                    "name": "1X2 Secco in Trasferta a Quota Compressa (< 1.65)",
                    "risk": "Fattore campo marcato per i viaggi aerei transcontinentali in MLS. I pareggi con gol sono frequentissimi."
                },
                {
                    "name": "No Gol (BTTS No)",
                    "risk": "Entrambe le difese concedono regolarmente occasioni da gol (BTTS frequente oltre il 60%)."
                }
            ])

            insights.append("I mercati sui CORNER (Over 6.5/7.5) rappresentano il benchmark matematico più sicuro in MLS.")
            insights.append("Sulle favorite in trasferta usare SEMPRE il Draw No Bet (DNB) o la Chance Mix (X2 o Over 1.5).")

        # -------------------------------------------------------------
        # 2. CASO ARGENTINA & SUDAMERICA (DEFENSIVE_ATTRITION)
        # -------------------------------------------------------------
        elif match_archetype == "DEFENSIVE_ATTRITION" or league_cluster == "DEFENSIVE_ATTRITION":
            recommended.extend([
                {
                    "name": "Under 3.0 Asiatico (o Under 3.25)",
                    "category": "ASIAN_UNDER",
                    "priority": "MASSIMA",
                    "why": (
                        "Il mercato perfetto per l'Argentina: incassa con 0, 1 o 2 gol; con esattamente 3 gol scatta il "
                        "RIMBORSO TOTALE del 100% (Push @ 1.00). P(No Loss) = 88.31%."
                    )
                },
                {
                    "name": "Under 3.5 Gol Totali",
                    "category": "GOALS_UNDER",
                    "priority": "MASSIMA",
                    "why": f"In {league} l'88.0% delle partite termina con meno di 4 reti. Media gol registrata di soli {league_data['stats'].get('avg_goals', 2.05):.2f}."
                },
                {
                    "name": "GG in Entrambi i Tempi: NO",
                    "category": "TEMPI_NO",
                    "priority": "MASSIMA",
                    "why": "Vedere entrambe le squadre segnare sia nel 1° che nel 2° tempo capita in meno dell'1.5% delle gare sudamericane."
                },
                {
                    "name": "Draw No Bet (DNB / AH 0.0)",
                    "category": "DNB",
                    "priority": "ALTA",
                    "why": "Data l'altissima incidenza di pareggi tattici (0-0, 1-1), il DNB neutralizza il rischio pareggio rimborsando il capitale."
                },
                {
                    "name": "Over 4.5 / Over 5.5 Cartellini Totali",
                    "category": "CARDS_OVER",
                    "priority": "ALTA",
                    "why": f"Intensità fisica e continue interruzioni: media di {league_data['stats'].get('avg_cards', 5.5):.1f} cartellini a gara."
                }
            ])

            prohibited.extend([
                {
                    "name": "Over 0.5 Gol Totali",
                    "risk": (
                        "TRAPPOLA MORTALE DELLO 0-0! In Argentina e Sudamerica lo 0-0 si registra in oltre il 18% delle sfide. "
                        "Scommettere su Over 0.5 a quota 1.05-1.10 ha un Edge matematico devastante (-15%) che distrugge il bankroll."
                    )
                },
                {
                    "name": "Over Corner Alti (> 7.5 / 8.5 Totali)",
                    "risk": (
                        f"In {league} la media corner scende a {league_data['stats'].get('avg_corners', 8.5):.1f}. "
                        "I continui falli a centrocampo spezzano le manovre offensive prima che la palla arrivi sul fondo."
                    )
                },
                {
                    "name": "Over 2.5 Gol Totali",
                    "risk": f"Oltre il 61.5% delle partite finisce Under 2.5. Giocare Over 2.5 va contro il DNA della lega."
                }
            ])

            insights.append("In Argentina MAI scommettere su Over 0.5: l'Under 3.0 Asiatico offre una sicurezza matematica immensamente superiore.")
            insights.append("Evitare le linee alte di corner: il calcio sudamericano è spezzettato e poco balistico sui corner totali.")

        # -------------------------------------------------------------
        # 3. CASO DOMINANZA ASIMMETRICA (BIG CONTRO BLOCCO BASSO)
        # -------------------------------------------------------------
        elif match_archetype == "ASYMMETRIC_DOMINANCE":
            is_offside_trap = any(c in h_norm or c in a_norm for c in self.OFFSIDE_TRAP_CLUBS)
            is_wing_corner = any(c in h_norm or c in a_norm for c in self.HIGH_WING_CORNER_CLUBS)

            recommended.extend([
                {
                    "name": "Corner Squadra Favorita Over 3.5 / Over 4.5",
                    "category": "TEAM_CORNERS",
                    "priority": "MASSIMA",
                    "why": "La big produce 18-22 tiri con oltre il 65% di possesso palla. L'avversario chiuso devia continuamente sul fondo."
                },
                {
                    "name": "Chance Mix: 1X o Over 1.5",
                    "category": "CHANCE_MIX",
                    "priority": "MASSIMA",
                    "why": "Protegge la vittoria 1-0, il pareggio 1-1 e incassa anche sull'upset 1-2 per il verificarsi dell'Over 1.5. P > 97%."
                },
                {
                    "name": "Parate Portiere Sfavorita Over 2.5 / Over 3.5",
                    "category": "SAVES_OVER",
                    "priority": "ALTA",
                    "why": "Il portiere del blocco basso è sottoposto a 7-10 tiri nello specchio in 90 minuti di assedio."
                },
                {
                    "name": "MultiGol Asimmetrico Tempi (MG 0-2 1°T + 1-3 2°T)",
                    "category": "MULTIGOL_HALF",
                    "priority": "ALTA",
                    "why": "Assorbe l'avvio diesel (0-0 all'intervallo) e incassa nella ripresa quando le difese avversarie cedono fisicamente."
                }
            ])

            if is_offside_trap:
                recommended.insert(0, {
                    "name": "Over 1.5 / Over 2.5 Fuorigioco Squadra Sfavorita",
                    "category": "OFFSIDES",
                    "priority": "MASSIMA",
                    "why": "Linea difensiva a metà campo di Flick: gli attaccanti avversari finiscono in trappola 5-8 volte a partita!"
                })

            prohibited.extend([
                {
                    "name": "1 Fisso a Quota Compressa (< 1.65)",
                    "risk": "Gate 0: Esposizione mortale al gol isolato o al catenaccio perfetto al 90' (Lezione Athletic Bilbao, Udinese)."
                },
                {
                    "name": "Over 1° Tempo a Quota Compressa (< 1.50)",
                    "risk": "Fase di studio: l'avversario fresco resiste per i primi 45 minuti e la scommessa muore all'intervallo."
                },
                {
                    "name": "MultiGol 1-3 con Tetto Basso (Anti-Ceiling Trap)",
                    "risk": "Regola #48: Rischio concreto di goleada (4-0, 5-0) se la partita si stappa presto. Usare mercati aperti verso l'alto."
                }
            ])

            insights.append("Sulle big dominanti non giocare MAI l'1X2 secco sotto 1.65: le Chance Mix e i Corner Squadra hanno P > 95%.")
            insights.append("Sfruttare le parate del portiere avversario e i fuorigioco contro le difese alte.")

        # -------------------------------------------------------------
        # 4. CASO PRAGMATISMO / CORTO MUSO
        # -------------------------------------------------------------
        elif match_archetype == "PRAGMATIC_MANAGEMENT":
            recommended.extend([
                {
                    "name": "1X + MultiGol 1-5 (o X2 + MultiGol 1-5)",
                    "category": "COMBO_PROTECTED",
                    "priority": "MASSIMA",
                    "why": "Copre perfettamente la vittoria di misura per 1-0 o 2-0, il pareggio 1-1 e non muore mai su un risultato corto."
                },
                {
                    "name": "Under 3.5 Gol Totali",
                    "category": "GOALS_UNDER",
                    "priority": "MASSIMA",
                    "why": "Le squadre pragmatiche congelano il ritmo dopo il vantaggio, proteggendo il clean sheet."
                },
                {
                    "name": "Draw No Bet (DNB)",
                    "category": "DNB",
                    "priority": "ALTA",
                    "why": "Rimborsa l'alta incidenza di pareggi a reti bianche o con pochi gol."
                },
                {
                    "name": "MultiGol 1-3 Squadra",
                    "category": "TEAM_MULTIGOL",
                    "priority": "ALTA",
                    "why": "Assicura il gol singolo (1-0) o il raddoppio controllato senza dipendere da goleade."
                }
            ])

            prohibited.extend([
                {
                    "name": "Combo Rigide con Over 1.5 (es. 1X + Over 1.5, 1 + Over 1.5)",
                    "risk": "Regola #51 Filtro Corto Muso: la squadra abbassa i ritmi sull'1-0, portando la frequenza dell'1-0 oltre il 25%."
                },
                {
                    "name": "Over 2.5 Gol Totali",
                    "risk": "La squadra non spinge mai per la goleada una volta in controllo."
                }
            ])

            insights.append("Contro o con tecnici pragmatici (Allegri, Simeone) l'1-0 è il risultato più probabile: MAI imporre Over 1.5.")

        # -------------------------------------------------------------
        # 5. CASO EQUILIBRATO STANDARD
        # -------------------------------------------------------------
        else:
            recommended.extend([
                {
                    "name": "Doppia Chance + MultiGol (1X + MG 1-5 o X2 + MG 1-5)",
                    "category": "COMBO_PROTECTED",
                    "priority": "MASSIMA",
                    "why": "Copre tutti i risultati corti e i pareggi senza morire su una vittoria di misura."
                },
                {
                    "name": "Under 3.5 Gol Totali",
                    "category": "GOALS_UNDER",
                    "priority": "ALTA",
                    "why": "Gli scontri equilibrati tendono a bloccarsi tatticamente nella zona centrale del campo."
                },
                {
                    "name": "Draw No Bet (DNB)",
                    "category": "DNB",
                    "priority": "ALTA",
                    "why": "Protegge la favorita eliminando il rischio pareggio con rimborso integrale."
                }
            ])

            prohibited.append({
                "name": "1X2 Secco",
                "risk": "In scontri equilibrati con delta punti ridotto il pareggio ha probabilità > 30%."
            })

            insights.append("Negli scontri diretti equilibrati privilegiare mercati che assorbono l'1-1 e l'1-0.")

        desc = f"Match Archetype: [{match_archetype}] — Campionato: {league} ({league_cluster})"

        return DNAMarketRecommendation(
            league_name=league,
            home_team=home_team,
            away_team=away_team,
            league_cluster=league_cluster,
            match_archetype=match_archetype,
            cluster_description=desc,
            league_stats=league_data.get("stats", {}),
            recommended_archetypes=recommended,
            prohibited_archetypes=prohibited,
            key_insights=insights
        )

    def check_market_suitability(
        self,
        league: str,
        home_team: str,
        away_team: str,
        market_name: str,
        market_category: str = "",
        bookmaker_odd: float = 0.0
    ) -> MarketSuitabilityResult:
        """
        Esegue il check completo di compatibilità tra il mercato proposto
        e il DNA tattico di campionato e squadre.
        """
        recs = self.get_market_recommendations(league, home_team, away_team)
        m_norm = market_name.lower().strip()
        c_norm = market_category.lower().strip()

        alt_markets = [r["name"] for r in recs.recommended_archetypes[:3]]

        # -------------------------------------------------------------
        # 1. VERIFICA DIVIETI TASSATIVI (SEMAFORO ROSSO)
        # -------------------------------------------------------------
        # A) Over 0.5 in campionati a logoramento difensivo (Argentina, Brasile, ecc.)
        if recs.league_cluster == "DEFENSIVE_ATTRITION":
            is_over_05 = (
                "0.5" in m_norm and "over" in m_norm
            ) or m_norm in ["over 0.5", "over 0.5 gol", "più di 0.5", "+0.5 gol"]
            if is_over_05:
                return MarketSuitabilityResult(
                    market_name=market_name,
                    is_recommended=False,
                    is_prohibited=True,
                    suitability_score=0.0,
                    status="RED",
                    tactical_rationale=(
                        f"VIETATO TASSATIVAMENTE dal DNA di {recs.league_name}: lo 0-0 si registra in oltre il 18% "
                        f"dei casi. Over 0.5 a quota compressa ha un Edge distruttivo (-15%)."
                    ),
                    league_cluster=recs.league_cluster,
                    team_archetype=recs.match_archetype,
                    rejection_reason="Trappola mortale dello 0-0 in campionato a logoramento difensivo.",
                    recommended_alternatives=["Under 3.0 Asiatico", "Under 3.5 Gol Totali", "GG Entrambi Tempi: NO"]
                )

            # B) Over Corner troppo alti in campionati sudamericani (> 7.5)
            is_corner = "corner" in m_norm or "angoli" in m_norm or "corner" in c_norm
            is_high_corner_line = any(line in m_norm for line in ["7.5", "8.5", "9.5", "10.5"])
            if is_corner and is_high_corner_line and "over" in m_norm:
                return MarketSuitabilityResult(
                    market_name=market_name,
                    is_recommended=False,
                    is_prohibited=True,
                    suitability_score=15.0,
                    status="RED",
                    tactical_rationale=(
                        f"VIETATO dal DNA di {recs.league_name}: i continui falli a centrocampo spezzano le manovre. "
                        f"Media corner della lega è di soli {recs.league_stats.get('avg_corners', 8.5):.1f} corner/partita."
                    ),
                    league_cluster=recs.league_cluster,
                    team_archetype=recs.match_archetype,
                    rejection_reason="Linee Over Corner elevate incompatibili con campionato a bassa produzione balistica.",
                    recommended_alternatives=["Under 3.0 Asiatico", "Under 3.5 Gol Totali", "Over Cartellini Totali"]
                )

        # C) Under stretti in campionati aperti (MLS, Bundesliga, Eredivisie)
        if recs.league_cluster == "OPEN_BALLISTIC":
            is_tight_under = (
                ("under 2.5" in m_norm or "under 2" in m_norm or "under 3.0" in m_norm)
                and "under" in m_norm
            )
            if is_tight_under:
                return MarketSuitabilityResult(
                    market_name=market_name,
                    is_recommended=False,
                    is_prohibited=True,
                    suitability_score=10.0,
                    status="RED",
                    tactical_rationale=(
                        f"VIETATO dal DNA di {recs.league_name}: campionato aperto con media {recs.league_stats.get('avg_goals', 3.18):.2f} "
                        f"gol a partita e difese allegre. Gli Under stretti sono ad altissimo rischio."
                    ),
                    league_cluster=recs.league_cluster,
                    team_archetype=recs.match_archetype,
                    rejection_reason="Under stretto incompatibile con campionato ad alta produzione offensiva.",
                    recommended_alternatives=["Over 6.5 Corner Totali Incontro", "Chance Mix X2 o Over 1.5", "Over 1.5 Gol Totali"]
                )

        # D) 1 Fisso a quota compressa (< 1.65) su Big Dominanti (Gate 0)
        is_straight_win = (
            m_norm in ["1", "2", "1 fisso", "2 fisso", "esito finale 1", "esito finale 2"]
            or c_norm in ["1x2", "esito finale"]
        )
        if is_straight_win and bookmaker_odd > 0 and bookmaker_odd < 1.65:
            return MarketSuitabilityResult(
                market_name=market_name,
                is_recommended=False,
                is_prohibited=True,
                suitability_score=20.0,
                status="RED",
                tactical_rationale=(
                    f"VIETATO DA GATE 0 & DNA TATTICO: 1X2 secco @ {bookmaker_odd:.2f} non offre copertura sufficiente. "
                    f"Espone interamente al pareggio o al gol subito in contropiede."
                ),
                league_cluster=recs.league_cluster,
                team_archetype=recs.match_archetype,
                rejection_reason="1X2 secco a quota compressa senza copertura pareggio.",
                recommended_alternatives=["Chance Mix 1X o Over 1.5", "Corner Squadra Over 3.5", "Draw No Bet (DNB)"]
            )

        # E) Combo rigida con Over 1.5 su squadre Corto Muso (Regola #51)
        if recs.match_archetype == "PRAGMATIC_MANAGEMENT":
            is_rigid_over15 = "over 1.5" in m_norm and ("+" in m_norm or "1x" in m_norm or "1" in m_norm)
            if is_rigid_over15:
                return MarketSuitabilityResult(
                    market_name=market_name,
                    is_recommended=False,
                    is_prohibited=True,
                    suitability_score=15.0,
                    status="RED",
                    tactical_rationale=(
                        "VIETATO DA REGOLA #51: squadra a gestione pragmatica ('corto muso'). "
                        "Sull'1-0 la squadra congela il possesso e protegge il minimo scarto. L'1-0 si verifica nel 25%+ dei casi."
                    ),
                    league_cluster=recs.league_cluster,
                    team_archetype=recs.match_archetype,
                    rejection_reason="Filtro Corto Muso: divieto di imporre Over 1.5 escludendo l'1-0.",
                    recommended_alternatives=["1X + MultiGol 1-5", "Under 3.5 Gol Totali", "Draw No Bet (DNB)"]
                )

        # -------------------------------------------------------------
        # 2. VERIFICA MERCATI RACCOMANDATI (SEMAFORO VERDE)
        # -------------------------------------------------------------
        # A) Corner in MLS / campionati aperti
        if recs.league_cluster == "OPEN_BALLISTIC":
            if "corner" in m_norm or "angoli" in m_norm:
                if any(line in m_norm for line in ["5.5", "6.5", "7.5"]):
                    return MarketSuitabilityResult(
                        market_name=market_name,
                        is_recommended=True,
                        is_prohibited=False,
                        suitability_score=98.0,
                        status="GREEN",
                        tactical_rationale=(
                            f"PERFETTAMENTE ALLINEATO AL DNA DI {recs.league_name}: la media registrata è di "
                            f"{recs.league_stats.get('avg_corners', 10.8):.1f} corner per incontro. "
                            f"La linea {market_name} ha una probabilità reale > 90%."
                        ),
                        league_cluster=recs.league_cluster,
                        team_archetype=recs.match_archetype,
                        recommended_alternatives=alt_markets
                    )

        # B) Under Asiatico o Under 3.5 in Argentina / Sudamerica
        if recs.league_cluster == "DEFENSIVE_ATTRITION":
            if "under 3.0" in m_norm or "asiatico" in m_norm or "under 3.5" in m_norm or "entrambi i tempi: no" in m_norm:
                return MarketSuitabilityResult(
                    market_name=market_name,
                    is_recommended=True,
                    is_prohibited=False,
                    suitability_score=97.0,
                    status="GREEN",
                    tactical_rationale=(
                        f"PERFETTAMENTE ALLINEATO AL DNA DI {recs.league_name}: calcio a logoramento difensivo con "
                        f"media {recs.league_stats.get('avg_goals', 2.05):.2f} gol. Copre l'88%+ dei risultati reali."
                    ),
                    league_cluster=recs.league_cluster,
                    team_archetype=recs.match_archetype,
                    recommended_alternatives=alt_markets
                )

        # C) Chance Mix o Corner Squadra su Big Dominanti
        if recs.match_archetype == "ASYMMETRIC_DOMINANCE":
            if "chance mix" in m_norm or "1x o over 1.5" in m_norm or ("corner" in m_norm and any(l in m_norm for l in ["2.5", "3.5", "4.5"])):
                return MarketSuitabilityResult(
                    market_name=market_name,
                    is_recommended=True,
                    is_prohibited=False,
                    suitability_score=96.0,
                    status="GREEN",
                    tactical_rationale=(
                        "PERFETTAMENTE ALLINEATO AL DNA DI ASYMMETRIC DOMINANCE: volume offensivo di 18-22 tiri "
                        "e possesso palla > 65%. La difesa chiusa genera corner continui e la Chance Mix offre P > 96%."
                    ),
                    league_cluster=recs.league_cluster,
                    team_archetype=recs.match_archetype,
                    recommended_alternatives=alt_markets
                )

        # D) Draw No Bet (DNB / AH 0.0)
        if "dnb" in m_norm or "draw no bet" in m_norm or "ah 0.0" in m_norm or "asian handicap 0" in m_norm:
            return MarketSuitabilityResult(
                market_name=market_name,
                is_recommended=True,
                is_prohibited=False,
                suitability_score=92.0,
                status="GREEN",
                tactical_rationale=(
                    "MERCATO A RESILIENZA DNB: rimborsa integralmente il capitale in caso di pareggio, "
                    "eliminando il rischio X ad alta frequenza."
                ),
                league_cluster=recs.league_cluster,
                team_archetype=recs.match_archetype,
                recommended_alternatives=alt_markets
            )

        # E) Combo Protetta 1X/X2 + MultiGol 1-5
        if ("1x" in m_norm or "x2" in m_norm) and ("1-5" in m_norm or "multigol" in m_norm):
            return MarketSuitabilityResult(
                market_name=market_name,
                is_recommended=True,
                is_prohibited=False,
                suitability_score=95.0,
                status="GREEN",
                tactical_rationale=(
                    "COMBO ELASTICA PROTETTA: copre perfettamente 1-0, 2-0, 1-1, 2-1, 3-0 "
                    "senza morire su un risultato corto o sul pareggio tattico."
                ),
                league_cluster=recs.league_cluster,
                team_archetype=recs.match_archetype,
                recommended_alternatives=alt_markets
            )

        # F) Under 3.5 in contesti pragmatici o difensivi
        if "under 3.5" in m_norm and recs.match_archetype in ["PRAGMATIC_MANAGEMENT", "DEFENSIVE_ATTRITION", "BALANCED_COMPETITIVE"]:
            return MarketSuitabilityResult(
                market_name=market_name,
                is_recommended=True,
                is_prohibited=False,
                suitability_score=94.0,
                status="GREEN",
                tactical_rationale=(
                    f"UNDER STRUTTURALE PROTETTO: in contesto {recs.match_archetype}, la tendenza al controllo "
                    "e ai ritmi bassi rende 4 o più reti un evento a bassissima probabilità (< 12-16%)."
                ),
                league_cluster=recs.league_cluster,
                team_archetype=recs.match_archetype,
                recommended_alternatives=alt_markets
            )

        # G) Chance Mix generale (1X o Over 1.5, X2 o Over 1.5)
        if "chance mix" in m_norm or "o over 1.5" in m_norm:
            return MarketSuitabilityResult(
                market_name=market_name,
                is_recommended=True,
                is_prohibited=False,
                suitability_score=96.0,
                status="GREEN",
                tactical_rationale=(
                    "CHANCE MIX AD ALTA RESILIENZA: disgiunzione logica ad alta frequenza di cassa (P >= 94-97%). "
                    "Incassa sia con la tenuta della favorita, sia su qualsiasi partita con 2 o più reti."
                ),
                league_cluster=recs.league_cluster,
                team_archetype=recs.match_archetype,
                recommended_alternatives=alt_markets
            )

        # Se non è né raccomandato top né vietato: stato neutro/accettabile
        return MarketSuitabilityResult(
            market_name=market_name,
            is_recommended=False,
            is_prohibited=False,
            suitability_score=72.0,
            status="YELLOW",
            tactical_rationale=f"Mercato neutro/standard per il contesto {recs.match_archetype} ({recs.league_cluster}).",
            league_cluster=recs.league_cluster,
            team_archetype=recs.match_archetype,
            recommended_alternatives=alt_markets
        )
