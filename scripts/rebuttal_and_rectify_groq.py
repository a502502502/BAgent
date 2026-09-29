import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from services.debate.groq_auditor import GroqAuditor

auditor = GroqAuditor()

rectified_tickets = [
    {
        "title": "Schedina 1 (Rettificata) — Raddoppio Paracadute Catenaccio Argentina",
        "legs": [
            {
                "match_name": "Defensa Y Justicia vs San Lorenzo",
                "tournament": "Primera Division Argentina (03/10 19:45 CEST)",
                "market": "Combo: 1X + Under 3.5",
                "book_odd": 1.50,
                "fair_odd": 1.35,
                "probability": 0.74,
                "edge": 0.111,
                "notes": "Accolta obiezione Groq su Under 2.5 secco: inserito paracadute Under 3.5 unito a 1X interno. Copre 0-0, 1-0, 2-0, 1-1, 2-1, 3-0."
            },
            {
                "match_name": "Atletico Tucuman vs Barracas Central",
                "tournament": "Primera Division Argentina (03/10 22:00 CEST)",
                "market": "Combo: 1X + Under 3.5",
                "book_odd": 1.40,
                "fair_odd": 1.26,
                "probability": 0.79,
                "edge": 0.106,
                "notes": "Accolta obiezione Groq: protezione estesa a Under 3.5 + 1X Tucuman in casa (imbattuto da 8 turni). Barracas non segna quasi mai 2 gol fuori casa."
            }
        ]
    },
    {
        "title": "Schedina 3 (Rettificata) — Raddoppio Blindato Bombonera & Galo",
        "legs": [
            {
                "match_name": "Boca Juniors vs Union Santa Fe",
                "tournament": "Primera Division Argentina (03/10 02:30 CEST)",
                "market": "Chance Mix: NoGol o Under 2.5",
                "book_odd": 1.32,
                "fair_odd": 1.20,
                "probability": 0.835,
                "edge": 0.102,
                "notes": "Bombonera roccaforte difensiva del Boca. Vince con qualsiasi NoGol (0-0, 1-0, 2-0, 0-1) o con qualsiasi Under 2.5."
            },
            {
                "match_name": "Atletico Mineiro Mg vs Bragantino Sp",
                "tournament": "Brasile Serie A (03/10 23:30 CEST)",
                "market": "Combo: 1X + Under 3.5",
                "book_odd": 1.58,
                "fair_odd": 1.38,
                "probability": 0.725,
                "edge": 0.145,
                "notes": "Accolta obiezione Groq: eliminato il rischioso derby San-Sao e ridotto a 2 eventi. Inserita Combo 1X + Under 3.5 per il Galo all'Arena MRV."
            }
        ]
    }
]

for t in rectified_tickets:
    print(f"\n========================================================")
    print(f"RE-AUDITING RECTIFIED: {t['title']}")
    res = auditor.audit_ticket(t['title'], t['legs'], bankroll=37.32)
    print(f"Success: {res.get('success')} | Approved: {res.get('approved')}")
    print(f"Model used: {res.get('model_used')}")
    print("CRITIQUE:")
    print(res.get("critique"))
