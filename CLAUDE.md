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
| Pi SSH (locale) | `pi@bagent.local` o `pi@192.168.1.70` |
| Pi SSH (remoto/Tailscale) | `pi@100.120.216.25` (da qualsiasi rete) |

### .env (mai condividere in chat)
Contiene: `API_FOOTBALL_KEY`, `ANTHROPIC_API_KEY`, `ODDS_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`

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
- **Task #30**: Live Monitor (`scripts/live_monitor.py`) — polling Sofascore/API-Football ogni 30s, alert Telegram con pick Poisson live

### In corso 🔄
- **Task #17**: Widget schedina Norway U19

### Pending ⏳
- **Task #22**: Modulo tennis completo (ATP/WTA/Doppio) — struttura già in `services/tennis/`
- Integrazione MultiMarketAnalyzer nel pipeline principale BAgent
- **Task #29**: ✅ Setup Pi come server autonomo — COMPLETATO 18/08/2026
  - ✅ `bagent-live.service` systemd attivo (`sudo systemctl status bagent-live`)
  - ✅ Cron 07:00 — `db_updater.py` aggiorna DB ogni mattina
  - ✅ Cron 07:30 — `rclone sync` DB → Google Drive (`gdrive:B-Agent/BAgent/data/`)
  - ✅ Tailscale attivo — SSH remoto: `ssh pi@100.120.216.25`

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

## Multipla — Regole & Filosofia di Gioco

- **Priorità Assoluta ai Mercati Alternativi Statistici (No 1X2 Forzato)**:
  - Ridurre al minimo indispensabile i segni secchi 1 o 2 (massima vulnerabilità a pareggi ed episodi casuali).
  - Privilegiare sempre:
    1. **Calci d'Angolo (1X2 Corner, Over Corner)**: Altissima stabilità e prevedibilità tattica (es. Celtic 1 Corner @1.40 al 93%).
    2. **Cartellini / Sanzioni (1X2 Cartellini ospiti/sfavoriti)**: Sfruttare falli tattici e frustrazione (es. 2 Cartellini LASK @2.00).
    3. **Doppie Chance Blindate (DC 1X / X2)**: Protezione totale contro il pareggio al 90° (tasso di successo > 88-94%).
    4. **Linee Gol Protette (Over 1.5, Under 2.5/3.5, No Gol)**: Bastano 2 gol qualsiasi senza dipendere da chi vince.
- Quota combinata target: ≥ 3.50× (Super Sicure) fino a 20-30× (Alta Quota)
- Probabilità minima per selezione in Super Sicure: > 80% (Media > 85%)
- Verificare quote reali su **Netwin** (non stime)
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

## Sessione 18 Agosto 2026 — Riepilogo Lavoro Svolto

### Schedine HTML create
| File | Contenuto |
|------|-----------|
| `reports/schedina_mattina_18ago.html` | Over 3.5 Slovan @1.88 + Sydney @1.27 + Guoan @2.95 → tripla @7.04×, €20 → **PERSA** (Thailand 2-1) |
| `reports/schedina_ucl_18ago.html` | 1 Dinamo @1.75 + Under Fener @2.07 + 1 Levski @3.10 → tripla @11.22 |

### Ticket Netwin Aperti (al 18/08 sera)
| Ticket | Selezioni | Stake | Pot. Vincita | Cashout |
|--------|-----------|-------|-------------|---------|
| **1303** | Kingsley BTTS + Guoan 2 + Thailand 1 + Dinamo 1 | €10 | €113.87 | ~€9 |
| **F009** | 10 sel. UCL/UEL (18-20 ago) — 9/10 aperte | €5 | €212.47 | ~€5 |
| **B402** | 9 sel. UCL/UEL (18-20 ago) — 8/9 aperte | €2 | €118.58 | ~€2 |
| **D80A** | 9 sel. UCL/UEL (18-20 ago) — 8/9 aperte | €3 | €439.39 | ~€3 |

**Saldo Netwin**: €59.72

