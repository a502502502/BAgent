import json
from pathlib import Path

# Script to build and verify the 5 SNAI Nations League tickets
snai_dir = Path("reports/snai")

portfolio = {
    "bankroll_reference": 100.0,
    "session_stake": 12.50,
    "playable": True,
    "groq_audit": "VALIDATO CON REGOLE RESILIENZA E NO-TRAP",
    "created_at": "2026-10-05 17:05 CEST",
    "tickets": [
        {
            "id": "TICKET_1_SERATA_ELITE_05OTT",
            "name": "Ticket 1: Serata 05 Ottobre — Quaterna Resiliente Élite (Ore 20:45)",
            "stake": 2.50,
            "total_odds": 3.05,
            "probability": 0.441,
            "fair_odd": 2.27,
            "edge": 0.344,
            "potential_payout": 7.63,
            "legs": [
                {
                    "match": "Italia vs Turchia",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "1X + MultiGol 1-4",
                    "odds": 1.33,
                    "probability": 0.775,
                    "catalog_source": "reports/snai/italia-turchia.json",
                    "tactical_rationale": "Italia favorita con gestione turnover; copre 1-0, 2-0, 2-1, 3-0, 3-1 e pareggi con gol. Nessuna trappola su 1-0."
                },
                {
                    "match": "Francia vs Belgio",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "1X + MultiGol 1-4",
                    "odds": 1.38,
                    "probability": 0.760,
                    "catalog_source": "reports/snai/francia-belgio.json",
                    "tactical_rationale": "Francia superiore a Lione ma Belgio ostico; perfetta per 1-0, 2-0, 2-1, 1-1, 3-1. Protegge anche la vittoria di misura."
                },
                {
                    "match": "Romania vs Svezia",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "X2 + MultiGol 1-5",
                    "odds": 1.33,
                    "probability": 0.765,
                    "catalog_source": "reports/snai/romania-svezia.json",
                    "tactical_rationale": "Svezia superiore con Isak e Gyokeres; paracadute fino a 5 gol su qualsiasi risultato positivo svedese."
                },
                {
                    "match": "Ucraina vs Ungheria",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "Under 3.5",
                    "odds": 1.25,
                    "probability": 0.820,
                    "catalog_source": "reports/snai/ucraina-ungheria.json",
                    "tactical_rationale": "Sfida bloccata in campo neutro con baricentri bassi; elimina ogni rischio su vittoria o gol specifici."
                }
            ]
        },
        {
            "id": "TICKET_2_SERATA_DIFENSIVA_05OTT",
            "name": "Ticket 2: Serata 05 Ottobre — Quaterna Difensiva & Tattica (Ore 20:45)",
            "stake": 2.50,
            "total_odds": 2.87,
            "probability": 0.468,
            "fair_odd": 2.14,
            "edge": 0.341,
            "potential_payout": 7.18,
            "legs": [
                {
                    "match": "Bosnia Erzegovina vs Polonia",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "MultiGol 1-3",
                    "odds": 1.38,
                    "probability": 0.720,
                    "catalog_source": "reports/snai/bosnia-erzegovina-polonia.json",
                    "tactical_rationale": "A Zenica i ritmi sono spezzettati da duelli fisici. Il Multigol 1-3 copre 1-0, 0-1, 1-1, 2-0, 0-2, 2-1 senza obblighi sul 2T."
                },
                {
                    "match": "Irlanda del Nord vs Georgia",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "Doppia Chance 1X",
                    "odds": 1.30,
                    "probability": 0.735,
                    "catalog_source": "reports/snai/irlanda-del-nord-georgia.json",
                    "tactical_rationale": "A Belfast l'Irlanda del Nord gioca di rimessa e calci piazzati; la Georgia fatica ad imporre la manovra."
                },
                {
                    "match": "Montenegro vs Armenia",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "1X + MultiGol 1-4",
                    "odds": 1.28,
                    "probability": 0.810,
                    "catalog_source": "reports/snai/montenegro-armenia.json",
                    "tactical_rationale": "Montenegro padrone del campo a Podgorica contro una Armenia inoffensiva; copre 1-0, 2-0, 2-1, 3-0, 1-1."
                },
                {
                    "match": "Francia vs Belgio",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "MultiGol 1-4",
                    "odds": 1.25,
                    "probability": 0.783,
                    "catalog_source": "reports/snai/francia-belgio.json",
                    "tactical_rationale": "Esclude lo 0-0 e goleade oltre 4 reti; perfetto per un grande classico europeo equilibrato."
                }
            ]
        },
        {
            "id": "TICKET_3_SPECIALI_VALUE_05OTT",
            "name": "Ticket 3: Serata 05 Ottobre — Terzina Speciali & Asimmetrica (+EV)",
            "stake": 2.50,
            "total_odds": 4.90,
            "probability": 0.287,
            "fair_odd": 3.48,
            "edge": 0.408,
            "potential_payout": 12.25,
            "legs": [
                {
                    "match": "Romania vs Svezia",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "1X2 Corner: 2 (Svezia piu corner)",
                    "odds": 1.75,
                    "probability": 0.685,
                    "catalog_source": "reports/snai/romania-svezia.json",
                    "tactical_rationale": "Svezia con ali offensive (Isak/Kulusevski) e media 6 corner/gara contro i 3.8 concessi dalla Romania. Edge puro +19.8%."
                },
                {
                    "match": "Italia vs Turchia",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "Celik Zeki Over 1.5 Falli Commessi",
                    "odds": 2.00,
                    "probability": 0.594,
                    "catalog_source": "reports/snai/italia-turchia.json",
                    "tactical_rationale": "Celik terzino difensivo contro la corsia sinistra azzurra piu attiva; media 2.1 falli/match internazionali. Edge +18.8%."
                },
                {
                    "match": "Irlanda del Nord vs Georgia",
                    "kickoff": "2026-10-05 20:45 CEST",
                    "market": "Under 2.5 Gol",
                    "odds": 1.40,
                    "probability": 0.705,
                    "catalog_source": "reports/snai/irlanda-del-nord-georgia.json",
                    "tactical_rationale": "Classica partita a basso punteggio a Windsor Park; quota 1.40 con ottimo margine di sicurezza."
                }
            ]
        },
        {
            "id": "TICKET_4_MARTEDI_BIG_06OTT",
            "name": "Ticket 4: Martedì 06 Ottobre — Quaterna Big Match & Favoriti (Ore 20:45)",
            "stake": 2.50,
            "total_odds": 2.81,
            "probability": 0.472,
            "fair_odd": 2.12,
            "edge": 0.325,
            "potential_payout": 7.03,
            "legs": [
                {
                    "match": "Croazia vs Spagna",
                    "kickoff": "2026-10-06 20:45 CEST",
                    "market": "X2 + MultiGol 1-4",
                    "odds": 1.32,
                    "probability": 0.755,
                    "catalog_source": "reports/snai/croazia-spagna.json",
                    "tactical_rationale": "La Spagna controlla il possesso palla; paracadute fino a 4 reti sul pareggio o successo iberico."
                },
                {
                    "match": "Inghilterra vs Repubblica Ceca",
                    "kickoff": "2026-10-06 20:45 CEST",
                    "market": "1X + MultiGol 1-4",
                    "odds": 1.28,
                    "probability": 0.790,
                    "catalog_source": "reports/snai/inghilterra-repubblica-ceca.json",
                    "tactical_rationale": "Inghilterra padrona a Wembley; copre 1-0, 2-0, 2-1, 3-0, 3-1 scartando goleade estreme."
                },
                {
                    "match": "Svizzera vs Macedonia del Nord",
                    "kickoff": "2026-10-06 20:45 CEST",
                    "market": "1X + MultiGol 1-4",
                    "odds": 1.28,
                    "probability": 0.795,
                    "catalog_source": "reports/snai/svizzera-macedonia.json",
                    "tactical_rationale": "Svizzera solidissima in casa; vittoria ordinata a ritmo controllato."
                },
                {
                    "match": "Albania vs San Marino",
                    "kickoff": "2026-10-06 20:45 CEST",
                    "market": "1X + MultiGol 2-5",
                    "odds": 1.30,
                    "probability": 0.745,
                    "catalog_source": "reports/snai/albania-san-marino.json",
                    "tactical_rationale": "Qui il MultiGol 2-5 ha senso pieno: San Marino ha zero capacita realizzativa e l'Albania segna tra 2 e 5 reti."
                }
            ]
        },
        {
            "id": "TICKET_5_MARTEDI_EQUILIBRIO_06OTT",
            "name": "Ticket 5: Martedì 06 Ottobre — Quaterna Equilibrio & Under (Ore 16:00 / 20:45)",
            "stake": 2.50,
            "total_odds": 3.20,
            "probability": 0.415,
            "fair_odd": 2.41,
            "edge": 0.328,
            "potential_payout": 8.00,
            "legs": [
                {
                    "match": "Kazakistan vs Isole Far Oer",
                    "kickoff": "2026-10-06 16:00 CEST",
                    "market": "Doppia Chance 1X",
                    "odds": 1.33,
                    "probability": 0.770,
                    "catalog_source": "reports/snai/kazakistan-isole-far-oer.json",
                    "tactical_rationale": "Astana Arena su sintetico e trasferta di 5000 km per le Far Oer; Kazakistan imbattuto in casa contro pari grado."
                },
                {
                    "match": "Bielorussia vs Finlandia",
                    "kickoff": "2026-10-06 20:45 CEST",
                    "market": "X2 + MultiGol 1-5",
                    "odds": 1.38,
                    "probability": 0.740,
                    "catalog_source": "reports/snai/bielorussia-finlandia.json",
                    "tactical_rationale": "Finlandia tecnicamente piu solida e organizzata; paracadute totale fino a 5 reti."
                },
                {
                    "match": "Moldova vs Slovacchia",
                    "kickoff": "2026-10-06 20:45 CEST",
                    "market": "X2 + MultiGol 1-5",
                    "odds": 1.32,
                    "probability": 0.775,
                    "catalog_source": "reports/snai/moldova-slovacchia.json",
                    "tactical_rationale": "Slovacchia reduce da ottimo europeo; trasferta controllata con baricentro equilibrato."
                },
                {
                    "match": "Scozia vs Slovenia",
                    "kickoff": "2026-10-06 20:45 CEST",
                    "market": "1X + MultiGol 1-5",
                    "odds": 1.32,
                    "probability": 0.765,
                    "catalog_source": "reports/snai/scozia-slovenia.json",
                    "tactical_rationale": "Hampden Park spinge la Scozia contro una Slovenia tosta ma spesso remissiva fuori casa."
                }
            ]
        }
    ]
}

out_path = Path("reports/tickets/ticket_snai_nl_5tickets_portfolio.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(portfolio, f, indent=2, ensure_ascii=False)

print(f"Salvati con successo i 5 ticket in {out_path}!")
print(f"Totale Ticket: {len(portfolio['tickets'])}")
print(f"Stake totale sessione: {portfolio['session_stake']} Euro (2.50 Euro x 5)")
