"""
services/quant/gem_scanner_engine.py — Scanner Universale di Gemme Matematiche (Stile BetBurger / RebelBetting).

Confronta ogni quota offerta dal catalogo reale di un bookmaker retail (es. Netwin, SNAI)
contro il Fair Benchmark sintetico derivato dal mercato privo di aggio (Shin De-vigging).
Identifica e classifica:
- Pure Value Bets (Edge >= +4% rispetto alla quota Fair Sharp)
- Sweet-Spot Value Gems (alta probabilità 72-88% con quota errata/sbilanciata)
- Lag Anomalies (quote lente a recepire i movimenti di mercato)
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from services.quant.sharp_synthetic_benchmark import SyntheticBenchmarkEngine, SharpMarketBenchmark
from services.analysis.statistical_combo import statistical_score, structural_block


@dataclass
class ValueGem:
    match_name: str
    kickoff: str
    market: str
    selection: str
    book_odd: float
    fair_odd: float
    probability: float
    edge: float
    score: float
    gem_type: str
    recommended_stake_pct: float
    verdict: str
    notes: str


class GemScannerEngine:
    """Motore di scansione e rilevamento gemme matematiche su palinsesti completi."""

    def __init__(self, benchmark_engine: Optional[SyntheticBenchmarkEngine] = None):
        self.benchmark_engine = benchmark_engine or SyntheticBenchmarkEngine()

    def scan_match_catalog(
        self,
        match_name: str,
        kickoff: str,
        catalog_markets: List[Dict[str, Any]],
        primary_1x2: Optional[tuple[float, float, float]] = None,
        primary_uo25: Optional[tuple[float, float]] = None
    ) -> List[ValueGem]:
        """Scansiona tutti i mercati di una partita alla ricerca di discrepanze di valore (Gemme)."""
        # Se non fornite, estrai 1X2 e U/O 2.5 dal catalogo stesso
        odds_1x2 = primary_1x2
        odds_uo25 = primary_uo25

        for m in catalog_markets:
            m_name = f"{m.get('market', '')} {m.get('line', '')}".strip()
            if not odds_1x2 and ("esito finale 1x2" in m_name.lower() or m_name.lower() == "1x2"):
                out_map = {str(o.get("selection", "")).strip(): float(o.get("odds", 0.0)) for o in m.get("outcomes", [])}
                if "1" in out_map and "X" in out_map and "2" in out_map:
                    odds_1x2 = (out_map["1"], out_map["X"], out_map["2"])

            if not odds_uo25 and ("u/o 2.5" in m_name.lower() or "under / over 2.5" in m_name.lower()):
                out_map = {str(o.get("selection", "")).upper().strip(): float(o.get("odds", 0.0)) for o in m.get("outcomes", [])}
                if "UNDER" in out_map and "OVER" in out_map:
                    odds_uo25 = (out_map["UNDER"], out_map["OVER"])

        if not odds_1x2 or not odds_uo25:
            # Fallback quote standard di default se non presenti
            odds_1x2 = odds_1x2 or (2.20, 3.20, 3.20)
            odds_uo25 = odds_uo25 or (1.80, 1.95)

        # Genera il Benchmark sintetico de-viggato
        benchmark = self.benchmark_engine.build_benchmark_from_primary_odds(
            match_name=match_name,
            odds_1x2=odds_1x2,
            odds_uo25=odds_uo25
        )

        gems: List[ValueGem] = []

        for m in catalog_markets:
            m_name = f"{m.get('market', '')} {m.get('line', '')}".strip()
            for o in m.get("outcomes", []):
                sel = str(o.get("selection", "")).strip()
                b_odd = float(o.get("odds", 0.0))
                if b_odd < 1.20 or b_odd > 2.60:
                    continue

                # Calcola probabilità FAIR reale con la matrice bivariata
                fair_prob = self.benchmark_engine.price_derived_market(benchmark, m_name, sel)
                if fair_prob <= 0.05 or fair_prob >= 0.95:
                    continue

                fair_odd = benchmark.get_fair_odd(fair_prob)
                edge = (b_odd * fair_prob) - 1.0

                # Verifica se si tratta di una gemma con Edge positivo o all'interno dello Sweet-Spot
                if edge >= 0.035:  # Almeno +3.5% di valore matematico puro
                    score = statistical_score(fair_prob, b_odd)
                    blocked = structural_block(
                        m_name,
                        xg_home=benchmark.lambda_home,
                        xg_away=benchmark.lambda_away
                    )
                    if blocked:
                        continue

                    # Calcolo stake frazionario di Kelly (1/4 Kelly conservativo)
                    b = b_odd - 1.0
                    q = 1.0 - fair_prob
                    f_star = max(0.0, (b * fair_prob - q) / b)
                    recommended_stake_pct = round(min(0.04, f_star * 0.25) * 100, 1)

                    gem_type = "PURE_SHARP_VALUE"
                    if 0.72 <= fair_prob <= 0.88 and 1.30 <= b_odd <= 1.65:
                        gem_type = "SWEET_SPOT_GOLD_GEM"
                    elif "tempo" in m_name.lower():
                        gem_type = "ASYMMETRIC_HALF_TIME_LAG"

                    verdict = "stella" if edge >= 0.05 else "occhio"

                    gems.append(
                        ValueGem(
                            match_name=match_name,
                            kickoff=kickoff,
                            market=m_name,
                            selection=sel,
                            book_odd=b_odd,
                            fair_odd=fair_odd,
                            probability=round(fair_prob, 3),
                            edge=round(edge, 3),
                            score=round(score, 3),
                            gem_type=gem_type,
                            recommended_stake_pct=recommended_stake_pct,
                            verdict=verdict,
                            notes=f"Fair Odd Sharp: {fair_odd} | Quota Banco: {b_odd} | Vantaggio: {edge*100:+.1f}%"
                        )
                    )

        # Ordina le gemme per Edge decrescente e Score gaussiano
        gems.sort(key=lambda g: (g.score, g.edge), reverse=True)
        return gems
