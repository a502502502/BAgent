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
