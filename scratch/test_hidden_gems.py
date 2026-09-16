import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.strict_ticket_pipeline import (
    StrictTicketPipeline,
    MarketCandidate
)
from scripts.strict_validator import format_report

pipeline = StrictTicketPipeline()

hidden_gems = [
    # Chicca 1: Corner Dominance Leverkusen
    MarketCandidate(
        match_name="Bayer Leverkusen vs NK Celje",
        tournament="Europa League",
        market_name="Bayer Leverkusen Over 6.5 Corner",
        market_type="CORNER",
        bookmaker_odd=1.52,
        estimated_p_90=0.76,
        team_avg_shots=18.8,
        team_avg_shots_on_target=7.2,
        sixth_sense_analysis="Regola #45 pienamente soddisfatta: Leverkusen tira 18.8 volte a match. Il Celje si chiuderà con un blocco basso a 10 uomini nell'area di rigore: pioggia di cross e tiri deviati oltre la linea di fondo."
    ),
    # Chicca 2: Cartellini nel Caldo del Pireo
    MarketCandidate(
        match_name="Olympiakos vs Jagiellonia",
        tournament="Europa League",
        market_name="Over 3.5 Cartellini Totali",
        market_type="CARDS",
        bookmaker_odd=1.45,
        estimated_p_90=0.81,
        sixth_sense_analysis="Ambiente incandescente al Georgios Karaiskakis: arbitro sotto pressione, Jagiellonia che spezzetterà il gioco con falli tattici continui per frenare la pressione greca. Media cartellini arbitri UEFA in Grecia > 4.8 a gara."
    ),
    # Chicca 3: MultiGol Squadra Casa Barça (Anti-Trap)
    MarketCandidate(
        match_name="FC Barcelona vs Racing Santander",
        tournament="La Liga",
        market_name="Barcellona MultiGol 2-4 Casa",
        market_type="MULTIGOL",
        bookmaker_odd=1.48,
        estimated_p_90=0.79,
        sixth_sense_analysis="Chicca asimmetrica: non dipende da un improbabile gol del Racing Santander (come il Gol/BTTS). Incassa con il 2-0, 3-0, 4-0, 2-1, 3-1, 4-1. Flick gestirà i minuti nel finale, garantendo il tetto massimo dei 4 gol."
    ),
    # Chicca 4: Over Differenziato Tempi Old Trafford (NO VAR)
    MarketCandidate(
        match_name="Manchester United vs Brighton",
        tournament="EFL Cup",
        market_name="Over 0.5 1°Tempo + Over 0.5 2°Tempo (Gol in Entrambi i Tempi)",
        market_type="COMBO",
        bookmaker_odd=1.50,
        estimated_p_90=0.78,
        sixth_sense_analysis="In Carabao Cup senza VAR il gioco è frenetico e le difese (De Ligt out nello United) concedono ripartenze immediate. Almeno una rete prima dell'intervallo e almeno una nella ripresa a ritmi allungati."
    ),
    # Chicca 5: MultiGol Squadra Atlético (Understatement Attacco)
    MarketCandidate(
        match_name="Atlético Madrid vs Osasuna",
        tournament="La Liga",
        market_name="Atlético Madrid MultiGol 1-2 Casa",
        market_type="MULTIGOL",
        bookmaker_odd=1.58,
        estimated_p_90=0.74,
        sixth_sense_analysis="Sfrutta le assenze simultanee di Julián Álvarez e Sørloth: l'Atlético vincerà 1-0 o 2-0, o al massimo pareggerà 1-1. Pagare 1.58 per l'Atlético che segna esattamente 1 o 2 gol contro l'Osasuna è una quota a valore enorme."
    )
]

print("=" * 85)
print("💎 AUDIT CERTIFICAZIONE CHICCHE NASCOSTE PRE-SCHEDINA")
print("=" * 85)

for gem in hidden_gems:
    rep = pipeline.validate_candidate(gem)
    print(format_report(rep))
    print("-" * 85)
