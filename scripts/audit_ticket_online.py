#!/usr/bin/env python3
"""
scripts/audit_ticket_online.py — Audit Istantaneo Schedina via Groq Cloud (0€, Online).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.debate.groq_auditor import GroqAuditor


PRESET_TICKETS = {
    "raddoppio": {
        "title": "Raddoppio Protetto Sudamerica",
        "legs": [
            {
                "match_name": "Fluminense vs Coritiba",
                "tournament": "Brasileirao Serie A",
                "market": "Chance Mix: X2 o Gol",
                "book_odd": 1.53,
                "fair_odd": 1.33,
                "probability": 0.750,
                "edge": 0.147,
                "sixth_sense": "Doppia via di fuga (risultato X2 o BTTS)"
            },
            {
                "match_name": "Sarmiento Junin vs River Plate",
                "tournament": "Primera Division Argentina",
                "market": "MultiGol 0-1 Ospite",
                "book_odd": 1.71,
                "fair_odd": 1.29,
                "probability": 0.773,
                "edge": 0.321,
                "sixth_sense": "Sarmiento blocco a 5; River soffre trasferte chiuse"
            }
        ]
    },
    "tripla": {
        "title": "Tripla Blindata Sudamerica",
        "legs": [
            {
                "match_name": "Clube Do Remo vs Gremio",
                "tournament": "Brasileirao Serie A",
                "market": "MultiGol 0-1 1° Tempo",
                "book_odd": 1.66,
                "fair_odd": 1.31,
                "probability": 0.762,
                "edge": 0.265,
                "sixth_sense": "Avvio diesel; 0-0/1-0 all'intervallo frequente"
            },
            {
                "match_name": "Ec Vitoria Ba vs Chapecoense Sc",
                "tournament": "Brasileirao Serie A",
                "market": "MultiGol 0-1 1° Tempo",
                "book_odd": 1.65,
                "fair_odd": 1.30,
                "probability": 0.769,
                "edge": 0.269,
                "sixth_sense": "Fase di studio; ritmi blandi primo tempo"
            },
            {
                "match_name": "Palmeiras vs Bahia Ba",
                "tournament": "Brasileirao Serie A",
                "market": "MultiGol 0-2 Casa",
                "book_odd": 1.38,
                "fair_odd": 1.20,
                "probability": 0.833,
                "edge": 0.150,
                "sixth_sense": "Palmeiras corto muso; gestione vantaggio"
            }
        ]
    }
}


def main():
    parser = argparse.ArgumentParser(description="Audit online a costo zero con Groq Cloud")
    parser.add_argument("--preset", choices=list(PRESET_TICKETS.keys()), default="raddoppio", help="Preset ticket da analizzare")
    parser.add_argument("--json-file", help="File JSON contenente un ticket personalizzato")
    parser.add_argument("--model", default="openai/gpt-oss-120b", help="Modello Groq da utilizzare")
    args = parser.parse_args()

    auditor = GroqAuditor(model=args.model)
    if not auditor.is_configured():
        print("Errore: GROQ_API_KEY mancante nel file .env!")
        sys.exit(1)

    if args.json_file:
        ticket_data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    else:
        ticket_data = PRESET_TICKETS[args.preset]

    print(f"\n🚀 Invio ticket a Groq Cloud [{args.model}] per audit indipendente...")
    result = auditor.audit_ticket(ticket_data["title"], ticket_data["legs"], model=args.model)

    if not result.get("success"):
        print(f"❌ Fallito: {result.get('error')}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print(f"🏛️ AUDIT REPORT GROQ CLOUD — Modello: {result['model_used']}")
    print(f"🎯 Ticket: {ticket_data['title']} (Quota: {result['total_odd']})")
    print("=" * 70)
    print(result["critique"])
    print("=" * 70)


if __name__ == "__main__":
    main()
