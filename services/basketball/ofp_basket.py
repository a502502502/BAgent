#!/usr/bin/env python3
"""
BAgent OFP Basket Engine (Oddspedia / Forebet / Pengwin & Quantitative Basketball)
Estensione del metodo OFP per l'Eurolega e l'NBA:
- O = Oddspedia (Moneyline T/T, linee Spread/Handicap, Total Points Over/Under)
- F = Forebet / Freebet (Modelli matematici di punteggio atteso, scarto medio e % vittoria)
- P = BAgent Quantitative & Tactical Model (4 fattori Dean Oliver, Pace, Offensive/Defensive Rating, H2H)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class OFPBasketMatch:
    match: str
    kickoff: str
    tournament: str
    
    # 1. O - Oddspedia
    moneyline: Dict[str, float]       # es. {"1": 2.05, "2": 1.80}
    book_spread: str                  # es. "+2.5 / -2.5"
    book_total: float                 # es. 162.5
    oddspedia_sentiment: str
    
    # 2. F - Forebet
    forebet_pred_score: str           # es. "82 - 79"
    forebet_win_prob: Dict[str, int]  # es. {"1": 54, "2": 46}
    forebet_total_pred: float         # es. 161.0
    
    # 3. P - BAgent Quantitative & Tattica
    h2h_trend: str                    # es. "La squadra di casa ha vinto gli ultimi 7 scontri diretti consecutivi"
    tactical_edge: str                # es. "Real 0-3 in trasferta in stagione; Wright dominante a rimbalzo"
    
    # Sintesi OFP Basket
    convergence_grade: str            # "AAA", "AA", "A"
    recommended_spread: str           # es. "Milano +5.5 Handicap"
    recommended_safe: str             # es. "Milano +6.5 / Under 166.5"
    target_odds: float                # es. 1.45 - 1.60
    confidence: str                   # "ALTA", "MEDIA"


class OFPBasketEngine:
    """Motore di incrocio OFP per il basket."""

    def __init__(self):
        self.matches: List[OFPBasketMatch] = []

    def add_match(self, match: OFPBasketMatch):
        self.matches.append(match)

    def get_top_picks(self) -> List[OFPBasketMatch]:
        return [m for m in self.matches if m.convergence_grade in ("AAA", "AA")]


def build_today_euroleague_ofp() -> OFPBasketEngine:
    """Popola l'analisi OFP per il Round 5 di Eurolega (13 Ottobre 2026)."""
    engine = OFPBasketEngine()

    # 1. EA7 Emporio Armani Milano vs Real Madrid (20:30)
    engine.add_match(OFPBasketMatch(
        match="EA7 Emporio Armani Milano vs Real Madrid",
        kickoff="13-10 20:30",
        tournament="Turkish Airlines EuroLeague",
        moneyline={"1": 2.05, "2": 1.80},
        book_spread="Milano +2.5 / Real -2.5",
        book_total=163.5,
        oddspedia_sentiment="Quote in perfetto equilibrio, leggero favore pubblico per Milano al Forum",
        forebet_pred_score="82 - 79",
        forebet_win_prob={"1": 53, "2": 47},
        forebet_total_pred=161.0,
        h2h_trend="La squadra di casa ha vinto gli ultimi 7 precedenti consecutivi tra Milano e Real Madrid",
        tactical_edge="Real Madrid ancora a secco fuori casa (0-3 in trasferta in Europa). Moses Wright in grande ascesa",
        convergence_grade="AAA",
        recommended_spread="Milano +4.5 Handicap",
        recommended_safe="Milano +6.5 Handicap (oppure Under 167.5)",
        target_odds=1.50,
        confidence="ALTA"
    ))

    # 2. Fenerbahce vs Zalgiris Kaunas (19:45)
    engine.add_match(OFPBasketMatch(
        match="Fenerbahçe vs Žalgiris Kaunas",
        kickoff="13-10 19:45",
        tournament="Turkish Airlines EuroLeague",
        moneyline={"1": 1.33, "2": 3.40},
        book_spread="Fenerbahçe -6.5 / Zalgiris +6.5",
        book_total=158.5,
        oddspedia_sentiment="Forte fiducia sul Fenerbahce in casa, quote T/T in calo",
        forebet_pred_score="83 - 73",
        forebet_win_prob={"1": 76, "2": 24},
        forebet_total_pred=156.0,
        h2h_trend="Fenerbahce 3-0 in casa in questo avvio di stagione",
        tactical_edge="Difesa di Jasikevicius tra le piu ermetiche della lega (concede < 74 punti al Forum turco)",
        convergence_grade="AAA",
        recommended_spread="Fenerbahçe 1 T/T (oppure -3.5 Handicap)",
        recommended_safe="Fenerbahçe 1 T/T",
        target_odds=1.33,
        confidence="ALTA"
    ))

    # 3. ASVEL Villeurbanne vs Stella Rossa Belgrado (20:00)
    engine.add_match(OFPBasketMatch(
        match="ASVEL Villeurbanne vs Stella Rossa",
        kickoff="13-10 20:00",
        tournament="Turkish Airlines EuroLeague",
        moneyline={"1": 2.25, "2": 1.65},
        book_spread="ASVEL +3.5 / Stella Rossa -3.5",
        book_total=161.5,
        oddspedia_sentiment="Stella Rossa favorita esterna grazie alla superiorita a rimbalzo",
        forebet_pred_score="77 - 82",
        forebet_win_prob={"1": 38, "2": 62},
        forebet_total_pred=159.0,
        h2h_trend="ASVEL in difficolta strutturale e con rotazioni corte",
        tactical_edge="Stella Rossa piu profonda e solida nei finali punto a punto",
        convergence_grade="AA",
        recommended_spread="Stella Rossa 2 T/T",
        recommended_safe="Stella Rossa +3.5 Handicap",
        target_odds=1.40,
        confidence="MEDIA"
    ))

    # 4. Partizan Belgrado vs Panathinaikos (20:30)
    engine.add_match(OFPBasketMatch(
        match="Partizan Belgrado vs Panathinaikos",
        kickoff="13-10 20:30",
        tournament="Turkish Airlines EuroLeague",
        moneyline={"1": 2.30, "2": 1.62},
        book_spread="Partizan +3.5 / Panathinaikos -3.5",
        book_total=164.5,
        oddspedia_sentiment="Panathinaikos campione in carica, ma la Stark Arena di Belgrado e un fattore decisivo",
        forebet_pred_score="81 - 83",
        forebet_win_prob={"1": 46, "2": 54},
        forebet_total_pred=164.0,
        h2h_trend="Partite a Belgrado sempre decise negli ultimi 60 secondi",
        tactical_edge="Obradovic prepara trappole difensive su Nunn e Sloukas. Gara da molti falli",
        convergence_grade="AA",
        recommended_spread="Partizan +6.5 Handicap",
        recommended_safe="Partizan +7.5 Handicap",
        target_odds=1.45,
        confidence="MEDIA"
    ))

    return engine


if __name__ == "__main__":
    eng = build_today_euroleague_ofp()
    print(f"Caricate {len(eng.matches)} gare di Eurolega con incrocio OFP Basket.")
    for m in eng.matches:
        print(f"[{m.convergence_grade}] {m.match} -> Pick: {m.recommended_spread} (Safe: {m.recommended_safe} @ {m.target_odds})")
