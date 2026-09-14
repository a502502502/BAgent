import json, os, datetime

input_path = r'C:\Users\demarj\.gemini\antigravity\brain\92ce61bf-f59b-42f9-bf87-0b12201a9eda\.system_generated\logs\transcript.jsonl'
output_path = r'C:\Users\demarj\.gemini\antigravity\scratch\BAgent\docs\CONVERSAZIONE_COMPLETA_14_SETTEMBRE_2026.md'

header = """# 📜 TRASCRIZIONE COMPLETA CONVERSAZIONE BAGENT (14 SETTEMBRE 2026)

> **Session ID**: 92ce61bf-f59b-42f9-bf87-0b12201a9eda  
> **Data e Ora Esportazione**: 14 Settembre 2026 - 19:15 CEST  
> **Oggetto**: Export completo cronologico per ripresa sessione su nuovo PC  

---
"""

with open(input_path, 'r', encoding='utf-8', errors='replace') as infile, open(output_path, 'w', encoding='utf-8') as outfile:
    outfile.write(header + '\n')
    count = 0
    for line in infile:
        if not line.strip():
            continue
        try:
            step = json.loads(line)
            stype = step.get('type', '')
            source = step.get('source', '')
            created = step.get('created_at', '')
            content = step.get('content', '')
            
            if stype == 'USER_INPUT':
                outfile.write(f"\n\n## 👤 UTENTE ({created})\n\n")
                outfile.write(content.strip() + "\n\n---\n")
                count += 1
            elif stype == 'PLANNER_RESPONSE':
                # only output the text response if present
                if content:
                    outfile.write(f"\n\n## 🤖 BAGENT ({created})\n\n")
                    outfile.write(content.strip() + "\n\n---\n")
                    count += 1
        except Exception as e:
            continue

print(f"Esportati {count} passaggi conversazionali in {output_path}")
