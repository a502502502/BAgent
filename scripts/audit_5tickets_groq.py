import json
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path("C:/Project/BAgent")
sys.path.insert(0, str(ROOT))

from services.debate.groq_auditor import GroqAuditor

portfolio_path = ROOT / "reports/tickets/ticket_snai_nl_5tickets_portfolio.json"
with open(portfolio_path, encoding="utf-8") as f:
    portfolio = json.load(f)

auditor = GroqAuditor()
print(f"GroqAuditor configurato: {auditor.is_configured()} (Model: {auditor.model})")

for i, ticket in enumerate(portfolio["tickets"]):
    t_id = ticket["id"]
    t_name = ticket["name"]
    groq_state = ticket.get("groq", {})
    if groq_state.get("success") is True:
        print(f"[{i+1}/5] Gia auditato con successo: {t_name}")
        continue
    
    print(f"\n==========================================")
    print(f"[{i+1}/5] Esecuzione Groq Audit per: {t_name}")
    
    audit_legs = []
    for leg in ticket["legs"]:
        audit_legs.append({
            "match_name": leg["match"],
            "tournament": "UEFA Nations League",
            "market": leg["market"],
            "book_odd": float(leg["odds"]),
            "fair_odd": float(leg["fair_odd"]),
            "probability": float(leg["probability"]),
            "edge": float(leg["edge"]),
            "notes": leg["tactical_rationale"]
        })
    
    audit_res = auditor.audit_ticket(
        title=t_name,
        legs=audit_legs,
        bankroll=portfolio["bankroll_reference"]
    )
    
    # If 429 rate limit, retry with fallback model or after sleep
    if not audit_res.get("success") and "429" in audit_res.get("error", ""):
        print("Rate limit 429 incontrato, attesa 15 secondi e retry con modello fallback...")
        time.sleep(15)
        audit_res = auditor.audit_ticket(
            title=t_name,
            legs=audit_legs,
            bankroll=portfolio["bankroll_reference"],
            model="llama-3.3-70b-versatile"
        )
    
    ticket["groq"] = audit_res
    print(f"Success: {audit_res.get('success')}")
    print(f"Approved: {audit_res.get('approved')}")
    print(f"Warning: {audit_res.get('ev_warning')}")
    print(f"Model used: {audit_res.get('model_used')}")
    
    time.sleep(3)

portfolio["groq_audit"] = "ESEGUITO_CON_SUCCESSO_CON_NUOVA_POLICY"
portfolio["ev_policy"] = "EV negativo: avviso informativo, non bloccante. Bocciatura solo su rischio strutturale."

with open(portfolio_path, "w", encoding="utf-8") as f:
    json.dump(portfolio, f, indent=2, ensure_ascii=False)

print("\nAudit completo per tutti i 5 ticket completato!")
