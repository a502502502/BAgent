# Session Handover — 23 Settembre 2026 (notte)

## Stato
- Bankroll ufficiale: **~€149.19**
- Telegram: **token 401** — aggiornare `TELEGRAM_TOKEN` via BotFather prima di `--telegram`
- Tennis: ban permanente (non toccare)

## Nations League 23–25/09 — Ticket certificati

Slate Odds API: `data/tickets/nl_slate_3d.json` (16 eventi)  
Master certificato: `data/tickets/nl_tickets_3d_certified.json`  
*(cartella `data/` su Google Drive, non su git)*

### Priorità (cap sessione 15% ≈ €22.38 → A+C = €19.40)

| Ticket | File | Quota | Stake | Pot |
|--------|------|------:|------:|----:|
| **A Acciaio 24/09** | `ticket_nl_a_acciaio_24set.json` | 4.88× | €7.46 | €36.38 |
| **C Acciaio 25/09** | `ticket_nl_c_acciaio_25set.json` | 3.76× | €11.94 | €44.93 |

**A (20:45 CEST 24/09)**
1. Norvegia–Danimarca Over 2.5 @1.74
2. Serbia–Grecia Under 2.5 @1.73
3. Portogallo–Galles Under 3.5 @1.62 *(1 POR @1.24 Gate 0 BAN)*

**C (20:45 CEST 25/09)**
1. Italia–Belgio Under 3.5 @1.40
2. Turchia–Francia Under 3.5 @1.68 *(#67: no 2/X2 Francia Istanbul)*
3. Svezia–Romania Over 2.5 @1.60 *(1 SWE @1.53 Gate 0 BAN)*

### Opzionali (solo budget residuo sotto cap)
- **B Ballistico 24/09** @2.31: Olanda–Germania O2.5 @1.54 + Austria–Israele O2.5 @1.50
- **D Equilibrio 25/09** @2.99: Ungheria–Ucraina U2.5 @1.74 + Polonia 1 @1.72

### Scartati
Andorra–Malta, Liechtenstein–Lituania (D) · Armenia–Lettonia, Montenegro–Cipro (C) · Inghilterra/Spagna assenti da Odds API in finestra.

## Fix codice (in questo commit)
Gate #56: false positive `" B "` su stringa `Nations League - League B` → whitelist in `strict_ticket_pipeline.py`.

## Ripresa domani
1. Verificare quote Netwin su A (e C se ancora aperte)
2. Piazzare A; poi C se kickoff ok
3. Refresh Telegram token → `python scripts/build_verified_ticket.py --telegram` se serve push
4. Argentino: prossima finestra Odds API ~2–6 Ottobre
