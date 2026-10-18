#!/usr/bin/env python3
"""
scripts/parse_and_ingest_telegram_archive.py — Parser e Ingestion Batch delle Scommesse Telegram in BAgent.

Prende l'output JSON prodotto da ocr_batch_runner (data/telegram_all_ocr.json),
effettua il parsing semantico di ogni schedina, associa mercati, quote, date ed esiti,
e popola il database bagent.db (tabelle tipster_tickets, tipster_legs e market_family_stats).
"""

from __future__ import annotations
import sys
import os
import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.tipster_intelligence import (
    TipsterIntelligenceEngine,
    TipsterTicketInput,
    TipsterLegInput,
    classify_market_family,
    CANONICAL_FAMILIES
)
from services.database.schema import DB_PATH

DATE_REGEX = re.compile(r'(\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2})')
ODDS_REGEX = re.compile(r'(?:quota\s*[:=]?\s*|@\s*)(\d+[\.,]\d{2})', re.IGNORECASE)


def parse_odds_value(text: str) -> Optional[float]:
    m = ODDS_REGEX.search(text)
    if m:
        try:
            return float(m.group(1).replace(',', '.'))
        except:
            return None
    return None


def parse_ticket_from_blocks(file_path: str, blocks: List[Dict[str, Any]], tipster_name: str = "Il Fenomeno") -> Optional[TipsterTicketInput]:
    """Analizza i blocchi OCR di un'immagine ed estrae un ticket e le sue selezioni."""
    if not blocks:
        return None

    # Verifica se compare il timbro "YES", "CASSA", "PRESA", "BOOM", "VINCENTE"
    has_global_yes = any(
        b["text"].strip().upper() in ["YES", "CASSA", "PRESA", "BOOM", "VINTA", "VINCENTE"] 
        or "CASSA" in b["text"].upper() 
        for b in blocks
    )

    # Identifica le selezioni basate sul formato standard Goldbet/Lottomatica/SNAI
    # Struttura tipica a blocchi:
    # 1. Data e ora (es. 04/01/2025 13:30)
    # 2. Squadre (es. TOTTENHAM - NEWCASTLE UNITED)
    # 3. Torneo (es. Inghilterra | Premier League)
    # 4. Mercato e Quota (es. TOT. ANGOLI (5 ESITI) : 15 o + Quota : 4.80)
    
    legs: List[TipsterLegInput] = []
    
    # Raccogliamo gli indici dei blocchi contenenti una data/ora
    date_indices = []
    for i, b in enumerate(blocks):
        txt = b["text"].strip()
        if DATE_REGEX.search(txt):
            date_indices.append(i)

    if date_indices:
        for idx_pos, start_i in enumerate(date_indices):
            end_i = date_indices[idx_pos + 1] if idx_pos + 1 < len(date_indices) else len(blocks)
            leg_blocks = blocks[start_i:end_i]
            
            # 1. Kickoff
            date_match = DATE_REGEX.search(leg_blocks[0]["text"])
            kickoff_str = date_match.group(1) if date_match else "01/01/2025 00:00"
            
            # 2. Match Name & Tournament
            match_name = ""
            tournament = ""
            market_lines = []
            odds_val = None
            leg_has_yes = False
            
            for b in leg_blocks[1:]:
                btxt = b["text"].strip()
                if btxt.upper() in ["YES", "VINTA", "OK"]:
                    leg_has_yes = True
                    continue
                if "|" in btxt and not tournament:
                    tournament = btxt
                    continue
                if (" - " in btxt or " VS " in btxt.upper()) and not match_name and not any(k in btxt.lower() for k in ["quota", "u/o", "gol"]):
                    match_name = btxt
                    continue
                    
                # Mercato & Quota
                o = parse_odds_value(btxt)
                if o:
                    odds_val = o
                market_lines.append(btxt)
                
            if match_name and (odds_val or market_lines):
                market_desc = " ".join(market_lines)
                if not odds_val:
                    odds_val = parse_odds_value(market_desc) or 1.50
                
                # Pulizia mercato
                market_desc = ODDS_REGEX.sub('', market_desc).strip(' :-,')
                if not market_desc:
                    market_desc = "Mercato Combinato"
                    
                outcome = "WON" if (leg_has_yes or has_global_yes) else "LOST"
                
                legs.append(TipsterLegInput(
                    match_name=match_name,
                    tournament=tournament or "Campionato",
                    kickoff_time=kickoff_str,
                    market_name=market_desc[:120],
                    odds=odds_val,
                    outcome=outcome
                ))

    # Formato alternativo: locandine grafiche ("LA MULTIPLA MISTA", quote riassuntive, ecc.)
    if not legs:
        # Cerca righe con "MATCH" e "MERCATO"
        for i, b in enumerate(blocks):
            txt = b["text"].strip()
            if " - " in txt and len(txt) > 6 and not any(k in txt.lower() for k in ["quota", "totale", "week"]):
                # Trovato possibile match
                match_cand = txt
                # Cerca mercato nelle righe successive vicine come Y
                market_cand = ""
                odds_cand = 1.50
                for j in range(max(0, i - 2), min(len(blocks), i + 4)):
                    if j == i: continue
                    other_txt = blocks[j]["text"].strip()
                    if any(m in other_txt.upper() for m in ["OVER", "UNDER", "GOL", "1X", "X2", "1", "2", "HANDICAP"]):
                        market_cand = other_txt
                        break
                if market_cand:
                    legs.append(TipsterLegInput(
                        match_name=match_cand,
                        tournament="Multipla Fenomeno",
                        kickoff_time="2025-01-01 15:00",
                        market_name=market_cand,
                        odds=odds_cand,
                        outcome="WON" if has_global_yes else "LOST"
                    ))

    if not legs:
        return None

    # Calcola quota totale
    tot_odds = 1.0
    for leg in legs:
        tot_odds *= leg.odds
    tot_odds = round(tot_odds, 2)
    
    ticket_status = "WON" if has_global_yes else "LOST"
    
    # Estrai data dal nome del file se possibile: photo_1000@04-01-2025_14-50-16.jpg
    file_stem = Path(file_path).stem
    date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', file_stem)
    ticket_date = date_match.group(1) if date_match else "2025-01-01"
    
    return TipsterTicketInput(
        tipster_name=tipster_name,
        ticket_date=ticket_date,
        total_odds=tot_odds,
        status=ticket_status,
        source=Path(file_path).name,
        legs=legs
    )


