import sys, json
sys.path.insert(0, ".")
from services.betting.strict_ticket_pipeline import (
    StrictTicketPipeline,
    MarketCandidate
)
from scripts.strict_validator import format_ticket_report

pipeline = StrictTicketPipeline()

print("=" * 90)
print("🔍 1. AUDIT PROGRAMMATICO DELLA PROPOSTA ORIGINALE DEL TIPSTER (6 EVENTI)")
print("=" * 90)

tipster_candidates = [
    MarketCandidate(
        match_name="Groningen vs Zwolle",
        tournament="Olanda | Eredivisie",
        market_name="MultiGol 2-5 Casa",
        bookmaker_odd=1.40,
        estimated_p_90=0.68,
        sixth_sense_analysis="Zwolle ha xG 1.57 e concede ma segna spesso. Groningen xG 1.96 ma rischio pareggio 1-1.",
        market_type="GOALS"
    ),
    MarketCandidate(
        match_name="Bayern Monaco vs Union Berlino",
        tournament="Germania | Bundesliga",
        market_name="Casa Vince Entrambi i Tempi",
        bookmaker_odd=1.47,
        estimated_p_1h=0.72,
        estimated_p_2h=0.65,
        is_compound_time_market=True,
        has_upcoming_midweek_cup=True,
        sixth_sense_analysis="Turnover e Champions imminente. Rischio vistoso rallentamento nella ripresa dopo vantaggio.",
        sixth_sense_risk_flags=["ROTATION_RISK", "COMPOUND_TIME_TRAP"],
        market_type="COMPOUND_TIME"
    ),
    MarketCandidate(
        match_name="Monaco vs Lens",
        tournament="Francia | Ligue 1",
        market_name="MultiGol 1-3 Casa",
        bookmaker_odd=1.30,
        estimated_p_90=0.82,
        sixth_sense_analysis="Monaco segna regolarmente in casa (1.8 gol/gara). Lens compatto non concede goleada (max 3 gol).",
        market_type="GOALS"
    ),
    MarketCandidate(
        match_name="Monza vs Sassuolo",
        tournament="Italia | Serie A",
        market_name="MultiGol 0-2 1°Tempo + 1-3 2°Tempo",
        bookmaker_odd=1.44,
        estimated_p_1h=0.91,
        estimated_p_2h=0.84,
        estimated_p_90=0.78,
        sixth_sense_analysis="Primo tempo tattico e bloccato in Serie A. Nella ripresa spazi aperti con xG congiunto 3.56.",
        market_type="COMBO"
    ),
    MarketCandidate(
        match_name="Espanyol vs Elche",
        tournament="Spagna | LaLiga",
        market_name="1X + Under 4.5",
        bookmaker_odd=1.41,
        estimated_p_90=0.79,
        sixth_sense_analysis="LaLiga a basso indice balistico. Espanyol roccioso al Cornellà, Elche debole fuori casa.",
        market_type="COMBO"
    ),
    MarketCandidate(
        match_name="Brentford vs Chelsea",
        tournament="Inghilterra | Premier League",
        market_name="Gol (Entrambe a Segno)",
        bookmaker_odd=1.43,
        estimated_p_90=0.75,
        sixth_sense_analysis="Derby londinese ad altissimo ritmo. xG combinato 3.60. Entrambe concedono transizioni.",
        market_type="GOALS"
    )
]

report_tipster = pipeline.validate_ticket(tipster_candidates, current_bankroll=100.0, proposed_stake=10.0)
print(format_ticket_report(report_tipster))

print("\n" + "=" * 90)
print("🛡️ 2. AUDIT PROGRAMMATICO DEI TICKET OTTIMIZZATI BAGENT (MAX 3 SELEZIONI - REGOLA #46)")
print("=" * 90)

# TICKET 1: LA TRIPLA D'ORO RESILIENTE
ticket1_candidates = [
    MarketCandidate(
        match_name="Espanyol vs Elche",
        tournament="Spagna | LaLiga",
        market_name="1X + Under 4.5",
        bookmaker_odd=1.41,
        estimated_p_90=0.79,
        sixth_sense_analysis="Espanyol imbattuto in casa contro l'Elche. Difesa rocciosa, LaLiga < 2.50 gol medi.",
        market_type="COMBO"
    ),
    MarketCandidate(
        match_name="Monza vs Sassuolo",
        tournament="Italia | Serie A",
        market_name="MultiGol 0-2 1°T + 1-3 2°T",
        bookmaker_odd=1.44,
        estimated_p_1h=0.91,
        estimated_p_2h=0.84,
        estimated_p_90=0.78,
        sixth_sense_analysis="Assorbe 0-0, 1-0 o 1-1 all'intervallo. Nella ripresa difese lunghe e gol quasi certo (Regola #47).",
        market_type="COMBO"
    ),
    MarketCandidate(
        match_name="Brentford vs Chelsea",
        tournament="Inghilterra | Premier League",
        market_name="Gol (Entrambe a Segno)",
        bookmaker_odd=1.43,
        estimated_p_90=0.76,
        sixth_sense_analysis="Brentford in casa xG 1.92. Chelsea con Maresca segna ma subisce contropiedi sistematici.",
        market_type="GOALS"
    )
]

report_t1 = pipeline.validate_ticket(ticket1_candidates, current_bankroll=100.0, proposed_stake=10.0)
print(format_ticket_report(report_t1))

# TICKET 2: IL TRIDENTE RETTIFICATO
ticket2_candidates = [
    MarketCandidate(
        match_name="Monaco vs Lens",
        tournament="Francia | Ligue 1",
        market_name="MultiGol 1-3 Casa",
        bookmaker_odd=1.30,
        estimated_p_90=0.83,
        sixth_sense_analysis="Monaco a segno al Louis II nel 95% dei match. Lens non subisce goleada (Regola #47).",
        market_type="GOALS"
    ),
    MarketCandidate(
        match_name="Bayern Monaco vs Union Berlino",
        tournament="Germania | Bundesliga",
        market_name="1X + Over 2.5",
        bookmaker_odd=1.28,
        estimated_p_90=0.85,
        sixth_sense_analysis="Sostituisce il trappolone 'vince entrambi i tempi'. Se Bayern chiude 3-0 nel 1T e passeggia, incassiamo comunque!",
        market_type="COMBO"
    ),
    MarketCandidate(
        match_name="Groningen vs Zwolle",
        tournament="Olanda | Eredivisie",
        market_name="Over 2.5 Gol Totali",
        bookmaker_odd=1.42,
        estimated_p_90=0.77,
        sixth_sense_analysis="Svincolato dai soli gol del Groningen. Copre 1-2, 2-1, 2-2, 3-1, sfruttando l'84% di Over 2.5 in Eredivisie.",
        market_type="GOALS"
    )
]

report_t2 = pipeline.validate_ticket(ticket2_candidates, current_bankroll=100.0, proposed_stake=10.0)
print(format_ticket_report(report_t2))
