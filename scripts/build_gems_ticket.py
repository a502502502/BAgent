import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from services.debate.groq_auditor import GroqAuditor

ROOT = Path(".")
p = Path("reports/snai_nl/catalog")

# Carica Croazia-Spagna
with open(p / "croazia---spagna.json", encoding="utf-8") as f:
    cro_spa = json.load(f)

# Carica Inghilterra-Rep. Ceca
with open(p / "inghilterra---repubblica-ceca.json", encoding="utf-8") as f:
    ing_cec = json.load(f)

gems = [
    {
        "match": "Croazia - Spagna",
        "category": "GOL O PALO ULTRA",
        "market": "Uno o l'Altro: Gol o Palo Ultra (Inc. TS)",
        "selection": "Matanovic I. o Yamal L. Goal o Palo (o loro Sostituti)",
        "odds": 1.50,
        "est_p": 0.74,
        "rationale": "Yamal terminale della Roja con media 1.3 tiri nello specchio e frequenti tiri a giro dal limite; Matanovic ariete d'area croato. La clausola SNAI copre sia il GOL sia il PALO/TRAVERSA di entrambi e dei rispettivi sostituti."
    },
    {
        "match": "Inghilterra - Repubblica Ceca",
        "category": "QUASI CARTELLINO / FALLI",
        "market": "Giocatore Quasi Cartellino (Inc. TS)",
        "selection": "Sadilek M. riceve almeno un cartellino O commette almeno 2 falli",
        "odds": 1.65,
        "est_p": 0.70,
        "rationale": "Sadilek mediano di rottura della Cechia, designato per fermare le transizioni centrali inglesi. La condizione vincente scatta con un'ammonizione OPPURE con soli 2 falli commessi in tutta la partita (media stagionale: 2.6 falli a match)."
    },
    {
        "match": "Croazia - Spagna",
        "category": "FALLI COMMESSI TEMPO",
        "market": "Giocatore Commette Almeno 1 Fallo nel 1° Tempo",
        "selection": "Cucurella M. commette almeno 1 fallo nel 1° Tempo",
        "odds": 1.70,
        "est_p": 0.68,
        "rationale": "Cucurella terzino sinistro spagnolo noto per l'aggressività asfissiante in anticipo. Nei primi 45 minuti affronta i duelli con Kramaric e Stanisic. È sufficiente un singolo fallo per incassare la quota a 1.70."
    },
    {
        "match": "Inghilterra - Repubblica Ceca",
        "category": "DUETTO TIRI IN PORTA",
        "market": "Duetto Tiri in Porta Ultra (Inc. TS)",
        "selection": "Kane H. e Hlozek A. (e Sostituti) almeno 3 tiri in porta in totale",
        "odds": 1.60,
        "est_p": 0.71,
        "rationale": "Kane festeggia la 125ª presenza da record ed è il fulcro di tutte le conclusioni inglesi (media 2.1 tiri nello specchio a gara). Hlozek principale terminale ceco nelle ripartenze. Bastano 3 tiri nello specchio sommati tra i due (e sostituti inclusi)."
    }
]

tot_odd = 1.0
tot_p = 1.0
for g in gems:
    tot_odd *= g["odds"]
    tot_p *= g["est_p"]

tot_odd = round(tot_odd, 2)
tot_p = round(tot_p, 3)
ev = round(tot_p * tot_odd - 1.0, 3)

print("==================================================================")
print(f"SCHEDINA GEMME NASCOSTE: PLAYER PROPS D'ELITE")
print(f"Quota Totale: {tot_odd} | Prob: {tot_p*100:.1f}% | EV: {ev*100:+.1f}%")
print("==================================================================")
for g in gems:
    print(f"• [{g['match']}] {g['market']}")
    print(f"  Selezione: {g['selection']} @ {g['odds']} (P: {g['est_p']*100:.1f}%)")
    print(f"  Rationale: {g['rationale']}\n")

# Audit Groq
auditor = GroqAuditor()
payload = [
    {
        "match_name": g["match"],
        "tournament": "UEFA Nations League",
        "market": f"{g['market']} - {g['selection']}",
        "book_odd": g["odds"],
        "fair_odd": round(1.0/g["est_p"], 2),
        "probability": g["est_p"],
        "edge": round(g["est_p"]*g["odds"] - 1.0, 3),
        "notes": g["rationale"]
    }
    for g in gems
]

res = auditor.audit_ticket("Schedina Gemme Nascoste Player Props", payload, bankroll=100.0)
print(f"Verdetto Groq: {'APPROVATA' if res.get('approved') else 'BOCCIATA'}")
print("Critique:")
print(res.get("critique"))

ticket_out = {
    "generated_at": "2026-10-06 13:40 CEST",
    "name": "Schedina Gemme Nascoste - Player Props & Speciali",
    "total_odds": tot_odd,
    "probability": tot_p,
    "ev": ev,
    "stake_eur": 3.0,
    "potential_payout_eur": round(3.0 * tot_odd, 2),
    "gems": gems,
    "groq_verdict": "APPROVATA" if res.get("approved") else "BOCCIATA",
    "groq_report": res.get("critique")
}

with open("reports/tickets/ticket_gemme_nascoste_player_props.json", "w", encoding="utf-8") as f:
    json.dump(ticket_out, f, indent=2, ensure_ascii=False)
print("Salvataggio completato in reports/tickets/ticket_gemme_nascoste_player_props.json!")
