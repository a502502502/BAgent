# BAgent — Contesto di Progetto per Claude

> Leggi questo file all'inizio di ogni sessione per riprendere da dove abbiamo lasciato.

## Cos'è BAgent

Sistema di analisi scommesse quantitative focalizzato **AL 100% SUL CALCIO (Tennis Tassativamente Abolito)** con:
- Modello Poisson / Dixon-Coles per stima probabilità gol ed esiti esatti
- Negative Binomial Engine per overdispersion dei corner
- Sesto Senso = OBBLIGATORIO & QUOTIDIANO (lettura stampa sportiva internazionale + infortuni)
- Edge formula: `Edge = (prob × quota) - 1` e Sharp CLV Sentinel (Metodo Shin 1992)
- MultiplaAdvisor e Fractional Kelly per la gestione del bankroll
- Database SQLite con storico partite, statistiche, log previsioni

---

## REGOLA SUPREMA — BAN PERMANENTE DEL TENNIS (TENNIS ABOLITO)
🛑 **DIVIETO ASSOLUTO DI SCOMMESSE SUL TENNIS**:
A partire dal 22 Settembre 2026, **il tennis è definitivamente ed irrevocabilmente CANCELLATO da qualsiasi programma, scansione, schedina o proposta di BAgent**.
- **Motivazione Operativa**: Il tennis (in particolare circuiti ATP minori, WTA e Challenger) presenta un livello di varianza asimmetrica, cali fisici occulti, ritiri e blackout mentali (es. bagel 0-6 inspiegabili) incompatibile con il betting quantitativo a lungo termine.
- **Direttiva**: TUTTI i ticket, le analisi, i modelli in-play e le automazioni devono essere concentrati **ESCLUSIVAMENTE SUL CALCIO** (campionati europei Tier 1/2/3, Serie A/B/C, Coppe Europee e leghe sudamericane regolamentate).


## Regole di Analisi (SEMPRE in vigore)

