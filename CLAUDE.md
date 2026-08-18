# BAgent — Contesto di Progetto per Claude

> Leggi questo file all'inizio di ogni sessione per riprendere da dove abbiamo lasciato.

## Cos'è BAgent

Sistema di analisi scommesse sportive (calcio + tennis) con:
- Modello Poisson per stima probabilità gol
- Sesto Senso (ricerca notizie/infortuni obbligatoria prima di ogni previsione)
- Edge formula: `Edge = (prob × quota) - 1`
- MultiplaAdvisor per costruire accumulator con quota ≥ 30 e prob > 79%
- Database SQLite con storico partite, statistiche, log previsioni

---

## Regole di Analisi (SEMPRE in vigore)

- **Sesto Senso = obbligatorio**: ricerca web su infortuni, squalifiche, formazioni per ogni partita analizzata
- **FootyStats = obbligatorio**: SEMPRE consultare https://footystats.org prima di ogni analisi per estrarre avg goals, Over2.5%, BTTS%, xG, forma recente. MAI stimare probabilità senza dati reali da FootyStats.
- **Edge formula**: `Edge = (prob × quota) - 1` — solo informativo, non decisionale
- **Probabilità proprie**: NON derivare da quote bookmaker, usare Poisson + dati FootyStats reali
- **Quota minima**: 1.20
- **Verdetto**: ⭐ edge ≥5% · 👀 edge positivo <5% · ❌ edge negativo
- **Terminologia**: usare "selezioni" o "partite" — MAI "gambe" (errore sessione precedente)
- **Mercati**: usare mix 1X2, Doppia Chance (DC), Over/Under — non solo 1X2
- **Quote Netwin**: verificare sempre direttamente su Netwin tramite Claude in Chrome

---

## Struttura Cartelle

```
BAgent/
├── analyzer/          # ELO, predictions, value bet
├── config/
│   └── settings.py   # Paths relativi (ROOT = Path(__file__).parent.parent)
├── data/
│   ├── bagent.db     # DB principale SQLite (su Google Drive, NON GitHub)
│   ├── matches.db    # DB secondario
│   ├── csv_import/   # CSV FootyStats per varie leghe
│   └── football/raw/ # Dati storici Premier League, Serie B
├── models/            # Dataclass: football, odds, probability, ecc.
├── reports/           # Output analisi (.txt)
├── scripts/
│   ├── db_updater.py # Aggiornamento DB da API-Football
│   ├── analizza_mercati.py
│   └── ...
├── services/
│   ├── football/
│   │   ├── sixth_sense/   # engine.py, analyzer.py, adjuster.py
│   │   └── external/      # multi_collector.py, sources/
│   ├── betting/
│   │   └── multipla_advisor.py
│   ├── analysis/
│   │   └── multi_market.py  # MultiMarketAnalyzer (tutti i mercati)
│   └── database/
│       ├── schema.py
│       └── stats_collector.py
├── scraper/           # flashscore.py, sofascore.py, odds.py
├── utils/
│   └── normalizer.py
└── CLAUDE.md          # Questo file
```

### Path pattern
Tutti i file usano path RELATIVI:
```python
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATABASE = DATA / "bagent.db"
```
**Non cambiare nulla per il Mac** — funziona già cross-platform.

---

## Configurazione Cloud & Git

| Cosa | Dove |
|------|------|
| Codice | GitHub: `https://github.com/a502502502/BAgent.git` (privato) |
| Dati (`data/`) | Google Drive (sincronizzato) |
| `.env` | Solo locale + Google Drive, **mai su git** |
| Pi SSH | `pi@bagent.local` o `pi@192.168.1.69` |

### .env (mai condividere in chat)
Contiene: `API_FOOTBALL_KEY`, `ANTHROPIC_API_KEY`, `ODDS_API_KEY`

---

## Stato Task (agosto 2026)

### Completati ✅
- Architettura base, scraper, modelli
- SixthSenseEngine completo (news → analyzer → adjuster → probabilità)
- MultiMarketAnalyzer (1X2, DC, Over/Under, BTTS)
- MultiplaAdvisor con filtri anti-errore
- Database SQLite + import CSV + db_updater.py da API-Football
- Log validazione previsioni
- **Task #25**: Schedina Quota 100 — multipla 4 giorni (17-20 Agosto) → `reports/multipla_quota100.html`
- **Task #26**: 3 HTML schedine prenotate Netwin → `reports/schedina_*.html`
- **Task #27**: Multipla 17-20 Agosto (nuova, UCL/EL style) → `reports/multipla_1720ago.html`
- **Task #28**: Multipla MLS Americas (20 agosto) → `reports/multipla_mls_americas.html`

### In corso 🔄
- **Task #17**: Widget schedina Norway U19

### Pending ⏳
- **Task #22**: Modulo tennis completo (ATP/WTA/Doppio) — struttura già in `services/tennis/`
- Integrazione MultiMarketAnalyzer nel pipeline principale BAgent
- Recovery `bagent.db` (journal file presente, stato dirty)
- Multipla stanotte 18 agosto (01:00-04:00) — solo 3 partite disponibili, troppo poche

---

## Note Tecniche Importanti

### Netwin Over/Under — struttura dati
- Alcune partite: 6 soglie (0.5–5.5 = 12 valori)
- Altre partite: 5 soglie (1.5–5.5 = 10 valori)
- **Contare sempre i valori prima di etichettare le soglie!**
- Errore precedente: Galatasaray letto Over 1.5@1.52 ma era Over 2.5@1.52

