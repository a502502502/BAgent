#!/usr/bin/env python3
"""
scripts/scan_live_gems.py — CLI Scanner di Gemme Matematiche (Stile BetBurger).

Carica i cataloghi quote ufficiali (SNAI e Netwin), applica il modello di Shin De-vigging
e cerca tutte le quote disallineate con Edge matematico positivo (Value Bets).
Stampa una dashboard chiara e salva il report in reports/tickets/live_value_gems.json.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.quant.gem_scanner_engine import GemScannerEngine
from services.quant.sharp_synthetic_benchmark import SyntheticBenchmarkEngine


def main():
    print("==================================================================")
    print("💎 BAGENT QUANT GEM SCANNER — VALUE BETTING ENGINE (BETBURGER STYLE)")
    print("==================================================================\n")

    scanner = GemScannerEngine()

    # 1. Scansiona i cataloghi SNAI
    snai_dir = ROOT / "reports/snai"
    all_gems = []

    print("[1/2] Scansione cataloghi SNAI per rilevamento quote disallineate...")
    if snai_dir.exists():
        for f in snai_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                m_name = data.get("match", f.stem)
                kickoff = data.get("kickoff_time", "")
                markets = data.get("markets", [])
                gems = scanner.scan_match_catalog(m_name, kickoff, markets)
                if gems:
                    all_gems.extend(gems)
                    print(f"  - {m_name}: Trovate {len(gems)} gemme matematiche")
            except Exception as e:
                pass

    # 2. Scansiona snapshot Netwin se presente
    netwin_nl = ROOT / "reports/tickets/netwin_nl_markets_20261006.json"
    if netwin_nl.exists():
        print("\n[2/2] Scansione catalogo ufficiale Netwin...")
        from scripts.build_netwin_tactical_portfolio import normalize_netwin_markets
        with open(netwin_nl, "r", encoding="utf-8") as fp:
            nw_data = json.load(fp)
        for m in nw_data.get("matches", []):
            m_name = m.get("match_name")
            kickoff = m.get("kickoff")
            cat_mkts = normalize_netwin_markets(m.get("markets", {}))
            gems = scanner.scan_match_catalog(m_name, kickoff, cat_mkts)
            if gems:
                all_gems.extend(gems)
                print(f"  - [Netwin] {m_name}: Trovate {len(gems)} gemme matematiche")

    # Ordina complessivamente tutte le gemme
    all_gems.sort(key=lambda g: (g.score, g.edge), reverse=True)

    print(f"\n==================== TOP GEMME IDENTIFICATE ({len(all_gems)} TOTALI) ====================")
    top_gems = all_gems[:15]
    for i, g in enumerate(top_gems, 1):
        print(f"\n[{i}] {g.match_name} ({g.kickoff})")
        print(f"    🎯 Mercato: {g.market} [{g.selection}]")
        print(f"    📈 Quota Banco: {g.book_odd} vs Quota Fair Sharp: {g.fair_odd} | Vantaggio: {g.edge*100:+.1f}% ({g.verdict.upper()})")
        print(f"    💎 Categoria: {g.gem_type} | Probabilità Reale: {g.probability*100:.1f}% | Stake Kelly: {g.recommended_stake_pct}%")

    out_file = ROOT / "reports/tickets/live_value_gems.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump([g.__dict__ for g in all_gems], fp, indent=2, ensure_ascii=False)
    print(f"\n✅ Report salvato con successo in {out_file}!")


if __name__ == "__main__":
    main()
