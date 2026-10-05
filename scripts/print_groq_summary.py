import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("reports/tickets/ticket_snai_nl_5tickets_portfolio.json", encoding="utf-8") as f:
    d = json.load(f)

print("=================================================================")
print("RISULTATI GROQ AUDIT CON LA NUOVA POLICY (EV COME WARNING)")
print("=================================================================\n")

for i, t in enumerate(d["tickets"], 1):
    g = t.get("groq", {})
    t_id = t["id"]
    name = t["name"]
    q_tot = t["total_odds"]
    appr = g.get("approved")
    warn = g.get("ev_warning")
    model = g.get("model_used")
    critique = g.get("critique", "")
    
    print(f"Ticket {i}: {name}")
    print(f"  - Quota totale: {q_tot} | Stake: 2.50 EUR | Bankroll: 100 EUR")
    print(f"  - Approvato: {'SI' if appr else 'NO'} | Modello: {model}")
    if warn:
        print(f"  - Avviso: {warn}")
    
    # Extract Verdetto finale from critique
    lines = [line.strip() for line in critique.split("\n") if line.strip()]
    verdetto_lines = []
    capture = False
    for line in lines:
        if "3. VERDETTO" in line.upper() or "VERDETTO FINALE" in line.upper() or "## 3." in line:
            capture = True
        if capture:
            verdetto_lines.append(line)
            if len(verdetto_lines) >= 6:
                break
    
    print("  - Sintesi Verdetto Groq:")
    if verdetto_lines:
        for vl in verdetto_lines[:4]:
            print(f"      {vl}")
    else:
        print(f"      {critique[-300:]}")
    print()