### Sofascore score format
- Formato `"3 | 3 | 0"` = [home | qualcosa | away] — NON 3-3
- Errore precedente: "3|3|0" letto come 3-3 invece di 3-0

### bagent.db
- Journal file presente → DB in stato dirty
- Prima di usare: `PRAGMA wal_checkpoint;` oppure aprire e chiudere con SQLite

---

## Multipla — Regole

- Quota combinata target: ≥ 30
- Probabilità minima per selezione: > 79%
- Mix mercati obbligatorio: 1X2, DC, Over/Under
- Verificare quote su **Netwin** (non stime)
- Aggiungere colonne: campionato, orario, tipo mercato
- Escludere partite già iniziate (verificare orari live su Sofascore)

---

## Come Riprendere da Mac

1. `git clone https://github.com/a502502502/BAgent.git`
2. Collegare cartella `data/` da Google Drive (o symlink)
3. Copiare `.env` da Google Drive nella root del progetto
4. `pip install -r requirements.txt`
5. Dire a Claude: **"leggi CLAUDE.md e riprendiamo"**

---

---

## Sessione 17 Agosto 2026 — Riepilogo Lavoro Svolto

### HTML Schedine create oggi (`reports/`)
| File | Contenuto | Quota |
|------|-----------|-------|
| `multipla_mls_americas.html` | 10 selezioni MLS — giovedì 20 agosto @01:30 IT | 1,246× base → **1,558× con bonus +25%** |
| (altri file da sessioni precedenti) | Vedere cartella reports/ | — |

### Multipla MLS Americas — 10 Selezioni (gio 20/08 @01:30 IT)
Quote verificate su Netwin tramite Claude in Chrome.

| # | Partita | Pick | Quota | Edge |
|---|---------|------|-------|------|
| 1 | Columbus Crew vs CF Montréal | 1 Columbus | @1.61 | ⭐ +7.9% |
| 2 | Minnesota United vs Atlanta United | 1 Minnesota | @1.80 | ⭐ +8.0% |
| 3 | Real Salt Lake vs FC Dallas | 1 RSL | @1.88 | 👀 +3.4% |
| 4 | FC Cincinnati vs New York City FC | 1 Cincinnati | @1.97 | 👀 +2.4% |
| 5 | Sporting KC vs St. Louis City SC | 2 St. Louis | @1.98 | 👀 +3.0% |
| 6 | Portland Timbers vs San Diego FC | 1 Portland | @2.10 | ⭐ +5.0% |
| 7 | DC United vs New England Revolution | 1 DC United | @2.17 | 👀 +4.2% |
| 8 | Toronto FC vs Charlotte FC | 1 Toronto | @2.20 | ⭐ +5.6% |
| 9 | LA Galaxy vs San Jose Earthquakes | 1 LA Galaxy | @2.25 | 👀 +3.5% |
| 10 | Philadelphia Union vs Inter Miami CF | 2 Inter Miami | @2.60 | 👀 +4.0% |

**ESCLUSE da Sesto Senso:**
- ❌ Seattle @1.61: 6 sconfitte consecutive, 7 infortuni (Morris, Roldan, Arriola, Dotson, De La Vega, Petkovic, Yeimar)
- ❌ Vancouver @1.55: 0-3-4 nelle ultime 7, 5 infortuni (Brian White, Veselinovic, Caicedo...)

### Partite 18 Agosto 01:00–04:00 IT (poche, no multipla)
- 01:00 → Internacional vs Clube Do Remo (Brazil) — Inter @1.46, U/O 2.5 Over @1.73 / Under @1.96
- 02:30 → Gimnasia vs Talleres (Argentina) — Talleres @2.50, DC X2 @1.35
- 02:30 → Palestino vs Huachipato (Cile) — Palestino @1.71, U/O 2.5 Over @1.63 / Under @2.10
- 00:15 → Velez vs Defensa Y Justicia (Argentina) — Velez @1.82
- Uruguay/Peru/Colombia: niente fino a venerdì/mercoledì

### Netwin — Quote MLS Verificate (gio 20/08)
```
Orlando City vs Chicago Fire:   Orlando @2.80, Chicago @2.22 (away fav)
DC United vs New England:       DC @2.17, NE @3.10
NY Red Bulls vs Nashville:      NYRB @2.82, Nashville @2.22 (away fav)
Columbus Crew vs CF Montreal:   Columbus @1.61, Montreal @4.70
Cincinnati vs NYC FC:           Cincinnati @1.97, NYC @3.25
Philadelphia vs Inter Miami:    Philly @2.35, Miami @2.60
Toronto vs Charlotte:           Toronto @2.20, Charlotte @2.95
Sporting KC vs St. Louis:       KC @3.30, St. Louis @1.98 (away fav!)
Minnesota vs Atlanta:           Minnesota @1.80, Atlanta @4.00
Colorado vs LA:                 Colorado @2.67, LA @2.40
Seattle vs Austin:              Seattle @1.61, Austin @4.70  ← SKIP (forma)
RSL vs Dallas:                  RSL @1.88, Dallas @3.70
Vancouver vs Houston:           Vancouver @1.55, Houston @5.00 ← SKIP (forma)
Portland vs San Diego:          Portland @2.10, San Diego @2.97
LA Galaxy vs San Jose:          Galaxy @2.25, San Jose @2.75
```

---

*Ultimo aggiornamento: 17 agosto 2026 — ore 23:00 IT*
