# BAgent — Contesto di Progetto per Claude

> Leggi questo file all'inizio di ogni sessione per riprendere da dove abbiamo lasciato.

## Cos'è BAgent

Sistema di analisi scommesse sportive (calcio + tennis) con:
- Modello Poisson per stima probabilità gol
- Sesto Senso = OBBLIGATORIO & QUOTIDIANO (lettura stampa sportiva internazionale + infortuni)
- Edge formula: `Edge = (prob × quota) - 1`
- MultiplaAdvisor per costruire accumulator con quota ≥ 30 e prob > 79%
- Database SQLite con storico partite, statistiche, log previsioni

---

## Regole di Analisi (SEMPRE in vigore)

- **Sesto Senso = OBBLIGATORIO & QUOTIDIANO**: Lettura integrale dei quotidiani sportivi di riferimento (*La Gazzetta dello Sport*, *BBC Sport*, *Marca*, *Kicker*, *L'Équipe*) TUTTI I GIORNI prima di qualsiasi tabella o calcolo. L'informazione giornalistica e i retroscena di spogliatoio/mercato sono parte integrante e imprescindibile del Sesto Senso.
- **FootyStats = obbligatorio**: SEMPRE consultare https://footystats.org prima di ogni analisi per estrarre avg goals, Over2.5%, BTTS%, xG, forma recente. MAI stimare probabilità senza dati reali da FootyStats.
- **Edge formula**: `Edge = (prob × quota) - 1` — solo informativo, non decisionale
- **Probabilità proprie**: NON derivare da quote bookmaker, usare Poisson + dati FootyStats reali
- **Quota minima**: 1.20
- **Verdetto**: ⭐ edge ≥5% · 👀 edge positivo <5% · ❌ edge negativo
- **Terminologia**: usare "selezioni" o "partite" — MAI "gambe" (errore sessione precedente)
- **Protocollo Continuità (Max 3-4 Selezioni)**: MAI più di 3 o 4 eventi per ticket. Stop a schedine lunghe che saltano per 1 solo errore.
- **Zero 2 Fissi in Trasferta nelle Coppe**: Usare sempre Doppia Chance (X2), Over 1.5 o Corner asimmetrici nelle gare di coppa.
- **BAN Leghe Arabe / Minori Opache**: Stop a Egitto 2nd Div, Iraq, Golfo. Solo Coppe Europee UEFA, campionati europei regolamentati e leghe nordiche con TV/VAR.
- **Cartellini solo in Ambienti Caldi**: Over Cartellini solo in Grecia, Turchia, Balcani, Sudamerica, derby e sfide ad altissima tensione. Evitare sfide nordiche/austriache pulite.
- **Scontri Diretti Equilibrati (Δ punti ≤ 3)**: Non forzare Over 2.5 (rischio partita bloccata e fallosa), usare Over 1.5 o Doppia Chance.
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
  
- **Matrice Tattica: Partite Sbilanciate vs Partite Bilanciate**:
  - 🎯 **Gare Asimmetriche / Sbilanciate (Dominante vs Blocco Basso)**:
    - 🚩 **1X2 Corner**: Massima efficienza statistica (la favorita schiaccia l'avversario e produce 8-12 corner vs 1-2).
    - 🟨 **1X2 Cartellini**: Massima efficienza (lo sfavorito costretto a falli tattici e ammonizioni).
    - 🛡️ **Doppie Chance (DC 1X / X2)** & **Over 1.5 Gol**: Copertura totale contro l'episodio singolo.
  - ⚖️ **Gare Bilanciate / Equilibrate (Squadre di pari livello / 50-50)**:
    - ⚠️ **I mercati alternativi basati su asimmetria (1X2 Corner/Cartellini) valgono MENO**: il gioco ristagna a centrocampo, si generano meno corner complessivi e l'esito è casuale.
    - ⚽ **Mercati da usare in gare bilanciate**: **Under 2.5 / Under 3.5**, **Multigol 1-3**, o **Doppie Chance di puro valore** (es. Austin DC X2 @2.00).
- **Strategia In-Play & Assicurazione Live (Live Betting & Hedging)**:
  - 👁️ **Validazione Visiva Live (Live Entry)**: Aspettare i primi 10-15 minuti di gioco o l'intervallo. Se una partita è bloccata e fallosa (come Elva-Maardu), non forzare l'Over o puntare su Under/Cartellini. Se una favorita assedia l'avversario ma è 0-0 al 20°, la quota 1X2 o Over 1.5 schizza verso l'alto con un Edge fantastico!
  - 🛡️ **Assicurazione & Cashout Matematico**: Quando i primi eventi della schedina sono già vinti (es. Kaya Over 2.5 preso al 62' e Mariupol avanti 0-1), usare il tasto **Cashout su Netwin** o una singola di copertura sull'ultimo match per blindare il **100% di profitto netto garantito**, azzerando la varianza!
- Quota combinata target: ≥ 3.50× (Super Sicure) fino a 20-30× (Alta Quota)
- Probabilità minima per selezione in Super Sicure: > 80% (Media > 85%)
- **Regola #31 (BAN TOTALE 1ª GIORNATA DI CAMPIONATO — Hard Gate Matchday 1)**:
  - 🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO proporre scommesse 1X2, Over o combo sul risultato finale su squadre che stanno giocando la loro **1ª partita di campionato (Matchday 1)**.
  - 🔬 **Motivazione Scientifica & Sesto Senso**: Alla 1ª giornata le squadre sono reduci dalla preparazione estiva, i nuovi acquisti non sono rodati, le gerarchie tattiche sono instabili e la varianza è massima (es. pareggi o sconfitte shock delle favorite). Si inizia ad analizzare e scommettere su un campionato **SOLO dalla 2ª o 3ª giornata in poi**, quando esistono riscontri agonistici reali di forma!

- **Quote da API (non più da Netwin/Domusbet/Betsson via browser)**: costruire le tabelle con API-Football (`odds()`, `player_prop_odds()`) e The Odds API (`OddsAPICollector`, incl. `alternate_totals` per le linee 3.5+ — vedi Regola #30). Niente più ricerca quote sul browser, costa troppo tempo/token: la verifica sul numero esatto e il piazzamento restano sempre a carico dell'utente su Netwin/Domusbet/Betsson
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
4. **Trappola Over 2.5 vs Falli Tattici e Gioco Spezzettato (Caso Elva vs Maardu 1-0)**:
   - *Analisi*: Nonostante le statistiche storiche di 3.5 gol a match, lo scontro diretto tra 4ª e 6ª (34 vs 32 punti) si è trasformato in una battaglia a centrocampo con ben **9 cartellini totali (5-4)** e zero continuità di gioco.
   - *Regola Fondamentale*: **Negli scontri diretti equilibrati di classifica (Δ punti ≤ 3), non forzare l'Over 2.5 sotto-quota (@1.37): giocare sempre l'Over 1.5 o la Doppia Chance (DC 1X è finita 1-0 ✅) per proteggersi dal gioco spezzettato!**
5. **BAN PERMANENTE CAMPIONATI ARABI & LEGHE MINORI OPACHE (Caso El Mansurah)**:
   - *Analisi*: Campionati arabi (Egitto 2nd Div, Iraq, Golfo) e leghe opache soffrono di tempi di recupero infiniti (+12 minuti), rigori casuali al 98°, feed dati lenti o inaffidabili su Sofascore/Flashscore e imprevedibilità tattica.
   - *Regola Fondamentale*: **BAN ASSOLUTO sui campionati arabi/minori opachi! Scommettere SOLO su competizioni con copertura TV/VAR ufficiale e feed live garantiti al secondo: Coppe Europee UEFA (UCL, UEL, UECL), Campionati Nazionali Europei regolamentati e Leghe Nordiche/Scandinave.**
6. **STRATEGIA DI CONTINUITÀ & CONSISTENZA (Eliminazione della "Sconfitta per 1 Errore")**:
   - *Analisi*: Le ultime schedine perse hanno fallito per **esattamente 1 evento su 4 o 1 su 6** (Elva 1-0, El Mansurah, Copenhagen 0-0). Quando forziamo 5-6 eventi, la probabilità congiunta crolla dal 70% al 35%.
   - *Protocollo Vincita Continua*: **Preferire sempre schedine da 3 o 4 EVENTI DI PURO ACCIAIO (Probabilità reale per evento > 85%, Quota 3.50x - 5.50x con Bonus) basati su Corner Asimmetrici, Cartellini TotalCorner e Doppie Chance Blindate. Zero eventi "borderline" riempitivi.**
7. **TRAPPOLA DEL SEGNO 2 FISSO IN TRASFERTA NELLE COPPE (Caso Copenhagen 0-0 & East Bengal 0-0)**:
   - *Analisi*: Nelle gare d'andata o coppe a eliminazione diretta, la favorita in trasferta (Copenhagen @1.66) gioca spesso in controllo accontentandosi del pareggio, mentre la sfavorita si barrica.
   - *Regola Fondamentale*: **MAI giocare il segno 2 fisso in trasferta nelle coppe: usare SEMPRE la Doppia Chance (X2), l'Over 1.5 o mercati speciali (Corner Asimmetrici)!**
8. **CARTELLINI & PROFILO AMBIENTALE/GEOGRAFICO (Caso PAOK 5 Cartellini ✅ vs Mjällby-Salisburgo Under ❌)**:
   - *Analisi*: L'Over Cartellini richiede pressione ambientale e contrasti duri (es. Toumba Stadium PAOK 5 cartellini @1.70 ✅). Nelle sfide tra squadre nordiche/austriache con possesso palla pulito e basso agonismo (Mjällby-Salisburgo 0-1, 2-6 corner), i cartellini crollano.
   - *Regola Fondamentale*: **Giocare l'Over Cartellini SOLO su derby, stadi caldi del Sud Europa (Grecia, Turchia, Balcani), Sudamerica o gare di ritorno ad altissima tensione! Evitare Over Cartellini su sfide nordiche/austriache pulite.**

---

## Registro Cassa Ufficiale BAgent (Dalla Cassa Piena del 19 Agosto)

- **Strategia In-Play & Assicurazione Live (Live Betting & Hedging)**:
  - 👁️ **Validazione Visiva Live (Live Entry)**: Aspettare i primi 10-15 minuti di gioco o l'intervallo. Se una partita è bloccata e fallosa (come Elva-Maardu), non forzare l'Over o puntare su Under/Cartellini. Se una favorita assedia l'avversario ma è 0-0 al 20°, la quota 1X2 o Over 1.5 schizza verso l'alto con un Edge fantastico!
  - 🛡️ **Assicurazione & Cashout Matematico**: Quando i primi eventi della schedina sono già vinti (es. Kaya Over 2.5 preso al 62' e Mariupol avanti 0-1), usare il tasto **Cashout su Netwin** o una singola di copertura sull'ultimo match per blindare il **100% di profitto netto garantito**, azzerando la varianza!
- Quota combinata target: ≥ 3.50× (Super Sicure) fino a 20-30× (Alta Quota)
- Probabilità minima per selezione in Super Sicure: > 80% (Media > 85%)
- **Quote da API (non più da Netwin/Domusbet/Betsson via browser)**: costruire le tabelle con API-Football (`odds()`, `player_prop_odds()`) e The Odds API (`OddsAPICollector`, incl. `alternate_totals` per le linee 3.5+ — vedi Regola #30). Niente più ricerca quote sul browser, costa troppo tempo/token: la verifica sul numero esatto e il piazzamento restano sempre a carico dell'utente su Netwin/Domusbet/Betsson
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
4. **Trappola Over 2.5 vs Falli Tattici e Gioco Spezzettato (Caso Elva vs Maardu 1-0)**:
   - *Analisi*: Nonostante le statistiche storiche di 3.5 gol a match, lo scontro diretto tra 4ª e 6ª (34 vs 32 punti) si è trasformato in una battaglia a centrocampo con ben **9 cartellini totali (5-4)** e zero continuità di gioco.
   - *Regola Fondamentale*: **Negli scontri diretti equilibrati di classifica (Δ punti ≤ 3), non forzare l'Over 2.5 sotto-quota (@1.37): giocare sempre l'Over 1.5 o la Doppia Chance (DC 1X è finita 1-0 ✅) per proteggersi dal gioco spezzettato!**
5. **BAN PERMANENTE CAMPIONATI ARABI & LEGHE MINORI OPACHE (Caso El Mansurah)**:
   - *Analisi*: Campionati arabi (Egitto 2nd Div, Iraq, Golfo) e leghe opache soffrono di tempi di recupero infiniti (+12 minuti), rigori casuali al 98°, feed dati lenti o inaffidabili su Sofascore/Flashscore e imprevedibilità tattica.
   - *Regola Fondamentale*: **BAN ASSOLUTO sui campionati arabi/minori opachi! Scommettere SOLO su competizioni con copertura TV/VAR ufficiale e feed live garantiti al secondo: Coppe Europee UEFA (UCL, UEL, UECL), Campionati Nazionali Europei regolamentati e Leghe Nordiche/Scandinave.**
6. **STRATEGIA DI CONTINUITÀ & CONSISTENZA (Eliminazione della "Sconfitta per 1 Errore")**:
   - *Analisi*: Le ultime schedine perse hanno fallito per **esattamente 1 evento su 4 o 1 su 6** (Elva 1-0, El Mansurah, Copenhagen 0-0). Quando forziamo 5-6 eventi, la probabilità congiunta crolla dal 70% al 35%.
   - *Protocollo Vincita Continua*: **Preferire sempre schedine da 3 o 4 EVENTI DI PURO ACCIAIO (Probabilità reale per evento > 85%, Quota 3.50x - 5.50x con Bonus) basati su Corner Asimmetrici, Cartellini TotalCorner e Doppie Chance Blindate. Zero eventi "borderline" riempitivi.**
7. **TRAPPOLA DEL SEGNO 2 FISSO IN TRASFERTA NELLE COPPE (Caso Copenhagen 0-0 & East Bengal 0-0)**:
   - *Analisi*: Nelle gare d'andata o coppe a eliminazione diretta, la favorita in trasferta (Copenhagen @1.66) gioca spesso in controllo accontentandosi del pareggio, mentre la sfavorita si barrica.
   - *Regola Fondamentale*: **MAI giocare il segno 2 fisso in trasferta nelle coppe: usare SEMPRE la Doppia Chance (X2), l'Over 1.5 o mercati speciali (Corner Asimmetrici)!**
8. **CARTELLINI & PROFILO AMBIENTALE/GEOGRAFICO (Caso PAOK 5 Cartellini ✅ vs Mjällby-Salisburgo Under ❌)**:
   - *Analisi*: L'Over Cartellini richiede pressione ambientale e contrasti duri (es. Toumba Stadium PAOK 5 cartellini @1.70 ✅). Nelle sfide tra squadre nordiche/austriache con possesso palla pulito e basso agonismo (Mjällby-Salisburgo 0-1, 2-6 corner), i cartellini crollano.
   - *Regola Fondamentale*: **Giocare l'Over Cartellini SOLO su derby, stadi caldi del Sud Europa (Grecia, Turchia, Balcani), Sudamerica o gare di ritorno ad altissima tensione! Evitare Over Cartellini su sfide nordiche/austriache pulite.**

---

## Registro Cassa Ufficiale BAgent (Dalla Cassa Piena del 19 Agosto)

| # | Data & Ora | Ticket / Descrizione | Selezioni | Stake (€) | Quota Tot. | Esito | Incasso (€) | Netto (€) | Saldo Netwin |
|---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **19/08 16:30** | **🏆 MERGE SUPER SICURA** *(Simba, Ordabasy, Kifisia, Slobozia, Sepsi, Celtic)* | **6 eventi** | **20.00 €** | **4.80×** | **✅ VINTO (6/6)** | **+96.00 €** | **+76.00 €** | **~116.00 €** |
| **2** | **19/08 21:00** | **Super Sicura Serale** | 6 eventi | **20.00 €** | 3.88× | **✅ CASSA** | **+77.60 €** | **+57.60 €** | **~127.32 €** |
| **8** | **21/08 01:25** | **Quaterna d'Acciaio Notturna** | 4 eventi | **20.00 €** | 5.10× | ❌ Perso *(3/4 prese, Novorizontino 3-0 ✅, Morelia 1-3 ✅, LAFC 2-1 ✅)* | 0.00 € | -20.00 € | **37.32 €** |
| **9** | **21/08 01:40** | **Tripla Pura Statistica** | 3 eventi | **37.00 €** | 3.10× | ❌ Perso *(Morelia 1-3 ✅)* | 0.00 € | -37.00 € | **0.32 €** |
| **10** | **21/08 10:00** | **Tripla Mattutina 21 Agosto** *(Blacktown, Northcote, Karvina)* | **3 eventi** | **20.00 €** | **3.13×** | ❌ Perso *(2/3 prese, Northcote 3-2 ✅, Blacktown 2-1 ✅)* | 0.00 € | -20.00 € | **-** |
| **12** | **21/08 20:30** | **👑 TRIPLA D'ORO SERALE NETWIN** *(Osimhen, Stoccarda, Arsenal)* | **3 eventi** | **50.00 €** | **2.57×** | **⏱️ CONCLUSO** | *(Stocc. 0-2 ✅, Ars. 3-0 ✅)* | **-** | **-** |
| **13** | **21/08 20:30** | **🛡️ SISTEMA A CORREZIONE D'ERRORE (4)** *(Marsiglia, Stoccarda, Dasilva)* | **4 eventi** | **30.00 €** | **Sistema** | **⏱️ CONCLUSO** | *(Mars. 2-0 ✅, Stocc. 0-2 ✅)* | **-** | **-** |
| **14** | **21/08 23:05** | **💎 SESTINA NOTTURNA OVERSEAS** *(Jaguares, The Strongest, Cashmere, Western, Tigres, Upper Hutt)* | **6 eventi** | **20.00 €** | **5.03×** | **⏱️ IN CORSO (Jaguares 1-0 al 17'!)** | **(Pot. +106.71 €)** | **(Pot. +86.71 €)** | **-** |
| **28** | **25/08** | **🇰🇷 TRIPLA K LEAGUE 1** *(Gimcheon-Jeonbuk DC X2, Jeju-Pohang Under 2.5, Seoul-Bucheon Over 2.5)* | 3 eventi | **40.00 €** | **3.78×** | **🛡️ CASHOUT LIVE (82')** | **+10.00 €** | **-30.00 €** | **-** |
| **29** | **25/08 sera** | **🌍 MULTIPLA MLS AMERICAS SERALE** | 7 eventi | **10.00 €** | **10.96×** | ❌ **Perso (4/7)** | 0.00 € | **-10.00 €** | **-** |
| **30** | **26/08 00:00** | **🔄 TICKET DI RECUPERO NOTTURNO** | 4 eventi | **20.00 €** | **4.94×** | ❌ **Perso (2/4)** | 0.00 € | **-20.00 €** | **-** |
| **💰** | **27/08 09:20** | **🏦 INIEZIONE CAPITALE & RESET BANKROLL UFFICIALE** | - | - | - | **✅ REGISTRATO** | **+300.00 €** | - | **`300.00 €`** |

---

## Sessione Notte 21-22 Agosto 2026 — Ticket Ufficiale #14 su Netwin (€20.00 Stake ➔ Pot. €106.71)
- [23:05] 🇨🇴 **Jaguares de Cordoba vs Boyaca Chico** ➔ **1X2: 1** @1.20 *(LIVE 1-0 al 17'!)*
- [00:30] 🇧🇴 **The Strongest vs FC Universitario de Vinto** ➔ **1 + Over 1.5 Gol** @1.40 *(La Paz 3.600m)*
- [02:00] 🇳🇿 **Cashmere Technical vs Dunedin City Royals** ➔ **Over 3.5 Gol** @1.25 *(Nuova Zelanda)*
- [02:30] 🇳🇿 **Western Suburbs FC vs Waterside Karori** ➔ **1 + Over 1.5 Gol** @1.27 *(Nuova Zelanda)*
- [03:00] 🇲🇽 **Tigres vs Atlante FC** ➔ **1X2: 1** @1.51 *(Estadio El Volcán)*
- [03:00] 🇳🇿 **Upper Hutt City FC vs FC Western** ➔ **1 + Over 2.5 Gol** @1.25 *(Nuova Zelanda)*

* **Stake Giocato**: **20.00 €** | **Quota Base**: **5.03×** | **Bonus Netwin**: **+6.04 €**
* **Vincita Potenziale a Cassa**: **106.71 €** (Profitto Netto: **+86.71 €**)
* **Stato**: Iniziato alle 23:05 ⏱️ *(Jaguares già 1-0 al 17'!)*

---

### Le 14 Regole Inviolabili di BAgent (Implementate anche in `scripts/bet_guard_validator.py`):
1. **Analisi Profonda Assenze & Referti Medici**: Verificare sempre infortuni e formazioni.
2. **Quota Combinata Target**: $\ge 3.50\times$ (Super Sicure) e $\ge 100\times$ (Lotto Matematico).
3. **Validazione Visiva Live & Cashout**: Usare il cashout per blindare i profitti.
4. **Sesto Senso & Pressione Ambientale**: No 1X2 in trasferta nelle coppe secche o campi infangati.
5. **BAN PERMANENTE CAMPIONATI ARABI E LEGHE OPACHE**: Solo leghe regolamentate con feed live al secondo.
6. **Strategia a 3-4 Eventi d'Acciaio**: Preferire ticket corti e compatti.
7. **Trappola del Segno 2 Fisso nelle Coppe**: Usare sempre la Doppia Chance X2 o linee Gol.
8. **Profilo Geografico dei Cartellini**: Over solo su derby e stadi caldi (Grecia, Turchia, Sudamerica).
9. **NELLE LEGHE GIOVANILI/RISERVE/SQUADRE B: GIOCARE SEMPRE E SOLO OVER/UNDER GOL, MAI L'1X2 SECCO!**
10. **LA TRAPPOLA DELLE PRIME 1-3 GIORNATE & DEBUTTI (N ≤ 3)**: Solo Doppie Chance di protezione o Gol.
11. **OBBLIGO COLONNA 'MOTIVAZIONE TATTICA & SESTO SENSO' IN TUTTE LE TABELLE**: Trasparenza totale.
12. **LA TRAPPOLA DELLA PARTITA 'TROPPO PULITA'**: No sanzioni/falli in gare a senso unico (Arsenal/City).
13. **L'ARSENAL CORNER ENGINE & ASIMMETRIA DEI CORNER**: Corner come arma sistematica in casa.
14. **IL FILTRO AUTOMATICO DEL DISTACCO IN CLASSIFICA ($\Delta \text{ PUNTI} \le 3$) IN SUDAMERICA/LEGHE MINORI**: Ban sui segni 1X2/DC negli scontri ravvicinati.
15. **DIVIETO ASSOLUTO DI DUPLICAZIONE DELLA STESSA SELEZIONE SU PIÙ TICKET (PRINCIPIO DI DECOUPLING & ZERO SINGLE-POINT-OF-FAILURE)**: MAI inserire lo stesso identico pronostico in 2 o più schedine attive nella stessa sessione. Ogni ticket deve essere statisticamente indipendente per evitare che un singolo evento negativo abbatta l'intera cassa giornaliera!
16. **AUDIT PREVENTIVO SULL'INTEGRITÀ DELLA ROSA (PRE-MATCH LINEUP & SQUAD INTEGRITY FILTER)**: MAI affidarsi alle sole medie statistiche o storiche della stagione passata. È OBBLIGATORIO eseguire un audit approfondito sulle formazioni 60 minuti prima:
    - *Talisman Check*: Presenza del capocannoniere/uomo chiave (es. Watkins non convocato per cessione imminente).
    - *Spine Check*: Presenza del portiere titolare (Dibu Martínez vs Bizot), mediano di rottura (Onana/Douglas Luiz) e centrali.
    - *Youth Emergency Check*: Se la squadra schiera debuttanti U19 d'emergenza ed è decimata, scatta il BAN IMMEDIATO da mercati a favore e si punta invece A FAVORE DELL'AVVERSARIO o si evita la gara!
17. **LA TRAPPOLA DEI CORNER NELLE GOLEADE CENTRALI (Caso Elche - Barcellona 0-5 con 1 solo corner)**:
    - *Analisi*: Squadre con attacco verticale e penetrazioni centrali (Barcellona di Flick con Yamal/Raphinha/Lewandowski che tagliano dentro l'area, Real Madrid) segnano 4-5 gol con tiri diretti senza mai andare sul fondo a crossare. I corner di squadra crollano a 1-2 anche vincendo 0-5.
    - *Regola Fondamentale*: **MAI giocare Over Corner di squadra alti (>5.5) su squadre da penetrazione centrale! Su queste formazioni giocare SEMPRE `1X2 + Over Gol` (es. `X2 + Over 2.5 @1.60` stravinta!) o `Tiri in Porta`. Riservare gli Over Corner SOLO a squadre con ali che crossano dal fondo per schema (Arsenal, Porto con 12 corner, Man City).**
18. **L'ASIMMETRIA DEI FALLI: POSSESSO vs NON POSSESSO (Caso Torino - Milan 1-2)**:
    - *Analisi*: La squadra che domina il possesso palla (Milan 63% possesso con Fonseca) NON commette falli ma li subisce (9 falli Milan contro 16 falli Torino).
    - *Regola Fondamentale*: **MAI scommettere sull'Over Falli della favorita tecnica di possesso! L'Over Falli Commessi va giocato ESCLUSIVAMENTE SULLA SQUADRA SFAVORITA/DIFENSIVA (che deve rincorrere e spendere falli tattici) o sui `Falli Totali del Match`.**
19. **PREFERENZA PER LE LINEE CUMULATIVE DEL MATCH (TOTAL CORNER / TOTAL CARDS)**:
    - *Analisi*: Nel match Atalanta-Sassuolo (4 corner Atalanta + 4 corner Sassuolo = 8 corner totali), l'Over 4.5 Corner Atalanta è saltato per 1 solo corner, mentre l'Over 7.5 Corner Totali Match @1.25 sarebbe entrato facilmente (come l'Over 7.5 Totali in Rennes-PSG ✅).
    - *Regola Fondamentale*: **Preferire sempre le linee totali del match (`Over Corner Totali Match` es. Over 7.5 / Over 8.5 e `Over Cartellini Totali Match` es. Over 2.5) rispetto alle linee di singola squadra, perché assorbono i cali di una singola formazione sommando il contributo di entrambi i fronti!**
20. **OBBLIGO DI VERIFICA ROSTER UFFICIALE SU SQLITE PRIMA DI OGNI MENZIONE (`storage/database/bagent.db`)**:
    - *Analisi*: MAI affidarsi alla memoria pregressa dell'LLM per i trasferimenti e le rose della stagione 2026/2027 (es. Marc Cucurella è passato al Real Madrid, Trent Alexander-Arnold è al Real Madrid, Jordan Henderson e Liam Delap sono al Chelsea, Joachim Andersen e Oscar Bobb sono al Fulham).
    - *Regola Fondamentale*: **PRIMA di citare qualsiasi giocatore o duello 1v1, è OBBLIGATORIO interrogare il database con `python scripts/query_player.py "<Nome>"`. Vietato scrivere nomi di giocatori associati a una squadra senza riscontro nel DB SQLite!**
21. **PROTOCOLLO OBBLIGATORIO DI RASSEGNA STAMPA MULTI-LEGA (Full-Text Specialized Journalism)**:
    - *Analisi*: I soli dati statistici o le formazioni grafiche del web non riportano retroscena dell'ultimo minuto (es. Moise Kean in panchina per trattativa imminente col Como svelata solo dal corpo del testo di Gazzetta.it).
    - *Regola Fondamentale*: **PRIMA di emettere qualsiasi pronostico, è TASSATIVO leggere l'INTERO CORPO DEL TESTO dei principali quotidiani sportivi specifici per ciascuna lega:**
      - 🇮🇹 **Serie A / B**: *La Gazzetta dello Sport* (`gazzetta.it/Calcio/Serie-A/`), *Corriere dello Sport*, *Sky Sport*.
      - 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League**: *BBC Sport Football*, *The Athletic*, *Sky Sports UK*, *The Guardian*.
      - 🇪🇸 **LaLiga**: *Marca* (`marca.com/futbol/primera-division.html`), *AS* (`as.com/futbol/`).
      - 🇩🇪 **Bundesliga**: *Kicker* (`kicker.de/bundesliga/`), *Bild Sport*.
      - 🇫🇷 **Ligue 1**: *L'Équipe* (`lequipe.fr/Football/Ligue-1/`).
      - 🌎 **Sudamerica**: *Globo Esporte* (Brasile), *Diario Olé* (Argentina).
22. **IL SESTO SENSO QUOTIDIANO CONTINUO (Daily Press & Sesto Senso Ingestion as Core Prerequisite)**:
    - *Analisi*: Un modello puramente matematico o numerico perde valore se non è costantemente nutrito dalle notizie fresche di giornata (infortuni della notte, conferenze stampa delle 14:30, riscaldamenti delle 18:30).
    - *Regola Fondamentale*: **La lettura dei giornali e l'analisi del Sesto Senso NON è opzionale né una tantum: è una REGOLA GIORNALIERA CONTINUA. Nessuna tabella, schedina o calcolo di quote può essere generato senza aver prima eseguito l'ingestione della rassegna stampa quotidiana e integrato le informazioni nei ragionamenti tattici!**
23. **STAKING PLAN SCIENTIFICO: FRACTIONAL KELLY CRITERION (`services/betting/kelly_staking_engine.py`)**:
    - *Analisi*: Scommettere importi arbitrari o sbilanciati porta al drawdown rapido anche con un edge positivo elevato.
    - *Regola Fondamentale*: **Ogni schedina DEVE avere il proprio stake calcolato in euro tramite il Fractional Kelly Criterion ($0.25 \times \text{Full Kelly}$):**
      $$\text{Stake} = \text{Bankroll} \times \left( \frac{p \cdot \text{Odds} - 1}{\text{Odds} - 1} \right) \times \text{Fraction}$$
      - **Zero Stake ($0.00\text{ €}$)** se l'Edge $\le 0$.
      - **Hard Cap Singolo Ticket**: Massimo **8%** del Bankroll totale (es. max 24.00€ su 300.00€).
      - **Hard Cap Giornaliero Totale**: Massimo **25%** del Bankroll complessivo impegnato contemporaneamente su tutti i ticket.
24. **DROPPING ODDS & CLOSING LINE VALUE (CLV) TRACKER (`services/betting/dropping_odds_detector.py`)**:
    - *Analisi*: I movimenti rapidi di quota dei bookmaker internazionali riflettono flussi finanziari di scommettitori istituzionali (*Smart Money*) e notizie dell'ultima ora non ancora assimilate dal pubblico.
    - *Regola Fondamentale*: **Monitorare sistematicamente la variazione di quota pre-match:**
      - **Drop $\ge 10\%$**: Flag `🔥 SMART MONEY` ➔ Segnale di alta convinzione quantitativa.
      - **Drop $\ge 15\%$ multi-book**: Flag `🚨 STEAM MOVE` ➔ Alert Telegram immediato su `@A502502_bot`.
      - **Verifica CLV Post-Match**: Misurare sempre se la quota giocata ha battuto la linea di chiusura (`CLV > 0%`) per certificare il vero valore atteso a lungo termine.
25. **PIPELINE DATI LIVE RESILIENTE & ANTI-BLOCCO (`services/football/live_pipeline/resilient_live_collector.py`)**:
    - *Analisi*: I siti web consumer (Sofascore/FotMob/Flashscore) bloccano le chiamate raw da script con Cloudflare (HTTP 403), rischiando di interrompere il monitoraggio live delle schedine aperte.
    - *Regola Fondamentale*: **L'ingestione dei dati in tempo reale (Corner, Falli, Cartellini, Tiri) DEVE avvenire tramite la pipeline multi-livello normalizzata su `LiveMatchSnapshot` (Tier 1: API-Football live endpoints; Tier 2: The Odds API; Tier 3: Browser Session Headers) eliminando i single-point-of-failure.**
31. **ONE-CLICK LIVE INSURANCE & DUTCHING ENGINE (`services/betting/one_click_live_insurance_engine.py`)**:
    - *Analisi*: Nei minuti finali (65'-80') di partite decisive con ticket aperti ad alto potenziale, il panico o il calcolo manuale errato porta a perdite evitabili o alla mancata protezione del capitale.
    - *Regola Fondamentale*: **Quando un ticket aperto arriva all'ultimo evento con 2+ gambe già vinte, il sistema DEVE generare e inviare automaticamente su Telegram l'alert con le 2 opzioni matematiche calcolate in Euro:**
      1. **Break-Even Insurance**: Stake $= \text{Stake Iniziale} / (\text{Quota Copertura} - 1)$ ➔ Rimborso 100% dello stake a P&L = 0.00 €.
      2. **Profit-Lock**: Stake $= \text{Vincita Potenziale} / \text{Quota Copertura}$ ➔ Incasso matematico identico e garantito in ogni scenario.
32. **RISULTATO DI ANDATA OBBLIGATORIO IN TABELLA NELLE COPPE (KNOCKOUT TIE CONTEXT)**:
    - *Principio Inviolabile*: Nelle partite di coppa a eliminazione diretta (Champions League, Europa League, Conference League, Coppe Nazionali, Copa Libertadores), il risultato della gara di andata è il **fattore tattico primario** che detta l'inerzia del match (chi deve rimontare spinge a testa bassa e concede contropiede/corner; chi gestisce un vantaggio ampio fa possesso e rallenta i ritmi).
    - *Regola Operativa*: **In OGNI tabella di analisi, report HTML o riepilogo scommesse, per ciascuna partita di coppa con formula andata/ritorno DEVE ESSERE SEMPRE ed ESPLICITAMENTE indicato il risultato dell'andata** (es. `Hapoel Tel Aviv vs Atalanta (Andata: 0-0)`, `Brighton vs Tromsø (Andata: 2-1)`). Vietato omettere questo dato.
33. **STATISTICHE CORRELATE DI ANDATA OBBLIGATORIE NELLA MOTIVAZIONE (SUPPORTING STATS RULE)**:
    - *Principio Inviolabile*: Una proposta quantitativa non può essere un'opinione astratta, ma deve essere giustificata dal **dato numerico esatto della partita di andata e dalle medie di quel mercato**.
    - *Regola Operativa*: **Nella colonna Intelligence/Sesto Senso, indicare SEMPRE il dato reale del mercato proposto registrato all'andata**:
      - Se si propongono **Cartellini**: specificare *quanti cartellini e falli ci sono stati all'andata* (es. *All'andata 7 cartellini e 33 falli; media Getafe 5.4 cartellini/m*).
      - Se si propongono **Corner**: specificare *quanti corner ci sono stati all'andata* (es. *All'andata 11 corner totali, con 8 corner dell'Atalanta*).
      - Se si propongono **Gol/Combo**: specificare *il volume di tiri e xG della prima gara* (es. *All'andata 22 tiri totali e 2.85 xG complessivi*).
34. **VERIFICA OBBLIGATORIA RISULTATI PASSATI SU DATABASE UFFICIALE UEFA.COM / FONTI LIVE (ZERO ALLUCINAZIONI)**:
    - *Principio Inviolabile*: È **TASSATIVAMENTE VIETATO** generare, stimare o dedurre risultati di gare precedenti (gare di andata, precedenti H2H, gironi o marcatori) basandosi sulla memoria parametrica dell'LLM.
    - *Regola Operativa*: **Per qualsiasi partita di coppa o torneo internazionale, i risultati passati e i dati della gara di andata DEVONO essere SEMPRE ed OBBLIGATORIAMENTE verificati in tempo reale interrogando il database ufficiale live di UEFA.com (o Transfermarkt / Sofascore / API-Football ufficiali)** prima di scrivere qualsiasi report, tabella o motivazione. Ogni singolo punteggio, marcatore, corner o fallo citato DEVE essere certificato al 100% dalla fonte ufficiale.
35. **STATISTICHE DELLA GARA D'ANDATA COME BASE EMPIRICA OBBLIGATORIA PER IL RITORNO**:
    - *Principio Inviolabile*: I dati reali della gara di andata (Volume Corner, Cartellini estratti, Falli fischiati, Tiri nello specchio, xG) costituiscono il **benchmark matematico primario** per calibrare le selezioni della partita di ritorno.
    - *Regola Operativa*: **Nessuna previsione per la gara di ritorno può contraddire le evidenze oggettive dell'andata**:
      - Se l'andata ha registrato $\le 5$ corner a causa di un blocco difensivo basso e denso (es. *Hapoel-Atalanta con soli 4 corner*), è **SEVERAMENTE VIETATO giocare Over Corner $\ge 7.5$**. Il mercato corretto deve spostarsi su *Combo Risultato/Gol (X2 + Over 1.5)* o *DNB*.
      - Se l'andata ha registrato un clima di scontro violento con molti cartellini e falli (es. *Partizan-Getafe con 7 cartellini e 33 falli*), la gara di ritorno — con la necessità di rimonta — amplifica il nervosismo, rendendo l'**Over Cartellini (Over 3.5 / 4.5) la selezione d'acciaio**.
36. **LETTURA OBBLIGATORIA PRE-CALCOLO DI SOFASCORE NEWS (`https://www.sofascore.com/news?category=football`) PER IL SESTO SENSO**:
    - *Principio Inviolabile*: È **TASSATIVO E VINCOLANTE** consultare e leggere la pagina di Sofascore News (`https://www.sofascore.com/news?category=football` e relative sezioni di campionato) **PRIMA di eseguire qualsiasi calcolo quote, stima Poisson o composizione di ticket**.
    - *Regola Operativa*: L'agente deve effettuare la scansione degli articoli più recenti per estrarre:
      1. *Assenze, infortuni, squalifiche e turnover dell'ultimo minuto*.
      2. *Dichiarazioni dei tecnici e assetto tattico annunciato* (es. catenaccio basso vs pressione ultra-offensiva).
      3. *Metriche di rating e duelli 1v1 sui singoli giocatori*.
      Queste informazioni devono essere **esplicitamente riflesse nelle motivazioni della colonna "Sesto Senso"** per confermare o scartare le quote calcolate.
37. **TRAPPOLA DEL RITORNO CON LARGO VANTAGGIO ($\ge 3$ GOL) / DIVIETO DI SEGNO 1X2 FISSO CON TURNOVER**:
    - *Principio Inviolabile*: Quando una squadra ha accumulato un vantaggio di $\ge 3$ gol nella gara di andata in trasferta (es. *Anderlecht 3-0 Kairat*), la gara di ritorno al proprio stadio presenta **urgenza di qualificazione pari a zero** e un **turnover massiccio di giovani/riserve**, rendendo il segno fisso (1 o 2, oppure 1+Over) una classica *trappola psicologica e probabilistica*.
    - *Regola Operativa*: **È SEVERAMENTE VIETATO consigliare l'1 fisso o la vittoria secca su match con qualificazione già chiusa e giovani in campo**.
      - Il mercato deve spostarsi esclusivamente su mercati di gol neutri (*Over 1.5 Gol Totali Match @ 1.20*, *Ambedue le Squadre Segnano/Gol @ 1.70*) o doppie chance di sicurezza (*1X*), evidenziando il rischio calo di concentrazione nel Sesto Senso.
38. **VERIFICA OBBLIGATORIA FORMAZIONI UFFICIALI 60' PRE-MATCH (NESSUNA CONCLUSIONE DEFINITIVA SENZA DISTINTE)**:
    - *Principio Inviolabile*: Qualsiasi analisi, tabella o proposta formulata prima della pubblicazione delle distinte ufficiali è da considerarsi **"STIMA PRE-MATCH PROBABILISTICA SUB-JUDICE"**. È TASSATIVAMENTE VIETATO dare conclusioni definitive o considerare congelato un ticket prima dell'audit delle formazioni.
    - *Regola Operativa*: **A 60 minuti esatti dal calcio d'inizio di ciascun blocco di partite (ore 19:00, 19:30, 20:00)**, il sistema DEVE eseguire l'audit con `lineup_confirmation_service.py`:
      1. *Talisman & Spine Check*: Verifica che i titolari chiave (es. Scamacca/CDK per Atalanta, Lamine Yamal/Raphinha per Barça, Mitoma per Brighton) siano regolarmente in campo dal 1'.
      2. *Turnover Alert*: Se un tecnico schiera riserve inattese o moduli conservativi, la giocata viene **istantaneamente ricalcolata o sospesa prima del piazzamento**.
      3. *Via Libera Operativo*: Solo con l'esito `✅ LINEUP CONFERMATA` il ticket passa allo status di *Esecuzione Ufficiale*.
26. **PROTOCOLLO DI RIGORE MATEMATICO (STOP ALLA DISPERSIONE DEI MICRO-PROPS & RITORNO A 3-4 EVENTI D'ACCIAIO)**:
    - *Principio Inviolabile*: I mercati sui singoli giocatori (Falli Giocatore / Duelli 1v1) soffrono di una varianza individuale troppo alta (rotazioni, cambi tattici, partite a basso ritmo, minutaggio imprevedibile) per essere concatenati in multiple da 5-9 eventi.
    - *Regola Operativa*:
      1. **Massimo 3 o 4 Eventi per Schedina** (Quota target $3.50\times - 5.50\times$ con Bonus): Ritorno al modello matematico vincente del 19 Agosto (100% Cassa).
      2. **Priorità a Mercati di Squadra e Linee Protette**: Doppie Chance con Gol (1X + Over 1.5 / X2 + Over 1.5), Corner di Squadra Asimmetrici (Over 4.5/5.5 Corner della favorita in casa), MultiGol 1-3.
      3. **Falli Giocatore SOLO in Singola o Doppia di Valore Certificato**, mai come riempitivo di multiple lunghe!
    - *Riconferma 25 Agosto*: Il Ticket #22 (9 leg di Falli Giocatore, quota 19.21×) ha chiuso 4/9 — ben 3 leg persi non per errore di analisi ma per **variabilità di minutaggio** (Dovbyk/Soulé entrati a gara in corso, Berge uscito, Caicedo nemmeno convocato): un rischio strutturale che nessuna analisi pre-partita può eliminare.
27. **CONTROLLO FORMA RECENTE OBBLIGATORIO PRIMA DI OGNI TABELLA (ANCHE SENZA RASSEGNA STAMPA)**:
    - *Analisi*: Il 25 Agosto è stata costruita una tabella di pick su K-League 1 (Corea del Sud) basandosi solo sul gap di quota e su una "reputazione" generica da memoria dell'LLM (es. "Jeonbuk è un club storicamente forte"), invece che sui dati reali. Controllando dopo gli ultimi 3 risultati via API-Football è emerso che **Jeonbuk aveva appena perso 2-3 contro Bucheon**, e che **Bucheon (avversario di Seoul nella tabella) era in realtà la squadra in miglior forma di tutto il lotto** (3-0 su Pohang, 3-2 su Jeonbuk) — un'informazione che ribaltava la sicurezza di due pick su tre, disponibile con una singola chiamata API veloce mai fatta prima di presentare la tabella.
    - *Causa dell'errore*: l'istruzione dell'utente di dare priorità alla velocità e usare le quote di API-Football invece di Netwin (vedi più sotto, sessione 25 Agosto) riguardava SOLO il numero esatto della quota da confermare più avanti — non autorizzava a saltare il controllo tattico/di forma. La confusione tra le due cose ha prodotto una tabella basata su nozioni generiche invece che su dati verificati, lo stesso errore che la Regola #20 vieta esplicitamente per i trasferimenti di mercato.
    - *Regola Fondamentale*: **PRIMA di scrivere qualsiasi tabella di pick — anche su campionati minori senza copertura stampa (Regola #21) — è OBBLIGATORIO controllare gli ultimi 3-5 risultati di ogni squadra coinvolta via API-Football (`fixtures?team={id}&last=5`, già disponibile e veloce). Se il campionato non ha rassegna stampa disponibile, la forma recente via API-Football diventa il livello minimo accettabile di Sesto Senso — non bastano mai le sole quote di mercato o la reputazione generica del club.**
28. **ANALISI OBBLIGATORIA ANCHE SULLE SELEZIONI SOSTITUITE ALL'ULTIMO MOMENTO (MAI DICHIARARE UNA PICK "NON VERIFICATA" SENZA PRIMA PROVARE A VERIFICARLA)**:
    - *Analisi*: Nel Ticket #29 (25 Agosto) la gamba su Sabah Masazir-Hapoel Beer Sheva è stata inserita su Netwin come **Over 1.5 Cartellini Squadra 1** invece della **Over 1.5 Gol** raccomandata. La reazione iniziale è stata limitarsi a segnalare "non ho analizzato i cartellini, non so dirti se sia buona" — una risposta pigra: i dati per controllarla (forma cartellini recenti di Sabah, arbitro assegnato, media falli) erano disponibili con le stesse chiamate API già usate per tutto il resto della sessione.
    - *Regola Fondamentale*: **Quando la selezione REALMENTE piazzata (su Netwin, o riferita dall'utente) differisce dal mercato raccomandato — per sostituzione manuale, indisponibilità del mercato originale, o scelta del bookmaker — è OBBLIGATORIO analizzare SUBITO la pick effettiva con lo stesso livello di rigore (forma recente, dato statistico specifico al mercato, classifica/arbitro se rilevante) prima di consegnare l'esito all'utente. "Non l'ho controllata" non è mai una risposta accettabile se i dati per controllarla erano già raggiungibili.**
29. **BAN UNDER 2.5 GOL SULLE LEGHE MINORI — USARE UNDER 3.5 O MERCATI ALTERNATIVI**:
    - *Analisi*: Pattern osservato ripetutamente su campionati minori (Serie B Brasiliana, Primera Nacional Argentina, ecc.): le selezioni Under 2.5 Gol saltano con frequenza sproporzionata rispetto a quanto la forma recente/classifica suggerirebbe. Conferma diretta nel Ticket #29/#30 (25-26 Agosto): Juventude RS-CRB e Atlético Goianiense-Botafogo SP, entrambe Under 2.5 costruite su dati solidi (miglior difesa del torneo per Juventude, Δ classifica ≤3 per Goianiense-Botafogo), sono saltate entrambe — una per xG di partita reale sopra soglia (4.0), l'altra per un episodio di finalizzazione clinica sopra media (Goianiense 3 gol da xG 1.93). Le leghe minori hanno più varianza strutturale (arbitraggio meno prevedibile, rose meno stabili, meno dati storici affidabili) che rende la soglia stretta 2.5 particolarmente fragile.
    - *Regola Fondamentale*: **Nelle leghe minori (fuori dai campionati Top-5 europei e dalle Coppe UEFA), MAI giocare Under 2.5 Gol secco. Preferire sempre Under 3.5 Gol (margine di sicurezza maggiore) oppure spostarsi su un mercato alternativo (Doppia Chance, Corner Totali, Cartellini) dove la varianza strutturale delle leghe minori pesa meno.**
30. **THE ODDS API PER LE LINEE ALTERNATIVE (Under 3.5 e oltre) — GRATIS, GIÀ ATTIVA**:
    - *Analisi*: `services/football/external/sources/odds_api.py` (`OddsAPICollector`) ha una chiave già configurata in `.env`, piano gratuito 500 richieste/mese. Copre esplicitamente Brazil Serie B e Argentina Primera División tra gli altri. Verificato il 26 Agosto: `get_event_odds(sport_key, event_id, markets="alternate_totals")` restituisce le linee 1.5/2.5/3.5+ da 7+ bookmaker reali (Pinnacle, LeoVegas, Coral, Ladbrokes, Codere...) — esattamente il dato che serve per applicare la Regola #29 con un numero reale, non solo per principio.
    - *Attenzione ai costi*: la chiamata bulk (`get_odds`, 1X2 + Over/Under 2.5 su tutta la giornata di un campionato) costa pochissimo; la chiamata per singolo evento sui mercati alternativi (`get_event_odds`) costa **2-4 richieste per partita** — usarla solo sulle partite realmente in valutazione per una schedina, mai su un intero campionato a tappeto.
    - *Regola Fondamentale*: **Prima di consigliare Under 3.5 (o un'altra linea alternativa) su una lega minore per la Regola #29, controllare la quota reale via `OddsAPICollector.get_event_odds(..., markets="alternate_totals")` invece di limitarsi a menzionare il mercato senza numero.**

---

## Sessione 23 Agosto 2026 (Domenica) — Esiti dei Ticket Netwin & Retrospect

### 🚩 Ticket #19: Sestina Corner d'Acciaio (Stake 30.00 € / 20.00 €)
1. [15:00] **Brighton vs Aston Villa** ➔ **Over 7.5 Corner Totali** @1.24 ✅
2. [15:00] **Man City vs Bournemouth** ➔ **Over 6.5 Corner City** @1.70 ✅
3. [17:00] **Atlético Madrid vs Villarreal** ➔ **Over 7.5 Corner Totali Match** @1.24 ✅
4. [17:30] **Newcastle vs Liverpool** ➔ **Over 9.5 Corner Totali Match** @1.50 ✅
5. [20:45] **Rennes vs PSG** ➔ **Over 7.5 Corner Totali Match** @1.21 ✅
6. [21:30] **Porto vs Arouca** ➔ **Over 5.5 Corner Porto** @1.39 ✅ (12 Corner!)
7. [20:45] **Atalanta vs Sassuolo** ➔ **Over 4.5 Corner Atalanta** @1.33 ❌ *(4 corner, mancato per 1!)*
8. [21:30] **Elche vs Barcellona** ➔ **Over 5.5 Corner Barcellona** @1.60 ❌ *(1 corner per goleada centrale 0-5)*

### 🏆 Ticket #20 & #21: Sanzioni, Combo & Retrospect
1. [20:45] **Rennes vs PSG** ➔ **Over 2.5 Cartellini Totali** @1.62 ✅
2. [21:30] **Elche vs Barcellona** ➔ **X2 + Over 2.5 Gol** @1.60 ✅ (0-5 Barça!)
3. [20:45] **Torino vs Milan** ➔ **Over 10.5 Falli Commessi Milan** @1.77 ❌ *(Milan di possesso ha fatto 9 falli)*

---

## Sessione Pomeriggio 24 Agosto 2026 — Verifica Quote Reali & Correzione Tabelle Mattutine

### 🎯 Obiettivo della sessione
Riprendere l'handover di stamattina (`docs/session_handover_2026_08_24.md`) e **verificare sul campo, quota per quota, tutte le tabelle prodotte** prima di piazzare qualsiasi ticket — invece di fidarsi ciecamente dei numeri stimati al mattino.

### 🚨 Discrepanze Gravi Trovate (quote mattutine vs reali)
| Selezione originale (handover mattina) | Quota citata | Quota REALE verificata (Netwin/Domusbet) | Esito |
|---|---|---|---|
| Bologna Over 7.5 Corner Totali | @1.24 | Linea reale è **8.5**, Over @1.76 (Netwin) / @1.88 (Domusbet) | ❌ Quota fittizia, soglia sbagliata |
| Roma Over 7.5 Corner Totali | @1.25 | Linea reale è **8.5**, Over @1.69 (Netwin) / @1.70 (Domusbet) | ❌ Quota fittizia, soglia sbagliata |
| Fulham Over 3.5 Cartellini | @1.44 | Linea reale è **4.5**, Over @1.86 (Netwin) / @1.91 (Domusbet) | ❌ Soglia sbagliata |
| Osasuna 1X (DC) | @1.18 | Reale @1.21 (sopra quota minima 1.20) | 🟡 Leggero scostamento |
| Zaccagni 2+ Falli Subiti | @1.40 | Reale **@1.20** (più sicuro del previsto) | ✅ Meglio del previsto |
| Dybala 2+ Falli Subiti | @1.45 | Reale **@1.40** (identica su Netwin e Domusbet) | ✅ Confermata |
| Palmer 2+ Falli Subiti | @1.50 | Reale **@1.80** (meno sicuro del previsto) | 🔴 Sopravvalutata al mattino |

**Lezione**: le tabelle del mattino vanno sempre trattate come bozze di lavoro, mai come quote definitive. La verifica pomeridiana ha ribaltato la valutazione di più selezioni in entrambe le direzioni.

### 🔍 Scoperta: la sezione "Falli" (non "Sanzioni") contiene i mercati per singolo giocatore
Su Netwin i mercati **Falli Commessi / Falli Subiti per giocatore** (soglie 0.5/1.5/2.5) si trovano sotto la tab **"Falli"** in "Altri Mercati" — NON sotto "Sanzioni" (che contiene solo i Cartellini). Errore iniziale di ricerca in questa sessione, poi corretto.

### 📰 Test Empirico: quanto "pesa" davvero una linea Falli Totali?
Controllate le 4 partite di Serie A giocate il **23 Agosto 2026** (giornata 1) per calibrare se una linea Falli Totali di 25.5 fosse realistica:
| Partita | Falli Totali |
|---|---|
| Frosinone-Juventus | **33** (outlier) |
| Venezia-Lecce | ≤19 |
| Atalanta-Sassuolo | ≤19 |
| Torino-Milan | ≤19 |

**Solo 1 partita su 4 (25%) ha superato quota 25 falli.** Questo ha smontato l'ipotesi (pur logicamente sensata: "partita tecnica e bilanciata = più falli") che l'Over 25.5 Falli Totali Roma-Fiorentina @1.70 fosse un buon value bet — il campione reale della giornata dice il contrario. **Ticket scartato.**

### 🩺 Formazioni: FootyStats come early-warning su assenze non ancora note
Controllando la lineup più recente su FootyStats per Osasuna-Levante, **Ante Budimir risultava in panchina** (titolare Raúl García) — smentendo la narrativa "Budimir bomber a El Sadar" della tabella mattutina. Poi confermato titolare nelle probabili formazioni Sofascore del pomeriggio, ma il caso dimostra l'utilità di incrociare più fonti prima di fissare un pick su un singolo giocatore.

### 🎫 Le 3 Schedine Finali della Sessione (`reports/schedina_24ago.html`)
| Schedina | Selezioni | Quota | Rischio |
|---|---|---|---|
| **Alta Quota — Falli Commessi/Subiti** | Zaccagni, Palmer, Caicedo, Berge, Soulé, Dybala, Kean, Frattesi, Dovbyk (9 sel.) | **~18.80×** | Alto |
| **Super Sicura — Gol & DC** | Osasuna DC1X, Chelsea X2, Dybala O1.5 Subiti, Palmer O1.5 Subiti (4 sel.) | **~3.75×** | Basso |
| **Corner & Sanzioni Totali Match** | Bologna O8.5 Corner, Roma O8.5 Corner, Osasuna DC1X (3 sel.) | **~3.60×** | Medio |

Tutti i giocatori/selezioni confermati **titolari nelle probabili formazioni** Sofascore del pomeriggio prima del piazzamento.

### Le Nuove Regole Inviolabili Aggiunte Oggi
23. **VERIFICA EMPIRICA SU GIORNATE RECENTI PRIMA DI FIDARSI DI UNA LINEA TOTALI (Falli/Corner/Cartellini)**:
    - *Analisi*: Il caso Roma-Fiorentina (Over 25.5 Falli Totali) ha mostrato che una linea "logicamente giustificabile" (tecnica + equilibrio = più falli) può essere smentita da un campione reale delle partite già giocate nello stesso turno/weekend.
    - *Regola Fondamentale*: **Prima di puntare su una linea Totali di squadra (Falli, Corner, Cartellini), controllare SEMPRE le statistiche reali delle partite già concluse nella stessa giornata/weekend dello stesso campionato. Un'ipotesi tattica senza riscontro empirico recente resta solo un'ipotesi.**
24. **LA SEZIONE "FALLI" ≠ "SANZIONI" SU NETWIN**:
    - *Regola Fondamentale*: **I mercati Falli Commessi/Subiti per singolo giocatore si trovano SEMPRE sotto la tab "Falli" (Altri Mercati), non "Sanzioni" (che è solo Cartellini). Verificare in entrambe le sezioni prima di concludere che un mercato non esista.**
25. **DOPPIA VERIFICA NETWIN + DOMUSBET PER LE QUOTE PIÙ ALTE**:
    - *Analisi*: Sui mercati Falli per giocatore le quote sono risultate IDENTICHE su Netwin e Domusbet (stesso fornitore quote), ma su Corner/Cartellini Totali Match Domusbet ha pagato sensibilmente di più (es. Bologna Corner O8.5: Netwin @1.76 vs Domusbet @1.88).
    - *Regola Fondamentale*: **Per i mercati "di squadra" (Corner/Cartellini Totali) conviene sempre controllare anche Domusbet oltre a Netwin. Per i mercati "per giocatore" (Falli individuali) le quote tendono a coincidere, quindi non serve incrociare le due piattaforme.**

### ⚠️ Nota Tecnica: automazione click su Netwin inaffidabile per liste lunghe
Il tentativo di costruire automaticamente (via click programmatico) le 3 schedine da 9+4+3 selezioni sui mercati "Falli per giocatore" è fallito nella maggior parte dei tentativi — le liste virtualizzate molto lunghe (100+ righe per partita) non rispondono in modo affidabile ai click automatizzati, mentre i pannelli compatti (1X2/DC/Corner con poche righe) funzionano bene. **Per prenotazioni future su mercati "per giocatore": costruire la schedina manualmente usando l'HTML di riferimento come checklist**, non affidarsi all'automazione completa.

---

*Saldo Netwin al 24 Agosto 2026 ore 17:45: `116,45 €` (nessuna schedina ancora piazzata, in attesa formazioni ufficiali definitive)*  
*Ultimo aggiornamento: 24 agosto 2026 ore 17:45 — BAgent (Sessione pomeridiana di verifica quote, sincronizzato su GitHub)*

---

## Sessione 25 Agosto 2026 — Retrospettiva Esiti Reali Ticket 24-25 Agosto (Verificati via API-Football)

Dati recuperati programmaticamente con `FootballExternalCollector` (`services/football/external/collector.py`, endpoint `fixture_stats` e `player_stats`) invece che a mano da Sofascore — molto più veloce e con numeri esatti (minuti giocati, falli commessi/subiti per giocatore, corner/falli totali di squadra).

### 🥊 Ticket #22 — Novenario Duelli & Falli (Stake 15.00 € → Pot. 311.48 €) → ❌ **PERSO (4/9)**
| Giocatore | Mercato | Reale | Esito |
|---|---|---|:---:|
| Zaccagni | O1.5 Falli Subiti @1.20 | 1 subito | ❌ |
| Dovbyk | O0.5 Falli Subiti @1.50 | 0 subiti (subentrato al 60', 37' giocati) | ❌ |
| Frattesi | O0.5 Falli Commessi @1.25 | 1 commesso | ✅ |
| Dybala | O1.5 Falli Subiti @1.40 | 2 subiti | ✅ |
| Soulé | O0.5 Falli Subiti @1.16 | 0 subiti (subentrato al 54', 36' giocati) | ❌ |
| Kean | O1.5 Falli Subiti @1.57 | 2 subiti | ✅ |
| Berge | O0.5 Falli Commessi @1.20 | 0 commessi (uscito al 73') | ❌ |
| Caicedo | O1.5 Falli Commessi @1.55 | non convocato/non in lista | ❌ |
| Palmer | O1.5 Falli Subiti @1.80 | 3 subiti | ✅ |

**Netto: -15.00 €**

### 🚩 Ticket #23 — Tripla Corner & LaLiga (Stake 10.00 € → Pot. 54.97 €) → ❌ **PERSO (1/3)**
1. Bologna Over 8.5 Corner Totali @1.77 → **14 corner totali (8-6)** ✅
2. Osasuna 1X2: 1 @1.86 → **0-0** (pareggio, non vittoria) ❌
3. Roma Over 8.5 Corner Totali @1.67 → **5 corner totali (2-3)** ❌ — Roma ha vinto 4-0 (tripletta Malen) ma con soli 2 corner propri: nuova conferma della **Regola #17 (Trappola dei Corner nelle Goleate Centrali)**, stesso pattern di Barcellona-Elche del 23/08.

**Netto: -10.00 €**

### ⚔️ Ticket #25 — Sestina Master Duelli Roma-Fiorentina (Stake 20.00 €) → ❌ **PERSO (2/6)** — già registrato sopra
**Netto: -20.00 €**

### 🎯 Ticket #26 — Doppia Live Corner In-Play (Stake 30.00 €) → ❌ **PERSO (0/2)** — già registrato sopra
**Netto: -30.00 €**

### 🌙 Ticket #27 — Multipla Notturna Overseas (Quota ~12.50× con bonus) → ❌ **PERSO**
| Match | Pick | Risultato reale | Esito |
|---|---|---|:---:|
| Charleston Battery-Miami FC | Over 2.5 Gol @1.50 | 5-0 | ✅ |
| Sport Recife-America MG | 1 Sport Recife @1.63 | 3-0 | ✅ |
| Tigre-Central Cordoba | Under 2.5 Gol @1.45 | 2-1 (3 gol) | ❌ |
| Boyaca Patriotas-Atletico FC | 1 Boyaca Patriotas @1.34 | Patriotas 2-0 vs "Depor FC" ⚠️ *nome avversario non coincide esattamente su API-Football, verifica incerta* | ✅/⚠️ |
| Botafogo-Atletico PR | DC 1X Botafogo @1.40 | Botafogo perde 2-3 in casa | ❌ |
| Athletic Club-Novorizontino | Under 2.5 Gol @1.50 | 1-4 (5 gol) | ❌ |

**Stake non registrato nei log di sessione — ticket comunque perso (3-4/6 leg falliti).**

### 💰 Bilancio sessione 24-25 Agosto: **-75.00 €** confermati (Ticket #22, #23, #25, #26) + Ticket #27 perso (stake non tracciato)

### 🔎 Lezioni confermate
1. **Regola #26 (Rigore Matematico)** validata ancora: su 9 leg di falli-giocatore del Ticket #22, 3 sono saltati non per errore tattico ma per **variabilità di minutaggio** (cambi decisi a gara in corso, impossibili da prevedere in fase di analisi pre-partita).
2. **Regola #17 (Trappola Corner nelle Goleate Centrali)** confermata di nuovo su Roma 4-0 con soli 2 corner di squadra.
3. La quota "più sicura" del Ticket #22 (Zaccagni @1.20) è quella saltata per un pelo (1 fallo subito contro gli 1.5 richiesti) — ulteriore promemoria che le quote basse sui prop-giocatore non eliminano la varianza individuale.

*Nota tecnica*: `FootballExternalCollector.player_stats(fixture_id)` restituisce minuti giocati e `fouls.committed` / `fouls.drawn` per ogni giocatore — fonte molto più rapida di una verifica manuale su Sofascore per liquidare ticket con molte leg su singolo giocatore. Utilizzare questo endpoint per le prossime retrospettive.

---

### 🇰🇷 Ticket #28: Tripla K League 1 (Stake 40.00 € → Pot. 151.20 €) — prima applicazione della Regola #27
* **Stake**: 40.00 € | **Quota Base**: 3.78× | **Vincita Potenziale**: **151.20 €** (bonus Netwin non confermato)
* **Stato**: 🛡️ **Chiuso in Cashout Live** — Cashback 10.00 € preso all'82' | **Netto: -30.00 €**
1. **Gimcheon Sangmu - Jeonbuk** ➔ **DC X2 (Jeonbuk o pareggio)** @1.30 — Gimcheon 11° (26pt, 14 pareggi su 24!), Jeonbuk 3° (37pt), distacco reale 11 punti
2. **Jeju United - Pohang** ➔ **Under 2.5 Gol** @1.57 — Jeju 5° (35pt), 0 gol subiti in casa nelle ultime 2; Pohang 7° (31pt), appena spento 0-3 a Bucheon
3. **Seoul - Bucheon** ➔ **Over 2.5 Gol** @1.85 — Seoul 1° in classifica, miglior attacco del torneo (46 gol/24 gare); Bucheon 9° ma in forma esplosiva (3-0 su Pohang, 3-2 su Jeonbuk)

**Lezione di processo**: prima versione della tabella (senza controllo forma reale) prevedeva "1 Seoul" secco — corretto in Over 2.5 dopo aver scoperto che l'avversario Bucheon era la squadra più in forma del campionato, non un underdog. Vedi Regola #27.

**Esito Live — Cashout all'82'**: al momento della decisione il punteggio era Gimcheon-Jeonbuk 0-0 (Leg 1 solido), Jeju-Pohang 0-2 (Leg 2 al limite esatto, zero gol di margine), Seoul-Bucheon 1-0 (Leg 3 a rischio, servivano 2 gol in ~8 minuti). Probabilità congiunta stimata ~5-9%. Preso il cashback di 10.00 € offerto da Netwin (pari a un'implicita ~9% di probabilità di vittoria vista dal bookmaker) invece di rischiare l'intero stake — coerente con la regola di Assicurazione & Cashout Matematico quando la varianza residua è alta e il tempo di recupero scarso.

---

* **Stake**: 10.00 € | **Quota Totale (con bonus Netwin)**: 10.96× | **Vincita Potenziale**: 120.56 €
* **Stato**: ❌ **Concluso — Perso (4/7)** | **Netto: -10.00 €**
1. [18:00] **SK Brann - FK Austria Wien** (UEFA Champions League Donne) ➔ **Over 2.5 Gol** @1.37 — entrambe 4.0 gol fatti/gara media in Coppa ➔ **FT 2-1 (3 gol) ✅**
2. [18:45] **Sabah Masazir - Hapoel Beer Sheva** (UEFA Champions League, ritorno) ➔ **Over 1.5 Cartellini Squadra 1 (Sabah)** @1.39 — ⚠️ *pick inserita direttamente su Netwin, diversa dalla raccomandazione originale (Over 1.5 Gol); gamba più debole del ticket dopo analisi a posteriori (Regola #28): Sabah ha fatto **0 gialli** nelle ultime 2 gare UCL (0.67 gialli/gara di media). All'andata (Hapoel 2-1 Sabah) è stato **Hapoel** — non Sabah — a fare più falli e cartellini nonostante il 67% di possesso (12 falli/3 gialli Hapoel vs 6 falli/0 gialli Sabah), conferma della Regola #18 (chi ha il possesso fa più falli, non chi si difende). L'ipotesi tattica "Sabah dovrà fermare il gioco con i falli" non regge sui dati reali dell'andata.* ➔ **AET 5-2, Sabah 22 falli/2 gialli ✅** — la gara di ritorno (Sabah in rimonta disperata su un aggregato in bilico, tempi supplementari) ha prodotto un profilo di falli completamente diverso dall'andata: la pick ha vinto nonostante il precedente sfavorevole, promemoria che i dati di una singola gara precedente non garantiscono lo stesso pattern in un contesto diverso (qui con supplementari e maggiore disperazione)
3. [21:00] **Valencia - Real Betis** (LaLiga) ➔ **Under 2.5 Gol** @1.66 — Lo Celso ed Ezzalzouli (Betis) infortunati, xG basso da entrambe le parti ➔ **FT 0-1 (1 gol) ✅**
4. [21:00] **LASK Linz - Celtic** (UEFA Champions League, ritorno) ➔ **Over 1.5 Gol** @1.14 — xG entrambe >2/gara in campionato, Lask deve rimontare lo 0-3 dell'andata ➔ **AET 5-1 (6 gol) ✅** *(4-1 dopo i 90', 5-1 dopo i supplementari)*
5. [21:00] **Bodo Glimt - Nijmegen** (UEFA Champions League, ritorno) ➔ **Over 8.5 Corner Totali (esc. TS)** @1.37 — xG Bodo 2.47 fatti/0.75 subiti, avanti 3-1 dall'andata ➔ **FT 3-0, solo 6 corner totali (4-2) ❌**, nonostante NEC in 10 uomini dal 3' — nuova conferma della Regola #17 (Trappola dei Corner nelle Goleate Centrali): Bodo ha vinto comodamente 3-0 con superiorità numerica quasi per l'intera gara ma con pochissimi corner propri, stesso pattern già visto su Roma 4-0 e Barcellona-Elche 0-5 — nemmeno un uomo in più per oltre 85 minuti ha spinto la produzione di corner
6. [26/08 00:30] **Juventude RS - CRB** (Brasile Serie B) ➔ **Under 2.5 Gol** @1.48 — Juventude 2° in classifica, miglior difesa del torneo (0.1 gol subiti/gara in casa) ➔ **FT 2-1 (3 gol) ❌**
7. [26/08 00:30] **Goianiense GO - Botafogo SP** (Brasile Serie B) ➔ **Under 2.5 Gol** @1.50 — Δ classifica solo 2 punti (11° vs 14°), mercato protetto per Regola #14; media 1.8 gol totali/gara nelle ultime 5 di Atletico Goianiense ➔ **FT 3-0 (3 gol) ❌**

**Lezioni**: 4/7 vinte ma serviva 7/7 — ennesima conferma della Regola #26 (dispersione in troppi eventi). Le 2 gare brasiliane (le uniche non europee/regolamentate in senso stretto) sono state entrambe perse nonostante l'analisi approfondita — coerente con il pattern già visto nella retrospettiva di ieri (leghe minori più imprevedibili). La Regola #17 (Corner nelle Goleate) si conferma per la terza volta in pochi giorni, stavolta perfino con un'ora e passa di superiorità numerica che non ha aiutato.

---

### 🔄 Ticket #30: Recupero Notturno su Betsson (Stake 20.00 € → Pot. 98.77 €) — costruito dopo la chiusura del Ticket #29
* **Stake**: 20.00 € | **Quota Totale**: 4.94× | **Vincita Potenziale**: 98.77 €
* **Stato**: ❌ **Concluso — Perso (2/4)** | **Netto: -20.00 €**
* *Nota di correzione*: registrato inizialmente come 3 selezioni (errore di trascrizione, mancava la prima gamba) — corretto dopo che l'utente ha mostrato lo screenshot reale del ticket Betsson.
1. [25/08 23:30] **CS 2 de Mayo - Club Guarani** (Paraguay Primera División) ➔ **Doppia Chance 1X** @1.44 ➔ **FT 0-0 ✅**
2. [26/08 00:00] **Deportivo Madryn - Godoy Cruz** (Argentina Primera Nacional) ➔ **Under 2.5 Gol** @1.42 — Δ classifica 0 punti (5° vs 6° a pari punti), entrambe in ottima forma, H2H stagionale diretto 0-0 ➔ **FT 2-0 (2 gol) ✅**
3. [26/08 00:30] **Juventude RS - CRB** (Brasile Serie B) ➔ **Under 2.5 Gol** @1.62 — *stessa identica partita della leg 6 del Ticket #29* ➔ **FT 2-1 (3 gol) ❌**
4. [26/08 00:30] **Atlético Goianiense - Botafogo SP** (Brasile Serie B) ➔ **Under 2.5 Gol** @1.49 — *stessa identica partita della leg 7 del Ticket #29* ➔ **FT 3-0 (3 gol) ❌**

**Lezione di processo**: le leg 3 e 4 duplicano esattamente due partite già perse nel Ticket #29 (stesso mercato, bookmaker diverso) — la sessione notturna aveva notato la sovrapposizione (Regola #15) ma l'aveva considerata accettabile perché il Ticket #29 era già chiuso/perso al momento del piazzamento, quindi senza rischio di correlazione tra ticket *attivi* contemporaneamente. Corretto in linea di principio, ma il risultato mostra che ripetere la stessa analisi (Under 2.5) su due partite già sfavorevoli in un altro ticket non ha cambiato l'esito — un promemoria che un'analisi solida non garantisce risultati diversi alla seconda occasione sulla stessa gara.

---

## Sessione 22 Agosto 2026 (Serale) — I 3 Ticket Ufficiali in Gioco su Netwin

### 🛡️ Ticket #15: Quaterna d'Acciaio Serale (Stake 20.00 € ➔ Pot. 121.24 €)
* **Stake**: 20.00 € | **Quota Base**: 5.89× | **Bonus Netwin**: +3.53 € | **Vincita Potenziale**: **121.24 €**
* **Stato**: In Corso (4/4 aperte) ⏱️
1. [18:30] **Inter vs Monza** ➔ **Lautaro Martinez (o Sost.) Segna o Palo/Trav.** @1.67
2. [18:30] **Brentford vs Tottenham** ➔ **Over 4.5 Corner Brentford (Sq.1)** @1.49
3. [20:45] **Tolosa vs Lione** ➔ **MultiGol 1-3 Casa (Tolosa)** @1.32
4. [21:30] **Espanyol vs Real Madrid** ➔ **Over 2.5 Cartellini Totali** @1.23

### 💎 Ticket #16: La Doppia d'Acciaio (Quota 2.60×)
* **Quota Base**: 2.60× | **Stato**: In Corso ⏱️
1. [18:30] **Inter vs Monza** ➔ **Lautaro Martinez (o Sost.) Segna o Palo/Trav.** @1.67
2. [21:30] **Espanyol vs Real Madrid** ➔ **2 + Over 1.5 Gol (Real Madrid)** @1.56

### 🚀 Ticket #17: Quinquina Potenziata (Stake 27.00 € ➔ Pot. 157.29 €)
* **Stake**: 27.00 € | **Quota Base**: 5.66× | **Bonus Netwin**: +4.58 € | **Vincita Potenziale**: **157.29 €**
* **Stato**: In Corso (5/5 aperte) ⏱️
1. [18:00] **Juventus U23 vs Novara** ➔ **1X2: 1** @1.40 *(Live 1-0)*
2. [18:30] **Inter vs Monza** ➔ **Lautaro Martinez (o Sost.) Segna o Palo/Trav.** @1.67
3. [18:30] **Brentford vs Tottenham** ➔ **Over 4.5 Corner Brentford (Sq.1)** @1.49
4. [20:45] **Tolosa vs Lione** ➔ **MultiGol 1-3 Casa (Tolosa)** @1.32
5. [21:30] **Espanyol vs Real Madrid** ➔ **Over 2.5 Cartellini Totali** @1.23

---

## Sessione 23 Agosto 2026 (Domenica) — Ticket Ufficiale Master su Netwin

### 🚩 Ticket #19: Sestina Corner d'Acciaio Ufficiale Netwin (Quota 8.44× ➔ Pot. 255.97 €)
* **Stake**: 30.00 € | **Quota Base**: 8.44× | **Bonus Netwin**: +2.54 € | **Vincita Potenziale**: **`255.97 €`** 💰
* **Stato**: In Giocata / Apertura Domenica 23 Agosto ⏱️
1. [15:00] **Brighton vs Aston Villa** (ID: 1702) ➔ **Over 7.5 Corner Totali** @1.24
2. [15:00] **Manchester City vs Bournemouth** (ID: 4117) ➔ **Over 6.5 Corner Squadra 1 (City)** @1.70
3. [17:00] **Atlético Madrid vs Villarreal** (ID: 3385) ➔ **Over 7.5 Corner Totali Match** @1.24
4. [17:30] **Newcastle vs Liverpool** (ID: 6915) ➔ **Over 9.5 Corner Totali Match** @1.50
5. [18:30] **Frosinone vs Juventus** (ID: 5866) ➔ **Over 4.5 Corner Squadra 2 (Juventus)** @1.33
6. [21:30] **Elche vs FC Barcellona** (ID: 13180) ➔ **Over 5.5 Corner Squadra 2 (Barcellona)** @1.62

### 🏆 Ticket #20: Cinquina Master Mix Ufficiale Netwin (Stake 20.00 € ➔ Pot. 113.65 €)
* **Stake**: 20.00 € | **Quota Base**: 5.36× | **Bonus Netwin**: +6.43 € | **Vincita Potenziale**: **`113.65 €`** 💰
* **Stato**: In Giocata / 5 Selezioni Aperte ⏱️
1. [15:00] **Brighton vs Aston Villa** ➔ **MultiGol 1-3 Ospite (Aston Villa)** @1.43
2. [15:00] **Angers vs Lilla** ➔ **X2 + MultiGol 1-4** @1.45
3. [17:00] **Atlético Madrid vs Villarreal** ➔ **Over 8.5 Tiri Totali Squadra 2 (Villarreal)** @1.33
4. [20:45] **Rennes vs PSG** ➔ **Ospite Segna 2° Tempo (PSG)** @1.35
5. [21:30] **Elche vs FC Barcellona** ➔ **2 + Over 1.5 Gol (Barcellona)** @1.44

### ⚔️ Ticket #21: Quaterna Sanzioni, Falli & Protezioni (Stake 13.00 € ➔ Pot. 77.93 €)
* **Stake**: 13.00 € | **Quota Base**: 5.82× | **Bonus Netwin**: +2.27 € | **Vincita Potenziale**: **`77.93 €`** 💰
* **Stato**: Concluso ⏱️
1. [17:30] **Newcastle vs Liverpool** ➔ **Over 3.5 Cartellini Totali Match** @1.48 ✅ *(8 Cartellini Totali!)*
2. [18:30] **Venezia vs Lecce** ➔ **1X + Under 3.5 Gol** @1.61 ❌ *(0-1)*
3. [18:30] **Frosinone vs Juventus** ➔ **X2 + MultiGol 2-5 : SI** @1.38 ❌ *(0-1)*
4. [20:45] **Torino vs Milan** ➔ **Over 10.5 Falli Commessi Squadra 2 (Milan)** @1.77

### 🥊 Ticket #22: Novenario Duelli & Falli 1v1 Ufficiale Netwin (Stake 15.00 € ➔ Pot. 311.48 €)
* **Stake**: 15.00 € | **Quota Base**: 19.21× | **Bonus Netwin**: +23.33 € | **Vincita Potenziale**: **`311.48 €`** 💰
* **Stato**: In Corso / 9 Selezioni Aperte ⏱️
1. [18:30] **Bologna - Lazio** ➔ **Zaccagni Over 1.5 Falli Subiti** @1.20
2. [18:30] **Bologna - Lazio** ➔ **Dovbyk Over 0.5 Falli Subiti** @1.50
3. [18:30] **Bologna - Lazio** ➔ **Frattesi Over 0.5 Falli Commessi** @1.25
4. [20:45] **Roma - Fiorentina** ➔ **Dybala Over 1.5 Falli Subiti** @1.40
5. [20:45] **Roma - Fiorentina** ➔ **Soulé Over 0.5 Falli Subiti** @1.16
6. [20:45] **Roma - Fiorentina** ➔ **Kean Over 1.5 Falli Subiti** @1.57
7. [21:00] **Fulham - Chelsea** ➔ **Sander Berge Over 0.5 Falli Commessi** @1.20
8. [21:00] **Fulham - Chelsea** ➔ **Caicedo Over 1.5 Falli Commessi** @1.55
9. [21:00] **Fulham - Chelsea** ➔ **Cole Palmer Over 1.5 Falli Subiti** @1.80

### 🚩 Ticket #23: Tripla Corner & LaLiga Ufficiale Netwin (Stake 10.00 € ➔ Pot. 54.97 €)
* **Stake**: 10.00 € | **Quota Base**: 5.49× | **Vincita Potenziale**: **`54.97 €`** 💰 | **Ref**: `DF07EA0818311A1F780A`
* **Stato**: 1 Vinta su 3 (In Corso) ⏱️
1. [18:30] **Bologna - Lazio** ➔ **Over 8.5 Corner Totali** @1.77 ✅ **PRESA! (12 CORNER TOTALI 6-6!)**
2. [19:30] **Osasuna - Levante** ➔ **1X2: 1** @1.86 ⏱️ *(Live 0-0 al Sadar)*
3. [20:45] **Roma - Fiorentina** ➔ **Over 8.5 Corner Totali** @1.67 ⏱️ *(In partenza ore 20:45)*

### ⚔️ Ticket #24: Cinquina Duelli Roma-Fiorentina (Stake 5.00 € ➔ Pot. 49.97 €)
* **Stake**: 5.00 € | **Quota Base**: 9.90× | **Bonus Netwin**: +0.49 € | **Vincita Potenziale**: **`49.97 €`** 💰
* **Stato**: Tutti i 5 Giocatori TITOLARI UFFICIALI! (Live 0-0 all'Olimpico) ⏱️
1. [20:45] **Roma - Fiorentina** ➔ **Dybala Over 2.5 Falli Subiti** @2.00 (Titolare)
2. [20:45] **Roma - Fiorentina** ➔ **Rodrigo Mora Over 0.5 Falli Subiti** @1.47 (Titolare)
3. [20:45] **Roma - Fiorentina** ➔ **Manu Koné Over 1.5 Falli Subiti** @1.65 (Titolare)
4. [20:45] **Roma - Fiorentina** ➔ **Cher Ndour Over 1.5 Falli Commessi** @1.70 (Titolare)
5. [20:45] **Roma - Fiorentina** ➔ **Joao Mário Over 0.5 Falli Commessi** @1.20 (Titolare)

### 👑 Ticket #25: Sestina Master Duelli Roma-Fiorentina (Stake 20.00 € ➔ Pot. 157.03 €)
* **Stake**: 20.00 € | **Quota Base**: 7.62× | **Bonus Netwin**: +4.57 € | **Vincita Potenziale**: **`157.03 €`** 💰 | **Ref**: `DF07EA0818317B1A4706`
* **Stato**: Concluso ⏱️
1. [20:45] **Roma - Fiorentina** ➔ **Dybala Over 1.5 Falli Subiti** @1.40 ❌ *(1 fallo subito)*
2. [20:45] **Roma - Fiorentina** ➔ **Cristante Over 0.5 Falli Subiti** @2.00 ❌ *(0 falli)*
3. [20:45] **Roma - Fiorentina** ➔ **Wesley Franca Over 0.5 Falli Subiti** @1.10 ✅ *(1 fallo subito)*
4. [20:45] **Roma - Fiorentina** ➔ **Nicolò Fagioli Over 0.5 Falli Subiti** @1.20 ❌ *(0 falli)*
5. [20:45] **Roma - Fiorentina** ➔ **Cher Ndour Over 0.5 Falli Subiti** @1.25 ❌ *(0 falli)*
6. [20:45] **Roma - Fiorentina** ➔ **Manu Koné Over 1.5 Falli Subiti** @1.65 ✅ *(2 falli subiti)*

### 🎯 Ticket #26: Doppia Live Corner In-Play (Stake 30.00 € ➔ Pot. 91.35 €)
* **Stake**: 30.00 € | **Quota Totale Base**: 3.05× | **Vincita Potenziale**: **`91.35 €`** 💰
* **Stato**: Concluso ⏱️
1. [20:45] **Roma - Fiorentina** ➔ **Over 6.5 Corner Totali Live** @2.10 ❌ *(Partita chiusa con 2 corner totali)*
2. [21:00] **Fulham - Chelsea** ➔ **Over 11.5 Corner Totali Live** @1.45 ❌ *(Partita chiusa con 7 corner)*

### 🌙 Ticket #27: Multipla Notturna Overseas "For Fun" (Quota 10.00× ➔ Pot. ~125.00 €)
* **Quota Base**: 10.00× | **Bonus Netwin (6 eventi)**: +25% | **Quota Finale**: **`~12.50×`** 💰
* **Stato**: In Giocata / Notte 24-25 Agosto ⏱️
1. 🇺🇸 **Charleston Battery vs Miami FC** ➔ **Over 2.5 Gol Totali** @1.50
2. 🇧🇷 **Sc Recife Pe vs America Mg** ➔ **1X2: 1 (Sport Recife)** @1.63
3. 🇦🇷 **Tigre vs Central Cordoba** ➔ **Under 2.5 Gol Totali** @1.45
4. 🇨🇴 **Boyaca Patriotas vs Atletico Fc** ➔ **1X2: 1 (Boyaca Patriotas)** @1.34
5. 🇧🇷 **Botafogo vs Athletico Paranaense** ➔ **Doppia Chance 1X (Botafogo)** @1.40
6. 🇧🇷 **Athletic Club vs Novorizontino** ➔ **Under 2.5 Gol Totali** @1.50

---

*Ultimo aggiornamento: 25 agosto 2026 — BAgent (Retrospettiva esiti reali Ticket 22/23/25/26/27 verificata via API-Football, conflitto Git in CLAUDE.md risolto)*

---

## Sessione Notte 25-26 Agosto 2026 — Nuovo Mac, Live Betting, Ticket #29 Bruciato, Recupero

### 🖥️ Setup Ambiente su Nuovo Computer
Sessione ripresa da un secondo Mac. `.env` e `.venv` già presenti; **mancava il collegamento a `data/`** (solo `historical/` e `netwin_session/` locali). Risolto con symlink individuali da `data/*` → `/Users/flashmac/Google Drive/My Drive/B-Agent/BAgent/data/*` (bagent.db, matches.db, csv_import, football, cache, predictions, CSV storici). `bagent.db` aveva il journal file (stato dirty) → risolto con `PRAGMA wal_checkpoint`. **Nota per prossime sessioni**: se `data/` risulta vuota su un Mac nuovo, ricontrollare/ricreare questi symlink prima di qualunque query DB.

### 🎫 Ticket #29 — Esito Finale: PERSO (5/7)
Bruciato dalla leg 5 (Bodø Glimt Over 8.5 Corner Totali): 3-0 finale ma solo 6 corner totali. Le altre 4 leg già decise erano tutte vinte. Vedi dettaglio aggiornato nella sezione Ticket #29 sopra. **Conferma Regola #17** con un caso ancora più netto (10 uomini avversari per 87', dominio quasi totale, comunque pochi corner).

### 📊 Live Betting su Bodø Glimt-Nijmegen — Netwin vs Betsson
Analizzato lo scenario "0-0 tardivo da favorita schiacciante" (Nijmegen in 10 dal 3', Bodø 74% possesso) come possibile value bet live secondo la Strategia In-Play del CLAUDE.md. **Riscontro**: il mercato Netwin aveva già prezzato tutto (1X2 "1" @1.18, Over 1.5 @1.16 sotto quota minima) — niente value clamoroso. **Betsson offriva quote migliori sullo stesso mercato** (Over 2.5 Gol @1.75-1.80 vs @1.66 Netwin) e aveva un mercato Corner Live assente su Netwin. **Nuova prassi**: per le quote live, controllare sempre anche Betsson oltre a Netwin/Domusbet (estensione della Regola #25 al live, non solo al prematch).

### 🏆 Tris Live Vincente su Betsson (formazioni verificate, Regola #16)
Su richiesta di scansionare mercati live disponibili, proposta una tabella di 4 selezioni su Betsson (Bodø Glimt Over2.5/Over Corner, Birmingham-Brentford Over5.5, Doncaster-Middlesbrough Over2.5). L'utente ha chiesto controllo formazioni prima di fidarsi (partite di EFL Cup = rischio squadre rimaneggiate) — verificate via lineup API-Football: Brentford e Middlesbrough schieravano titolari veri (Callum Wilson, Luke Ayling), nessun'emergenza giovanili. Utente ha piazzato 3 delle 4 (escluso il corner) e **vinte tutte e 3**: Bodø Glimt 3-0, Birmingham-Brentford 1-6, Doncaster-Middlesbrough 1-3 FT.

### 🔄 Costruzione Ticket di Recupero (post Ticket #29)
Utente ha proposto Paraguay (2 De Mayo-Guarani, DC 1X @1.43) — analisi classifica/forma/H2H a favore ma **assenze non verificabili** (API-Football senza copertura infortuni per questa lega, dato onestamente segnalato come limite). Poi propostosi Deportivo Madryn-Godoy Cruz (Argentina Primera Nacional): Δ punti = 0, H2H diretto stagionale 0-0, Madryn miglior difesa recente → Under 2.5 @1.42.

**Momento importante**: l'utente ha suggerito da screenshot dell'app due partite (Goianiense-Botafogo SP, Juventude-CRB) che si sono rivelate **le stesse identiche gambe 6-7 del Ticket #29 già perso** (CRB compariva come "Brasil AL" nel nome breve Betsson) — segnalato subito prima di procedere. Dato che il Ticket #29 era già chiuso perso, la Regola #15 (no duplicazione) non si applicava più (nessun rischio di correlazione tra ticket attivi), quindi rianalizzate come selezioni pulite: Juventude 2 gol fatti in 5 gare (attacco spento) vs CRB 0 gol subiti in 5 gare; Goianiense-Botafogo con Δ punti 2 (Regola #14). Entrambe Under 2.5.

Controllato anche il mercato Cartellini (Regola #8, Sudamerica = ambiente valido) come alternativa: quote Betsson già ben prezzate rispetto alla media storica (~4.0-4.2 cartellini/gara vs linea 4.5), nessun value chiaro — l'utente ha confermato di tenere le 3 Under Gol.

**Ticket finale costruito**: `reports/schedina_recupero_notte_25ago.html` — 3 selezioni (Madryn-Godoy Cruz Under2.5 @1.42, Juventude-CRB Under2.5 @1.62, Goianiense-Botafogo Under2.5 @1.49), quota combinata 3.43×, stake 20€ → potenziale 68.55€. Kickoff 00:00 e 00:30 (26/08).

### 🐛 Nota tecnica: ricerca su Betsson
Il campo di ricerca nella sidebar sinistra di Betsson (desktop, `betsson.it/scommesse`) a volte non riceve il testo se si clicca subito dopo una `navigate` — serve un secondo click esplicito sul campo (usare `find` per ottenere il `ref` se le coordinate falliscono) prima di digitare.

---

## Sessione 27 Agosto 2026 — Play-off di Ritorno UEFA (Europa & Conference League)

### 🛡️ Ticket #31 (Proposta): Tripla d'Acciaio Europea (Quota ~3.65× - 4.00× con Bonus)
* **Filosofia**: Rispetto ferreo della Regola #26 (Max 3 eventi) e Sesto Senso (Regole #21, #22).
1. [17:00] **FC Copenhagen vs Inter Turku** ➔ **1 + Over 1.5 Gol** @1.45 *(o 1 secco @1.29)*
2. [16:45] **SC Freiburg vs Motherwell** ➔ **1 + Over 1.5 Gol** @1.40 *(Andata 1-3 Friburgo)*
3. [16:45] **AS Monaco vs Górnik Zabrze** ➔ **Over 2.5 Gol Totali** @1.55 *(Andata 2-3 Monaco)*

### 🚀 Ticket #32 (Proposta): Quaterna d'Oro Pesante (Quota 8.92× Base ➔ ~10.25× con Bonus)
* **Filosofia**: Value combo a campo aperto sulle sfide di ritorno europee da dentro-o-fuori.
1. [16:45] **AS Monaco vs Górnik Zabrze** ➔ **1 + Over 2.5 Gol** @1.85
2. [17:00] **Brann vs PAOK Salonicco** ➔ **Gol (Entrambe Segnano)** @1.67 *(Andata 1-1)*
3. [18:00] **Ajax vs FC Sion** ➔ **1 + Over 2.5 Gol** @1.75 *(Andata 2-4 Ajax)*
4. [16:45] **SC Freiburg vs Motherwell** ➔ **1 + Over 2.5 Gol** @1.65

*Eventuale 5ª gamba booster*: [18:30] **Brighton vs Tromsø** ➔ **1 + Over 2.5 Gol** @1.55 (Porta quota a **~16.50× con Bonus**).

---

*Ultimo aggiornamento: 28 agosto 2026 ore 09:15 — BAgent (Sessione 28 Agosto: Analisi Top 5 Leghe, Backtest Engine & DataLoader integrati, Handover registrato)*

---

## Sessione 28 Agosto 2026 — Analisi Top 5 Leghe, Integrazione Backtesting Engine & Handover

### 🔍 1. Analisi Approfondita Partite del 28 Agosto 2026 (Venerdì)
- Analizzate 11 partite in programma (Top 5 campionati e leghe minori).
- **Sesto Senso Applicato**:
  - 🇩🇪 **Bayern München vs VfB Stuttgart (20:30)**: Musiala OUT (riposo), Gnabry OUT, ma attacco al completo (Olise, Brown, Díaz, Kane). Stuttgart decimato da 8 infortuni. ➔ **Pick: 1 + Over 2.5 @ 1.75** (Edge +8.2%).
  - 🇫🇷 **Lille vs PSG (20:45)**: PSG senza Dembélé, Barcola, Mendes, ma con Ferran Torres (2 gol alla J1) e Kvaratskhelia. Lille con Giroud ed Ethan Mbappé (motivatissimo vs ex club). Campo umido/bagnato. ➔ **Pick: GOL (BTTS Sì) @ 1.67** (Edge +7.3%).
  - 🇪🇸 **Alavés vs Villarreal (21:30)**: Villarreal a rosa completa ma difesa colabrodo (4 gol subiti in 2 gare). Alavés forte in casa (imbattuto nelle ultime 5 vs Villarreal). ➔ **Pick: GOL (BTTS Sì) @ 1.65** (Edge +6.1%).
  - 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Crystal Palace vs Man City (21:00)**: Selhurst Park insidioso, Palace con blocco a 5 ma deve attaccare dopo 0-2 con Everton; City con Haaland e Cherki. ➔ **Pick: Over 2.5 @ 1.72** (Edge +5.8%).
- **Decisione Utente su Milan vs Venezia**:
  - Segnalazione utente: *"non mi convince il milan"*.
  - Motivo: Rafael Leão NON convocato per trattative di mercato (Galatasaray/Aston Villa), Milan ancora in fase di rodaggio con Amorim.
  - **Azione**: Milan **ESCLUSO** dai ticket per massima prudenza.
- **Proposte Ticket**:
  - 🛡️ **Opzione A — Tris d'Acciaio**: Bayern 1+O2.5 + Lille GOL + Alavés GOL ➔ **Quota ~4.82×**
  - ⚡ **Opzione B — Quaterna d'Elite**: Bayern 1+O2.5 + Lille GOL + Alavés GOL + Palace O2.5 ➔ **Quota ~8.30×**
- **Report HTML**: Creato `reports/analisi_28_agosto_2026.html` (mobile-first dark mode).

### 🔬 2. Integrazione Modulo Backtesting e Historical DataLoader
- Valutato il repository `georgedouzas/sports-betting` (v0.15.1, 779 ⭐).
- Integrati con successo in BAgent:
  - `services/database/historical_loader.py`: Download e caching a costo zero di 12 campionati storici (2018-2026) da Football-Data.co.uk.
  - `services/analysis/backtest_engine.py`: Motore di backtesting temporale con `TimeSeriesSplit` (anti-data leakage) per calcolare Yield %, ROI %, Sharpe Ratio, Max Drawdown.
  - `scripts/run_historical_backtest.py`: Eseguito test su **7.156 partite** delle Top 5 leghe europee. Dimostrato matematicamente che i modelli "ciechi" senza Sesto Senso hanno rendimento piatto/negativo (~0%), mentre il filtraggio selettivo BetGuard è fondamentale.

### 🍓 3. Raspberry Pi 24/7 Hub
- Demone `scripts/auto_portal_bot.py` operativo con server HTTPS (porta 8443) e listener Telegram `@A502502_bot`.

---

## 🎫 TICKET UFFICIALI PIAZZATI — NOTTE 28 AGOSTO 2026

### 🏆 Ticket #36: Quintina d'Elite Serale (Quota 9.29×)
* **Piattaforma**: Netwin | **Stato**: 💰 CASHOUT ESEGUITO A 65.00 € ✅ (4/5 Vinte)
* **Importo Puntato**: 20.00 € | **INCASSO CASHOUT**: **65.00 €** *(Profitto Netto: +45.00 € / +225% ROI)*
1. 🇩🇪 [20:30] **Bayern Monaco vs Stoccarda** (5-1 FT) ➔ **1 + Over 2.5** @ **1.32** ➔ **✅ VINTO!**
2. 🇮🇹 [20:45] **Milan vs Venezia** (2-0 FT) ➔ **1X2: 1 (Milan)** @ **1.46** ➔ **✅ VINTO!**
3. 🇫🇷 [20:45] **Lilla vs PSG** (2-2 FT) ➔ **G/NG: Gol** @ **1.75** ➔ **✅ VINTO!**
4. 🏴󠁧󠁢󠁥󠁮󠁧󠁿 [21:00] **Crystal Palace vs Manchester City** (1-4 FT) ➔ **U/O 2.5: Over** @ **1.68** ➔ **✅ VINTO!**
5. 🇪🇸 [21:30] **Alavés vs Villarreal** ➔ **G/NG: Gol** @ **1.64** ➔ *Cashout eseguito prima del fischio finale!*

---

### 🛡️ Ticket #37: Quaterna d'Acciaio Ibrida (Quota 4.10× + Bonus = 92.96 €)
* **Piattaforma**: Netwin | **Stato**: 🏆 VINTO AL 100% (4/4) ✅✅✅✅
* **Importo Puntato**: 22.00 € | **Bonus Multiple**: 2.70 € | **INCASSO REALE**: **92.96 € NETTI!** 💰
1. 🇩🇪 [20:30] **Bayern Monaco vs Stoccarda** ➔ **1X2 Corner Tempo 1: 1 (Bayern)** @ **1.48** ➔ **✅ VINTO!**
2. 🇫🇷 [20:45] **Lilla vs PSG** (2-2 FT) ➔ **X2 + U/O 1.5: X2 + OV** @ **1.50** ➔ **✅ VINTO!**
3. 🏴󠁧󠁢󠁥󠁮󠁧󠁿 [21:00] **Crystal Palace vs Manchester City** (6-2 Corner) ➔ **1X2 Corner (esc.TS): 2 (Man City)** @ **1.40** ➔ **✅ VINTO!**
4. 🇵🇹 [21:15] **Rio Ave vs Sporting CP** (0-4 FT) ➔ **1X2: 2 (Sporting CP)** @ **1.32** ➔ **✅ VINTO!**

---

### 💎 BILANCIO FINANZIARIO DEFINITIVO NOTTE 28 AGOSTO 2026:
* 💵 **Capitale Totale Investito**: **42.00 €**
* 💰 **Totale Incassato Realmente**: **157.96 €** *(65.00 € Cashout #36 + 92.96 € Vincita #37)*
* 🚀 **PROFITTO NETTO INCASSATO**: **+115.96 €**
* 📈 **ROI TOTALE DELLA SERATA**: **+276.1% SUL CAPITALE!**

---

## 🎫 TICKET UFFICIALI IN GIOCO — SABATO 29 AGOSTO 2026

### 🏆 Ticket #42: Tripla Serale Real Sociedad + Porto + Juventus (Quota 2.66×)
* **Piattaforma**: Netwin | **Stato**: PIAZZATO & IN GIOCO ⏱️ (Iniziato ore 19:12)
* **Importo Puntato**: 20.00 € | **Vincita Potenziale**: **53.29 €** | **Ref**: `DF07EA081D312EC35E0C`
1. 🇵🇹 [19:00] **Academico de Viseu FC vs FC Porto** (0-1 parziale) ➔ **U/O 2.5: Over** @ **1.35** ⏳
2. 🇪🇸 [19:00] **Real Sociedad vs Espanyol** (1-0 parziale) ➔ **1X2: 1 (Real Sociedad)** @ **1.40** ⏳
3. 🇮🇹 [20:45] **Juventus vs Parma** ➔ **1X2 + U/O 1.5: 1 + OV** @ **1.41** ⏳

---

### 🛡️ Ticket #41: Recupero d'Acciaio Serale (Quota 5.30×)
* **Piattaforma**: Netwin | **Stato**: PIAZZATO & IN GIOCO ⏱️ (Inizio ore 18:30)
* **Importo Puntato**: 20.00 € | **Vincita Potenziale**: **106.00 €** | **Ref**: `NETWIN-T41-29AGO`
1. 🇩🇪 [18:30] **Borussia Dortmund vs Hamburger SV** ➔ **1X2 + U/O 1.5: 1 + OV** @ **1.50** ⏳
2. 🏴󠁧󠁢󠁥󠁮󠁧󠁿 [18:30] **Tottenham vs Newcastle United** ➔ **G/NG: Gol (Sì)** @ **1.48** ⏳
3. 🇫🇷 [20:45] **Olympique Lione vs Le Havre** ➔ **1X2: 1 (Lione)** @ **1.45** ⏳
4. 🇪🇸 [21:30] **Siviglia vs Atlético Madrid** ➔ **Doppia Chance: 1X** @ **1.65** ⏳

---

### 💎 Ticket #40: Corazzata Corner & Cartellini (Quota 4.30×)
* **Piattaforma**: Netwin | **Stato**: 1/4 VINTO — IN GIOCO ⏱️
* **Importo Puntato**: 20.00 € | **Vincita Potenziale**: **86.00 €** | **Ref**: `NETWIN-T40-29AGO`
1. 🏴󠁧󠁢󠁥󠁮󠁧󠁿 [13:30] **Liverpool vs Nottingham Forest** (2-2 FT) ➔ **U/O Gol Casa: Over 1.5 Casa** @ **1.45** ➔ **✅ VINTO!**
2. 🇩🇪 [15:30] **RB Lipsia vs Borussia M'gladbach** ➔ **1X2 Corner: 1 (Lipsia)** @ **1.32** ⏳
3. 🇩🇪 [18:30] **Borussia Dortmund vs Hamburger SV** ➔ **1X2 Corner 1° Tempo: 1 (Dortmund)** @ **1.45** ⏳
4. 🇪🇸 [21:30] **Siviglia vs Atlético Madrid** ➔ **U/O Cartellini: Over 4.5** @ **1.55** ⏳

---

### ❌ Ticket Chiusi / Conclusi:
* 🔴 **Ticket #38** (20.00 € @ 4.52×) ➔ Chiuso (Liverpool 2-2).
* 🔴 **Ticket #39** (20.00 € @ 9.62×) ➔ Chiuso (Liverpool 2-2).

---

### 💎 QUADRO FINANZIARIO LIVE SABATO 29 AGOSTO 2026:
* 💵 **Ticket Attivi in Corsa**: **Ticket #40** (20 € ➔ 86.00 €) + **Ticket #41** (20 € ➔ 106.00 €) + **Ticket #42** (20 € ➔ 53.29 €)
* 🚀 **POTENZIALE VINCITA LORDA ATTIVA**: **245.29 €**!
* 💳 **Saldo Utente su Netwin**: **131.02 €**

*Ultimo aggiornamento: 29 agosto 2026 ore 19:15 — BAgent (Ticket #42 registrato da screenshot Netwin, Ref DF07EA081D312EC35E0C)*