- **Sesto Senso = OBBLIGATORIO & QUOTIDIANO**: Lettura integrale dei quotidiani sportivi di riferimento (*La Gazzetta dello Sport*, *BBC Sport*, *Marca*, *Kicker*, *L'Équipe*) e delle fonti specializzate di analisi e comparazione (*MondoPengwin* - https://www.mondopengwin.it/pronostici/calcio/) TUTTI I GIORNI prima di qualsiasi tabella o calcolo. L'informazione giornalistica, le dichiarazioni pre-partita, i ballottaggi e i retroscena di spogliatoio/mercato sono parte integrante e imprescindibile del Sesto Senso.
- **FootyStats = obbligatorio**: SEMPRE consultare https://footystats.org prima di ogni analisi per estrarre avg goals, Over2.5%, BTTS%, xG, forma recente. MAI stimare probabilità senza dati reali da FootyStats.
- **Interazione 100% via Chat (Zero Terminale per l'Utente)**: L'utente non deve digitare comandi da terminale: interagisce esclusivamente via chat in linguaggio naturale. È compito dell'assistente invocare in background tutti gli script di controllo e calcolo (`verify_squad_control.py`, `scan_omni_markets.py`, `build_verified_ticket.py`, `scan_live_matches.py`), elaborare i dati e presentare direttamente nella conversazione i risultati già filtrati, certificati e pronti all'uso.
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
- **Regola #39 — Mercati Evoluti di Protezione & Flessibilità (STOP ai mercati convenzionali rigidi)**:
  1. **MultiGol di Squadra (es. MultiGol 1-3 Casa/Ospite)**: Preferire SEMPRE a Over/Under gol totali quando una squadra deve fare la partita. Copre l'1-0, 0-1, 2-0, 1-2, 0-3... evitando di dipendere dall'avversario.
  2. **Combo con MultiGol Esteso (es. 1X + MultiGol 1-5 o X2 + MultiGol 1-5)**: Sostituire le fragili combo "1 + Over 1.5" con "1X + MultiGol 1-5". Copre l'1-0, 2-0, 1-1, 2-1, 3-0 senza mai morire su un risultato corto.
  3. **Casa/Ospite Segna in Entrambi i Tempi: SI**: Per le big dominanti, MA SOLO SE QUOTA >= 1.55 E EDGE POSITIVO (vedi Regola #40).
  4. **Over Differenziato per Tempo (`OV 1°T 0.5 + OV 2°T 1.5`)**: Sfrutta la dinamica fisiologica (fase di studio nel 1°T dove basta 1 gol, difese stanche nella ripresa con almeno 2 gol).
  5. **Doppia Chance + Entrambe Segnano (es. 1X + GG)**: Da usare negli scontri diretti ad alta intensità europea dove la favorita casalinga non perde ma subisce gol (quote eccellenti @ 1.80× - 2.00×).
- **Regola #40 — Strict Ticket Pipeline (Il Funnel Matematico Integrato a 7 Fasi)**:
  Implementato in `services/betting/strict_ticket_pipeline.py` e testabile con `python scripts/build_verified_ticket.py`.
  Nessuna selezione o schedina può essere proposta senza aver superato in ordine rigido tutte le fasi:
  1. **Fase 1 (Roster Gate - Regola #38)**: Controllo anagrafico 2026/27 (DB locale + API Transfers). Chi è ceduto viene bloccato istantaneamente.
  2. **Fase 2 (Absence & Injury Gate)**: Query `/injuries?fixture={id}`. Giocatori infortunati, squalificati o fuori rosa scartati alla radice.
  3. **Fase 3 (Lineup & Starting XI Gate - Regola #37)**: Distinte ufficiali obbligatorie per mercati individuali. Se parte dalla panchina o le formazioni non sono uscite, la giocata sul giocatore è BLOCCATA.
  4. **Fase 4 (Calcolo Probabilità Coniugata Reale & Tempi)**: Se mercato composto (es. Segna Entrambi Tempi: $P_{1T} \times P_{2T}$), la probabilità reale composta e la Fair Odd ($1/P_{reale}$) DEVONO essere calcolate esplicitamente.
  5. **Fase 5 (Filtro Edge Positivo Obbligatorio)**: $\text{Edge} = (P_{reale} \times \text{Quota}) - 1$. Se $\text{Edge} < +4.0\%$, l'evento è **BOCCIATO AUTOMATICAMENTE** (es. Bayern Segna Entrambi @ 1.20 ha Edge -23.5% = BAN TOTALE!).
  6. **Fase 6 (Anti-Scadenza 45')**: Divieto assoluto di mercati che possono morire all'intervallo (45') a quote compresse (< 1.55). Privilegiare SEMPRE mercati con 90 minuti di vita (MultiGol, 1X+Over 1.5).
  7. **Fase 7 (Money Management Scientifico - Kelly Frazionario)**: Max 5-8% del bankroll per singolo ticket; max 15% del bankroll per intera sessione. MAI più rischiare l'intera cassa in un solo turno.

- **Regola #41 — PROTOCOLLO DEI 7 COMANDAMENTI PRE-SCHEDINA (Ordine Sequenziale Rigoroso)**:
  🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO proporre una schedina o selezione "a braccio" o basandosi su impressioni e quote grezze.
  📌 **Flusso Operativo Obbligatorio**:
  1. *Esegui lo scanner assenze*: `python scripts/verify_squad_control.py --fixture <ID>` prima di formulare analisi sui giocatori.
  2. *Valida ogni singolo mercato*: Esegui l'audit via `StrictTicketPipeline` (`scripts/build_verified_ticket.py`).
  3. *Zero allucinazioni*: Se un giocatore non compare nella distinta ufficiale come titolare confermato, proporre SOLO mercati di squadra.
  4. *Rifiuto matematico automatico*: Se un mercato non ha un vantaggio matematico certo sul banco ($\text{Edge} \ge +4.0\%$), NON VA GIOCATO, anche se sembra una "quota sicura" a 1.20.

- **Regola #42 — SCANSIONE ONNIMERCATO & BALANCED SAFETY SCORE (Il Sweet Spot Probabilità-Valore-Quota)**:
  🎯 **Principio Fondamentale**: "Più sicuro" per noi NON significa quota stracciata (1.10-1.20 a edge negativo = trappola mortale), né quota alta speculativa (> 2.50 a varianza ingestibile). "Più sicuro" significa il **Punto di Equilibrio Perfetto (Sweet Spot)**:
  1. **Scansione Onnimercato (TUTTI i mercati a disposizione)**:
     BAgent DEVE scansionare tutti i 100+ mercati bookmaker tramite `OmniMarketScanner` (`scripts/scan_omni_markets.py --fixture <ID>`):
     - Esiti Finali & Doppie Chance (1X2, 1X, X2, Draw No Bet)
     - Over/Under Gol (0.5, 1.5, 2.5, 3.5 totali e di squadra)
     - Gol / No Gol (BTTS)
     - MultiGol Squadra (1-3 Casa, 1-3 Ospite) e MultiGol Partita (1-4, 1-5, 2-4)
     - Combo Protette Classiche (1X + Over 1.5, 1X + Under 3.5, 1X + MultiGol, X2 + Over 1.5)
     - Corner 1X2, Corner Totali, Corner Squadra Over/Under
     - Cartellini 1X2, Cartellini Totali Over/Under
     - Tiri in Porta / Totali
  2. **I 4 Pilastri del Balanced Safety Score (BSS)**:
     - **Alta Probabilità Reale**: $P_{\text{reale}} \ge 72\% - 88\%$ (Poisson & distribuzioni congiunte). Sotto al 70% il mercato è scartato.
     - **Quota Efficace e Utile**: Range target **`1.28 — 1.65`** (fino a 1.85 per combo a doppia chance). Penalizzazione pesante per quote stracciate $< 1.22$ ("falsa sicurezza" che distrugge il bankroll).
     - **Edge Matematico Reale**: $\text{Edge} = (P_{\text{reale}} \times \text{Quota}) - 1 \ge \mathbf{+5.0\%}$. Nessuna scommessa può essere giocata se la quota è inferiore alla Fair Odd ($1/P$).
     - **Respiro a 90 Minuti (Anti-Fragilità)**: Moltiplicatore premio $+20\%$ per mercati elastici (MultiGol, 1X+Over 1.5, Corner); moltiplicatore $0.0$ (bocciatura) per mercati che muoiono al 45' a quota compressa.
- **Regola #43 — INTEGRAZIONE PROGRAMMATICA OBBLIGATORIA DEL SESTO SENSO (Hard Gate Contextual Intelligence)**:
  🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO proporre qualsiasi quota, mercato o schedina basandosi esclusivamente su numeri, formule di Poisson o quote bookmaker SENZA aver integrato formalmente il **SESTO SENSO**.
  🔬 **Motivazione Scientifica & Lezione Bayern-Bodo 0-0 HT**:
  I numeri dicevano che il Bayern segna valanghe di gol, ma il Sesto Senso (giornali, motivazione d'esordio, blocco basso scandinavo, tendenza all'avvio diesel) segnalava chiaramente il rischio di un 1° tempo a ritmi bassi e senza urgenza agonistica. Saltare il Sesto Senso porta a giocare mercati ciechi a quota 1.20 che si schiantano.
  📌 **Protocollo Operativo di Ingegnerizzazione del Sesto Senso**:
  1. **Fase 4 di `StrictTicketPipeline` è BLOCCANTE**: Nessun candidato mercato può essere validato se non possiede una motivazione di Sesto Senso documentata (`sixth_sense_analysis`).
  2. **Audit delle Bandiere Rosse di Sesto Senso**:
     - `ROTATION_RISK` (turnover massiccio, coppe infrasettimanali, turnover pre-derby) ➔ Ban player props e mercati sui due tempi.
     - `SLOW_START` / `DIESEL_TEMPO` (partita di studio, campo pesante, trasferte lunghe) ➔ Ban su mercati 1° tempo a quota compressa.
     - `LOW_MOTIVATION` / `DEAD_RUBBER` (squadra già qualificata o appagata) ➔ Ban su handicap o vittorie larghe.
  3. **Obbligo Rassegna & Contesto**: Prima di finalizzare una proposta, BAgent DEVE sempre specificare il retroscena tattico, il clima ambientale e la motivazione psicologica che confermano la selezione.

- **Regola #44 — RICERCA ONNIMERCATO AUTONOMA & PRINCIPIO DI NEUTRALITÀ (Zero Pregiudizi di Default, Solo il Mercato Migliore)**:
  - 🎯 **Principio Fondamentale (Neutralità & Pragmatismo Assoluto)**:
    Noi usiamo **i mercati migliori in assoluto** per ciascuna partita e **NON denigriamo né escludiamo NESSUN mercato di default**.
    Nessun mercato è un tabù: se per una partita il mercato migliore e più solido è un **1X2 secco** (es. Boca Juniors 1 Fisso stanotte @ 1.47, vinto 3-1), un **Under/Over**, una **Doppia Chance**, un **MultiGol**, un mercato sui **Corner**, sui **Cartellini** o una **Combo**, **SI GIOCA QUEL MERCATO SENZA ALCUN PREGIUDIZIO**.
  - 🛑 **Cosa è Vietato**: È vietata unicamente la **pigrizia analitica**, ovvero proporre sempre e solo 1X2 o Under 2.5 per abitudine cieca quando nel sottomenu del match esistono mercati statisticamente superiori o molto più protetti.
  - 📌 **Direttiva Operativa Obbligatoria**:
    1. **Ricerca Autonoma e Proattiva**: Anche se l'utente fornisce solo la riga base con 1X2 e Under/Over 2.5, BAgent **HA IL DOVERE IMPERATIVO** di scansionare autonomamente (tramite `OmniMarketScanner`, modelli xG/xC/xK e banche dati) l'intero spettro dei mercati per quel match (1X2, DC, Under/Over, MultiGol Squadra, 1X2 Corner, Over Cartellini, Chance Mix, Combo).
    2. **Scelta Imparziale del Mercato Ottimale**: BAgent valuta TUTTE le opzioni a 360° e propone all'utente **IL MERCATO CHE OFFRE IL MIGLIOR EQUILIBRIO TRA PROBABILITÀ REALE, QUOTA E RESPIRO TATTICO A 90 MINUTI**, spiegando con trasparenza perché quella specifica selezione è la più vantaggiosa per noi in quella partita, senza dogmatismi e senza chiusure a priori.

- **Regola #45 — FILTRO VOLUME OFFENSIVO PER I MERCATI CORNER (Soglia Obbligatoria ≥18-20 Tiri Totali & Elevati Tiri in Porta)**:
  - 🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO selezionare mercati sui Corner (1X2 Corner, Over Corner Totali, Over Corner Squadra) per squadre che praticano un possesso palla sterile, lento o orizzontale, o che hanno una produzione offensiva media inferiore a 16-18 conclusioni a partita.
  - 🔬 **Motivazione Scientifica & Meccanica Balistica**:
    I corner non nascono dalla percentuale pura di possesso palla o dal blasone del club, bensì sono una diretta conseguenza meccanica di tre fattori:
    1. Conclusioni e tiri in porta deviati in tuffo o respinti dal portiere oltre il fondo;
    2. Tiri dal limite o dall'interno dell'area respinti dai corpi e dalle scivolate dei difensori (Blocked Shots);
    3. Traversoni e cross tesi dal fondo deviati in extremis dai terzini avversari.
    Se una squadra dominante si accontenta di un vantaggio corto o non calcia verso lo specchio, la produzione di corner si blocca.
  - 📌 **Requisiti Quantitativi Vincolanti per Selezionare i Corner**:
    Perché una giocata su 1X2 Corner o Over Corner sia approvata dal sistema:
    1. **Volume di Fuoco Balistico**: La squadra favorita DEVE avere una media registrata (FootyStats / ESPN / Sofascore) di **`≥ 18 — 20 tiri totali a partita`**.
    2. **Pressione nello Specchio**: Almeno **`≥ 6-7 tiri nello specchio (Shots on Target)`** o tiri ribattuti a match.
    3. **Asimmetria Difensiva dell'Avversario**: L'avversario deve concedere sistematicamente più di 15-18 tiri a partita e difendere con un blocco molto basso nell'ultimo terzo di campo.
    Se questi requisiti di volume non sono certificati, il mercato Corner viene **BOCCIATO AUTOMATICAMENTE** e si opta per mercati protetti alternativi (Doppia Chance, MultiGol Squadra o Under/Over).

- **Regola #46 — BLOCCO ESECUTIVO PROGRAMMATICO OBBLIGATORIO (`scripts/strict_validator.py`) & HARD GATES**:
  - 🛑 **Divieto Assoluto di Proposta in Chat senza Audit Eseguito**:
    È TASSATIVAMENTE VIETATO proporre all'utente qualsiasi selezione, mercato o schedina basandosi su stime narrative o ragionamenti in chat senza aver PRIMA eseguito `scripts/strict_validator.py` in background.
    Ogni proposta presentata in chat DEVE contenere il certificato di superamento emesso dallo script con stato `🟢 CERTIFICATO ED APPROVATO`.
  - 🛡️ **I 4 Hard Gates Inviolabili**:
    1. **Gate 0 (Anti-Straight-Win Low Odds Ban)**: Divieto assoluto di 1 o 2 fisso a quota compressa (`< 1.65`). L'esposizione al pareggio o all'episodio fortuito è inaccettabile (Lezione Athletic Bilbao 1-1). Obbligo di sostituzione con linee protette: `1X`, `1X + Over 1.5`, `DNB`, `MultiGol 1-3 Squadra`.
    2. **Gate 0.5 (Regola #45 Volume Corner)**: Divieto assoluto di scommettere sui corner per squadre con produzione offensiva inferiore a **`18-20 tiri totali a partita`** (Lezione Liverpool-Fulham 4-8 corners).
    3. **Gate 4 (Rischio Coppe Europee Infrasettimanali & Tempi)**: Se una big affronta un match prima di una gara di Champions/Europa League nei 3-4 giorni successivi, sono TASSATIVAMENTE VIETATI i mercati 1° tempo a quota compressa o mercati composti sui due tempi per rischio turnover e approccio "diesel" a basso ritmo (Lezione Sunderland-Arsenal 0-0 HT).
    4. **Gate 8 (Protocollo Continuità & Money Management)**: Max 3-4 selezioni per ticket (5+ gambe bannate per sempre) e max 8% del bankroll per singola schedina.

- **Regola #47 — MERCATI AD ALTA RESILIENZA BALISTICA (MultiGol Asimmetrico Tempi, MultiGol 1-3 Squadra & Over Tiri Totali)**:
  - 🎯 **Origine e Benchmark Competitivo (Lezione Tipster Screenshot 12/09/2026)**:
    L'analisi di ticket vincenti su match ad alta varianza ha evidenziato 3 mercati ad altissima resilienza dove il nostro sistema convenzionale è stato vulnerabile:
    1. **MultiGol Asimmetrico Tempi (`MG 0-2 1°T + 1-3 2°T`)**:
       - *Meccanica*: Assorbe perfettamente lo 0-0 all'intervallo (oltre a 1-0 o 0-1) senza morire al 45' come accaduto ad Arsenal/Sunderland. Nella ripresa (`1-3 2°T`), con difese stanche e spazi aperti, basta 1 solo gol fino a un massimo di 3 per andare alla cassa.
    2. **MultiGol di Squadra in Big Match (`MultiGol 1-3 Ospite/Casa`)**:
       - *Meccanica*: Nei match insidiosi fuori casa (es. Napoli a Firenze, Barça o Real Madrid), scommettere su 1X2 o Over totali espone a beffe. Il `MultiGol 1-3 Squadra` copre vittorie per 0-1, 0-2, 0-3, ma anche pareggi come 1-1, 2-2 o sconfitte aperte (1-2, 2-3). È totalmente disgiunto dalla tenuta difensiva della favorita.
    3. **Over Tiri Totali Partita (`Over 21.5 / Over 23.5 Tiri Totali`)**:
       - *Meccanica*: Svincola completamente la giocata dall'esito 1X2 e dalla varianza di conversione dei gol. Grandi squadre offensive che subiscono gol al primo contropiede o sbattono su portieri saracinesca (es. Atalanta-Cagliari 1-2 con 25 tiri) distruggono l'1X2 o l'Over gol, ma chiudono con 24-28 conclusioni totali.
  - 📌 **Direttiva di Integrazione Software**:
    I tre mercati sono implementati nativamente in `OmniMarketScanner` (`services/analysis/omni_market_scanner.py`) con calcolo Poisson congiunto, distribuzioni stocastiche dei tiri e classificati come mercati elastici a 90 minuti (`90_MIN_ELASTIC`) con bonus BSS.

- **Regola #48 — ANTI-CEILING TRAP (Divieto di Tetto Massimo su Attacchi Dominanti)**:
  - 🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO selezionare mercati con tetto massimo stretto (`MultiGol 1-3`, `MultiGol 1-2`, `Under 2.5`) a favore di squadre con potenziale offensivo devastante (Barcellona di Flick, Bayern Monaco, Manchester City, Real Madrid) quando affrontano squadre di fascia bassa con difese fragili.
  - 🔬 **Motivazione Scientifica & Lezione Utente 13/09/2026**:
    In queste sfide asimmetriche la distribuzione dei gol non è un Poisson standard piatto, ma presenta una marcata coda destra (Heavy Right-Tail). Il rischio concreto di goleada (4-0, 5-0, 4-1, 6-1) supera il 22%. Perdere una schedina perché la favorita stravince segnando "troppi gol" è una distorsione algoritmica inaccettabile.
  - 📌 **Direttiva di Integrazione**:
    Sostituire tassativamente con **mercati aperti verso l'alto (Uncapped Markets)**: `2 + Over 1.5` (o `1 + Over 1.5`), `Over 1.5 Squadra`, `X2 + Over 1.5` o `MultiGol 2-5`. Implementato come `Gate 0.75` in `StrictTicketPipeline`.

- **Regola #49 — DIVIETO ASSOLUTO DI ALLUCINAZIONE NOMINALE & AUDIT ANAGRAFICO/FORMAZIONI OBBLIGATORIO (Zero Parametric Memory Gate)**:
  - 🛑 **Divieto Assoluto di Memoria Parametrica**:
    È TASSATIVAMENTE VIETATO citare giocatori, allenatori o moduli tattici basandosi sulla memoria pregressa (2023-2024). Il calcio si evolve continuamente: citare Kvaratskhelia o Lukaku al Napoli nel 2026 quando Kvaratskhelia è al PSG, o Italiano al Bologna quando le panchine sono cambiate, è un errore gravissimo che mina l'attendibilità dell'analisi.
  - 🔬 **Motivazione Scientifica & Lezione Utente 13/09/2026 (Napoli-Bologna)**:
    Quando l'assistente formula motivazioni narrative pre-gara, l'assenza di un controllo sul testo permetteva alla memoria non aggiornata di inventare coppie d'attacco o guide tecniche fantasma. L'algoritmo deve bloccare alla radice qualsiasi discrepanza tra il testo del Sesto Senso e il database anagrafico della stagione corrente.
  - 📌 **Direttiva di Integrazione Software (Gate 0.8)**:
    1. **Audit Entità Testuali (`audit_text_entities`)**: In `StrictTicketPipeline.validate_candidate()`, ogni testo di Sesto Senso viene scansionato contro i 2500+ giocatori registrati in `bagent.db`. Se un giocatore citato appartiene ad un'altra squadra (es. Kvaratskhelia al PSG) o non figura nella rosa attuale del club (es. Lukaku), il ticket viene **BOCCIATO AUTOMATICAMENTE** (`[BLOCCATO - REGOLA #49: ALLUCINAZIONE NOMINALE NON CERTIFICATA]`).
    2. **Divieto di Titolari Garantiti Pre-Distinte (Timing Gate a 60')**: Finché le formazioni ufficiali non sono depositate (kickoff > 60'), il Sesto Senso ha il **DIVIETO ASSOLUTO di dare per certa la titolarità di singoli calciatori** o di basare mercati di squadra su presenze individuali speculative.
    3. **Analisi di Squadra Obbligatoria**: Pre-distinte, l'analisi deve basarsi esclusivamente su parametri oggettivi di collettivo: xG casalinghi/esterni 2026, medie gol fatti/subiti, congestione del calendario europeo, solidità difensiva e motivazione di classifica.

- **Regola #50 — PROTOCOLLO ASSEDIO LIVE & TRIGGER ASIMMETRICO ("Underdog Leads Favorite")**:
  - 🎯 **Principio Fondamentale & Dinamica Tattica**:
    Quando una squadra nettamente sfavorita ("piccola", quota pre-match della favorita $\le 1.60$) passa inaspettatamente in vantaggio in una partita in-play (tra il 12' e il 78'), l'equilibrio tattico si spezza e si instaura la modalità "Assedio Asimmetrico":
    1. La favorita riversa 8-9 uomini nella trequarti avversaria per rimontare;
    2. La piccola si rifugia nel blocco basso ("park the bus"), spazza palloni sul fondo, perde tempo e ricorre a falli tattici di transizione.
  - 🔬 **Attivazione Istantanea dei 4 Mercati Asimmetrici**:
    1. **Corner Boom Favorita**: Tasso di produzione balistica pari a $\sim 1.35$ corner ogni 10 minuti di assedio ($E[\Delta \text{Corner}] = \text{Minuti Rimanenti} \times 0.135$). Si attiva la linea `Over X.5 Corner Squadra Favorita Live`.
    2. **Cartellini Ostruzionismo Piccola**: Nel 2° tempo (dopo il 45'), il tasso sanzioni per perdite di tempo e falli sale a $\sim 0.045$ cartellini/min. Si attiva `Over X.5 Cartellini Squadra Sfavorita Live`.
    3. **Volume Balistico Tiri Favorita**: Pressione costante con $\ge 2.8$ tiri ogni 10 minuti. Si attiva `Over X.5 Tiri Totali Favorita Live`.
    4. **Value Bet Rimonta Live (1X / X2 Live)**: La quota della Doppia Chance a favore della big schizza da 1.15-1.25 pre-gara a quote espanse ($@ 1.55 - 2.20$) con probabilità reale residua del 60%-75%, generando un Edge matematico compreso tra $+15\%$ e $+25\%$.
  - 📌 **Integrazione Software (`services/live/siege_engine.py`)**:
    Implementato nel Live Sentinel (`scripts/live_tracker.py` e `scripts/live_monitor.py`). Invia automaticamente un alert Telegram ad altissima priorità (`🚨 ALLERTA ASSEDIO LIVE: PICCOLA IN VANTAGGIO SULLA BIG!`) con le 4 selezioni in tempo reale non appena la sfavorita passa in vantaggio.

- **Regola #51 — FILTRO "CORTO MUSO" & DIVIETO OVER 1.5 SU SQUADRE PRAGMATICHE (Lezione Allegri al Napoli)**:
  - 🛑 **Divieto Assoluto**:
    È TASSATIVAMENTE VIETATO selezionare mercati rigidi che escludono l'1-0 (come `1X + Over 1.5`, `1 + Over 1.5`, `Over 1.5 Squadra`) per club guidati da allenatori storicamente pragmatici e specialisti della gestione a basso ritmo / "corto muso" (in primis **Massimiliano Allegri al Napoli**, o Diego Simeone all'Atletico Madrid), specialmente contro squadre che impostano un blocco basso.
  - 🔬 **Motivazione Scientifica & Lezione Utente 13/09/2026**:
    La filosofia tattica di Allegri non cerca mai la goleada né il raddoppio forzato; una volta sbloccata la gara sull'1-0, la squadra abbassa l'intensità di pressing, congela il pallone, gestisce il cronometro e protegge il clean sheet con il minimo scarto. La probabilità che la partita si chiuda esattamente sull'1-0 o 0-1 sale dal normale 9-11% a oltre il 24-28%. Pretendere per forza l'Over 1.5 è un suicidio tattico che espone al tradimento del gol singolo.
  - 📌 **Direttiva di Sostituzione Obbligatoria (Gate 0.85)**:
    Implementato come `Gate 0.85` in `StrictTicketPipeline` (`services/betting/strict_ticket_pipeline.py`). Qualsiasi proposta che combini Napoli o contesti "corto muso" con Over 1.5 viene **BOCCIATA AUTOMATICAMENTE**. Obbligo di sostituzione con mercati resilienti che incassano sull'1-0:
    1. `1X + MultiGol 1-5` (o `X2 + MultiGol 1-5`);
    2. `1X + Under 3.5` (o `X2 + Under 3.5`);
    3. `1 Fisso` (se quota $\ge 1.65$) o `Draw No Bet (DNB)`;
    4. `MultiGol 1-3 Squadra`.

- **Regola #52 — SPECIALIZZAZIONE DEI 4 CIRCUITI SATELLITE (Brasile, Argentina, Olanda, Norvegia)**:
  - 🎯 **Principio Fondamentale & DNA Tattico**:
    BAgent adotta modelli quantitativi e filtri dedicati per i 4 campionati satellite ad alta frequenza di scommessa:
    1. **Brasileirão Serie A 🇧🇷 (`bra.1`)**: "Fortino Casalingo & Usura da Trasferta". Fattore campo elevatissimo ($V_{\text{casa}} \approx 48\%$) dovuto a trasferte di 3000+ km e pressione ambientale (Maracanã, Allianz Parque). *Mercati Re*: `1X + MultiGol 1-5`, `1X + Under 3.5`, `1 Fisso Big in Casa`. Divieto di 2 fissi esterni a quota compressa.
    2. **Liga Profesional Argentina 🇦🇷 (`arg.1`)**: "Guerra Tattica, Catenaccio & Arbitraggio di Ferro". Media gol $< 2.10$, Under 2.5 al $62\%$, media oltre 30 falli e 5.8 cartellini/gara. *Mercati Re*: `Under 2.5 / Under 3.5`, `Over 4.5 / 5.5 Cartellini Totali`, `Doppia Chance Protetta`. Divieto di Over 2.5 compressi.
    3. **Eredivisie Olandese 🇳🇱 (`ned.1`)**: "Total Football & Heavy Right-Tail". Media gol $3.28$/partita, Over 2.5 al $68.5\%$. PSV, Feyenoord e Ajax macchine da gol. *Mercati Re*: `1/2 + Over 1.5`, `1/2 + Over 2.5`, `MultiGol 2-5`, `Over Corner Big`. Divieto di Under 2.5 o tetti stretti (Anti-Ceiling Regola #48).
    4. **Eliteserien Norvegese 🇳🇴 (`nor.1`)**: "Sintetico Veloce, Ritmi Alti & Fair Play". Campi in erba sintetica, rimbalzo rapido, Bodø/Glimt e Brann a trazione anteriore (Over 2.5 al $64\%$). Arbitraggi permissivi all'inglese (media $< 2.9$ cartellini). *Mercati Re*: `Over 2.5`, `Gol / BTTS`, `1X2 Corner Dominante`. **DIVIETO ASSOLUTO DI OVER CARTELLINI IN NORVEGIA**.
- **Regola #53 — VERIFICA OBBLIGATORIA DEL CALENDARIO UEFA & COPPE (Zero Allucinazioni Temporali Turni Infrasettimanali)**:
  - 🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO citare turni di Champions League, Coppe Europee o turni infrasettimanali basandosi sulla memoria parametrica o su presunte abitudini di calendario senza prima aver interrogato l'API con il calendario reale della stagione corrente.
  - 🔬 **Motivazione Scientifica & Lezione Utente 14/09/2026**:
    La 1ª giornata della UEFA Champions League 2026/27 si è svolta l'**8-10 Settembre 2026** (conclusa con le partite di Barcellona, Bayern, PSG e Liverpool). La 2ª giornata si disputerà il **13-14 Ottobre 2026**. Questa settimana (16-17 Settembre 2026) vede invece il debutto della **UEFA Europa League** (Milan vs Benfica, Celta Vigo), della **Coppa Italia** (Genoa, Fiorentina) e della **Carabao Cup inglese**, e NON la Champions League.
- **Regola #54 — PROTOCOLLO ELASTICO DI ESPANSIONE PALINSESTO (MultiGol Tempi 1-3 1°T + 1-4 2°T & DC + MultiGol Esteso)**:
  - 🎯 **Origine & Benchmark Vincente (Lezione Screenshot Tipster 13/09/2026 @ 8.47×)**:
    L'analisi della schedina vincente ha dimostrato che la rigidità dei mercati convenzionali (`1X2`, `Over 1.5/2.5`) limitava drasticamente il palinsesto ed esponeva a trappole mortali (come l'1-0 del Napoli che bruciava l'Over 1.5).
  - 🚀 **I 3 Pilastri di Espansione del Palinsesto (+300% match giocabili)**:
    1. **MultiGol Asimmetrico Tempi (`MultiGol 1-3 1°T + 1-4 2°T : SI` @ 1.40 — 1.48)**:
       - Rende immediatamente giocabili tutte le partite ad alto ritmo (Bundesliga, Eredivisie, Eliteserien, Premier) **SENZA dover indovinare l'esito 1X2 né chi segna**. Chiede semplicemente almeno 1 gol nei primi 45' e almeno 1 gol nella ripresa.
    2. **Doppia Chance + MultiGol Esteso (`1X + MultiGol 1-4` o `X2 + MultiGol 1-5` @ 1.45 — 1.58)**:
       - Sblocca i big match più spinosi (derby, scontri diretti) e le trasferte insidiose. **Non muore MAI sull'1-0 né sull'1-1 o 0-1**. Incassa sull'1-0 corto di Allegri come sul 2-1 o 3-1.
     3. **MultiGol di Squadra (`MultiGol 1-3 Ospite/Casa` @ 1.28 — 1.42)**:
       - Sblocca le trasferte delle grandi (es. Juventus a Sassuolo, Real Madrid). È totalmente immune ai crolli difensivi della favorita (la Juve perde 3-2 ma incassa la quota).
  - 📌 **Direttiva di Sistema**:
    BAgent adotta questi tre mercati come strumenti primari di scansione in `OmniMarketScanner`, preferendoli a qualsiasi combo rigida.

- **Regola #55 — PROTOCOLLO FERREO DI CONSULTAZIONE DIRETTA & TRIPLA VERIFICA FONTI (Zero Allucinazioni, Triplo Check Obbligatorio Pre-Schedina)**:
  - 🛑 **Divieto Assoluto di Memoria Parametrica & Inferenza Narrativa**:
    È TASSATIVAMENTE VIETATO formulare qualsiasi pronostico, quota, posizione di classifica, rendimento casa/trasferta o stato di forma basandosi sulla memoria pregressa o su impressioni generali. Nessuna affermazione (es. "X è in vetta", "Y ha una difesa chiusa", "H2H dominato") può essere generata senza un riscontro verificato in tempo reale su una fonte primaria ufficiale (FootyStats / Sofascore / Flashscore).
  - 🔬 **Motivazione Scientifica & Lezione Catastrofica 14/09/2026**:
    L'affidarsi a ricordi di stagioni passate ha portato a distorsioni inaccettabili che hanno causato la perdita delle schedine:
    1. *Irlanda*: Shelbourne e Derry dipinti come capilista in lotta per il titolo (situazione del 2024), mentre la classifica reale vedeva lo Shelbourne 6° e Derry 5°, e in vetta c'erano Shamrock e St. Patrick's.
    2. *Francia (Ligue 2)*: Red Star vs Metz descritta come gara sbilanciata a favore del Metz, quando in realtà erano separate da 1 solo punto (5° contro 6°), violando il principio di prudenza sugli scontri diretti equilibrati.
    3. *Portogallo*: Moreirense vs Marítimo catalogata come "gara a basso indice di gol" proponendo l'Under 2.5, ignorando che entrambe le squadre avevano subito imbarcate pesanti (0-4 e 0-3) e avevano difese altamente permeabili.
    4. *Argentina*: Presupporre che la squadra di casa (Defensores de Belgrano) fosse una garanzia senza controllare i precedenti diretti (dove il Deportivo Madryn era imbattuto negli ultimi 4 scontri).
  - 📌 **Il Triplo Check Obbligatorio Pre-Schedina**:
    Prima di proporre qualsiasi selezione, BAgent DEVE eseguire il seguente controllo incrociato obbligatorio:
    1. **Check 1: Classifica Reale & Δ Punti della Stagione Corrente (FootyStats / Sofascore / Flashscore)**:
       - Posizione effettiva in classifica di entrambe le squadre, punti totali e $\Delta$ punti reale. Se $\Delta \le 3$, si applica il divieto di mercati 1X2 rigidi.
       - Forma certificata delle ultime 5 partite (`W-D-L`).
       - Gol fatti e subiti effettivi (totali e casa/trasferta).
    2. **Check 2: Scontri Diretti Storici (H2H Reale)**:
       - Verifica dei tabellini degli ultimi 3-5 precedenti diretti. Vietato dichiarare "storico dominato" o "sempre Under" senza tabellini verificati.
    3. **Check 3: Roster, Guida Tecnica & Distinte Ufficiali**:
       - Verifica dell'allenatore attuale certificato e assenze pesanti (squalifiche e infortuni).
  - 🛡️ **Blocco Preventivo (Safe-Discard Policy)**:
    Se per un match i dati di classifica, forma recente o H2H non sono reperibili con certezza assoluta in tempo reale, **IL MATCH VIENE SCARTATO AUTOMATICAMENTE DAL PALINSESTO**. Nessun compromesso e zero scommesse al buio.
  - 💻 **Integrazione Software (Gate 0.9)**:
    Implementato come `Gate 0.9` (`SourceGroundingGate`) in `StrictTicketPipeline` (`services/betting/strict_ticket_pipeline.py`). Ogni candidato deve certificare le fonti reali (`verified_standings_source`, `verified_h2h_data`, `verified_form_data`). In assenza di fonti validate, il candidato viene bocciato con `[BLOCCATO - REGOLA #55: MANCATA CONSULTAZIONE FONTI REALI OBIETTIVE]`.

- **Regola #56 — BAN TOTALE SECONDE DIVISIONI, CAMPIONATI MINORI & SQUADRE RISERVE/B (Solo Prime Divisioni & Coppe Ufficiali d'Élite)**:
  - 🛑 **Divieto Assoluto & Inviolabile (Zero Seconde Categorie)**:
    È TASSATIVAMENTE VIETATO selezionare, proporre o inserire in schedina qualsiasi partita appartenente a:
    1. **Seconde Divisioni e Categorie Minori Nazionali**: Serie B (Italia), Ligue 2 (Francia), LaLiga 2 (Spagna), 2. Bundesliga (Germania), Championship / League One / Two (Inghilterra), Eerste Divisie (Olanda), Primera Nacional / B (Argentina), Serie B (Brasile), Primera B (Cile/Colombia), Segunda División (Paraguay), ecc.
    2. **Campionati Dilettantistici, Regionali e Amatori**: Isthmian League, Southern League, National League, Regionalliga, Serie C/D, ecc.
    3. **Squadre Riserve, Seconde Squadre ("B Teams") e Formazioni Giovanili**: Tutte le squadre B/riserve indipendentemente dalla lega (Jong Ajax, Jong PSV, Jong Utrecht, Jong AZ, Barça Atlètic, Real Madrid Castilla, Celta Fortuna, Athletic B, Porto B, Benfica B, PAOK B, MLS Next Pro / Portland Timbers II, St. Louis II, U21, U23, Primavera, ecc.).
  - 🔬 **Motivazione Scientifica & Lezione Utente 14/09/2026**:
    Le seconde categorie e le formazioni B presentano un tasso di volatilità e imprevedibilità ingestibile:
    - Formazioni instabili soggette a continui prestiti, convocazioni in prima squadra e turnover non annunciato;
    - Dati statistici e di infortunio opachi, ritardati o incompleti rispetto ai massimi campionati;
    - Motivazioni sportive asimmetriche (le seconde squadre non possono salire di categoria e sperimentano continuamente moduli e giovani acerbi, distruggendo le metriche di Poisson).
  - 🎯 **Perimetro Esclusivo Ammesso (Solo Tier 1 d'Élite)**:
    Sono ammesse esclusivamente:
    1. **Le Prime Divisioni Nazionali Ufficiali (Tier 1)**:
       - Top 5 Europee (Serie A, Premier League, La Liga, Bundesliga, Ligue 1);
       - Altre Prime Divisioni Europee regolamentate con copertura TV/VAR (Liga Portugal, Eredivisie, Premiership scozzese, Jupiler Pro League belga, Superliga danese, Eliteserien norvegese, Allsvenskan svedese, Super League greca/turca/svizzera);
       - Prime Divisioni Sudamericane Tier 1 regolamentate (Brasileirão Serie A, Liga Profesional Argentina).
    2. **Grandi Coppe Ufficiali UEFA & Nazionali Maggiori**:
       - UEFA Champions League, Europa League, Conference League;
       - Fasi finali delle Coppe Nazionali maggiori (Coppa Italia, FA Cup, Copa del Rey, DFB Pokal) SOLO tra squadre di Prima Divisione.
  - 💻 **Integrazione Software (Gate 0.2)**:
    Implementato come `Gate 0.2` (`Tier1OnlyGate`) in `StrictTicketPipeline` (`services/betting/strict_ticket_pipeline.py`). Qualsiasi evento appartenente a seconde divisioni o squadre riserve viene bloccato istantaneamente con `[BLOCCATO - REGOLA #56: BAN SECONDE DIVISIONI & SQUADRE RISERVE/B]`.

- **Regola #57 — ANTI-FAVORITE BLIND SPOT (Divieto di Giudizio Narrativo da Posizione di Classifica & Falsa Base d'Acciaio)**:
  - 🛑 **Divieto Assoluto**:
    È TASSATIVAMENTE VIETATO etichettare come "base d'acciaio", "quota sicura" o "partita sbilanciata" una scommessa basandosi esclusivamente sul divario di classifica (es. "prima contro ultima"). Più la partita appare sbilanciata sulla carta, più il bookmaker comprime la quota aggiungendo margine a favore del banco, distruggendo l'Edge matematico ($\text{Edge} < 0\%$).
  - 🔬 **Motivazione Scientifica & Lezione América de Cali - Deportivo Pasto (14/09/2026)**:
    L'assistente ha approvato a parole `1 + Over 1.5 @ 1.45` definendola "ottima base d'acciaio" solo perché l'América era 1ª e il Pasto ultimo. L'interrogazione reale dei dati FootyStats ha invece svelato che negli ultimi 3 precedenti a Cali il match è terminato **1-1, 0-0, 1-1** (3 pareggi consecutivi, Pasto autentica bestia nera in blocco basso) e la quota 1.45 offriva un Edge negativo $(-1.4\%)$.
  - 📌 **Direttiva di Validazione Vincolante (Gate 0 Esteso)**:
    In ogni scontro asimmetrico:
    1. Divieto di combo rigide con segno 1 o 2 fisso sotto quota 1.65 (`1 + Over 1.5`, `1 + Under 3.5`);
    2. Obbligo di sostituzione con mercati elastici che assorbono il pareggio: `1X + MultiGol 1-4`, `MultiGol 1-3 Casa`;
    3. Verifica obbligatoria dell'H2H storico negli ultimi 3 precedenti.

- **Regola #58 — PROTOCOLLO "CODE-FIRST REFLEX" & ZERO CONVALIDA VERBALE SENZA CERTIFICATO ESEGUITO**:
  - 🛑 **Divieto Assoluto di Compiacenza e Giudizi a Parole**:
    È TASSATIVAMENTE VIETATO commentare o approvare verbalmente una quota comunicata dall'utente (es. *"Perfetto, quota eccellente!", "Base di ferro!", "Ottima intuizione!"*) prima di aver materialmente eseguito il motore di validazione in background.
  - 📌 **Flusso Operativo Improrogabile (I 3 Passaggi Meccanici)**:
    1. **Fase 1 (Zero Aggettivi Qualificativi)**: Vietato usare parole rassicuranti prima dell'audit.
    2. **Fase 2 (Esecuzione Programmatica Immediata)**: Lancio istantaneo di `scripts/strict_validator.py` con dati FootyStats e H2H reali.
    3. **Fase 3 (Verdetto Trasparente)**: Se lo script fallisce anche uno solo degli Hard Gates (Gate 0, Gate 6, ecc.), l'assistente DEVE esporre immediatamente il motivo del blocco, senza mai tentare di giustificare o promuovere la quota.

- **Regola #59 — REGOLA FERREA DEL TORNEO IN ESSERE (Divieto Assoluto di Statistiche Storiche degli Anni Passati)**:
  - 🛑 **Divieto Assoluto & Inviolabile**:
    È TASSATIVAMENTE VIETATO calcolare o basare statistiche, rendimento casa/trasferta, medie gol, xG, percentuali di vittoria o giudizi di affidabilità sullo storico degli anni/stagioni passate, A MENO CHE l'utente non lo richieda esplicitamente (es. *"confronta con l'anno scorso"*, *"mostrami lo storico decennale"*).
  - 🔬 **Motivazione Scientifica & Lezione Kalimantan Borneo (16/09/2026)**:
    L'affidarsi alla presunta reputazione storica passata (*"il Borneo a Samarinda è storicamente un fortino inespugnabile da anni"*, o vecchi precedenti come il 4-0 del 2025) ha accecato l'analisi, ignorando che nel **torneo in corso (stagione 2026/27)** il Borneo ha perso 2 delle ultime 3 partite casalinghe (compreso lo 0-1 con il Persija). Le squadre di calcio cambiano allenatori, interpreti, condizione atletica e chimica di squadra a ogni stagione: lo storico remoto degli anni passati è rumore distorsivo che nasconde le fragilità attuali.
  - 📌 **Direttiva di Calcolo Obbligatoria (Current Season Only)**:
    Tutte le valutazioni statistiche devono basarsi ESCLUSIVAMENTE sui dati del torneo in corso:
    1. **Classifica & Dati della Stagione Attuale**: Punti, partite giocate, vittorie, pareggi e sconfitte unicamente del campionato o della coppa in corso;
    2. **Rendimento Casa/Trasferta Attuale**: Gol fatti e subiti in casa/trasferta solo della stagione corrente;
    3. **Forma Recente (Ultime 3-5 Gare della Stagione Corrente)**: Verifica obbligatoria del trend immediato (`W-D-L` recente con la rosa attuale);
    4. **Scontri Diretti (H2H)**: Considerare solo gli scontri diretti disputati nell'anno in corso; quelli degli anni passati sono vietati come base previsionale salvo specifica richiesta dell'utente.
  - 💻 **Integrazione Software**:
    Ogni query a DB, API-Football o FootyStats deve includere esplicitamente il vincolo `season == current_season`.

- **Regola #60 — PROTOCOLLO RASSEGNA STAMPA MULTI-LEGA & KNOW-HOW SPECIALISTICO (Direct Newspaper Intelligence)**:
  - 🛑 **Divieto Assoluto di Analisi Senza Rassegna Stampa**:
    È TASSATIVAMENTE VIETATO formulare pronostici o convalidare selezioni basandosi unicamente su numeri freddi o metriche xG senza aver eseguito l'estrazione e lettura diretta degli articoli dei principali quotidiani sportivi specialistici (`scripts/fetch_sports_news.py`) e dei portali di analisi comparata (*MondoPengwin* — `https://www.mondopengwin.it/pronostici/calcio/`).
  - 🔬 **Motivazione Scientifica**:
    I numeri non conoscono liti nello spogliatoio, rotazioni concordate in conferenza stampa, contratti in scadenza, carichi di lavoro atletici o cambi di modulo all'ultimo minuto. Solo la stampa specializzata locale (*Gazzetta/Corriere* in Italia, *Marca/AS* in Spagna, *The Athletic/BBC* in UK, *Kicker* in Germania, *L'Équipe* in Francia, *A Bola* in Portogallo) e le fonti di studio tattico pre-match (*MondoPengwin*) forniscono il know-how tattico profondo indispensabile per il Sesto Senso.
  - 📌 **Direttiva Operativa Obbligatoria**:
    Per ogni match candidato a finire nei ticket, BAgent DEVE interrogare `scripts/fetch_sports_news.py --home "<Home>" --away "<Away>" --league "<League>"` (e consultare le schede match di `mondopengwin.it`) ed estrarre le dichiarazioni degli allenatori, i ballottaggi e il clima ambientale pre-gara.

- **Regola #61 — PARADIGMA 1X2-AGNOSTICO (Zero Bias sull'Esito & Priorità ai Mercati Indipendenti)**:
  - 🎯 **Principio Fondamentale (Disaccoppiamento dal Risultato)**:
    Non ci deve interessare chi vince, chi pareggia o chi perde. Scommettere su esiti 1X2 o su doppie chance espone alla varianza più distruttiva del calcio (gol casuale al 93', espulsioni, rigori). I mercati migliori sono quelli **100% indipendenti dall'esito finale**:
    1. **MultiGol Totale Partita (`MultiGol 2-5`, `MultiGol 1-4`, `MultiGol 2-4`)**: Incassa con qualsiasi vincitore (1-1, 2-0, 0-2, 2-1, 1-2, 2-2, 3-1, 0-3...);
    2. **Corner Totali Match (`Over 7.5 / Over 8.5 Totali`)**: Somma la produzione balistica di ambo i fronti a prescindere dal punteggio;
    3. **Cartellini Totali Match (`Over 3.5 / Over 4.5 Totali`)**: Sfrutta la tensione agonistica e la severità arbitrale;
    4. **Tiri Totali Partita (`Over 21.5 / Over 22.5 Tiri Totali`)**: Svincolato dalla precisione realizzativa sotto porta;
    5. **MultiGol 2° Tempo (`MG 1-3 2° Tempo`)**: Massimizza la resa fisica ed elastica negli ultimi 45 minuti quando le difese calano.
  - 🛑 **Divieti Vincolanti**:
    - Ban totale di `Over 0.5 1° Tempo` a quote compresse (< 1.40) che possono morire all'intervallo;
    - Ban totale di `Under 3.5` o `MultiGol 1-2` su squadre ad alto potenziale offensivo in casa (Ceiling Trap);
    - Max 3 selezioni per ticket (Protocollo Continuità).

- **Regola #62 — I 5 PILASTRI DI POTENZIAMENTO & INTEGRAZIONE END-TO-END (Piattaforma Professionale Unificata)**:
  - 🎯 **Architettura Integrata**: BAgent opera attraverso 5 motori sinergici integrati nel codice:
    1. **Netwin Live Odds Connector & Aggio Sentinel (`services/betting/netwin_odds_checker.py`)**:
       - Verifica automatica delle quote reali di Netwin.it rispetto a quelle teoriche.
       - Implementato come **Gate 6.5** in `StrictTicketPipeline`: se il bookmaker taglia la quota e fa crollare l'Edge sotto al $+4.0\%$, la scommessa viene **BOCCIATA AUTOMATICAMENTE** (`[BLOCCATO - GATE 6.5: NETWIN AGGIO TRAP]`) e viene proposta la linea elastica non compressa (es. MultiGol 2-4 o Over Corner).
    2. **Bankroll Ledger & P&L Tracker in SQLite (`scripts/manage_bankroll.py`)**:
       - Registro transazioni e storico del conto memorizzato in `data/bagent.db` (`bankroll_history`, `ticket_ledger`, `bet_leg_ledger`).
       - Calcolo automatico di saldo corrente (base 37,32 €), volume giocato, payout incassato, profitto netto, Yield% e Win Rate per mercato.
    3. **Push Telegram Sentinel (`services/telegram/telegram_sentinel.py`)**:
       - Invio automatico del Master Ticket Certificato direttamente su Telegram non appena approvato con quote, motivazioni Sesto Senso e puntata consigliata;
       - Invio immediato dell'allerta **Protocollo Assedio (Regola #50)** in tempo reale su smartphone quando la sfavorita segna contro la favorita.
    4. **Post-Mortem Engine & Tactical Feedback Loop (`services/analysis/post_mortem_engine.py` & `scripts/run_post_mortem.py`)**:
       - Diagnosi analitica post-partita sui ticket conclusi (gol FT/HT, corner, tiri, cartellini rossi prematuri, rigori).
       - Classificazione della causa di fallimento (`EARLY_RED_CARD`, `LOW_SHOT_VOLUME`, `PARK_THE_BUS`, `PENALTY_VARIANCE`, `DIESEL_FIRST_HALF`) e archiviazione della lezione nella tabella `tactical_lessons` per auto-calibrare il modello.
    5. **Weighting Dinamico delle Fonti di Sesto Senso (`services/football/external/sources/news.py`)**:
       - Matrice `SOURCE_WEIGHTS_BY_CATEGORY` e funzione `calculate_weighted_confidence()`: ponderazione euristica che valorizza *MondoPengwin* sui MultiGol (peso 1.40), *Gazzetta/Marca* su formazioni e infortuni (1.50) e *FootyStats* su volumi balistici e corner (1.50).

- **Regola #63 — INGEGNERIZZAZIONE COMBINAZIONI SPECIALI, CHANCE MIX & ANTI-FRAGILITÀ BALISTICA**:
  - 🎯 **Principio Fondamentale (Superamento dei Mercati Convenzionali Fragili)**:
    BAgent adotta l'ingegnerizzazione stocastica avanzata tramite `SpecialCombinationsEngine` (`services/analysis/special_combinations_engine.py`) per identificare combinazioni speciali con probabilità congiunta reale dell'**`88% — 94%`**:
    1. **Chance Mix a Matrice Unione ($P(A \cup B)$)**:
       - **`1X o Over 1.5`**: L'unico scenario perdente dell'intero spettro calcistico è lo **0-1 esatto**. Copre vittorie interne, pareggi (0-0, 1-1, 2-2) e qualsiasi vittoria esterna con 2+ reti ($P_{reale} \ge 91\%-94\%$).
       - **`X2 o Over 1.5`**: Perde unicamente sull'1-0 esatto della squadra casalinga. Ideale per trasferte delle favorite.
       - **`Gol o Over 2.5`**: Esclude solo 0-0, 1-0, 2-0, 0-1, 0-2; incassa su tutti i pareggi con gol e su tutte le goleade.
    2. **MultiGol Asimmetrico per Tempi (`MG 0-2 1°T + MG 1-3 2°T`)**:
       - Sfrutta la fisiologia atletica: studio controllato nei primi 45' (P 0-2 gol > 94%) ed espansione nella ripresa con difese allungate (P 1-3 gol > 91%).
    3. **Disaccoppiamento Stocastico Ortogonale (Anti-Varianza a 3 Fattori Indipendenti)**:
       - Incrocio di variabili non correlate: `Over Corner Totali` (balistica pura) + `MultiGol Ampio 1-4` (tenuta gol) + `Over Cartellini Totali` (agonismo arbitrale). Nessuna variabile contamina le altre.
    4. **Dutching Asimmetrico a Paracadute (Twin-Ticket Lock Anti-Ceiling)**:
       - Neutralizzazione definitiva della Ceiling Trap (Regola #48) su attacchi dominanti: ripartizione dello stake con l'80% su `MultiGol 1-3 Squadra` e il 20% su `Over 3.5 Squadra` ad alta quota. Se la favorita segna 1, 2 o 3 gol si va alla cassa; se dilaga con 4+ reti, il paracadute copre l'intero capitale garantendo utile netto.

- **Regola #64 — ARCHITETTURA TWIN-TICKET A CAPITALE PROTETTO & ZERO PERDITA**:
  - 🎯 **Principio Fondamentale (Eliminazione Totale del Rischio Capitale)**:
    Ogni qualvolta l'utente alloca un budget di sessione ($S_{tot}$), BAgent calcola e propone una **Schedina di Backup Paracadute** accoppiata alla Schedina Principale Core, dimensionata affinché il fallimento della principale comporti **ZERO PERDITE** sul capitale totale.
  - 📐 **Vincolo Matematico Zero-Loss**:
    La quota di backup ($Q_2 \ge 4.50$) e lo stake ($S_2$) sono vincolati dall'uguaglianza di copertura integrale:
    $$S_2 \times Q_2 \ge S_{tot} \implies S_2 = \left\lceil \frac{S_{tot}}{Q_2} \right\rceil, \quad S_1 = S_{tot} - S_2$$
  - 🛡️ **Matrice Scenari Garantiti**:
    1. **Scenario A (Vince Principale, Perde Backup)**: Payout $S_1 \times Q_1$ con cospicuo utile netto (+80% / +200% sul budget);
    2. **Scenario B (Perde Principale, Vince Backup)**: Payout $S_2 \times Q_2 \ge S_{tot}$, **capitale recuperato al 100% e perdita azzerata (0,00 €)**;
    3. **Scenario C (Eventi Disgiunti ed Entrambe Vincenti)**: Incasso cumulativo di entrambi i ticket.
  - 💻 **Integrazione Software**:
    Implementato in `services/betting/backup_hedge_engine.py` e richiamabile con `scripts/build_backup_ticket.py --budget <EUR> --main-odd <Q1> --backup-odd <Q2>`.

- **Regola #65 — IN-PLAY REAL-TIME MOMENTUM ENGINE & SNIPING SENTINEL (Allerte Live a Picco Probabilistico)**:
  - 🎯 **Principio Fondamentale (Sniping di Valore in Tempo Reale)**:
    Durante le partite in corso, BAgent monitora minuto per minuto il flusso balistico, il punteggio, le espulsioni e la pressione territoriale per individuare anomalie tattiche e picchi probabilistici ($\ge 75\%-85\%$), segnalando all'utente l'esatto mercato da prendere immediatamente su Netwin.
  - ⚡ **I 5 Trigger In-Play Obbligatori**:
    1. **`LATE_PRESSURE_COOKER` (Minuti 68' – 85')**: Parità o scarto 1 gol con volume $\ge 15$ tiri ➔ `Over Corner Totali Live` o `MultiGol Elastico Live` ($P \ge 83.5\%$);
    2. **`ASYMMETRIC_SIEGE_LIVE` (Minuti 25' – 75')**: Sfavorita in vantaggio o espulsione a favore della big ➔ `Over Corner Favorita Live` o `Doppia Chance Rimonta Live (1X/X2)` ($P \ge 81.5\%$);
    3. **`HALFTIME_TACTICAL_UNLOCK` (Minuti 46' – 55')**: 0-0 all'intervallo con alto xG/tiri ➔ `MultiGol 1-3 2° Tempo` ($P \ge 84.0\%$);
    4. **`FAST_BREAKOUT` (Minuti 15' – 30')**: Gol lampo precoce e transizioni ad alto ritmo ➔ `Over 2.5 Totali Live` ($P \ge 76.5\%$);
    5. **`DISCIPLINE_ESCALATION` (Minuti 55' – 78')**: Tensione agonistica alta con $\ge 4$ cartellini già estratti e scarto minimo ➔ `Over Cartellini Totali Live` ($P \ge 79.0\%$).
  - 📲 **Integrazione Notifiche & Staking**:
    Implementato in `services/live/live_momentum_sniper.py` ed eseguibile con `scripts/monitor_live_sniping.py`. Notifica istantanea via `TelegramSentinel` con percorso categoria Netwin e stake micro-consigliato (max 3% bankroll).

- **Regola #66 — NETWIN ODDS DOWNLOADER & REAL AGGIO SHIELD (Zero Quote Teoriche, Solo Quote Reali Netwin.it)**:
  - 🛑 **Divieto Assoluto di Quote Teoriche o Medie di Mercato**:
    È TASSATIVAMENTE VIETATO validare e proporre schedine basandosi su quote teoriche o stime generiche senza aver prima verificato la quota effettiva offerta da **Netwin.it**. I bookmaker italiani AAMS/ADM applicano un aggio specifico e tagli di quota che possono distruggere completamente l'Edge atteso.
  - 📥 **Architettura di Scarico Live XSport / Netwin**:
    Implementato in `services/betting/netwin_odds_downloader.py` ed eseguibile con `scripts/download_netwin_odds.py`.
    Intercetta direttamente il motore sportivo XSport/Microgame di Netwin (`https://www.netwin.it/xsportapp/xsport_desktop/`), decodificando in tempo reale palinsesto, avvenimenti AAMS, 1X2, Doppie Chance, Under/Over 0.5-5.5 e Gol/NoGol, salvando i dati in `data/netwin_live_odds.json` e aggiornando la cache `data/netwin_odds_cache.json`.
  - 🛡️ **Gate 6.5 Automatizzato (`StrictTicketPipeline`)**:
    La pipeline interroga automaticamente la cache quote Netwin. Se la quota reale Netwin è decurtata rispetto alla quota teorica al punto da far scendere l'Edge sotto al $+4.0\%$, scatta il blocco immediato per `[BLOCCATO - GATE 6.5: NETWIN AGGIO TRAP]`, evitando a monte qualsiasi scommessa a valore atteso negativo.

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
- **Task #30**: Live Monitor (`scripts/live_monitor.py`) — polling API-Football, alert Telegram con pick Poisson live
- **Task #29**: Setup Pi come server autonomo — `bagent-live.service`, cron `db_updater.py` alle 07:00, sync Drive alle 07:30, Tailscale `ssh pi@100.120.216.25`

### In corso 🔄
- **Task #17**: Widget schedina Norway U19

### Pending ⏳
- Integrazione MultiMarketAnalyzer nel pipeline principale BAgent

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

- **Regola #32 (FALLACIA DELL'ASSENZA OFFENSIVA — No 1X2 Contro Big solo per Assenza Punte)**:
  - 🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO puntare sulla sfavorita (1X, 2 o Doppia Chance) solo perché alla squadra big mancano i centravanti titolari.
  - 🔬 **Motivazione Scientifica & Sesto Senso (Lezione Siviglia-Atlético 0-3 del 29/08/2026)**: L'assenza delle punte titolari in una big riduce il volume potenziale dei gol, ma **NON cancella l'abisso tecnico, atletico e strutturale tra le due rose**. Centrocampisti, ali e calci piazzati di una big sono comunque in grado di dominare una squadra fragile. In questi contesti, se proprio si interviene, si usano SOLO mercati alternativi/sanzioni, MAI puntate sull'esito favorevole all'inferiore!

- **Regola #33 (PROTOCOLLO DI SCANSIONE ONNIMERCATO — Adattamento Dinamico al DNA del Match)**:
  - 🎯 **Principio Fondamentale**: Non essere MAI rigidi o limitati a 2-3 tipologie di scommessa. Per OGNI singola partita del palinsesto, BAgent deve scansionare TUTTI i mercati disponibili (1X2, Doppie Chance Combo, Asian Handicap, Multigol Squadra, Multigol Tempi, Tiri in Porta, Tiri Totali, Corner 1X2/Handicap, Cartellini Over, Chance Mix X o GG, Entrambi i Tempi Over 0.5) e selezionare unicamente il **MERCATO A MASSIMA ASIMMETRIA E MINIMA VARIANZA** calzato sul DNA tattico di quello specifico match!
  - 🔬 **Mappatura DNA ➔ Mercato Ottimale**:
    * *Assedio su fascia contro catenaccio* ➔ 1X2 Corner / Tiri in Porta / Multigol Casa 1-3.
    * *Derby / Scontro Salvezza ad alta tensione* ➔ Over Cartellini / Falli.
    * *Scontro aperto ad alto ritmo* ➔ Chance Mix (X o GG) / Over 0.5 Entrambi i Tempi / Over 2.5.
    * *Partita equilibrata e bloccata* ➔ Doppia Chance + Under 3.5 / Multigol 1-3 Totale.
    * *Gara a sviluppo lento con accelerazione nella ripresa* ➔ Multigol 2° Tempo / Tempo con più Gol: 2°T.

- **Regola #34 (BAN TOTALE AL BLASONE & PRIMATO ASSOLUTO DELLA RECENCY DELLA STAGIONE IN CORSO — Name Bias Ban)**:
  - 🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO assegnare superiorità, fiducie tattiche o mercati asimmetrici a una squadra basandosi sul suo blasone storico, nome prestigioso, trofei passati o sui risultati dei campionati degli anni precedenti (es. 2024, 2025).
  - 🔬 **Motivazione Scientifica & Lezione Marseille-Paris FC 2-3 e Espanyol-Sevilla 0-0 del 06/09/2026**:
    * Il nome "Marsiglia" o "Siviglia" appartiene alla storia, ma in campo ci vanno la rosa, l'allenatore e la condizione atletica del campionato ATTUALE.
    * Il Paris FC (neopromossa sulla carta, ma con nuova proprietà e reduce da un roboante 3-0 al Nizza nella stagione in corso) è andato al Vélodrome con baricentro alto, tirando 17 volte e segnando 3 gol. Considerarlo un blocco basso da schiacciare è stato un grave errore di name bias.
    * Il Siviglia, nobile europea, nella stagione in corso produce un attacco sterile (0 tiri nel primo tempo, 0-0 a Barcellona), distruggendo qualsiasi scommessa su Gol/Gol basata sul passato.
  - 📌 **Direttiva Operativa**: L'analisi statistica DEVE pesare al **100% solo le ultime 3-5 partite della STAGIONE IN CORSO** (`recent_season_form`). H2H precedenti a 12 mesi o statistiche di due anni prima hanno valore nullo. Se una neopromossa vola nel campionato attuale, è una squadra di vertice; se una big arranca nelle ultime 3 giornate, è una squadra fragile.

- **Regola #35 (VERIFICA ANAGRAFICA OBBLIGATORIA DELLO STAFF TECNICO DA API — Zero Allucinazioni)**:
  - 🛑 **Divieto Assoluto**: È VIETATO citare allenatori, assetti tattici o dichiarazioni di tecnici basandosi sulla memoria parametrica o su stagioni passate (es. De Zerbi al Marsiglia nel 2026, quando in realtà siede Bruno Genesio).
  - 📌 **Direttiva Operativa**: Prima di redigere l'analisi, BAgent DEVE interrogare l'endpoint `/coachs?team={id}` tramite `collector.current_coach(team_id)` o verificare le formazioni ufficiali su `/fixtures/lineups`. Se il nome del tecnico non è validato da API, non può essere menzionato nel report.

- **Regola #36 (MODULO COMBO VALUE OPTIMIZER — Boost Quote Valore/Raddoppio 1.75 - 2.50+ nei Campionati Maggiori)**:
  - 🛑 **Divieto Assoluto**: Nei campionati importanti (Serie A, Premier League, La Liga, Champions League, Bundesliga), è VIETATO proporre quote 1X2 base schiacciate e passive (1.20 - 1.35) quando esiste una combinazione classica a correlazione positiva.
  - 🔬 **Motivazione Scientifica & Architettura**:
    * Utilizzare il modulo `ClassicComboOptimizer` (`services/analysis/classic_combo_optimizer.py`) e lo script CLI `python scripts/boost_match_combos.py --fixture <ID>`.
    * Scarica i 100+ mercati reali da API-Football (Bet365, Marathonbet, William Hill) e calcola la distribuzione congiunta di Poisson sui dati rolling stagionali/xG.
    * Mappa esclusivamente le **combo pre-compilate classiche** giocabili su Netwin/Domusbet:
      1. `1X2 + Over/Under 1.5, 2.5, 3.5, 4.5` (Bet ID 25)
      2. `1X2 + Gol/No Gol` (Bet ID 24)
      3. `Doppia Chance + Over/Under 1.5, 2.5, 3.5` (Bet ID 38)
      4. `Totale Squadra Over 1.5` (Bet ID 16, 17)
      5. `Gol/No Gol + Over/Under` (Bet ID 49)
    * Target Quota: **`1.75 – 2.50+`** con probabilità congiunta $P \ge 40-45\%$ ed Edge reale $EV \ge 0$.
- **Regola #37 (HARD GATE FORMAZIONI UFFICIALI SUI GIOCATORI — Zero Player Props Senza Starting XI Verificato)**:
  - 🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO proporre qualsiasi scommessa su mercati individuali dei singoli giocatori (Falli Subiti, Falli Commessi, Tiri Totali, Tiri in Porta, Marcatori Anytime, Cartellini Giocatore, Assist) PRIMA che siano state depositate e verificate le **FORMAZIONI UFFICIALI (Starting XI)** e senza aver accertato con certezza assoluta che il giocatore sia **SCHIERATO TITOLARE DAL 1° MINUTO**.
  - 🔬 **Motivazione Scientifica & Lezione Zaccagni/Oyarzabal del 07/09/2026 e Doku del 08/09/2026**:
    * Proporre scommesse su giocatori prima delle distinte ufficiali espone al rischio fatale di turnover, panchina o infortunio dell'ultimo minuto (come Doku oggi nel City, o Zaccagni e Oyarzabal ieri con 0 falli subiti).
    * Se un giocatore non parte titolare o entra al 75', la scommessa è matematicamente bruciata, distruggendo qualsiasi edge probabilistico.
  - 📌 **Direttiva Operativa Rigorosa**:
    1. **Fino a 60-75 minuti prima del calcio d'inizio**: BAgent DEVE proporre **ESCLUSIVAMENTE mercati di SQUADRA** (1X2, Doppie Chance, Under/Over Gol, 1X2 Corner, Corner Totali, 1X2 Falli Squadra, Falli Totali Squadra, Totale Cartellini).
    2. **Solo a formazioni ufficiali pubblicate**: È consentito analizzare e proporre mercati su singoli giocatori, ma SOLO DOPO aver controllato la distinta ufficiale da API (`/fixtures/lineups`) o da referto ufficiale UEFA/Lega, verificando che il giocatore figuri negli 11 partenti.
    3. Se una formazione ufficiale non è ancora disponibile o il giocatore parte dalla panchina, la giocata sul giocatore è **BLOCCATA ALLA FONTE**.

- **Regola #38 (VERIFICA ANAGRAFICA ROSA & TRASFERIMENTI 2026/2027 — Hard Gate Roster Check & Zero Allucinazioni di Mercato)**:
  - 🛑 **Divieto Assoluto**: È TASSATIVAMENTE VIETATO citare qualsiasi giocatore, analizzare duelli individuali 1v1 o proporre qualsiasi giocata su mercati-giocatore (Marcatori, Tiri, Tiri in Porta, Falli Commessi/Subiti, Cartellini, Assist) collegando un atleta a una squadra SENZA aver prima verificato l'effettiva appartenenza alla rosa 2026/2027 nel database SQLite locale (`storage/database/bagent.db` / `data/bagent.db`) tramite `python scripts/verify_squad_control.py --player <NOME> --team <SQUADRA>` o via API (`/players/squads?team={id}`).
  - 🔬 **Motivazione Scientifica & Lezione Mercato Estivo 2026**:
    * Nella sessione estiva 2026 decine di big hanno cambiato maglia (es. Robert Lewandowski trasferitosi ai Chicago Fire e sostituito al Barcellona da Gabriel Jesus e Adeyemi; Denzel Dumfries al Real Madrid; Alexander Isak al Liverpool; Ademola Lookman e Alexander Sørloth all'Atlético Madrid; Nathan Aké al Fenerbahçe; Leandro Paredes ed Enner Valencia al Boca Juniors).
    * Affidarsi alla memoria parametrica o a dataset obsoleti genera allucinazioni distruttive (es. considerare Lewandowski al Barcellona o Cavani al Boca Juniors, bruciando il ticket prima del fischio d'inizio).
  - 📌 **Protocollo Operativo di Controllo (Doppio Hard Gate Giocatori)**:
    1. **Gate 1 — Controllo Rosa & Trasferimento (Regola #38)**: Prima di scrivere il nome di un giocatore associato a un club, verificare che compaia nella rosa attiva 2026 con `python scripts/verify_squad_control.py --player "Cognome" --team "Squadra"`. Se il giocatore non è tesserato con quella squadra o è stato ceduto, la giocata è BLOCCATA ALLA FONTE con status `[BLOCKED - RULE 38]`.
    2. **Gate 2 — Controllo Formazione Ufficiale Titolare (Regola #37)**: Anche se il giocatore appartiene alla rosa, NESSUNA scommessa individuale può essere proposta prima delle distinte ufficiali (60-75 min pre-match) e senza conferma che parta titolare dal 1° minuto (`startXI`).
    3. **Aggiornamento Database Costante**: Mantenere costantemente sincronizzato il database SQLite con `python scripts/update_squads_2026.py --today-ucl` o `--fixtures <ID>` prima di ogni sessione operativa.

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


## Regole aggiunte a settembre 2026

Il diario delle sessioni (ticket, saldi, screenshot) sta in `docs/archive/session_log_2026.md`.
Qui restano solo le regole entrate dopo il blocco iniziale. Due numeri si ripetono: la #66 di questa sezione è il game-state dei corner, distinta dalla #66 Netwin più sopra; la #70 telemetria è distinta dalla #70 mercati pavimento.

- **Regola #66 — PROTOCOLLO ASIMMETRICO GAME-STATE SUI CORNER & PARACADUTE IN SINGOLA DIRETTA**:
  1. **Game-State Bias sui Corner (Gate 0.6)**:
     - Quando una favorita schiacciante (quota pre-match $\le 1.35$) dilaga subito nel 1° tempo (es. Crystal Palace 3-0 Lech Poznan al 45'), la produzione di corner del 2° tempo crolla fisiologicamente (ritmi bassi, cambi conservativi, possesso orizzontale di congelamento). Palace ha battuto 4 corner nel 1°T e solo 2 nella ripresa, chiudendo a 6 e facendo saltare la linea Over 6.5 per 1 solo corner!
     - Al contrario, le linee Over Corner alte ($\ge 6.5$) sono micidiali **quando la favorita è sotto o bloccata** (Celtic sotto 1-2 ha scatenato l'inferno battendo **11 corner**!).
     - *Hard Gate*: Divieto assoluto di linee Over Corner di squadra elevate ($\ge 6.5$) per favorite da possibile goleada rapida (quota $\le 1.35$). Sostituire con linee conservative (Over 4.5/5.5) o mercati aperti sui gol.
  2. **Paracadute Exclusively in Singola Diretta (Gate 8.5)**:
     - Un paracadute di copertura difensiva **NON PUÒ MAI ESSERE UNA MULTIPLA** (es. due corner insieme a quota 5.00): se una sola gamba manca per un soffio, l'intera copertura muore.
     - Il Paracadute DEVE essere giocato come **SINGOLA SECCA** ad alto moltiplicatore (@ 1.85 - 2.40) calibrata per coprire con il payout l'importo esatto del ticket principale.

- **Regola #67 — FATTORE AMBIENTALE AD ALTA TOSSICITÀ NELLE COPPE EUROPEE (Ban Doppie Chance Esterne nei Campi Caldi - Gate 0.3)**:
  - Nelle notti di coppe europee UEFA (Champions, Europa League, Conference), è TASSATIVAMENTE VIETATO scommettere su esiti a favore della squadra in trasferta (`2 fisso`, `X2`, `X2 + MultiGol`) contro club di Turchia (Besiktas, Galatasaray, Fenerbahce, Trabzonspor), Grecia (Olympiakos, Panathinaikos, PAOK, AEK) e Balcani (Stella Rossa, Partizan).
  - *Motivazione*: L'aggressività ambientale, la pressione del tifo e la carica agonistica azzerano il gap teorico di xG/rosa e producono disastri ad alta varianza (Lezione Besiktas 4-1 Marsiglia). Nelle trasferte in questi stadi caldi, giocare solo mercati neutri o Under/Over gol/cartellini.

- **Regola #70 — PROTOCOLLO PAVIMENTO DI SICUREZZA & FLOOR-LEVEL COMPOUNDING (La Strategia del 90%+ di Realizzazione)**:
  1. **Principio Fondamentale (Abbattimento Totale del Rischio Dogmatico)**:
     - Stop all'inseguimento di quote speculative a varianza ingestibile (1.60 - 2.00) che impongono a una specifica favorita di vincere o segnare.
     - L'investimento scientifico si sposta sui **Mercati Pavimento (Floor Markets)**: soglie minime di volume fisiologico che si verificano nel **90.0% – 96.0%** delle partite professionistiche in qualsiasi campionato del mondo.
  2. **I 4 Mercati Pavimento Ammessi (Floor Categories)**:
     - **Corner Floor**: `Over 3.5 / Over 4.5 Corner Totali` (P reale: 92% - 99%). In 90 minuti di qualsiasi campionato, 4-5 deviazioni sul fondo o cross ribattuti arrivano per mera fisica di gioco.
     - **Gol Floor**: `Over 0.5 Totale Partita / MultiGol 1-5 Totale` (P reale: 92% - 96%). Lo 0-0 si verifica solo nel 5-8% dei casi; MultiGol 1-5 assorbe tutti i punteggi reali (1-0, 0-1, 2-0, 1-1, 2-1, 2-2, 3-1).
     - **Tiri Floor**: `Over 15.5 / Over 16.5 Tiri Totali Partita` (P reale: 92% - 98%). Volume combinato che non dipende dall'esito o dalla precisione balistica.
     - **Cartellini Ceiling Floor**: `Under 6.5 / Under 7.5 Cartellini Totali` (P reale: 90% - 95%) in campionati a basso attrito.
  3. **Le Due Strutture di Compounding Matematico**:
     - **La Doppia d'Acciaio**: Combina 2 selezioni floor a quota `1.13 — 1.18` ciascuna.
       - Quota finale combinata: **`@ 1.28 — 1.38`**
       - Probabilità reale congiunta: **`86.0% — 91.0%`**
       - Resa netta sul capitale: **`+28.0% — +38.0% netto`** per singolo ciclo!
     - **La Tripla Blindata**: Combina 3 selezioni floor.
       - Quota finale combinata: **`@ 1.45 — 1.60`**
       - Probabilità reale congiunta: **`80.0% — 85.0%`**
       - Resa netta sul capitale: **`+45.0% — +60.0% netto`**!
  4. **I 3 Divieti Assoluti (Hard Floor Gates)**:
     - 🚫 **Divieto 1X2 / Vincente Secca**: Anche a quota 1.10, vietato scommettere sulla vittoria secca (Lezione Udinese 0-1, Nottingham 0-1).
     - 🚫 **Divieto Mercati Monosquadra**: La giocata non deve mai dipendere dal fatto che una specifica squadra riesca a segnare.
     - 🚫 **Divieto Scadenza Intermedia 45'**: Consentiti solo mercati con 90 minuti pieni di vita.
  5. **Filtro Anti-Chasing & Hard Stop-Loss Giornaliero (Gate 8.8)**:
     - Se un ticket pomeridiano fallisce, la sessione di quel turno è **IMMEDIATAMENTE CONGELATA**. È tassativamente vietato piazzare ticket di "recupero" serali emotivi a quote compresse. Il capitale si protegge fermandosi e ripartendo a mente lucida.

- **Regola #71 — PROFILAZIONE TATTICA DNA CAMPIONATO & SQUADRE (League & Team Tactical DNA Matching)**:
  - 🛑 **Divieto Assoluto di Mercati Generici Ciechi**:
    È TASSATIVAMENTE VIETATO proporre lo stesso mercato floor o standard per qualsiasi campionato o squadra senza averne prima controllato l'incompatibilità con il DNA statistico e tattico.
  - 🔬 **I 4 Grandi Cluster Tattici Codificati (`services/analysis/league_dna_market_matcher.py`)**:
    1. **Cluster 1: DEFENSIVE_ATTRITION (Argentina, Brasileirão, Serie B, Colombia, Uruguay)**:
       - *DNA*: Ritmi spezzettati da falli continui, baricentri bassi, xG medio $\le 2.15$, 0-0 frequente nel 18.2% dei casi, media corner ridotta a ~8.5.
       - *Semaforo Verde (Consigliati P $\ge$ 88%-96%)*:
         - **`Under 3.0 Asiatico (o Under 3.25)`**: Incassa con 0, 1, 2 gol; con esattamente 3 gol scatta il RIMBORSO TOTALE 100% (Push @ 1.00). $P(\text{No Loss}) = 88.31\%$.
         - `Under 3.5 Gol Totali` / `GG in Entrambi i Tempi: NO` ($P = 98.2\%$).
         - `Draw No Bet (DNB / AH 0.0)` su favorita per neutralizzare l'alta frequenza di pareggi.
         - `Over 4.5 / 5.5 Cartellini Totali`.
       - *Semaforo Rosso (VIETATI TASSATIVAMENTE)*:
         - ❌ **`Over 0.5 Gol Totali`**: TRAPPOLA MORTALE DELLO 0-0! Giocare Over 0.5 a quota 1.06-1.10 in Argentina distrugge il bankroll (Edge -15%).
         - ❌ `Over Corner Totali > 7.5`: I falli a centrocampo spezzano le manovre offensive prima della linea di fondo.
         - ❌ `Over 2.5 Gol`.
    2. **Cluster 2: OPEN_BALLISTIC_TRANSITION (MLS USA, Bundesliga, Eredivisie, Scandinavia, Austria)**:
       - *DNA*: Campi larghi, difese alte e allegre, transizioni rapide coast-to-coast, xG medio $\ge 3.18$, frequenza 0-0 inferiore al 6%, produzione balistica e corner elevatissima (media 10.8 corner/partita).
       - *Semaforo Verde (Consigliati P $\ge$ 88%-96%)*:
         - **`Over 6.5 / Over 7.5 Corner Totali Incontro`**: Il mercato d'elezione per la MLS ($P \ge 91\%$).
         - **`Chance Mix: X2 o Over 1.5`** (o `1X o Over 1.5`): $P \ge 94\%-96\%$.
         - **`Draw No Bet (DNB / AH 0.0)`** su favorita in trasferta: Rimborsa il pareggio ad alto punteggio (2-2) a quote remunerative (@ 1.55 - 1.68).
         - `Over 1.5 Gol Totali Partita` ($P \ge 84.5\%$).
       - *Semaforo Rosso (VIETATI TASSATIVAMENTE)*:
         - ❌ `Under Stretti (Under 2.5 / 3.0)`: Altissimo rischio di 2-2, 3-1.
         - ❌ `1X2 Secco in Trasferta a quota compressa`: Viaggi lunghi e fattore campo rendono i pareggi frequenti.
         - ❌ `No Gol (BTTS No)`.
    3. **Cluster 3: ASYMMETRIC_DOMINANCE (City, Barca, Real, Sporting CP, Bayern, PSG vs Blocco Basso)**:
       - *DNA*: Possesso palla $> 65\%$, 18-22 tiri verso lo specchio, avversario rintanato nella propria area.
       - *Semaforo Verde*:
         - **`Corner Squadra Favorita Over 3.5 / 4.5`** ($P \ge 93\%$).
         - **`Chance Mix: 1X o Over 1.5`** ($P \ge 97\%$).
         - **`Parate Portiere Sfavorita Over 2.5 / 3.5`** (7-10 tiri nello specchio subiti).
         - **`Over Fuorigioco Sfavorita`** (contro la linea alta di Flick al Barça o Aston Villa).
       - *Semaforo Rosso*:
         - ❌ `1 Fisso a Quota Compressa (< 1.65)` (Gate 0).
         - ❌ `MultiGol 1-3 Squadra` (Gate 0.75 Anti-Ceiling: rischio goleada 4-0, 5-0).
    4. **Cluster 4: PRAGMATIC_MANAGEMENT / CORTO MUSO (Napoli con Allegri, Atletico Madrid con Simeone, Huracán, Corinthians)**:
       - *DNA*: Gestione del minimo scarto, baricentro basso dopo il vantaggio, clean sheet prioritario (frequenza 1-0/0-1 $> 25\%$).
       - *Semaforo Verde*: `1X + MultiGol 1-5`, `Under 3.5`, `Draw No Bet (DNB)`, `MultiGol 1-3 Squadra`.
       - *Semaforo Rosso*: ❌ Combo rigide con Over 1.5 (`1X + Over 1.5`, `1 + Over 1.5`).
  - 📌 **Integrazione Obbligatoria (Gate 0.90 di `StrictTicketPipeline`)**:
    Ogni selezione pre-schedina DEVE essere verificata con `LeagueDNAMarketMatcher.check_market_suitability()` (`scripts/audit_match_dna.py`). Se il mercato proposto appartiene al Semaforo Rosso per il DNA di quella specifica sfida, il ticket viene **BOCCIATO AUTOMATICAMENTE**.

### 🚫 REGOLA #69 — PROTOCOLLO BLOCCO TASSATIVO PER MANCANZA DATI CERTIFICATI & DIVIETO RICOSTRUZIONI FRAMMENTATE
1. **Hard-Gate Dati Ufficiali**: Se una competizione o una partita non è presente nei feed ufficiali e certificati di BAgent (es. FootyStats API, Sofascore/Flashscore verificati con coperture complete di classifiche, rose e orari), **DEVE ESSERE BLOCCATA AUTOMATICAMENTE DAL VALIDATORE (HARD REJECT)**.
2. **Ban Leghe Non Coperte (es. Liga Alef, 3ª divisione israeliana o leghe amatoriali/minori)**: È tassativamente vietato proporre scommesse su campionati minori o amatoriali privi di telemetria ufficiale.
3. **Divieto Assoluto di Fabbricazione / Fonti Frammentate**: È severamente vietato all'agente tentare di dedurre o ricostruire classifiche, punti, forma o rose da snippet di motori di ricerca o fonti non omogenee. In assenza di dati certificati, la risposta obbligatoria deve essere: *"Dati non certificati nel feed ufficiale: partita scartata dal validatore"*.
4. **Verifica Orario Kickoff Obbligatoria**: Prima di proporre qualsiasi selezione, verificare che il kickoff sia strettamente nel futuro rispetto all'ora corrente (`kickoff_is_future == True`). Qualsiasi match già avviato o in corso deve essere respinto a monte.

---

### 📡 REGOLA #70 — PROTOCOLLO TELEMETRIA LIVE BASATA SU FLASHSCORE / DIRETTA (Zero Stime & Zero Timer Locali)
1. **Divieto di Timer di Sistema per i Minuti di Gioco**: È severamente vietato stimare il minuto di gara calcolando la differenza tra l'orologio locale e il kickoff (`now - kickoff`).
2. **Obbligo Motore Delta Feed Ufficiale**: Qualsiasi monitoraggio live o file HTML desktop DEVE attingere esclusivamente dal feed raw di Flashscore/Diretta.it (`local-it.flashscore.ninja/2/x/feed/f_1_0_1_it_1`) tramite `FlashscoreLiveEngine` (`services/football/external/sources/flashscore_live.py`).
3. **CORS-Proof Desktop Architecture**: L'HTML locale (`live_ticket_tracker.html`) deve sempre essere pre-renderizzato in modo statico da Python con direttiva nativa `<meta http-equiv="refresh" content="15">` per garantire l'aggiornamento automatico su protocollo `file:///` senza blocchi di sicurezza cross-origin.
4. **Trasparenza Immediata delle Fonti**: In qualsiasi momento l'agente deve saper dichiarare l'origine esatta di ogni singolo dato esposto all'utente.