def run_pipeline(ocr_json_path: str = "data/telegram_all_ocr.json", tipster_name: str = "Il Fenomeno"):
    print("=" * 75)
    print(f"🧠 BAGENT DEEP HISTORICAL INGESTION — {tipster_name.upper()}")
    print("=" * 75)
    
    if not os.path.exists(ocr_json_path):
        print(f"❌ File OCR non ancora presente: {ocr_json_path}")
        return

    with open(ocr_json_path, "r", encoding="utf-8") as fp:
        raw_data = json.load(fp)

    print(f"📦 Immagini lette da OCR cache: {len(raw_data)}")
    
    engine = TipsterIntelligenceEngine()
    total_tickets = 0
    total_legs = 0
    won_legs = 0
    lost_legs = 0
    
    family_counter = {}

    for file_path, blocks in raw_data.items():
        ticket = parse_ticket_from_blocks(file_path, blocks, tipster_name=tipster_name)
        if not ticket or not ticket.legs:
            continue
            
        try:
            t_id = engine.ingest_ticket(ticket)
            total_tickets += 1
            total_legs += len(ticket.legs)
            for leg in ticket.legs:
                fam = classify_market_family(leg.market_name)
                family_counter[fam] = family_counter.get(fam, 0) + 1
                if leg.outcome == "WON":
                    won_legs += 1
                else:
                    lost_legs += 1
        except Exception as e:
            pass

    print(f"\n✅ Ingestion completata con successo!")
    print(f"🎟️ Schedine totali estratte e salvate: {total_tickets}")
    print(f"⚽ Selezioni/Gambe totali indicizzate: {total_legs}")
    print(f"🏆 Selezioni Vincenti: {won_legs} | ❌ Selezioni Perdenti: {lost_legs}")
    
    print("\n📊 DISTRIBUZIONE FAMIGLIE DI MERCATO RICONOSCIUTE:")
    print("-" * 75)
    for fam, cnt in sorted(family_counter.items(), key=lambda x: x[1], reverse=True):
        fam_info = CANONICAL_FAMILIES.get(fam, {"name": fam})
        print(f"  • {fam:25} | {fam_info.get('name', fam):40} : {cnt:4d} selezioni")

    # Mostra la matrice di efficacia mercati aggiornata
    print("\n🔄 Estrazione Matrice di Efficacia Mercati (Market Efficacy Weights)...")
    summary = engine.get_intelligence_summary()
    
    print("\n🏆 CLASSIFICA AGGIORNATA EFFICACY WEIGHTS IN BAGENT DB:")
    print("=" * 85)
    print(f"{'FAMIGLIA':25} | {'BETS':6} | {'WIN %':7} | {'AVG QTA':7} | {'ROI %':7} | {'EFFICACY'}")
    print("-" * 85)
    for row in summary:
        fam = row.get("market_family", "")
        tot = row.get("total_bets", 0)
        wr = row.get("win_rate", 0.0)
        avg_q = row.get("avg_odds", 0.0)
        roi = row.get("empirical_roi", 0.0)
        eff = row.get("efficacy_weight", 1.0)
        print(f"{fam:25} | {tot:6d} | {wr*100:6.1f}% | {avg_q:7.2f} | {roi*100:6.1f}% | {eff:7.3f}x")
    print("=" * 85)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/telegram_all_ocr.json"
    name = sys.argv[2] if len(sys.argv) > 2 else "Il Fenomeno"
    run_pipeline(path, tipster_name=name)
