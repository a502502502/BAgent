#!/usr/bin/env python3
"""
services/betting/strict_ticket_pipeline.py
Pipeline Sequenziale Rigorosa & Calcolo Matematico Pre-Costruzione Schedine (Regole #37, #38, #39, #40, #41, #42, #43).

Nessun ticket o selezione può essere proposto se non supera TUTTI gli 8 Stadi in ordine sequenziale:
Fase 1: Verifica Roster 2026/27 (DB Locale + API Transfers — Anti-Allucinazione)
Fase 2: Verifica Infortuni & Squalifiche (API /injuries — Anti-Indisponibili)
Fase 3: Verifica Distinte Ufficiali Titolari (API /fixtures/lineups — Anti-Panchina)
Fase 4: Audit di Sesto Senso & Contesto Tattico (OBBLIGATORIO: rassegna stampa, motivazione, spogliatoio, trappole)
Fase 5: Calcolo Probabilità Reale Coniugata & Tempi (Poisson Bivariata ponderata da Sesto Senso)
Fase 6: Filtro Edge Matematico Reale (Edge = P_real * Quota - 1 >= +4.0%)
Fase 7: Filtro Strutturale di Mercato (Anti-Scadenza 45' a quota compressa < 1.55)
Fase 8: Staking Scientifico & Money Management (Kelly Frazionario: Max 5-8% cassa per ticket)
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

from services.analysis.xg_poisson_engine import QuantitativeEngine
from services.football.squad_absence_checker import SquadAbsenceChecker, PlayerAuditReport
from services.betting.kelly_staking_engine import KellyStakingEngine
from services.betting.netwin_odds_checker import NetwinOddsChecker

@dataclass
class MarketCandidate:
    match_name: str
    tournament: str
    market_name: str
    bookmaker_odd: float
    fixture_id: Optional[int] = None
    player_name: Optional[str] = None
    team_name: Optional[str] = None
    sixth_sense_analysis: str = ""        # Analisi tattica, rassegna stampa, motivazioni, clima spogliatoio
    sixth_sense_risk_flags: List[str] = field(default_factory=list) # es. "ROTATION_RISK", "SLOW_START", "LOW_MOTIVATION"
    estimated_p_1h: float = 0.50          # Probabilità evento nel 1°T (0.0 - 1.0)
    estimated_p_2h: float = 0.60          # Probabilità evento nel 2°T (0.0 - 1.0)
    estimated_p_90: Optional[float] = None # Ignorata dal gate: la P reale esce dal motore
    xg_home: Optional[float] = None
    xg_away: Optional[float] = None
    avg_corners_home: Optional[float] = None
    avg_corners_away: Optional[float] = None
    is_compound_time_market: bool = False  # Richiede evento in entrambi i tempi? (es. Segna Entrambi Tempi)
    is_intermediate_deadline: bool = False # Può morire al 45' cancellando il 2°T? (es. HT/FT, Gol Entrambi Tempi)
    market_type: str = ""                  # '1X2', 'CORNER', 'FIRST_HALF', 'GOALS', 'COMBO', 'CARDS'
    team_avg_shots: Optional[float] = None # Regola #45: media tiri totali squadra a partita
    team_avg_shots_on_target: Optional[float] = None # Regola #45: media tiri in porta
    has_upcoming_midweek_cup: bool = False # Rischio turnover/coppe europee infrasettimanali
    is_first_half_only: bool = False       # Mercato che si conclude al 45'
    verified_standings_delta: Optional[int] = None # Regola #55: Differenza punti reale tra le due squadre
    verified_sources_checked: bool = True  # Regola #55: Obbligo di consultazione diretta fonti reali
    verified_source_notes: str = ""        # Regola #55: Fonti reali consultate (FootyStats / Sofascore)
    netwin_actual_odd: Optional[float] = None # Pilastro 1: Quota reale rilevata su Netwin.it
    pre_match_odd_favorite: Optional[float] = None # Quota 1X2 pre-match della favorita
    is_parachute_market: bool = False      # Regola #66: Mercato inteso come paracadute/copertura difensiva
    kickoff_time: Optional[str] = None     # Data e ora del match (es. '2026-09-24 20:45 CEST')


@dataclass
class ValidationReport:
    passed: bool
    candidate: MarketCandidate
    stage_failed: Optional[int] = None
    rejection_reason: Optional[str] = None
    real_probability: float = 0.0
    fair_odds: float = 0.0
    mathematical_edge: float = 0.0
    details: str = ""
    sixth_sense_summary: str = ""


@dataclass
class TicketValidationReport:
    passed: bool
    num_selections: int
    total_odds: float
    recommended_stake: float
    stake_percentage: float
    legs_reports: List[ValidationReport]
    rejection_reasons: List[str]


class StrictTicketPipeline:
    """
    Pipeline di validazione a 8 stadi con Sesto Senso integrato obbligatorio.
    """

    MIN_EDGE_THRESHOLD = 0.04       # Minimo +4.0% di edge reale sul bookmaker
    MIN_LEG_PROBABILITY_THRESHOLD = 0.72 # Minimo 72.0% di probabilità per singola gamba di multipla
    MAX_SESSION_BANKROLL_PCT = 0.15 # Max 15% del capitale totale investito in una sessione
    MAX_TICKET_BANKROLL_PCT = 0.08  # Max 8% del capitale su singolo ticket

    def __init__(
        self,
        checker: Optional[SquadAbsenceChecker] = None,
        netwin_checker: Optional[NetwinOddsChecker] = None,
        engine: Optional[QuantitativeEngine] = None,
    ):
        self.checker = checker or SquadAbsenceChecker()
        self.netwin_checker = netwin_checker or NetwinOddsChecker()
        self.engine = engine or QuantitativeEngine()

    @staticmethod
    def calculate_poisson(lmbda: float, k: int) -> float:
        if lmbda <= 0:
            return 1.0 if k == 0 else 0.0
        return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

    def _probability_from_model(self, candidate: MarketCandidate) -> Optional[float]:
        """P reale dal Poisson gol o dalla binomiale negativa dei corner. Mai da estimated_p_90."""
        name = candidate.market_name.lower()
        if "corner" in name:
            if candidate.avg_corners_home is None or candidate.avg_corners_away is None:
                return None
            return self.engine.corner_market_probability(
                candidate.avg_corners_home,
                candidate.avg_corners_away,
                candidate.market_name,
            )
        if candidate.xg_home is None or candidate.xg_away is None:
            return None
        return self.engine.goal_market_probability(
            candidate.xg_home,
            candidate.xg_away,
            candidate.market_name,
        )

    def calculate_joint_probability(self, candidate: MarketCandidate) -> Tuple[Optional[float], float, str]:
        """
        Probabilità, fair odd ed edge dal motore quantitativo.
        Ritorna p=None se mancano xG/corner o se il mercato non è mappato.
        """
        p_full = self._probability_from_model(candidate)
        if p_full is None:
            return None, 0.0, (
                "Probabilità non calcolata: servono xg_home e xg_away "
                "(oppure medie corner per i mercati corner) e un mercato mappato sul motore."
            )

        fair_odd = 1.0 / max(0.001, p_full)
        implied_prob = 1.0 / candidate.bookmaker_odd
        edge = (p_full * candidate.bookmaker_odd) - 1.0
        report = (
            f"Motore Dixon-Coles: P(Reale)={p_full*100:.1f}% (Fair Odd: @{fair_odd:.2f}). "
            f"Quota bookmaker @{candidate.bookmaker_odd:.2f} richiede {implied_prob*100:.1f}%. "
            f"Edge Matematico: {edge*100:+.1f}%"
        )
        return p_full, edge, report

    def ticket_joint_probability(self, candidates: List[MarketCandidate]) -> Optional[float]:
        """
        Probabilità del ticket. Partite diverse si moltiplicano.
        Due mercati sulla stessa partita si intersecano sulla matrice dei punteggi:
        il prodotto delle marginali vale solo se gli eventi sono indipendenti.
        """
        if not candidates:
            return None
        groups: Dict[tuple, List[MarketCandidate]] = {}
        for candidate in candidates:
            if candidate.fixture_id is not None:
                key = ("fixture", candidate.fixture_id)
            else:
                key = ("name", " ".join(candidate.match_name.lower().split()))
            groups.setdefault(key, []).append(candidate)

        joint = 1.0
        for group in groups.values():
            if len(group) == 1:
                probability = self._probability_from_model(group[0])
                if probability is None:
                    return None
                joint *= probability
                continue
            if any("corner" in candidate.market_name.lower() for candidate in group):
                return None
            xg_pairs = {(candidate.xg_home, candidate.xg_away) for candidate in group}
            if len(xg_pairs) != 1:
                return None
            xg_home, xg_away = next(iter(xg_pairs))
            if xg_home is None or xg_away is None:
                return None
            probability = self.engine.joint_goal_probability(
                xg_home,
                xg_away,
                [candidate.market_name for candidate in group],
            )
            if probability is None:
                return None
            joint *= probability
        return joint

    def validate_candidate(self, candidate: MarketCandidate) -> ValidationReport:
        """
        Applica il funnel sequenziale degli Stadi Obbligatori con Hard Gates.
        """
        # =====================================================================
        # GATE 0.05: ANTI-TIME-TRAVEL & CONTROLLO VALIDITÀ TEMPORALE
        # =====================================================================
        # Rifiuta match con date passate (2024, 2025) o eventi già chiusi
        if candidate.kickoff_time:
            time_str = candidate.kickoff_time.strip().upper()
            if any(past in time_str for past in ["2024", "2025", "2023", "2022"]):
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=0,
                    rejection_reason=(
                        f"[BLOCCATO - GATE 0.05: DATA NON ATTUALE / PARTITA VECCHIA] {candidate.match_name} "
                        f"ha data '{candidate.kickoff_time}', relativa a una stagione passata. "
                        f"Tassativamente vietato scommettere su match archiviati o anacronistici!"
                    ),
                    details=f"Data evento '{candidate.kickoff_time}' antecedente alla stagione operativa corrente."
                )

        # =====================================================================
        # GATE 0: DIVIETO 1 O 2 FISSO E COMBO RIGIDE SOTTO QUOTA 1.65 (Protocollo Protezione & Anti-Varianza)
        # =====================================================================
        m_upper = candidate.market_name.strip().upper()
        # Rileva 1X2 secco o combo rigide che impongono la vittoria secca senza doppia chance (es. '1 + Over 1.5')
        is_straight_win_market = (
            candidate.market_type.upper() in ["1X2", "ESITO FINALE", "WINNER"]
            or m_upper in ["1", "2", "1 FISSO", "2 FISSO", "ESITO FINALE 1", "ESITO FINALE 2"]
            or m_upper.startswith("1 +") or m_upper.startswith("2 +")
            or m_upper.startswith("1+") or m_upper.startswith("2+")
            or " 1 + " in m_upper or " 2 + " in m_upper
        )
        # Se c'è una doppia chance (1X, X2, 12) o DNB, la selezione è protetta
        is_protected_dc = ("1X" in m_upper or "X2" in m_upper or "12" in m_upper or "DNB" in m_upper or "DRAW NO BET" in m_upper)
        
        if is_straight_win_market and not is_protected_dc and candidate.bookmaker_odd < 1.65:
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=0,
                rejection_reason=(
                    f"[BLOCCATO - PROTOCOLLO PROTEZIONE: DIVIETO 1/2 FISSO O COMBO RIGIDA SOTTO 1.65] {candidate.market_name} @ {candidate.bookmaker_odd:.2f} su {candidate.match_name}. "
                    f"È tassativamente vietato scommettere su 1 o 2 fisso o su combo non protette (es. '1 + Over 1.5') a quota inferiore a 1.65 "
                    f"per l'eccessiva esposizione a pareggi ed episodi casuali (es. Athletic Bilbao 1-1, America de Cali 1-1). "
                    f"Sostituire obbligatoriamente con opzioni protette: Doppia Chance (1X/X2), Combo '1X + MultiGol 1-4', DNB o MultiGol Squadra."
                ),
                details="Quota < 1.65 su segno 1 o 2 secco o combo rigida non offre margine sufficiente a coprire il rischio pareggio."
            )

        # =====================================================================
        # GATE 0.2: REGOLA #56 - BAN TOTALE SECONDE DIVISIONI, CAMPIONATI MINORI & SQUADRE RISERVE/B
        # =====================================================================
        # Divieto assoluto di Seconde Categorie (Serie B, Ligue 2, LaLiga 2, Eerste Divisie, ecc.)
        # e squadre riserve (Jong, II, 2, B, Castilla, Primavera, Next Pro, ecc.)
        text_to_check = f"{candidate.tournament or ''} {candidate.match_name or ''}".upper()
        
        banned_leagues_keywords = [
            "SERIE B", "LIGUE 2", "LALIGA 2", "LA LIGA 2", "2. BUNDESLIGA", "2.BUNDESLIGA",
            "CHAMPIONSHIP", "LEAGUE ONE", "LEAGUE TWO", "EERSTE DIVISIE", "PRIMERA NACIONAL",
            "PRIMERA B", "PRIMERA C", "PRIMERA D", "METROPOLITANA", "TORNEO FEDERAL", "SEGUNDA", "SECOND DIVISION", "MLS NEXT PRO", "ISTHMIAN", "SOUTHERN LEAGUE",
            "REGIONALLIGA", "SERIE C", "SERIE D", "AMATORI", "DILETTANTI", "NATIONAL LEAGUE"
        ]
        banned_reserve_keywords = [
            "JONG ", "JONG-", " II", " 2", " B ", "BARÇA ATLÈTIC", "BARCELONA ATLÈTIC", "BILBAO ATHLETIC",
            "BARCA ATLETIC", " CASTILLA", " U21", " U23", " U19", " PRIMAVERA", " RISERVE", " RESERVES"
        ]
        
        # Gestione eccezioni nomi legittimi contenenti 'II' (es. Willem II in Eredivisie)
        # e false positive " B " su "UEFA Nations League - League B" (coppa UEFA ammessa)
        text_for_reserves = text_to_check.replace("WILLEM II", "WILLEM_CLUB")
        for _nl_token in (
            "NATIONS LEAGUE - LEAGUE A",
            "NATIONS LEAGUE - LEAGUE B",
            "NATIONS LEAGUE - LEAGUE C",
            "NATIONS LEAGUE - LEAGUE D",
            "NATIONS LEAGUE LEAGUE A",
            "NATIONS LEAGUE LEAGUE B",
            "NATIONS LEAGUE LEAGUE C",
            "NATIONS LEAGUE LEAGUE D",
        ):
            text_for_reserves = text_for_reserves.replace(_nl_token, "NATIONS_LEAGUE_UEFA")
        
        is_banned_tier2 = any(kw in text_to_check for kw in banned_leagues_keywords)
        is_banned_reserve = any(kw in text_for_reserves for kw in banned_reserve_keywords)
        
        if is_banned_tier2 or is_banned_reserve:
            banned_reason_type = "SECONDA CATEGORIA / SERIE B" if is_banned_tier2 else "SQUADRA RISERVE / B TEAM"
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=0,
                rejection_reason=(
                    f"[BLOCCATO - REGOLA #56: BAN SECONDE DIVISIONI & SQUADRE B/RISERVE] "
                    f"Rilevato '{candidate.tournament}' / '{candidate.match_name}' ({banned_reason_type}). "
                    f"È tassativamente vietato scommettere su seconde divisioni, campionati minori e squadre riserve/giovanili. "
                    f"Ammesse esclusivamente le Prime Divisioni Nazionali d'Élite (Tier 1) e Coppe Ufficiali UEFA/FIFA."
                ),
                details="Violazione Regola #56: selezione appartenente a categoria minore o squadra riserve."
            )

        # =====================================================================
        # GATE 0.3: REGOLA #67 - FATTORE AMBIENTALE AD ALTA TOSSICITÀ NELLE COPPE EUROPEE
        # =====================================================================
        # Divieto assoluto di scommettere su esiti favorevoli alla squadra in trasferta (2, X2, X2+MG)
        # contro squadre turche, greche o balcaniche in casa nelle coppe europee UEFA (Champions, EL, Conference).
        tournament_upper = (candidate.tournament or "").upper()
        is_uefa_cup = any(c in tournament_upper for c in ["CHAMPIONS", "EUROPA LEAGUE", "CONFERENCE", "UEFA", "INTERNAZIONALI"])
        hostile_home_teams = [
            "BESIKTAS", "GALATASARAY", "FENERBAHCE", "TRABZONSPOR",
            "OLYMPIACOS", "OLYMPIAKOS", "PANATHINAIKOS", "PAOK", "AEK",
            "CRVENA ZVEZDA", "STELLA ROSSA", "PARTIZAN"
        ]
        home_team_name = (
            candidate.team_name if candidate.team_name
            else candidate.match_name.split(" vs ")[0] if " vs " in candidate.match_name
            else candidate.match_name.split(" - ")[0]
        ).upper()
        is_hostile_home = any(t in home_team_name for t in hostile_home_teams)
        is_away_favoring_pick = ("X2" in m_upper or " 2" in m_upper or m_upper.startswith("2") or "OSPITE" in m_upper)

        if is_uefa_cup and is_hostile_home and is_away_favoring_pick:
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=0,
                rejection_reason=(
                    f"[BLOCCATO - REGOLA #67: BAN ESITO ESTERNO IN AMBIENTE AD ALTA TOSSICITÀ] {candidate.market_name} su {candidate.match_name}. "
                    f"Nelle notti di coppa europea è tassativamente vietato scommettere su esiti a favore della squadra in trasferta "
                    f"(2 fisso, X2, X2 + MultiGol) nei campi caldi di Turchia, Grecia o Balcani (Lezione Besiktas 4-1 Marsiglia). "
                    f"La pressione acustica e l'intensità ambientale azzerano i modelli convenzionali di xG generando crolli ad alta varianza."
                ),
                details=f"Ambiente ostile rilevato ({home_team_name}) in competizione UEFA."
            )

        # =====================================================================
        # GATE 0.5: REGOLA #45 - FILTRO VOLUME OFFENSIVO SUI CORNER
        # =====================================================================
        is_corner_market = (
            candidate.market_type.upper() == "CORNER"
            or "CORNER" in candidate.market_name.upper()
            or "ANGOLO" in candidate.market_name.upper()
        )
        if is_corner_market:
            if candidate.team_avg_shots is not None and candidate.team_avg_shots < 18.0:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=0,
                    rejection_reason=(
                        f"[BLOCCATO - REGOLA #45: VOLUME TIRI INSUFFICIENTE PER CORNER] {candidate.market_name} su {candidate.match_name}. "
                        f"Media tiri registrata: {candidate.team_avg_shots:.1f} (soglia minima vincolante: >= 18.0 tiri/gara). "
                        f"Squadre con possesso orizzontale o basso volume di conclusioni sono vietate per i corner (Lezione Liverpool-Fulham 4-8 corners)."
                    ),
                    details=f"Tiri squadra: {candidate.team_avg_shots:.1f}/partita < 18.0 soglia minima."
                )

        # =====================================================================
        # GATE 0.6: REGOLA #66 - GAME-STATE BIAS SUI CORNER (Anti-Blowout Corner Trap)
        # =====================================================================
        # Se la favorita è schiacciante (quota pre-match <= 1.35 con alto rischio di 3-0 / 4-0 rapido),
        # vietare linee Over Corner di squadra elevate (Over >= 6.5 Corner)
        # perché quando la gara va in ghiaccio nel 1° tempo, l'intensità balistica del 2° tempo crolla.
        is_team_corner_high_line = (
            is_corner_market
            and any(w in m_upper for w in ["SQUADRA", "CASA", "OSPITE", "TEAM"])
            and any(line in m_upper for line in ["6.5", "7.5", "8.5", "9.5"])
            and "OVER" in m_upper
        )
        if is_team_corner_high_line:
            is_blowout_risk = (
                candidate.bookmaker_odd < 1.35
                or (candidate.pre_match_odd_favorite is not None and candidate.pre_match_odd_favorite <= 1.35)
            )
            if is_blowout_risk:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=0,
                    rejection_reason=(
                        f"[BLOCCATO - REGOLA #66: GAME-STATE BIAS SUI CORNER] {candidate.market_name} su {candidate.match_name}. "
                        f"Le linee Over Corner elevate di squadra (Over >= 6.5) sono vietate per favorite da possibile goleada rapida "
                        f"(Lezione Crystal Palace 4-0 Lech Poznan: 4 corner nel 1°T, solo 2 nella ripresa sul match già chiuso, fermandosi a 6). "
                        f"Sostituire con linee conservative (max Over 4.5/5.5) o mercati aperti sui gol."
                    ),
                    details="Rischio crollo produzione corner nella ripresa per partita già decisa nel primo tempo."
                )

        # =====================================================================
        # GATE 0.75: REGOLA #48 - FILTRO TETTO MASSIMO SU ATTACCHI DEVASTANTI (Anti-Ceiling Trap)
        # =====================================================================
        # Se una squadra è una macchina da gol (es. Barcellona di Flick, Bayern, Man City) contro una difesa debole,
        # vietare mercati con tetto massimo a 3 gol (MultiGol 1-3) per il rischio concreto di goleada (4-0, 5-0, 4-1).
        dominant_blowout_teams = ["BARCELONA", "BARCELLONA", "BAYERN", "MANCHESTER CITY", "MAN CITY", "REAL MADRID", "PSG", "PARIS"]
        has_dominant_offense = any(t in candidate.match_name.upper() for t in dominant_blowout_teams)
        is_narrow_ceiling_market = "1-3" in candidate.market_name or "UNDER 2.5" in candidate.market_name.upper()
        
        if has_dominant_offense and is_narrow_ceiling_market and "MULTIGOL" in candidate.market_name.upper():
            # Se la squadra dominante è quella a cui si applica il multigol
            team_affected = any(t in candidate.market_name.upper() for t in dominant_blowout_teams)
            if team_affected:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=0,
                    rejection_reason=(
                        f"[BLOCCATO - ANTI-CEILING TRAP: TETTO MASSIMO SU ATTACCO DEVASTANTE] {candidate.market_name} su {candidate.match_name}. "
                        f"Squadre con attacchi ad altissima produzione (Barça, Bayern, Man City) contro difese deboli hanno oltre il 22% di rischio goleada (4+ gol). "
                        f"È vietato imporre un tetto a 3 gol. Usare mercati aperti verso l'alto: '2 + Over 1.5', 'Over 1.5 Squadra' o 'X2 + Over 1.5'."
                    ),
                    details="Rischio concreto di sconfitta per troppi gol segnati dalla favorita (4-0, 5-0, 4-1)."
                )

        # =====================================================================
        # GATE 0.8: REGOLA #49 - DIVIETO ASSOLUTO ALLUCINAZIONE NOMINALE & AUDIT ANAGRAFICO TESTO
        # =====================================================================
        if candidate.sixth_sense_analysis:
            passed_text_audit, entity_violations = self.checker.audit_text_entities(
                text=candidate.sixth_sense_analysis,
                match_name=candidate.match_name,
                home_team=candidate.team_name if candidate.team_name else None
            )
            if not passed_text_audit:
                violations_str = " | ".join(entity_violations)
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=0,
                    rejection_reason=(
                        f"[BLOCCATO - REGOLA #49: ALLUCINAZIONE NOMINALE NON CERTIFICATA] {violations_str}. "
                        f"È tassativamente vietato citare giocatori trasferiti o appartenenti ad altre squadre (Memoria parametrica pregressa vietata!). "
                        f"Riscrivere l'analisi con parametri oggettivi di squadra o con la rosa reale 2026/27."
                    ),
                    details=f"Violazioni anagrafiche riscontrate nel Sesto Senso: {violations_str}"
                )

        # =====================================================================
        # GATE 0.85: REGOLA #51 - FILTRO "CORTO MUSO" & DIVIETO OVER 1.5 SU SQUADRE PRAGMATICHE
        # =====================================================================
        pragmatic_keywords = ["allegri", "corto muso", "simeone", "gestione corta", "blocco basso"]
        is_pragmatic_context = any(pk in (candidate.sixth_sense_analysis or "").lower() for pk in pragmatic_keywords)
        
        team_lower = (candidate.team_name or candidate.match_name or "").lower()
        # Napoli 2026/27 con Allegri o squadre ad alta vocazione pragmatica/corto muso
        if "napoli" in team_lower or is_pragmatic_context:
            m_upper = candidate.market_name.upper()
            if "OVER 1.5" in m_upper or "OV 1.5" in m_upper or "+ OVER 1.5" in m_upper:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=0,
                    rejection_reason=(
                        f"[BLOCCATO - REGOLA #51: FILTRO CORTO MUSO (ALLEGRI/PRAGMATISMO)] Il mercato '{candidate.market_name}' "
                        f"su '{candidate.match_name}' impone la condizione Over 1.5, escludendo l'1-0 o lo 0-1. "
                        f"Sotto la guida di tecnici pragmatici (come Allegri al Napoli o Simeone), una volta in vantaggio "
                        f"la squadra abbassa il ritmo e congela il minimo scarto (frequenza 1-0/0-1 oltre il 25%). "
                        f"Obbligo tassativo di sostituire con mercati resilienti che coprono l'1-0: "
                        f"'1X + MultiGol 1-5', '1 Fisso', 'MultiGol 1-3 Squadra' o '1X + Under 3.5'!"
                    ),
                    details="Vietato imporre Over 1.5 escludendo l'1-0/0-1 su squadre a gestione pragmatica 'corto muso'."
                )

        # =====================================================================
        # GATE 0.9: REGOLA #71 - CHECK SUL MERCATO PIÙ ADATTO IN BASE AL CAMPIONATO E ALLA SQUADRA
        # =====================================================================
        from services.analysis.league_dna_market_matcher import LeagueDNAMarketMatcher
        dna_matcher = LeagueDNAMarketMatcher()
        league_target = candidate.tournament or candidate.match_name or ""
        
        # Estrai home e away da match_name
        parts = candidate.match_name.split(" vs ") if " vs " in candidate.match_name else candidate.match_name.split(" - ")
        h_team = parts[0].strip() if len(parts) >= 1 else candidate.team_name or ""
        a_team = parts[1].strip() if len(parts) >= 2 else ""

        dna_res = dna_matcher.check_market_suitability(
            league=league_target,
            home_team=h_team,
            away_team=a_team,
            market_name=candidate.market_name,
            market_category=candidate.market_type,
            bookmaker_odd=candidate.bookmaker_odd
        )
        if dna_res.is_prohibited:
            alts = ", ".join(dna_res.recommended_alternatives) if dna_res.recommended_alternatives else "Consultare matrice DNA"
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=0,
                rejection_reason=(
                    f"[BLOCCATO - REGOLA #71: INCOMPATIBILITÀ CON DNA CAMPIONATO & SQUADRA] {dna_res.tactical_rationale} "
                    f"Rifiuto: {dna_res.rejection_reason}. Alternative raccomandate da DNA Tattico: ⭐ {alts}."
                ),
                details=f"Incompatibilità tra mercato '{candidate.market_name}' e DNA tattico ({dna_res.league_cluster} / {dna_res.team_archetype})."
            )

        # =====================================================================
        # GATE 0.95: REGOLA #55 - PROTOCOLLO FERREO DI CONSULTAZIONE FONTI REALI & SCONTRI EQUILIBRATI
        # =====================================================================
        # 1. Se fonti reali non sono state verificate
        if not candidate.verified_sources_checked:
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=0,
                rejection_reason=(
                    f"[BLOCCATO - REGOLA #55: MANCATA CONSULTAZIONE FONTI REALI OBIETTIVE] "
                    f"Per la partita '{candidate.match_name}' non sono state verificate le statistiche reali su FootyStats/Sofascore. "
                    f"Divieto assoluto di scommesse basate su memoria parametrica o supposizioni."
                ),
                details="Verifica fonti reali (classifica, forma, H2H) obbligatoria pre-schedina."
            )

        # 2. Se scontro diretto equilibrato (delta punti <= 3), vietare 1 o 2 secco
        if candidate.verified_standings_delta is not None and abs(candidate.verified_standings_delta) <= 3:
            m_upper = candidate.market_name.upper()
            if candidate.market_type.upper() in ["1X2", "1", "2"] or m_upper in ["1", "2"]:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=0,
                    rejection_reason=(
                        f"[BLOCCATO - REGOLA #55: SCONTRO DIRETTO EQUILIBRATO (Δ PUNTI <= 3)] "
                        f"La partita '{candidate.match_name}' presenta un divario di soli {abs(candidate.verified_standings_delta)} punti. "
                        f"In scontri diretti equilibrati è TASSATIVAMENTE VIETATO esporsi su 1 o 2 fisso (Lezione Red Star-Metz). "
                        f"Obbligo di usare mercati protetti: Doppia Chance, MultiGol 1-4, Under 3.5."
                    ),
                    details=f"Δ Punti = {abs(candidate.verified_standings_delta)} <= 3. Scontro equilibrato ad alta volatilità."
                )

        # =====================================================================
        # FASE 1, 2, 3: CONTROLLO ANAGRAFICO, SANITARIO & FORMAZIONI
        # =====================================================================
        if candidate.player_name and candidate.team_name:
            audit = self.checker.full_player_audit(
                player_name=candidate.player_name,
                team_name=candidate.team_name,
                fixture_id=candidate.fixture_id
            )

            # Fase 1: Roster check
            if not audit.in_squad:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=1,
                    rejection_reason=audit.rejection_reason,
                    details=f"Il giocatore non appartiene alla rosa 2026/27 di {candidate.team_name}."
                )

            # Fase 2: Infortuni / Squalifiche
            if audit.is_injured_or_suspended:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=2,
                    rejection_reason=audit.rejection_reason,
                    details=f"Il giocatore è indisponibile per infortunio o squalifica ({audit.injury_reason})."
                )

            # Fase 3: Lineup Ufficiale
            if not audit.can_bet_player_prop:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=3,
                    rejection_reason=audit.rejection_reason,
                    details=f"Stato formazione: {audit.lineup_status}."
                )

        # =====================================================================
        # FASE 4: SESTO SENSO & AUDIT CONTESTUALE (OBBLIGATORIO)
        # =====================================================================
        if not candidate.sixth_sense_analysis or len(candidate.sixth_sense_analysis.strip()) < 15:
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=4,
                rejection_reason=(
                    f"[BLOCCATO - FASE 4: SESTO SENSO MANCANTE] {candidate.match_name}. "
                    f"È tassativamente vietato proporre mercati senza aver prima compilato l'analisi del Sesto Senso "
                    f"(rassegna stampa, clima spogliatoio, motivazione, trappole tattiche e rotazioni)!"
                ),
                details="Manca la colonna motivazione tattica e Sesto Senso."
            )

        # Audit Semantico Automatico via Hugging Face SportsBERT RAG
        try:
            from services.nlp.sports_semantic_rag import get_sports_semantic_rag
            rag = get_sports_semantic_rag()
            sem_report = rag.audit_text_semantics(candidate.sixth_sense_analysis, threshold=0.65)
            known_risk_keys = {"ROTATION_RISK", "SLOW_START", "LOW_MOTIVATION", "INJURY_ALARM"}
            for sem_flag in sem_report.get("flags", []):
                if sem_flag in known_risk_keys and sem_flag not in candidate.sixth_sense_risk_flags:
                    candidate.sixth_sense_risk_flags.append(sem_flag)
        except Exception:
            pass

        # Controllo coppe infrasettimanali
        risk_flags_upper = [f.upper() for f in candidate.sixth_sense_risk_flags]
        has_cup = candidate.has_upcoming_midweek_cup or "MIDWEEK_CUP" in risk_flags_upper
        if has_cup and (candidate.is_intermediate_deadline or candidate.is_first_half_only or candidate.is_compound_time_market):
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=4,
                rejection_reason=(
                    f"[BLOCCATO - SESTO SENSO: TURNOVER PRE-COPPA & AVVIO DIESEL] {candidate.match_name} ha un impegno europeo nei giorni successivi. "
                    f"Tassativamente vietati mercati 1° tempo o mercati rigidi sui due tempi a quota compressa (Lezione Sunderland-Arsenal 0-0 HT)!"
                ),
                sixth_sense_summary=candidate.sixth_sense_analysis
            )

        # Controllo bandiere rosse Sesto Senso
        for flag in candidate.sixth_sense_risk_flags:
            flag_upper = flag.upper()
            if flag_upper == "ROTATION_RISK" and (candidate.player_name or candidate.is_compound_time_market or is_straight_win_market):
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=4,
                    rejection_reason=f"[BLOCCATO - SESTO SENSO: RISCHIO TURNOVER] Rilevato turnover massiccio per {candidate.match_name}!",
                    sixth_sense_summary=candidate.sixth_sense_analysis
                )
            if flag_upper == "SLOW_START" and (candidate.is_intermediate_deadline or candidate.is_first_half_only):
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=4,
                    rejection_reason=f"[BLOCCATO - SESTO SENSO: AVVIO DIESEL] Rilevato rischio primo tempo bloccato/a bassi ritmi per {candidate.match_name}!",
                    sixth_sense_summary=candidate.sixth_sense_analysis
                )
            if flag_upper == "LOW_MOTIVATION" and candidate.bookmaker_odd < 1.45:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=4,
                    rejection_reason=f"[BLOCCATO - SESTO SENSO: SQUADRA APPAGATA] Partita senza stimoli di classifica per la favorita ({candidate.match_name})!",
                    sixth_sense_summary=candidate.sixth_sense_analysis
                )

        # =====================================================================
        # FASE 5 & 6: CALCOLO MATEMATICO ED EDGE REALE
        # =====================================================================
        p_real, edge, math_report = self.calculate_joint_probability(candidate)
        if p_real is None:
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=5,
                rejection_reason=(
                    f"[BLOCCATO - FASE 5: PROBABILITÀ NON CALCOLATA DAL MOTORE] {candidate.market_name} su {candidate.match_name}. "
                    f"{math_report}"
                ),
                details=math_report,
                sixth_sense_summary=candidate.sixth_sense_analysis,
            )
        fair_odd = 1.0 / max(0.001, p_real)

        if edge < self.MIN_EDGE_THRESHOLD:
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=6,
                rejection_reason=(
                    f"[BLOCCATO - FASE 6: TRAPPOLA EDGE NEGATIVO] {candidate.market_name} su {candidate.match_name}. "
                    f"Edge: {edge*100:+.1f}% (Soglia minima richiesta: +{self.MIN_EDGE_THRESHOLD*100:.1f}%). "
                    f"Quota offerta @{candidate.bookmaker_odd:.2f} inferiore alla quota equa reale @{fair_odd:.2f}!"
                ),
                real_probability=p_real,
                fair_odds=fair_odd,
                mathematical_edge=edge,
                details=math_report,
                sixth_sense_summary=candidate.sixth_sense_analysis
            )

        if p_real < self.MIN_LEG_PROBABILITY_THRESHOLD:
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=6,
                rejection_reason=(
                    f"[BLOCCATO - FASE 6: PROBABILITÀ INSUFFICIENTE SOTTO SOGLIA 72%] {candidate.market_name} su {candidate.match_name}. "
                    f"Probabilità reale calcolata: {p_real*100:.1f}% (soglia minima vincolante per gambe di multipla: >={self.MIN_LEG_PROBABILITY_THRESHOLD*100:.1f}%). "
                    f"Linee sotto il 72% distruggono il win rate della schedina anche in presenza di un edge teorico marginale."
                ),
                real_probability=p_real,
                fair_odds=fair_odd,
                mathematical_edge=edge,
                details=math_report,
                sixth_sense_summary=candidate.sixth_sense_analysis
            )

        # =====================================================================
        # GATE 6.5: NETWIN AGGIO SENTINEL (Pilastro 1)
        # =====================================================================
        netwin_odd = candidate.netwin_actual_odd
        if netwin_odd is None:
            # Query automatica della cache quote reali Netwin
            cached_odd = self.netwin_checker.get_netwin_odd(candidate.match_name, candidate.market_name, fallback_odd=None)
            if cached_odd is not None:
                netwin_odd = float(cached_odd)
                candidate.netwin_actual_odd = netwin_odd

        if netwin_odd is not None:
            netwin_edge = (p_real * netwin_odd) - 1.0
            if netwin_edge < self.MIN_EDGE_THRESHOLD:
                return ValidationReport(
                    passed=False,
                    candidate=candidate,
                    stage_failed=6,
                    rejection_reason=(
                        f"[BLOCCATO - GATE 6.5: NETWIN AGGIO TRAP] Quota proposta @{candidate.bookmaker_odd:.2f} tagliata a @{netwin_odd:.2f} su Netwin. "
                        f"L'Edge reale crolla da {edge*100:+.1f}% a {netwin_edge*100:+.1f}% (minimo richiesto: +{self.MIN_EDGE_THRESHOLD*100:.1f}%). "
                        f"Margine del banco eccessivo che distrugge il valore atteso."
                    ),
                    real_probability=p_real,
                    fair_odds=fair_odd,
                    mathematical_edge=netwin_edge,
                    details=f"Quota Netwin @{netwin_odd:.2f} vs Teorica @{candidate.bookmaker_odd:.2f}.",
                    sixth_sense_summary=candidate.sixth_sense_analysis
                )

        # =====================================================================
        # FASE 7: FILTRO STRUTTURALE DI MERCATO (ANTI-SCADENZA 45')
        # =====================================================================
        if candidate.is_intermediate_deadline and candidate.bookmaker_odd < 1.55:
            return ValidationReport(
                passed=False,
                candidate=candidate,
                stage_failed=7,
                rejection_reason=(
                    f"[BLOCCATO - FASE 7: TRAPPOLA SCADENZA INTERMEDIA 45'] {candidate.market_name} a quota @{candidate.bookmaker_odd:.2f}. "
                    f"Può morire all'intervallo (45') cancellando il 2° tempo a quota compressa (< 1.55). "
                    f"Consentiti solo mercati con 90 minuti di respiro!"
                ),
                real_probability=p_real,
                fair_odds=fair_odd,
                mathematical_edge=edge,
                details=math_report,
                sixth_sense_summary=candidate.sixth_sense_analysis
            )

        # Approvato!
        return ValidationReport(
            passed=True,
            candidate=candidate,
            stage_failed=None,
            rejection_reason=None,
            real_probability=p_real,
            fair_odds=fair_odd,
            mathematical_edge=edge,
            details=math_report,
            sixth_sense_summary=candidate.sixth_sense_analysis
        )

    def calculate_recommended_stake(
        self,
        current_bankroll: float,
        total_odds: float,
        num_selections: int,
        estimated_prob: Optional[float] = None,
    ) -> float:
        """
        FASE 8: stake da Kelly frazionario sulla probabilità congiunta del ticket.
        num_selections resta nel contratto dei chiamanti; il tetto 8% è dentro Kelly.
        """
        del num_selections
        if current_bankroll <= 0 or total_odds <= 1.0 or not estimated_prob or estimated_prob <= 0:
            return 0.0
        recommendation = KellyStakingEngine(current_bankroll).calculate_stake(
            odds=total_odds,
            estimated_prob=estimated_prob,
        )
        return recommendation.recommended_stake

    def validate_ticket(self, candidates: List[MarketCandidate], current_bankroll: float, proposed_stake: Optional[float] = None) -> TicketValidationReport:
        """
        Audit di Livello Ticket: valida tutte le selezioni ed applica i vincoli di schedina.
        - Protocollo Continuità: Max 3-4 selezioni per ticket (5+ gambe tassativamente vietate).
        - Staking Management: Max 8% del bankroll per singolo ticket.
        """
        rejection_reasons: List[str] = []
        legs_reports: List[ValidationReport] = []
        total_odds = 1.0
        passed_candidates: List[MarketCandidate] = []

        # Vincolo 1: Max 3-4 selezioni
        if len(candidates) > 4:
            rejection_reasons.append(
                f"[BLOCCATO - PROTOCOLLO CONTINUITÀ] Proposte {len(candidates)} selezioni. "
                f"Il limite assoluto è di massimo 3 o 4 eventi per ticket (stop alle schedine lunghe)."
            )
        elif len(candidates) < 1:
            rejection_reasons.append("[BLOCCATO] Nessuna selezione proposta nel ticket.")

        # Validazione singole selezioni
        for c in candidates:
            rep = self.validate_candidate(c)
            legs_reports.append(rep)
            if rep.passed:
                total_odds *= c.bookmaker_odd
                passed_candidates.append(c)
            else:
                rejection_reasons.append(f"{c.match_name} ({c.market_name}): {rep.rejection_reason}")

        joint_probability = self.ticket_joint_probability(passed_candidates) if passed_candidates else None
        if passed_candidates and joint_probability is None:
            rejection_reasons.append(
                "[BLOCCATO - PROBABILITÀ CONGIUNTA] Due o più mercati sulla stessa partita "
                "non sono indipendenti e non sono prezzabili insieme sulla matrice dei punteggi. "
                "Il prodotto delle probabilità singole non è una probabilità del ticket."
            )
        elif passed_candidates and joint_probability <= 0:
            rejection_reasons.append(
                "[BLOCCATO - PROBABILITÀ CONGIUNTA] I mercati sulla stessa partita si escludono: "
                "la probabilità dell'intersezione è zero."
            )

        # Money Management
        rec_stake = self.calculate_recommended_stake(
            current_bankroll,
            total_odds,
            len(candidates),
            estimated_prob=joint_probability if joint_probability and joint_probability > 0 else None,
        )
        chosen_stake = proposed_stake if proposed_stake is not None else rec_stake
        stake_pct = (chosen_stake / max(0.01, current_bankroll)) * 100

        if chosen_stake > (current_bankroll * self.MAX_TICKET_BANKROLL_PCT) and current_bankroll > 20.0:
            rejection_reasons.append(
                f"[BLOCCATO - MONEY MANAGEMENT] Stake proposto di €{chosen_stake:.2f} ({stake_pct:.1f}%) "
                f"supera il limite massimo consentito dell'8% (€{current_bankroll * self.MAX_TICKET_BANKROLL_PCT:.2f})."
            )

        # =====================================================================
        # GATE 8.5: REGOLA #66 - DIVIETO PARACADUTE IN MULTIPLA (Solo Singola Diretta)
        # =====================================================================
        # Un paracadute di copertura non può mai essere una multipla dipendente da 2 o più eventi:
        # se uno solo salta, la copertura fallisce vanificando l'hedging.
        # Deve essere giocato esclusivamente come Singola Secca ad alto moltiplicatore (@ 1.85 - 2.40).
        is_multi_parachute = len(candidates) > 1 and (
            any(c.is_parachute_market for c in candidates)
            or (len(candidates) == 2 and all(("CORNER" in c.market_name.upper() and ("6.5" in c.market_name or "7.5" in c.market_name)) for c in candidates))
        )
        if is_multi_parachute:
            rejection_reasons.append(
                f"[BLOCCATO - REGOLA #66: PARACADUTE IN MULTIPLA VIETATO] Proposto paracadute di copertura composto da {len(candidates)} eventi (@ {total_odds:.2f}). "
                f"Il Paracadute per definizione matematica NON può essere una multipla: combinare due linee (es. due Over 6.5 Corner) espone al rischio "
                f"che un singolo evento manchi di poco (es. Crystal Palace fermatosi a 6 sul 4-0), distruggendo l'intera protezione. "
                f"Il Paracadute DEVE essere giocato come SINGOLA DIRETTA (@ 1.85 - 2.40) calibrata per coprire con la vincita l'importo del ticket principale."
            )

        ticket_passed = (len(rejection_reasons) == 0)

        return TicketValidationReport(
            passed=ticket_passed,
            num_selections=len(candidates),
            total_odds=round(total_odds, 2),
            recommended_stake=chosen_stake,
            stake_percentage=round(stake_pct, 1),
            legs_reports=legs_reports,
            rejection_reasons=rejection_reasons
        )
