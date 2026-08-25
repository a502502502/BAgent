# 📋 CONVERSAZIONE COMPLETA — 25 AGOSTO 2026

> Sessione lunga, partita da una retrospettiva sugli esiti reali dei ticket 22-27 e finita con due nuovi ticket costruiti e piazzati con un flusso di analisi molto più veloce e rigoroso rispetto alle sessioni precedenti.

---

## 🔍 1. Retrospettiva Ticket #22/23/25/26/27

Richiesta iniziale: "controlla tutto e facciamo una retrospettiva". Prime verifiche fatte a mano su Sofascore via browser — lente. L'utente ha fatto notare la lentezza: **"ci metti troppo a raccogliere i dati. hai bisogno di un api per fare veloce?"**

Scoperto che il progetto ha già una `FootballExternalCollector` (API-Football) con `fixture_stats()` e `player_stats()` — usata per liquidare in pochi minuti tutti i ticket pendenti invece dei 20+ minuti di browsing manuale.

**Esiti confermati**:
- Ticket #22 (9 leg Falli Giocatore): 4/9 — Palmer, Dybala, Kean, Frattesi ✅; Zaccagni, Dovbyk, Soulé, Berge, Caicedo ❌ (3 di questi persi per variabilità di minutaggio, non errore di analisi)
- Ticket #23 (Tripla Corner): 1/3 — solo Bologna Corner presa
- Ticket #27 (Multipla Overseas): 2/6 confermati, resto perso

Bilancio sessione 24-25 agosto: **-75€ confermati** + Ticket #27 perso (stake non tracciato nei log).

---

## 🛠️ 2. Fix del Conflitto Git in CLAUDE.md

