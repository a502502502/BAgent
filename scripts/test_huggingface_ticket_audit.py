#!/usr/bin/env python3
"""
scripts/test_huggingface_ticket_audit.py
Test di Validazione Completo con Hugging Face SportsBERT Semantic RAG + Strict Validator.
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.nlp.sports_semantic_rag import get_sports_semantic_rag
from services.betting.strict_ticket_pipeline import StrictTicketPipeline, MarketCandidate

def run_test():
    print("=" * 80)
    print("🧠 TEST INTEGRAZIONE HUGGING FACE SPORTSBERT + STRICT VALIDATOR")
    print("=" * 80)

    rag = get_sports_semantic_rag()
    pipeline = StrictTicketPipeline()

    # CASO 1: Trappola con rischio turnover celato nel testo (Trappola pre-coppa)
    print("\n[TEST 1: Rilevamento Trappola Nascosta da SportsBERT]")
    c_trap = MarketCandidate(
        match_name="Real Madrid F vs PSG F",
        tournament="UEFA Women Champions League",
        market_name="MultiGol 1-3 1°Tempo",
        bookmaker_odd=1.42,
        market_type="FIRST_HALF",
        is_first_half_only=True,
        is_intermediate_deadline=True,
        sixth_sense_analysis=(
            "Il tecnico nell'intervista ha preannunciato un ampio turnover tenendo a riposo "
            "le attaccanti titolari per gestire le energie, schierando le seconde linee. "
            "Partita che si prospetta molto bloccata e con ritmi lenti."
        ),
        estimated_p_1h=0.68,
        verified_sources_checked=True
    )

    # Analisi semantica NLP
    nlp_report = rag.audit_text_semantics(c_trap.sixth_sense_analysis)
    print(f"• Testo Analizzato: \"{c_trap.sixth_sense_analysis}\"")
    print(f"• Cluster Dominante NLP: {nlp_report['dominant_cluster']} (Score: {nlp_report['dominant_score']:.2f})")
    print(f"• Bandiere di Rischio Rilevate da SportsBERT: {nlp_report['flags']}")
    print(f"• Score Dettagliati: {nlp_report['scores']}")

    # Validazione Pipeline
    rep_trap = pipeline.validate_candidate(c_trap)
    print(f"• Esito Validator: {'🟢 APPROVATO' if rep_trap.passed else '🔴 BLOCCATO'}")
    if not rep_trap.passed:
        print(f"  Motivo Blocco: {rep_trap.rejection_reason}")

    # CASO 2: Schedina Certificata e Protetta (Green Light)
    print("\n" + "=" * 80)
    print("[TEST 2: Schedina Protetta con Certificazione Semantica Completa]")
    print("=" * 80)

    candidates_green = [
        MarketCandidate(
            match_name="Petrolul Ploiesti vs Csikszereda",
            tournament="Romania Superliga",
            market_name="1X (Doppia Chance In)",
            bookmaker_odd=1.23,
            market_type="DOUBLE_CHANCE",
            team_name="Petrolul Ploiesti",
            sixth_sense_analysis=(
                "Petrolul quarto in classifica ed imbattuto in casa con miglior difesa interna. "
                "Csikszereda fanalino di coda con un solo punto conquistato in nove giornate. "
                "Padroni di casa con motivazione alle stelle per i playoff."
            ),
            estimated_p_90=0.91,
            verified_sources_checked=True,
            verified_standings_delta=15
        ),
        MarketCandidate(
            match_name="Barracas Central vs Independiente Rivadavia",
            tournament="Argentina Liga Profesional",
            market_name="Under 3.0 Asiatico",
            bookmaker_odd=1.22,
            market_type="GOALS",
            sixth_sense_analysis=(
                "Match tipico del DNA argentino a logoramento difensivo. "
                "Barracas a secco di vittorie da sette turni gioca con baricentro bassissimo e catenaccio. "
                "Arbitra Lamolina, ritmo spezzettato e pochissimo tempo effettivo di gioco."
            ),
            estimated_p_90=0.92,
            verified_sources_checked=True
        ),
        MarketCandidate(
            match_name="Arsenal F vs HB Koge F",
            tournament="UEFA Women Champions League",
            market_name="1X + MultiGol 1-5",
            bookmaker_odd=1.26,
            market_type="COMBO",
            team_name="Arsenal F",
            sixth_sense_analysis=(
                "Arsenal nettamente superiore sul piano tecnico al Meadow Park contro le danesi dell'HB Koge. "
                "Inglesi con controllo totale del possesso palla e solida tenuta difensiva per blindare i 3 punti."
            ),
            estimated_p_90=0.90,
            verified_sources_checked=True
        )
    ]

    ticket_rep = pipeline.validate_ticket(candidates_green, current_bankroll=100.0, proposed_stake=8.0)
    print(f"\nSTATUS FINALE SCHEDINA: {'🟢 CERTIFICATO ED APPROVATO' if ticket_rep.passed else '🔴 BOCCIATO'}")
    print(f"• Numero Selezioni: {ticket_rep.num_selections}")
    print(f"• Quota Totale: @{ticket_rep.total_odds:.2f}")
    print(f"• Stake Consigliato: €{ticket_rep.recommended_stake:.2f} ({ticket_rep.stake_percentage:.1f}%)")

    for idx, r in enumerate(ticket_rep.legs_reports, 1):
        c = r.candidate
        nlp_c = rag.audit_text_semantics(c.sixth_sense_analysis)
        print(f"\n[SELEZIONE #{idx}] {c.match_name} ({c.tournament})")
        print(f"• Mercato: {c.market_name} @ {c.bookmaker_odd:.2f}")
        print(f"• NLP Dominant Cluster: {nlp_c['dominant_cluster']} (Score: {nlp_c['dominant_score']:.2f})")
        print(f"• Prob. Reale: {r.real_probability*100:.1f}% | Edge: {r.mathematical_edge*100:+.1f}%")
        print(f"• Esito: {'🟢 PASS' if r.passed else '🔴 FAIL'}")

if __name__ == "__main__":
    run_test()