### Picks stasera (18/08 21:00) per ticket aperti
- **Dinamo 1** @1.76 → serve a F009 e D80A ⭐⭐
- **Levski DC X2** @1.37 → serve a F009 (pareggio o AEK)
- **Levski DC 12** @1.34 → serve a B402 (Levski o AEK)
- **Levski AEK 2** @2.48 → serve a D80A (AEK outright)
- ~~**Fener 2 (Lyon)** @2.03~~ → ❌ ABBANDONATO (non giochiamo più)
- ~~**Under 2.5 Fener** @2.07~~ → ❌ ABBANDONATO

### Live Monitor — `scripts/live_monitor.py`
- Usa **API-Football** (non Sofascore, bloccata con 403)
- Polling ogni 30 secondi
- Notifiche **Telegram** su gol con pick Poisson aggiornati al minuto
- Telegram chat_id: 466378357
- Avvio: `python3 scripts/live_monitor.py`
- **TODO**: deployare sul Pi come servizio systemd (Task #29)

### Sofascore Match IDs utili
| Partita | ID |
|---------|-----|
| Kingsley vs Gwelup | 16816280 |
| Shanghai Shenhua vs Guoan | 16851672 |
| Dinamo Zagabria vs Viking | 16707702 |
| Levski vs AEK | 16707695 |
| Fenerbahce vs Lyon | 16707704 |

### Lesson Learned — Gare di Ritorno
⚠️ Prima di analizzare una gara di ritorno, obbligatorio verificare:
1. **xG e possesso della gara di andata** — se le stats contraddicono il risultato, la squadra "perdente" è più pericolosa di quanto dica il punteggio
2. **Motivazione reale** — la squadra avanti nell'aggregato può giocare in controllo/risparmio
3. **Rotazioni** — verifica se la squadra forte cambia formazione essendo già qualificata
4. **Esempio**: Thailand 1 @1.43 analizzata male — Singapore aveva 75% possesso nella gara di andata ma aveva perso 1-3. Nel ritorno Singapore ha vinto 2-1 e si è qualificata.

### Analisi UCL 18/08 — Sesto Senso
**Fenerbahce vs Lyon**: Fener senza Lukaku, Amrabat, Soyuncu, Ederson, Gunok, Oosterwolde (6 assenti). Ha perso 2-1 in campionato sabato. Under 2.5 ⭐, Fener 1 ❌ rischio alto.
**Levski vs AEK**: Levski 8V/9 ma manca Sangare/Kamdem/Bouras. AEK 13 senza sconfitta ma solo amichevoli estate. DC 12 B402 ⭐⭐.
**Dinamo vs Viking**: Dinamo 11 gol in 2 qualificazioni, Viking debutto assoluto ai playoff UCL. Pick più solido della serata ⭐⭐.

---

### Schedina Svezia 18/08 (sera) — 5 selezioni
| Partita | Pick | Quota |
|---------|------|-------|
| Skovde vs Falkenbergs | 2 @1.24 | ⭐ |
| Karlstad vs Sandviken | DC X2 @1.24 | ⭐ |
| Karlbergs vs Brage | DC X2 @1.33 | ⭐ |
| Eskilstuna vs Oddevold | 2 @1.51 | 👀 |
| Nosaby vs Trelleborg | DC 1X @1.80 | 👀 |

**Quota: 5.55×** · Tutte le partite ore 18:30 · Quote verificate e inserite su Netwin

---

## Sessione 19 Agosto 2026 — Riepilogo Lavoro Svolto

### Schedine HTML create (19 Agosto 2026)
| File | Contenuto | Quota | Esito |
|------|-----------|-------|:---:|
| `reports/schedina_asia_19ago.html` | 5 selezioni Asia & Coppe: Shanghai Port 1 + Pohang 1 + Jeonbuk 1 + Nagano 1 + Reilac Shiga 1 | **4.05×** | Conclusa |
| `reports/schedina_doppia_pomeriggio_19ago.html` | 2 Multiple Pomeriggio: Super Sicura (5 eventi 3.84x) + Maxi Quota (11 eventi 119x) | **3.84×** / **119.37×** | Conclusa |
| `reports/schedina_merge_sicura_19ago.html` | **Merge Super Sicura (6 eventi)**: Simba Over 1.5 + Ordabasy Over 1.5 + Kifisia Over 1.5 + Slobozia DC X2 + Sepsi DC X2 + Celtic 1 Corner | **4.36×** (~4.80×) | **CASSA PIENA 100% VINCENTE! 🏆** |
| `reports/schedina_serale_19ago.html` | 2 Multiple Serata: Super Sicura Serale (6 eventi 3.88x) + Alta Quota (8 eventi 22.62x) | **3.88×** | **CASSA PIENA 100% VINCENTE! 🏆 (€30 ➔ €116.60)** |

### Lezioni Apprese & Validazioni (19 Agosto 2026)
1. **Trappola 1X2 in Trasferta nelle Coppe Secche**: East Bengal finita 0-0 nei 90 min (2 pali). Il segno 2 secco nelle coppe a eliminazione diretta è rischioso; le **Doppie Chance X2** (es. Slobozia e Sepsi) e gli **Over 1.5** (Simba, Ordabasy, Kifisia) garantiscono la sicurezza matematica.
2. **Successo della Strategia Merge & Super Sicura**: Entrambe le multiple blindate (Pomeriggio @4.80x e Serata @3.88x) hanno chiuso con 6 su 6 vinte al 100%.
3. **Regola Over 2.5 Sotto Quota (@1.12-@1.18)**: L'Under inaspettato nel match KV Vesturbaer (0-1) ha mostrato che chiedere 3 gol a quota @1.12 in leghe minori ha un'asimmetria di rischio sfavorevole. Se un match ha aspettativa over ma quota schiacciata, o si scende a **Over 1.5** o si esclude la selezione.

---

### Esiti Ticket Notturni (20 Agosto 2026)
- **Ticket #1 (Multipla Booster 6 selezioni)**: 4 su 6 prese (Cerro DC X2 ✅, Pelotas DC 1X ✅, Houston 2 GG ✅, Forge 1 ✅, Fortaleza 1-1 ❌, Inter Miami 2 4-2 ❌) ➔ Non vincente (-€10.00).
- **Ticket #2 (Maxi Value Sesto Senso 4 selezioni)**: 2 su 4 prese (Flamengo 1 ✅, Austin FC DC X2 @2.00 ✅, Fortaleza 1-1 ❌, Columbus 1-2 ❌) ➔ Non vincente (-€10.00).

### Lesson Learned Notte 20 Agosto (Sesto Senso Rafforzato):
1. **Trappola "Posizione in Classifica vs Punti Reali" (Caso Fortaleza vs Sao Bernardo)**:
   - *Analisi*: Fortaleza sembrava favorita per la distanza in classifica (es. 5ª vs 12ª), ma il divario reale era di **soli 6 punti** in un campionato storicamente equilibrato e ad alto tasso di pareggio come la Serie B brasiliana.
   - *Regola*: **Se il distacco in classifica è ampio solo sulla carta ma la differenza reale è $\le 6$ punti, MAI forzare il segno 1 secco: giocare sempre la Doppia Chance (DC 1X) o mercati protetti (Under/No Gol)!**
2. **Conferma Value Bet Analitiche Contro-Mercato**: Centrata in pieno la quota **@2.00** su **Austin FC DC X2** (vittoria 1-2 a Seattle) grazie allo studio accurato sulle 6 sconfitte e 7 assenze di Seattle.
3. **Volatilità Leghe Riserve / Sviluppo (MLS Next Pro)**: Evitare segni secchi in trasferta (New England II caduto 4-2) a causa dei continui cambi di roster.

---

*Ultimo aggiornamento: 20 agosto 2026 ore 09:20 — BAgent su Antigravity (Tutto sincronizzato su GitHub)*

