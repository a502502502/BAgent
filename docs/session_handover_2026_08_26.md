# 🚀 BAgent — Session Handover & Complete Checkpoint

**Data Checkpoint**: Mercoledì 26 Agosto 2026 — Ore ~19:00 (CEST)
**Stato**: Salvato e sincronizzato su GitHub (`origin/main`)

---

## 📌 1. Riepilogo Esecutivo della Sessione di Oggi (26 Agosto)

Sessione di continuazione da ieri (25 agosto), partita dalla liquidazione dei ticket notturni e finita con una giornata intera di analisi molto approfondita sulle partite di Champions League (uomini e donne) di stasera.

1. **Liquidazione ticket notturni**: Ticket #28 (K-League, cashout live -30€), Ticket #29 (7 eventi, perso 4/7, -10€), **Ticket #30 corretto** — l'utente ha mostrato uno screenshot reale del ticket Betsson che rivelava una selezione mancante (2 de Mayo-Guarani DC 1X, vinta) mai registrata: quota reale 4.94× non 3.43×, esito 2/4 non 1/3.
2. **Regola #29 nata**: ban su Under 2.5 Gol secco nelle leghe minori, dopo che Juventude-CRB e Goianiense-Botafogo (Brasile Serie B) sono saltate entrambe in due ticket diversi nonostante analisi solida.
3. **Regola #30**: scoperta che The Odds API (già gratis, chiave in `.env`) offre `alternate_totals` (linee 1.5/2.5/3.5+) da 7+ bookmaker reali — verificato su Brazil Serie B, esattamente il dato che serve per applicare la Regola #29 con un numero reale.
4. **Cambio drastico di workflow**: l'utente ha chiesto esplicitamente di **smettere di cercare quote su Netwin/Domusbet/Betsson via browser** ("perdiamo troppo tempo e token") — CLAUDE.md aggiornato, ora si costruisce tutto con API-Football + The Odds API, la verifica del numero esatto resta all'utente al momento del piazzamento.
5. **Costruzione di 3 (poi 4) tabelle per le partite di oggi**, con un livello di approfondimento molto alto su richiesta esplicita ("fai delle analisi approfondite"):
   - Analisi xG, forma recente, infortuni (verificati su 3 fonti indipendenti per Fenerbahçe: API-Football, Transfermarkt, InfoBetting — trovata discrepanza importante, la lista iniziale di 13 assenti era gonfiata, solo 4 reali)
   - Scoperta e superamento di un blocco cookie-consent di Google News usando il browser vero (click "Rifiuta" sui cookie, non un aggiramento di protezioni)
   - Trovati articoli reali di rassegna stampa (Hearts Standard, Sofascore preview) con dati fortissimi su Dinamo Zagabria (28 partite senza sconfitta, Over 2.5 in 4/5, Over 10.5 corner in 4/5)
   - Audit sistematico di tutte le partite del giorno, segnalando dove mancano i dati (rassegna stampa mai usata prima su queste partite, classifica non controllata per le coppe, xG assente per il calcio femminile)
6. **Esperimento "Fuori Regole"** su richiesta esplicita dell'utente: costruita una quarta tabella violando deliberatamente le Regole #5/#9/#27, usando un dump di quote Netwin incollato dall'utente su leghe minori/giovanili — confermato che per quelle partite non esiste nessuna rassegna stampa reale (solo pagine automatiche di stat), rafforzando il motivo per cui quelle regole esistono.
7. **Report HTML creato**: `reports/schedina_26ago.html` con tutte e 4 le tabelle, stile coerente con le schedine precedenti del progetto.

---

## 🎫 2. Le 4 Tabelle di Oggi (26 Agosto, verificare stato/esito all'apertura sessione)

### Tabella 1 — Gol (6 selezioni, quota 12.05×)
| Partita | Orario | Pick | Quota |
|---|---|---|---|
| Lyon - Fenerbahçe | 21:00 IT | 1 (Lyon) | @1.90 |
| Real Madrid - Real Sociedad | 21:00 IT | 1 (Real Madrid) | @1.31 |
| Celje - Slovan Bratislava | 21:00 IT | Over 1.5 Gol | @1.36 |
| Viking - Dinamo Zagabria | 21:00 IT | Over 2.5 Gol | @1.57 |
| Viking - Dinamo Zagabria | 21:00 IT | Over 9.5 Corner Totali | @1.62 |
| AEK Athens - Levski Sofia | 21:00 IT | Over 1.5 Gol | @1.35 |