Durante la registrazione degli esiti, scoperto un **conflitto Git irrisolto mai chiuso**: marker `<<<<<<< HEAD` a riga 351 e `=======` a riga 701, senza il marker di chiusura `>>>>>>>`, con ~350 righe di contenuto duplicato (sessioni 17-21 agosto ripetute due volte con leggere differenze). Risolto unendo il contenuto unico di entrambi i lati: mantenuta la sezione "Verifica Quote Pomeridiana 24 Agosto" (Regole 23-25) da un lato, e "Sessione 22-23 Agosto Ticket Ufficiale" (Ticket #15-27) dall'altro. Recuperata la Regola vecchia #17 (Rigore Matematico) rinumerata come **Regola #26**, perché era solo nel lato "perdente" del conflitto ma direttamente rilevante per la retrospettiva appena fatta.

---

## 🚀 3. Domanda sui Mercati Combo e Scoperta API-Football

L'utente ha chiesto perché non usiamo mai mercati combo/multigol. Risposta: li usiamo a volte come singola leg dentro una multipla, mai come motore centrale, perché il modello Poisson assume eventi indipendenti mentre i Bet Builder hanno eventi correlati.

Poi l'utente ha chiesto da dove vengono scaricati i dati, lamentando lentezza. Inventario fatto: API-Football (veloce, dati strutturati) vs Sofascore/FootyStats/Netwin-Domusbet (lenti, serve il browser).

**Scoperta chiave**: testando l'endpoint `odds()` di API-Football, trovati **185 mercati da 14 bookmaker** per una singola fixture, incluso **"Player Fouls Committed"** con nomi reali e soglie (es. "Timothy Castagne 2+ @2.25") — esattamente il mercato che aveva richiesto ore di click manuali su Netwin nelle sessioni precedenti. Aggiunti `player_prop_odds()` e `list_available_markets()` a `collector.py`.

L'utente ha poi chiarito un'importante distinzione: sì al mercato "Falli Committed" via API, ma quelle sono quote di *altri* bookmaker (Bet365, 10Bet), non di Netwin — vanno usate per lo scouting veloce, non per piazzare direttamente senza verifica finale.

**Istruzione esplicita per la velocità**: *"al momento non mi interessa il numero esatto, lo risolviamo più avanti. Adesso mi interessa la velocità di calcolo e quindi devi prendere le quote da API-Football"* — salvata in memoria persistente come preferenza di workflow.

---

## 🧪 4. Test del Flusso Veloce su Partite Minori

Provato il nuovo flusso su un lotto di partite minori incollate dall'utente (Australia, India, Corea, Uzbekistan, riserve inglesi). Trovate 8/17 con quote reali. Costruita una prima tabella di pick, ma **l'utente ha fatto una domanda cruciale**: *"il nostro sesto senso dovrebbe fare questi controlli prima di fare la tabella. perché non lo fa?"*

Riconosciuto l'errore: la tabella era stata costruita su gap di quota + reputazione generica da memoria ("Jeonbuk è storicamente forte"), non su dati reali. Controllando dopo la forma recente via API-Football, emerso che **Jeonbuk aveva appena perso 2-3 contro Bucheon**, e Bucheon era la squadra più in forma del lotto — informazione che ribaltava due pick su tre.

**Nata la Regola #27**: controllo forma recente (`fixtures?team={id}&last=5`) OBBLIGATORIO prima di ogni tabella, anche senza rassegna stampa disponibile.

Tabella ricostruita da zero applicando la regola: aggiunta colonna classifica, cambiata la pick "1 Seoul" secca in "Over 2.5 Gol" dopo aver scoperto la vera forma di Bucheon.

---

## 🇰🇷 5. Ticket #28 — Costruzione, Piazzamento, Monitoraggio Live, Cashout

Tabella finale K-League 1 (Gimcheon-Jeonbuk DC X2 @1.30, Jeju-Pohang Under 2.5 @1.57, Seoul-Bucheon Over 2.5 @1.85, quota 3.78×). L'utente ha inserito il ticket da 40€ su Netwin.

Monitoraggio live fatto a mano su richiesta, con l'utente che incollava screenshot testuali da Sofascore (formato con testo duplicato per accessibilità, decifrato confrontandolo sempre con i dati precisi di API-Football). Errore mio corretto a metà strada: avevo scritto che un punteggio "1-2" sarebbe stato "ancora buona" per un Under 2.5 già a 2 gol — **sbagliato**, l'utente mi ha corretto giustamente (**"ma 1-2 non è buona!!"**), qualsiasi gol in più avrebbe fatto perdere la pick.

All'82', con Leg 2 al limite esatto (0-2, zero margine) e Leg 3 in salita (1-0, servivano 2 gol in 8 minuti), Netwin ha offerto un cashback di 14€, sceso a 10€ col passare del tempo (probabilità implicita in calo). L'utente ha accettato i 10€. **Netto: -30€**.

---

## 🌍 6. Scoperta LiveScore.in Funzionante, Costruzione Ticket #29, Regola #28

Chiesto un task automatico per controllare le formazioni. Prima tentata la strada degli agenti cloud schedulati — scartata perché non hanno accesso ai segreti locali (.env) e l'intervallo minimo è 1 ora, non adatto. L'utente ha chiesto di controllare le formazioni "adesso", non di costruire infrastruttura — richiamo diretto: **"non hai capito. chiedevo di verificare le formazioni e di segnalare eventuali considerazioni"**.

Confermato che **Sofascore è bloccata (403) a livello di IP** da questo ambiente (anche solo la home page), non risolvibile con cookie/header. Su suggerimento dell'utente, testato **LiveScore.in** — **funziona!** Trovato l'endpoint `local-global.flashscore.ninja`, reverse-ingegnerizzato il formato pipe-delimited delle formazioni, creato `services/football/external/sources/flashscore.py`. Le formazioni erano disponibili **prima** di quelle ufficiali di API-Football.

Aggiornato `lineup_watcher.py` per usare Flashscore come fonte primaria. L'utente ha specificato: **"per le partite live è fondamentale"** — il modulo include anche `stats()` (corner/falli/cartellini live) e un fetcher grezzo per gli incidenti live (non ancora parsato in eventi strutturati, da calibrare su una partita davvero in corso).

Testato live durante il Ticket #28: dati corner/tiri/possesso recuperati in tempo reale via Flashscore, usati per valutare lo stato delle 3 gambe al 51' e all'82'.

**Ricostruzione tabella "di recupero"** dopo il cashout: l'utente ha chiesto un'analisi "molto approfondita" per le partite serali europee (Brann-Austria Wien, Bodo/Glimt-NEC, Valencia-Betis). Aggiunta la dimensione xG (già disponibile in `fixture_stats` come `expected_goals`, mai sfruttata prima), season stats con split casa/trasferta (`team_stats()`), e head-to-head (`head_to_head()`). Emerso che Valencia-Betis aveva un H2H storico che andava in direzione opposta rispetto alla pick Under 2.5 — segnalato onestamente come gamba più debole.

Costruite 2 versioni della tabella (gol vs corner su Bodo/Glimt-NEC), l'utente ha scelto la versione corner. Poi richiesta esplicita di allargare a quota >10× **"con altre partite anche"**: cercate partite più tardive nella stessa giornata (allargata la ricerca a tutto il giorno, trovate solo 8 partite totali in leghe regolamentate — giornata scarica). Aggiunte 2 partite di Serie B brasiliana (Juventude-CRB, Atletico Goianiense-Botafogo SP) dopo aver corretto un bug (league_id sbagliato nella prima query di classifica) e trovato dati solidi: Juventude 2° in classifica con miglior difesa del torneo (0.1 gol subiti/gara in casa).

Tabella finale a 7 eventi, quota 11.18× stimata. L'utente ha piazzato il ticket su Netwin e mandato uno screenshot: quota reale 10.96× (bonus incluso, potenziale 120.56€ su 10€ di stake). **Scoperta una discrepanza**: la gamba Sabah-Hapoel era stata inserita come "Over 1.5 Cartellini Squadra 1" invece della raccomandazione originale "Over 1.5 Gol".

Prima reazione: segnalata come "non verificata, non so se sia buona" — **l'utente non ha gradito**: *"non mi piace la frase... Dovresti farlo sempre, metti la regola nel .md"*. Nata la **Regola #28**: quando la selezione piazzata differisce da quella raccomandata, va sempre analizzata con lo stesso rigore, mai lasciata "non verificata" se i dati erano raggiungibili.

Fatta l'analisi reale: Sabah ha 0.67 cartellini/gara di media, 0 nelle ultime 2. L'utente ha proposto un'ipotesi tattica (*"Sabah non può rischiare e dovrà interrompere le azioni... il livello tecnico di Hapoel è più alto"*) — verificata contro i dati reali della gara d'andata: è stato **Hapoel**, non Sabah, a fare più falli e cartellini nonostante il possesso dominante (67%), confermando la Regola #18 già esistente (chi ha il possesso fa più falli, non chi si difende). L'utente ha accettato: **"capisco"**.

---

## 📡 7. Monitoraggio Automatico Ticket #29

Creato `scripts/ticket_watcher.py`: controlla lo stato live delle 7 gambe via API-Football, manda un riepilogo su Telegram solo quando cambia qualcosa. Configurazione in `data/ticket_watch.json` (gitignored, va ricreato su ogni macchina).

L'utente ha chiesto un task che resti attivo sul Raspberry Pi, perché stava per chiudere il computer. Verificato che **questo ambiente non ha connettività verso la rete Tailscale del Pi** (SSH timeout) — impossibile agire direttamente lì. Preparati i comandi esatti per il deploy manuale sul Pi.

L'utente ha poi chiesto un'alternativa: tenere attiva la sessione dal telefono invece del Pi. Confermato che è possibile via `ScheduleWakeup` (auto-risveglio ogni 10 minuti che esegue lo script e manda gli aggiornamenti), con l'unica incertezza onesta sulla sopravvivenza della sessione se l'app viene chiusa a lungo sul telefono — il Pi resta il piano B più affidabile.

Monitoraggio attivato: risveglio automatico ogni 10 minuti fino a conclusione di tutte e 7 le partite, con liquidazione finale automatica e aggiornamento del Registro Cassa quando tutte finiscono.

---

*Sessione salvata su richiesta esplicita dell'utente ("salva tutto compreso la nostra conversazione così posso riprendere da un altro computer") — vedi anche `docs/session_handover_2026_08_25.md` per lo stato tecnico dettagliato e le istruzioni di ripresa.*
