# BAgent — Indice delle regole operative

> **Source of truth**: il testo completo e aggiornato delle regole vive in `CLAUDE.md` e `.cursorrules`.  
> Questo file è un **indice navigabile** per umani e agent: non sostituisce CLAUDE.md.

Tennis abolito dal 22 settembre 2026. Solo calcio.

---

## 1. Principi non negoziabili

| Principio | Sintesi |
|-----------|---------|
| Niente 1X2 rigido | Vietato 1 o 2 secco e combo tipo `1 + Over`. Preferire MultiGol tempi, Chance Mix, Over 0.5 entrambi i tempi, MultiGol aperti. |
| Probabilità dai dati | Poisson / Dixon-Coles, xG da `data/bagent.db`. Edge = (prob × quota) − 1 è solo informativo. |
| Reality Gate | Rose, allenatori, giocatori solo da registry 2026/27 e feed ufficiali. Niente memoria. |
| Certificato obbligatorio | Nessuna schedina “giocabile” senza `scripts/strict_validator.py`. |
| Bankroll | Max 8% per ticket, 5–8% Kelly, max 15% sessione. Niente chasing. |
| Ortogonalità portfolio | Stessa partita / prop in un solo ticket per sessione (Core 70% / Satellite 30%). |

---

## 2. Regole numerate (riferimento rapido)

Dettaglio completo in `CLAUDE.md`.

| # | Titolo breve |
|---|--------------|
| 55 | Storico gol / xG da DB (o FootyStats) obbligatorio |
| 75 | Certificato locale pre-emissione (`strict_validator`) |
| 76 | Data e ora kickoff obbligatorie su ogni selezione |
| 77 | Rettifica locale prima di pubblicare |
| 78 | Unificazione certificato + avvisi (prob < 72%, edge < 4%) |
| 79 | Stream unico: `netwin_live_odds.json` + `bagent.db` |
| 82 | Sblocco mercati tempi + abolizione 1X2 rigido |
| 83 | Triangolazione Oddspedia + Forebet + BAgent |
| 84 | Anagrafica giocatori da feed bookmaker / registry |
| 85 | Reality Gate (rose e coach 2026/27) |
| 86 | Ortogonalità portfolio (zero single-point-of-failure) |
| 87 | No citazioni nominali non certificate + blacklist ceduti |
| 88 | No player props senza formazione ufficiale titolare |
| 89 | Mercato ottimale per partita (mix flessibile nel ticket) |
| 90 | Auto-download on-demand; no scarto preventivo per dati mancanti |
| 91 | Spazio di ricerca 7 famiglie di mercati |
| 92+ | Generazione autonoma multi-mercato (vedi CLAUDE.md) |

---

## 3. Pipeline minima per una schedina

1. Sesto Senso / news (`scripts/fetch_sports_news.py` se serve)
2. xG e storico da `data/bagent.db` (Regola 55 / 90)
3. Quote fresche da snapshot Netwin
4. Scansione mercati (`scan_omni_markets` / engine correlati)
5. Triangolazione OFP se disponibile (Regola 83)
6. Reality Gate su rose / coach / props (85, 87, 88)
7. `scripts/build_verified_ticket.py` → probabilità, edge, Kelly
8. **`scripts/strict_validator.py`** → certificato (75, 76, 78)
9. Pubblicazione solo se certificato; portfolio ortogonale (86)

---

## 4. Cosa non fare (checklist anti-errore)

- [ ] Proporre 1 o 2 secco / `1 + Over` su favorite
- [ ] Citare giocatori o allenatori a memoria
- [ ] Player prop senza distinta ufficiale titolare
- [ ] Stessa partita in due ticket della stessa sessione
- [ ] Schedina senza data/ora kickoff
- [ ] Dire “giocabile” senza output di `strict_validator`
- [ ] Chasing dopo una perdita di sessione
- [ ] Usare dati hard-coded di giornate passate come se fossero live

---

## 5. File correlati

| File | Ruolo |
|------|--------|
| `CLAUDE.md` | Vincoli operativi completi (source of truth) |
| `.cursorrules` | Regole per agent in Cursor |
| `BAGent_Master_Project_Context_for_Argon.md` | Contesto architetturale / audit pack (può essere datato) |
| `docs/archive/` | Storico sessioni e versioni estese |
| `README.md` | Panoramica progetto e quick start |
