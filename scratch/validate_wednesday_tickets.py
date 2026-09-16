import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.strict_ticket_pipeline import (
    StrictTicketPipeline,
    MarketCandidate,
    TicketValidationReport
)
from scripts.strict_validator import format_ticket_report

pipeline = StrictTicketPipeline()

bankroll = 300.0

# Ticket 1 — Elite Mix (@ 2.66, 7% stake)
t1_candidates = [
    MarketCandidate(
        match_name="Atlético Madrid vs Osasuna",
        tournament="La Liga",
        market_name="1X + MultiGol 1-4",
        market_type="COMBO",
        bookmaker_odd=1.40,
        estimated_p_90=0.82,
        sixth_sense_analysis="Simeone punta sulla solidità al Metropolitano; Osasuna squadra chiusa che difficilmente fa goleada. Copre 1-0, 2-0, 1-1, 2-1, 3-0, 3-1."
    ),
    MarketCandidate(
        match_name="AC Milan vs Benfica",
        tournament="Europa League",
        market_name="1X + MultiGol 1-5",
        market_type="COMBO",
        bookmaker_odd=1.42,
        estimated_p_90=0.80,
        sixth_sense_analysis="San Siro trascina il Milan all'esordio europeo; il Benfica è tecnico ma vulnerabile in trasferta. Range 1-5 ultra-elastico contro ogni draw."
    ),
    MarketCandidate(
        match_name="FC Barcelona vs Racing Santander",
        tournament="La Liga",
        market_name="MultiGol 2-5",
        market_type="MULTIGOL",
        bookmaker_odd=1.34,
        estimated_p_90=0.84,
        sixth_sense_analysis="Barcellona travolgente al Montjuïc, Racing Santander chiusa ma permeabile. MultiGol 2-5 esclude lo 0-0 e l'1-0 risicato."
    )
]

# Ticket 2 — High Resiliency (@ 2.53, 6% stake)
t2_candidates = [
    MarketCandidate(
        match_name="Deportivo La Coruña vs Sevilla",
        tournament="La Liga",
        market_name="1X + MultiGol 1-4",
        market_type="COMBO",
        bookmaker_odd=1.40,
        estimated_p_90=0.81,
        sixth_sense_analysis="Al Riazor il Dépor ritrova entusiasmo e compattezza; Siviglia convalescente e poco brillante in trasferta. Copertura 1X su match tirato."
    ),
    MarketCandidate(
        match_name="Bayer Leverkusen vs NK Celje",
        tournament="Europa League",
        market_name="MultiGol 2-5",
        market_type="MULTIGOL",
        bookmaker_odd=1.33,
        estimated_p_90=0.85,
        sixth_sense_analysis="Leverkusen con volume offensivo spaventoso alla BayArena contro gli sloveni del Celje; atteso match vivace con 2-4 reti."
    ),
    MarketCandidate(
        match_name="Manchester United vs Brighton",
        tournament="EFL Cup",
        market_name="MultiGol 2-5",
        market_type="MULTIGOL",
        bookmaker_odd=1.36,
        estimated_p_90=0.82,
        sixth_sense_analysis="Coppa di Lega inglese a Old Trafford con squadre propositive; United e Brighton concedono sempre spazi tra le linee."
    )
]

# Ticket 3 — Conference & Europa League Special (@ 2.63, 6% stake)
t3_candidates = [
    MarketCandidate(
        match_name="Omonia Nicosia vs Celta Vigo",
        tournament="Europa League",
        market_name="X2 + MultiGol 1-5",
        market_type="COMBO",
        bookmaker_odd=1.42,
        estimated_p_90=0.80,
        sixth_sense_analysis="Celta Vigo nettamente superiore tecnicamente a Cipro; la doppia chance X2 protegge dall'ambiente caldo di Nicosia."
    ),
    MarketCandidate(
        match_name="Olympiakos vs Jagiellonia",
        tournament="Europa League",
        market_name="1X + MultiGol 1-4",
        market_type="COMBO",
        bookmaker_odd=1.38,
        estimated_p_90=0.83,
        sixth_sense_analysis="Pireo infuocato: l'Olympiakos vince la maggior parte delle gare interne; Jagiellonia catenacciaro che punta a limitare i danni."
    ),
    MarketCandidate(
        match_name="RSC Anderlecht vs Lyon",
        tournament="Europa League",
        market_name="MultiGol 2-5",
        market_type="MULTIGOL",
        bookmaker_odd=1.34,
        estimated_p_90=0.84,
        sixth_sense_analysis="Due scuole di calcio votate all'attacco e al pressing alto a Bruxelles. Match ideale per un intervallo di 2-4 reti."
    )
]

print("=== VALIDAZIONE TICKET 1: ELITE MIX ===")
rep1 = pipeline.validate_ticket(t1_candidates, current_bankroll=bankroll, proposed_stake=21.0)
print(format_ticket_report(rep1))

print("\n=== VALIDAZIONE TICKET 2: HIGH RESILIENCY ===")
rep2 = pipeline.validate_ticket(t2_candidates, current_bankroll=bankroll, proposed_stake=18.0)
print(format_ticket_report(rep2))

print("\n=== VALIDAZIONE TICKET 3: CONFERENCE & EUROPA LEAGUE SPECIAL ===")
rep3 = pipeline.validate_ticket(t3_candidates, current_bankroll=bankroll, proposed_stake=18.0)
print(format_ticket_report(rep3))
