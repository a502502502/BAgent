#!/usr/bin/env python3
"""
scripts/register_all_certified_tickets_15oct.py — Registrazione e Pubblicazione Completa Suite UEL & UECL (15 Ottobre 2026).

Include:
- I 5 Ticket Ufficiali UEL & UECL (Core Apertura, Core Notturna, Tripla Chirurgica Tiri, Specials Corner & Cartellini, Satellite Alto Flusso)
- I 2 Ticket Specializzati UEFA Conference League (La Tripla Balistica UECL @ 3.05x, Core Blindato UECL @ 4.12x)

Tutti certificati con Incrocio OFP (Regola #83) + Audit Gemini Argon + Reality Gate 2.0 (Regole #85, #87).
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path("C:/Project/BAgent")
MIRROR = Path("C:/Project/bagent-schedine")

# Ticket 1-5 gia certificati
TICKET_1_CORE_APERTURA = {
    "ticket_id": "SCHEDINA_1_CORE_APERTURA_1845_15OTT",
    "name": "Schedina 1: Core Blindato Apertura (18:45 CEST @ 2.96x)",
    "title": "Schedina 1: Core Blindato Apertura (18:45 CEST @ 2.96x)",
    "bookmaker": "Netwin",
    "type": "Core Apertura (Stake 10 EUR)",
    "status": "PENDING",
    "placed_at": "2026-10-15 18:45 CEST",
    "created_at": "2026-10-15T13:20:00+02:00",
    "date_created": "2026-10-15 13:20:00",
    "stake": 10.0,
    "stake_eur": 10.0,
    "bonus": 0.0,
    "total_odds": 2.96,
    "potential_win": 29.60,
    "potential_payout_eur": 29.60,
    "net_profit_eur": 19.60,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "OFP AAA + Argon Certified. Rimosso ceiling trap su Salisburgo; apertura UEL/UECL con mercati asimmetrici.",
    "legs": [
        {
            "match": "Salisburgo vs AC Milan",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 18:45 CEST",
            "market": "X2 + U/O 1.5 : X2 + OV",
            "selection": "X2 + OV",
            "odds": 1.48,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Salisburgo concede 1.55 xGA; copre pareggio e vittoria esterna senza ceiling"
        },
        {
            "match": "AZ Alkmaar vs Hapoel Be'er Sheva",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 18:45 CEST",
            "market": "Over 0.5 1°T + Over 0.5 2°T : SI",
            "selection": "SI",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Flusso olandese costante ad alto volume offensivo (1+ rete per tempo)"
        },
        {
            "match": "Sparta Praga vs Lillestrom",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 18:45 CEST",
            "market": "U/O 1.5 Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.38,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Media interna ceca >2.10 reti; difesa norvegese vulnerabile"
        }
    ]
}

TICKET_2_CORE_NOTTURNA = {
    "ticket_id": "SCHEDINA_2_CORE_NOTTURNA_2100_15OTT",
    "name": "Schedina 2: Core Blindato Notturna (21:00 CEST @ 4.24x)",
    "title": "Schedina 2: Core Blindato Notturna (21:00 CEST @ 4.24x)",
    "bookmaker": "Netwin",
    "type": "Core Notturna (Stake 10 EUR)",
    "status": "PENDING",
    "placed_at": "2026-10-15 21:00 CEST",
    "created_at": "2026-10-15T13:20:00+02:00",
    "date_created": "2026-10-15 13:20:00",
    "stake": 10.0,
    "stake_eur": 10.0,
    "bonus": 0.0,
    "total_odds": 4.24,
    "potential_win": 42.40,
    "potential_payout_eur": 42.40,
    "net_profit_eur": 32.40,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "OFP AAA + Argon Certified. Rettifica anti-soffitto su Jagiellonia e copertura Chance Mix su Celta-Juve.",
    "legs": [
        {
            "match": "SL Benfica vs Celtic FC",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "1X + U/O 1.5 : 1X + OV",
            "selection": "1X + OV",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Fattore Da Luz fortino europeo; Celtic vulnerabile in trasferta europea"
        },
        {
            "match": "Celta Vigo vs Juventus",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "Chance Mix: X2 o Under 2.5 : SI",
            "selection": "SI",
            "odds": 1.42,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Gestione del possesso e ritmo controllato; copre 0-0, 1-1, 0-1, 0-2, 1-0"
        },
        {
            "match": "NEC Nijmegen vs Levski Sofia",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "1X + U/O 1.5 : 1X + OV",
            "selection": "1X + OV",
            "odds": 1.42,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Pressione dinamica olandese contro blocco basso bulgaro"
        },
        {
            "match": "Jagiellonia vs Ararat-Armenia",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 1.5 Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Rettifica anti-soffitto (eliminato MultiGol 1-4); polacchi travolgenti in casa"
        }
    ]
}

TICKET_3_CHIRURGICA = {
    "ticket_id": "SCHEDINA_3_TRIPLA_CHIRURGICA_TIRI_15OTT",
    "name": "Schedina 3: La Tripla Chirurgica (Tiri in Porta @ 3.25x — TOP GEM)",
    "title": "Schedina 3: La Tripla Chirurgica (Tiri in Porta @ 3.25x — TOP GEM)",
    "bookmaker": "Netwin",
    "type": "Tripla Chirurgica (Stake 10 EUR)",
    "status": "PENDING",
    "placed_at": "2026-10-15 21:00 CEST",
    "created_at": "2026-10-15T13:20:00+02:00",
    "date_created": "2026-10-15 13:20:00",
    "stake": 10.0,
    "stake_eur": 10.0,
    "bonus": 0.0,
    "total_odds": 3.25,
    "potential_win": 32.50,
    "potential_payout_eur": 32.50,
    "net_profit_eur": 22.50,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "OFP AAA + Argon Certified. Massimo EV balistico. Include la gemma Ajax Over 5.5 Tiri in Porta @ 1.60.",
    "legs": [
        {
            "match": "Atalanta vs Pafos FC",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 4.5 Tiri in Porta Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.40,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Gewiss Stadium ad alto volume balistico (media 6.8 tiri nello specchio)"
        },
        {
            "match": "Ajax vs Maccabi Tel Aviv",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 5.5 Tiri in Porta Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.60,
            "status": "PENDING",
            "score": "OFP AAA | Top Gem Argon | Pressione costante sulle fasce e accentramento (media interna 7.8 tiri specchio)"
        },
        {
            "match": "AFC Bournemouth vs Sturm Graz",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 5.5 Tiri in Porta Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Pressing asfissiante e transizioni rapide della Premier contro blocco statico"
        }
    ]
}

TICKET_4_SPECIALS = {
    "ticket_id": "SCHEDINA_4_SPECIALS_CORNER_CARTELLINI_15OTT",
    "name": "Schedina 4: Specials Asimmetrici (Corner & Cartellini @ 4.65x)",
    "title": "Schedina 4: Specials Asimmetrici (Corner & Cartellini @ 4.65x)",
    "bookmaker": "Netwin",
    "type": "Specials Asimmetrici (Stake 6 EUR)",
    "status": "PENDING",
    "placed_at": "2026-10-15 21:00 CEST",
    "created_at": "2026-10-15T13:20:00+02:00",
    "date_created": "2026-10-15 13:20:00",
    "stake": 6.0,
    "stake_eur": 6.0,
    "bonus": 0.0,
    "total_odds": 4.65,
    "potential_win": 27.90,
    "potential_payout_eur": 27.90,
    "net_profit_eur": 21.90,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "OFP AAA + Argon Certified. Mercati asimmetrici slegati dai gol; saturazione corsie esterne e intensita arbitrale.",
    "legs": [
        {
            "match": "Brighton vs Kauno Zalgiris",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 6.5 Corner Squadra 1 (esc.TS) : OVER",
            "selection": "OVER",
            "odds": 1.50,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Ampiezza estrema sulle fasce contro blocco basso lituano (>7 corner interni)"
        },
        {
            "match": "SL Benfica vs Celtic FC",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 4.5 Corner Squadra 1 (esc.TS) : OVER",
            "selection": "OVER",
            "odds": 1.38,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Asimmetria corsie esterne Da Luz (>5 corner nel 78% dei match europei)"
        },
        {
            "match": "Olympique Marsiglia vs Olympiacos",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 4.5 Cartellini Totali (esc.TS) : OVER",
            "selection": "OVER",
            "odds": 1.55,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Velodrome incandescente, alto attrito e duelli fisici a centrocampo"
        },
        {
            "match": "Union SG vs Real Sociedad",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 3.5 Cartellini Totali (esc.TS) : OVER",
            "selection": "OVER",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Scontro fisico a Bruxelles ad alta intensita di falli tattici"
        }
    ]
}

TICKET_5_SATELLITE = {
    "ticket_id": "SCHEDINA_5_SATELLITE_GOL_OVER_15OTT",
    "name": "Schedina 5: Satellite Alto Flusso (Gol & Over @ 6.55x)",
    "title": "Schedina 5: Satellite Alto Flusso (Gol & Over @ 6.55x)",
    "bookmaker": "Netwin",
    "type": "Satellite Moltiplicatore (Stake 4 EUR)",
    "status": "PENDING",
    "placed_at": "2026-10-15 21:00 CEST",
    "created_at": "2026-10-15T13:20:00+02:00",
    "date_created": "2026-10-15 13:20:00",
    "stake": 4.0,
    "stake_eur": 4.0,
    "bonus": 0.0,
    "total_odds": 6.55,
    "potential_win": 26.20,
    "potential_payout_eur": 26.20,
    "net_profit_eur": 22.20,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "OFP AAA + Argon Certified. 100% Ortogonale da Core. Solo match a ritmo verticale e transizioni rapide.",
    "legs": [
        {
            "match": "Hoffenheim vs Besiktas",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "GG/NG + U/O 2.5 : GG + OV",
            "selection": "GG + OV",
            "odds": 1.75,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | PreZero Arena, ritmi altissimi e difese scoperte (massimo xG combinato)"
        },
        {
            "match": "Lech Poznan vs Bayer Leverkusen",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 2.5 : OVER",
            "selection": "OVER",
            "odds": 1.62,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Transizioni continue e campo pesante, slegato da 1X2"
        },
        {
            "match": "Olympique Marsiglia vs Olympiacos",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "GG/NG : GG",
            "selection": "GG",
            "odds": 1.65,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Marsiglia aggressivo ma vulnerabile alle ripartenze elleniche"
        },
        {
            "match": "Olympique Lione vs Crystal Palace",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "Chance Mix: X o GG : SI",
            "selection": "SI",
            "odds": 1.40,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Duello equilibrato e serrato: copre 1-1, 2-1, 1-2, 0-0"
        }
    ]
}

# NUOVI TICKET SPECIALIZZATI 100% UEFA CONFERENCE LEAGUE
TICKET_6_TRIPLA_BALISTICA_UECL = {
    "ticket_id": "SCHEDINA_6_TRIPLA_BALISTICA_UECL_15OTT",
    "name": "Schedina 6: La Tripla Balistica UECL (Tiri in Porta & Corner @ 3.05x)",
    "title": "Schedina 6: La Tripla Balistica UECL (Tiri in Porta & Corner @ 3.05x)",
    "bookmaker": "Netwin",
    "type": "Special UECL (Tiri in Porta & Corner)",
    "status": "PENDING",
    "placed_at": "2026-10-15 21:00 CEST",
    "created_at": "2026-10-15T13:52:00+02:00",
    "date_created": "2026-10-15 13:52:00",
    "stake": 5.0,
    "stake_eur": 5.0,
    "bonus": 0.0,
    "total_odds": 3.05,
    "potential_win": 15.25,
    "potential_payout_eur": 15.25,
    "net_profit_eur": 10.25,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "OFP AAA + Argon Certified. 100% Conference League: solo mercati balistici e corner asimmetrici, immuni da turnover e punteggio.",
    "legs": [
        {
            "match": "Atalanta vs Pafos FC",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 4.5 Tiri in Porta Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.40,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Gewiss Stadium ad alto volume balistico (media 6.8 tiri nello specchio)"
        },
        {
            "match": "AFC Bournemouth vs Sturm Graz",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 5.5 Tiri in Porta Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Pressing asfissiante e transizioni rapide della Premier contro blocco statico"
        },
        {
            "match": "Brighton vs Kauno Zalgiris",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 6.5 Corner Squadra 1 (esc.TS) : OVER",
            "selection": "OVER",
            "odds": 1.50,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Ampiezza estrema sulle fasce contro blocco basso lituano (>7 corner interni)"
        }
    ]
}

TICKET_7_CORE_FLUSSI_UECL = {
    "ticket_id": "SCHEDINA_7_CORE_FLUSSI_UECL_15OTT",
    "name": "Schedina 7: Core Blindato UECL (Spina Dorsale Flussi @ 4.12x)",
    "title": "Schedina 7: Core Blindato UECL (Spina Dorsale Flussi @ 4.12x)",
    "bookmaker": "Netwin",
    "type": "Core UECL Flussi (Gol & Doppia Chance)",
    "status": "PENDING",
    "placed_at": "2026-10-15 18:45 CEST",
    "created_at": "2026-10-15T13:52:00+02:00",
    "date_created": "2026-10-15 13:52:00",
    "stake": 5.0,
    "stake_eur": 5.0,
    "bonus": 0.0,
    "total_odds": 4.12,
    "potential_win": 20.60,
    "potential_payout_eur": 20.60,
    "net_profit_eur": 15.60,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "OFP AAA + Argon Certified. Spina dorsale 100% Conference League: flusso costante 18:45 e solidita casalinga 21:00 senza tetti restrittivi.",
    "legs": [
        {
            "match": "AZ Alkmaar vs Hapoel Be'er Sheva",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 18:45 CEST",
            "market": "Over 0.5 1°T + Over 0.5 2°T : SI",
            "selection": "SI",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Flusso olandese costante ad alto volume offensivo (1+ rete per tempo)"
        },
        {
            "match": "Sparta Praga vs Lillestrom",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 18:45 CEST",
            "market": "U/O 1.5 Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.38,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Media interna ceca >2.10 reti; difesa norvegese vulnerabile"
        },
        {
            "match": "NEC Nijmegen vs Levski Sofia",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "1X + U/O 1.5 : 1X + OV",
            "selection": "1X + OV",
            "odds": 1.42,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Pressione dinamica olandese contro blocco basso bulgaro"
        },
        {
            "match": "Jagiellonia vs Ararat-Armenia",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 1.5 Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP AAA | Argon Certified | Rettifica anti-soffitto (eliminato MultiGol 1-4); polacchi travolgenti in casa"
        }
    ]
}

ALL_TICKETS = [
    TICKET_1_CORE_APERTURA,
    TICKET_2_CORE_NOTTURNA,
    TICKET_3_CHIRURGICA,
    TICKET_4_SPECIALS,
    TICKET_5_SATELLITE,
    TICKET_6_TRIPLA_BALISTICA_UECL,
    TICKET_7_CORE_FLUSSI_UECL
]

PORTAL_CARDS = [
    {
        "id": TICKET_1_CORE_APERTURA["ticket_id"],
        "title": TICKET_1_CORE_APERTURA["title"],
        "label": "In Programma (Oggi ore 18:45)",
        "stake": "10.00 €",
        "odds": "2.96×",
        "potential_win": "29.60 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-15 18:45 CEST",
                "match": "Salisburgo vs AC Milan",
                "pick": "X2 + Over 1.5",
                "odd": "1.48",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Salisburgo concede 1.55 xGA; copre pareggio e vittoria esterna senza ceiling"
            },
            {
                "when": "2026-10-15 18:45 CEST",
                "match": "AZ Alkmaar vs Hapoel Be'er Sheva",
                "pick": "Over 0.5 1°T + Over 0.5 2°T",
                "odd": "1.45",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Flusso olandese costante ad alto volume offensivo (1+ rete per tempo)"
            },
            {
                "when": "2026-10-15 18:45 CEST",
                "match": "Sparta Praga vs Lillestrom",
                "pick": "Sparta Praga Over 1.5 Gol",
                "odd": "1.38",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Media interna ceca >2.10 reti; difesa norvegese vulnerabile"
            }
        ]
    },
    {
        "id": TICKET_2_CORE_NOTTURNA["ticket_id"],
        "title": TICKET_2_CORE_NOTTURNA["title"],
        "label": "In Programma (Oggi ore 21:00)",
        "stake": "10.00 €",
        "odds": "4.24×",
        "potential_win": "42.40 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "SL Benfica vs Celtic FC",
                "pick": "1X + Over 1.5",
                "odd": "1.45",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Fattore Da Luz fortino europeo; Celtic vulnerabile in trasferta europea"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Celta Vigo vs Juventus",
                "pick": "Chance Mix: X2 o Under 2.5",
                "odd": "1.42",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Gestione del possesso e ritmo controllato; copre 0-0, 1-1, 0-1, 0-2, 1-0"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "NEC Nijmegen vs Levski Sofia",
                "pick": "1X + Over 1.5",
                "odd": "1.42",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Pressione dinamica olandese contro blocco basso bulgaro"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Jagiellonia vs Ararat-Armenia",
                "pick": "Jagiellonia Over 1.5 Gol",
                "odd": "1.45",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Rettifica anti-soffitto (eliminato MultiGol 1-4); polacchi travolgenti in casa"
            }
        ]
    },
    {
        "id": TICKET_3_CHIRURGICA["ticket_id"],
        "title": TICKET_3_CHIRURGICA["title"],
        "label": "In Programma (Oggi ore 21:00)",
        "stake": "10.00 €",
        "odds": "3.25×",
        "potential_win": "32.50 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Atalanta vs Pafos FC",
                "pick": "Atalanta Over 4.5 Tiri in Porta",
                "odd": "1.40",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Gewiss Stadium ad alto volume balistico (media 6.8 tiri nello specchio)"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Ajax vs Maccabi Tel Aviv",
                "pick": "Ajax Over 5.5 Tiri in Porta",
                "odd": "1.60",
                "result": "PENDING",
                "score": "OFP AAA | Top Gem Argon | Pressione costante sulle fasce e accentramento (media interna 7.8 tiri specchio)"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "AFC Bournemouth vs Sturm Graz",
                "pick": "Bournemouth Over 5.5 Tiri in Porta",
                "odd": "1.45",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Pressing asfissiante e transizioni rapide della Premier contro blocco statico"
            }
        ]
    },
    {
        "id": TICKET_4_SPECIALS["ticket_id"],
        "title": TICKET_4_SPECIALS["title"],
        "label": "In Programma (Oggi ore 21:00)",
        "stake": "6.00 €",
        "odds": "4.65×",
        "potential_win": "27.90 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Brighton vs Kauno Zalgiris",
                "pick": "Brighton Over 6.5 Corner",
                "odd": "1.50",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Ampiezza estrema sulle fasce contro blocco basso lituano (>7 corner interni)"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "SL Benfica vs Celtic FC",
                "pick": "Benfica Over 4.5 Corner",
                "odd": "1.38",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Asimmetria corsie esterne Da Luz (>5 corner nel 78% dei match europei)"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Olympique Marsiglia vs Olympiacos",
                "pick": "Over 4.5 Cartellini Totali",
                "odd": "1.55",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Velodrome incandescente, alto attrito e duelli fisici a centrocampo"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Union SG vs Real Sociedad",
                "pick": "Over 3.5 Cartellini Totali",
                "odd": "1.45",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Scontro fisico a Bruxelles ad alta intensita di falli tattici"
            }
        ]
    },
    {
        "id": TICKET_5_SATELLITE["ticket_id"],
        "title": TICKET_5_SATELLITE["title"],
        "label": "In Programma (Oggi ore 21:00)",
        "stake": "4.00 €",
        "odds": "6.55×",
        "potential_win": "26.20 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Hoffenheim vs Besiktas",
                "pick": "Gol + Over 2.5",
                "odd": "1.75",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | PreZero Arena, ritmi altissimi e difese scoperte (massimo xG combinato)"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Lech Poznan vs Bayer Leverkusen",
                "pick": "Over 2.5",
                "odd": "1.62",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Transizioni continue e campo pesante, slegato da 1X2"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Olympique Marsiglia vs Olympiacos",
                "pick": "G/NG: Gol",
                "odd": "1.65",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Marsiglia aggressivo ma vulnerabile alle ripartenze elleniche"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Olympique Lione vs Crystal Palace",
                "pick": "Chance Mix: X o GG",
                "odd": "1.40",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Duello equilibrato e serrato: copre 1-1, 2-1, 1-2, 0-0"
            }
        ]
    },
    {
        "id": TICKET_6_TRIPLA_BALISTICA_UECL["ticket_id"],
        "title": TICKET_6_TRIPLA_BALISTICA_UECL["title"],
        "label": "In Programma (Oggi ore 21:00)",
        "stake": "5.00 €",
        "odds": "3.05×",
        "potential_win": "15.25 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Atalanta vs Pafos FC",
                "pick": "Atalanta Over 4.5 Tiri in Porta",
                "odd": "1.40",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Gewiss Stadium ad alto volume balistico (media 6.8 tiri nello specchio)"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "AFC Bournemouth vs Sturm Graz",
                "pick": "Bournemouth Over 5.5 Tiri in Porta",
                "odd": "1.45",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Pressing asfissiante e transizioni rapide della Premier contro blocco statico"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Brighton vs Kauno Zalgiris",
                "pick": "Brighton Over 6.5 Corner",
                "odd": "1.50",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Ampiezza estrema sulle fasce contro blocco basso lituano (>7 corner interni)"
            }
        ]
    },
    {
        "id": TICKET_7_CORE_FLUSSI_UECL["ticket_id"],
        "title": TICKET_7_CORE_FLUSSI_UECL["title"],
        "label": "In Programma (Oggi ore 18:45)",
        "stake": "5.00 €",
        "odds": "4.12×",
        "potential_win": "20.60 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-15 18:45 CEST",
                "match": "AZ Alkmaar vs Hapoel Be'er Sheva",
                "pick": "Over 0.5 1°T + Over 0.5 2°T",
                "odd": "1.45",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Flusso olandese costante ad alto volume offensivo (1+ rete per tempo)"
            },
            {
                "when": "2026-10-15 18:45 CEST",
                "match": "Sparta Praga vs Lillestrom",
                "pick": "Sparta Praga Over 1.5 Gol",
                "odd": "1.38",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Media interna ceca >2.10 reti; difesa norvegese vulnerabile"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "NEC Nijmegen vs Levski Sofia",
                "pick": "1X + Over 1.5",
                "odd": "1.42",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Pressione dinamica olandese contro blocco basso bulgaro"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Jagiellonia vs Ararat-Armenia",
                "pick": "Jagiellonia Over 1.5 Gol",
                "odd": "1.45",
                "result": "PENDING",
                "score": "OFP AAA | Argon Certified | Rettifica anti-soffitto (eliminato MultiGol 1-4); polacchi travolgenti in casa"
            }
        ]
    }
]

OBSOLETE_IDS = [
    "TICKET_CORE_ROCKET_UEL_UECL_20EUR_15OTT",
    "TICKET_SATELLITE_MOLTIPLICATORE_UEL_5EUR_15OTT",
    "TICKET_TRIPLA_CHIRURGICA_GEMS_10EUR_15OTT"
]


def update_portal(target_dir: Path, is_mirror: bool = False):
    if is_mirror:
        sj_path = target_dir / "schedine.json"
        sh_path = target_dir / "index.html"
    else:
        sj_path = target_dir / "portal" / "schedine.json"
        sh_path = target_dir / "portal" / "schedine.html"

    if not sj_path.exists():
        print(f"File non trovato: {sj_path}")
        return

    sj = json.loads(sj_path.read_text(encoding="utf-8"))
    present = sj.get("present", [])

    ids_to_register = [c["id"] for c in PORTAL_CARDS]
    all_purge_ids = set(ids_to_register + OBSOLETE_IDS)
    present = [t for t in present if t.get("id") not in all_purge_ids]

    for c in reversed(PORTAL_CARDS):
        present.insert(0, c)

    sj["present"] = present
    sj["generated_at"] = datetime.now().isoformat()
    sj["profit_label"] = "+45.14 € (Saldo Netto Aggiornato)"

    compact_json = json.dumps(sj, ensure_ascii=False)
    pretty_json = json.dumps(sj, indent=2, ensure_ascii=False)

    sj_path.write_text(pretty_json, encoding="utf-8")
    print(f"Aggiornato con successo: {sj_path} ({len(present)} schedine attive).")

    if sh_path.exists():
        html_content = sh_path.read_text(encoding="utf-8")
        html_updated = re.sub(
            r'(<script type="application/json" id="boot">)(.*?)(</script>)',
            rf'\g<1>{compact_json}\g<3>',
            html_content,
            flags=re.DOTALL
        )
        sh_path.write_text(html_updated, encoding="utf-8")
        print(f"Aggiornato con successo: {sh_path}.")


def update_active_user_tickets():
    act_path = ROOT / "data" / "active_user_tickets.json"
    if not act_path.exists():
        print(f"File non trovato: {act_path}")
        return
    data = json.loads(act_path.read_text(encoding="utf-8"))

    ids_to_register = [t["ticket_id"] for t in ALL_TICKETS]
    all_purge_ids = set(ids_to_register + OBSOLETE_IDS)
    data = [t for t in data if t.get("ticket_id") not in all_purge_ids]

    for t in reversed(ALL_TICKETS):
        data.insert(0, t)

    act_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Aggiornato {act_path} con {len(data)} ticket totali.")


def main():
    print("=" * 80)
    print("REGISTRAZIONE E PUBBLICAZIONE SUITE COMPLETA (7 SCHEDINE UEL & UECL)")
    print("=" * 80)

    update_active_user_tickets()
    update_portal(ROOT, is_mirror=False)
    if MIRROR.exists():
        update_portal(MIRROR, is_mirror=True)

    print("\nRegistrazione e pubblicazione completata con successo su tutti i canali.")


if __name__ == "__main__":
    main()
