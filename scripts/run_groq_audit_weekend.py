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
print(f"Groq Auditor configured: {auditor.is_configured()}")

tickets = [
    {
        "title": "Schedina 1 — Raddoppio Catenaccio Argentina",
        "legs": [
            {
                "match_name": "Defensa Y Justicia vs San Lorenzo",
                "tournament": "Primera Division Argentina (03/10 19:45 CEST)",
                "market": "Under 2.5",
                "book_odd": 1.43,
                "fair_odd": 1.32,
                "probability": 0.757,
                "edge": 0.083,
                "notes": "Blocco difensivo San Lorenzo (0.75 gol concessi/match) e xG combinato < 1.95."
            },
            {
                "match_name": "Atletico Tucuman vs Barracas Central",
                "tournament": "Primera Division Argentina (03/10 22:00 CEST)",
                "market": "Under 2.5",
                "book_odd": 1.38,
                "fair_odd": 1.17,
                "probability": 0.852,
                "edge": 0.176,
                "notes": "Tucuman fortino in casa, Barracas sterile in trasferta (0.6 gol/match). Storico 88% Under."
            }
        ]
    },
    {
        "title": "Schedina 2 — Tripla Tattica Weekend Sudamerica",
        "legs": [
            {
                "match_name": "Independiente vs Instituto Cordoba",
                "tournament": "Primera Division Argentina (03/10 00:15 CEST)",
                "market": "1X (Doppia Chance)",
                "book_odd": 1.32,
                "fair_odd": 1.24,
                "probability": 0.805,
                "edge": 0.063,
                "notes": "Independiente imbattuto in casa da 7 turni; Instituto in flessione offensiva."
            },
            {
                "match_name": "Argentinos Juniors vs Tigre",
                "tournament": "Primera Division Argentina (04/10 00:15 CEST)",
                "market": "MultiGol 0-1 1° Tempo",
                "book_odd": 1.41,
                "fair_odd": 1.25,
                "probability": 0.802,
                "edge": 0.130,
                "notes": "Fase di studio prolungata a La Paternal: 78% dei primi tempi chiusi 0-0 o 1-0."
            },
            {
                "match_name": "Talleres De Cordoba vs Belgrano",
                "tournament": "Primera Division Argentina (04/10 22:00 CEST)",
                "market": "MultiGol 0-1 1° Tempo",
                "book_odd": 1.43,
                "fair_odd": 1.27,
                "probability": 0.785,
                "edge": 0.123,
                "notes": "Clasico Cordobes ad altissima tensione agonistica, ritmi spezzettati nei primi 45'."
            }
        ]
    },
    {
        "title": "Schedina 3 — Tripla Nobile Notturna Sudamerica",
        "legs": [
            {
                "match_name": "Sao Paulo Fc Sp vs Santos Sp",
                "tournament": "Brasile Serie A (03/10 01:00 CEST)",
                "market": "1X (Doppia Chance)",
                "book_odd": 1.27,
                "fair_odd": 1.20,
                "probability": 0.830,
                "edge": 0.054,
                "notes": "Clasico San-Sao al Morumbi: Santos in forte affanno esterno, Sao Paulo imbattuto nelle ultime 6 uscite casalinghe."
            },
            {
                "match_name": "Boca Juniors vs Union Santa Fe",
                "tournament": "Primera Division Argentina (03/10 02:30 CEST)",
                "market": "Chance Mix: NoGol o Under 2.5",
                "book_odd": 1.32,
                "fair_odd": 1.20,
                "probability": 0.835,
                "edge": 0.102,
                "notes": "Alla Bombonera Boca solidissimo in retroguardia; vince con qualsiasi NoGol (0-0, 1-0, 2-0, 0-1, ecc.) o con qualsiasi Under 2.5."
            },
            {
                "match_name": "Atletico Mineiro Mg vs Bragantino Sp",
                "tournament": "Brasile Serie A (03/10 23:30 CEST)",
                "market": "1X (Doppia Chance)",
                "book_odd": 1.30,
                "fair_odd": 1.22,
                "probability": 0.820,
                "edge": 0.066,
                "notes": "Galo all'Arena MRV con netta superiorita tecnica e territoriale contro un Bragantino sterile fuori casa."
            }
        ]
    }
]

results = []
for t in tickets:
    print(f"\n---> Auditing: {t['title']}...")
    res = auditor.audit_ticket(t['title'], t['legs'], bankroll=37.32)
    print("Success:", res.get("success"))
    print("Approved:", res.get("approved"))
    print("Critique:\n", res.get("critique"))
    results.append({
        "title": t["title"],
        "result": res
    })

with open("reports/tickets/groq_audit_weekend_3tickets.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\nAudit completato e salvato in reports/tickets/groq_audit_weekend_3tickets.json")