### Tabella 2 — Falli Totali (4 selezioni, quota 12.75×, esplorativa/n=1)
Under 25.5 Viking-Dinamo @1.93, Under 26.5 Celje-Slovan @1.82, Under 25.5 AEK-Levski @1.88, Over 25.5 Lyon-Fenerbahçe @1.93.

### Tabella 3 — Champions League Femminile (3 selezioni, quota 3.01×)
Over 2.5 Frankfurt-PSG @1.57, 2 Real Madrid (Ajax-RM) @1.35, Over 2.5 Chelsea-Real Sociedad @1.42.

### Tabella 4 — "Fuori Regole" (sperimentale, deroga esplicita, non nel Registro Cassa allo stesso livello)
Vedi `reports/schedina_26ago.html` per il dettaglio — 5 selezioni su leghe minori/giovanili senza verifica reale.

**Nessuna delle 4 è stata ancora registrata come Ticket numerato nel Registro Cassa** — l'utente non ha confermato di averle piazzate su Netwin/Betsson. Se lo fa, chiedere lo stake e registrare come Ticket #31+.

---

## 🛠️ 3. Nuovi Strumenti/Tecniche di Oggi

### Tecnica: superare il muro cookie di Google News
I link RSS di Google News rimbalzano su `consent.google.com`. **Non aggirare via WebFetch/curl** (fallisce sempre, loop di redirect) — usare invece il **browser vero** (`mcp__Claude_Browser__*`), navigare al link, leggere la pagina di consenso con `read_page filter:all` (i bottoni "Reject all"/"Accept all" a volte non compaiono col filtro `interactive`), cliccare "Reject all" (opzione privacy-first di default), poi `get_page_text` sulla pagina reale che segue. La sessione cookie resta valida per i link successivi nella stessa tab.

### `sources/news.py` — finalmente usato in produzione
Prima serviva solo per i titoli (funziona sempre), oggi dimostrato che con la tecnica sopra si può leggere anche il corpo completo degli articoli quando il link è un redirect Google News verso un sito che non blocca il fetch diretto (es. Sofascore, Hearts Standard). Siti con protezione forte (UEFA.com: 503; DuckDuckGo: CAPTCHA) restano non accessibili — non aggirare, riportarlo onestamente.

### Betsson: bloccato da Cloudflare
Confermato oggi (403 "Attention Required") — stesso destino di Sofascore, non risolvibile da questo ambiente. Netwin invece è stato incollato manualmente dall'utente (non testato l'accesso diretto).

---

## 🛡️ 4. Le Regole Inviolabili — solo le nuove di oggi (29, 30)

- **#29**: Ban Under 2.5 Gol secco sulle leghe minori — usare Under 3.5 o mercato alternativo. Nato da Juventude-CRB e Goianiense-Botafogo saltate due volte.
- **#30**: The Odds API per le linee alternative (Under 3.5+), gratis, chiave già in `.env`, verificato funzionante su Brazil Serie B. Attenzione al costo: `get_event_odds` costa 2-4 richieste per partita, usarla solo sulle gare realmente in valutazione.

**Cambio di workflow non numerato ma importante**: eliminata la ricerca quote su Netwin/Domusbet/Betsson via browser dal flusso standard — vedi CLAUDE.md, sezione "Multipla — Regole & Filosofia di Gioco", modificata oggi.

---

## 📋 5. Come Riprendere la Sessione sul Nuovo Computer

```bash
cd BAgent
git pull origin main
```

Poi:
> *"Ho riaperto BAgent su un altro computer, ho letto il checkpoint in `docs/session_handover_2026_08_26.md` e `CLAUDE.md`. Controlla lo stato delle 4 tabelle di oggi (26 agosto) e degli eventuali ticket aperti, poi riprendiamo da lì."*

**Nota**: nessun `ScheduleWakeup` di monitoraggio automatico attivo in questa sessione al momento del salvataggio — se l'utente ha piazzato una delle 4 tabelle nel frattempo, chiedere se vuole riattivare il monitoraggio live (`scripts/ticket_watcher.py` + `data/ticket_watch.json`, quest'ultimo va ricreato perché gitignored).

---
*Tutto salvato, committato e pushato.*
