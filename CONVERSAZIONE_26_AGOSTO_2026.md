# 📋 CONVERSAZIONE COMPLETA — 26 AGOSTO 2026

> Sessione di continuazione da ieri (25 agosto). Partita con la liquidazione dei ticket notturni, proseguita con una giornata di analisi molto approfondita sulle partite di Champions League di stasera, e chiusa con un esperimento deliberato "fuori regole" su richiesta dell'utente.

---

## 🔧 1. Correzione del Ticket #30

L'utente ha mostrato uno screenshot reale del ticket Betsson piazzato la notte scorsa: **4 selezioni, non 3** come registrato — mancava la prima gamba (CS 2 de Mayo - Club Guarani, DC 1X @1.44, **vinta** 0-0). Corretto il Registro Cassa: quota reale 4.94× (non 3.43×), esito 2/4 (non 1/3), netto invariato a -20€ perché serviva comunque 4/4.

---

## 📜 2. Regola #29 — Ban Under 2.5 sulle leghe minori

L'utente ha notato un pattern ("ci perdiamo sempre con le under 2.5 nelle partite di campionati minori") — confermato: Juventude-CRB e Atlético Goianiense-Botafogo SP sono saltate **due volte**, in due ticket diversi (#29 e #30), nonostante analisi solida su entrambe (miglior difesa del torneo per Juventude, distacco in classifica ≤3 per Goianiense-Botafogo). Nuova regola: nelle leghe minori usare sempre Under 3.5 o un mercato alternativo, mai Under 2.5 secco.

---

## 🔍 3. Retrospettiva sul Ticket #30 — xG delle due gare perse

Su richiesta dell'utente, controllati gli xG reali delle due gare perse: Juventude-CRB ha avuto un xG totale di partita di **4.0** (molto sopra la soglia 2.5, spiegando il 2-1 finale nonostante la miglior difesa del torneo); Goianiense-Botafogo ha visto Goianiense **sovraperformare pesantemente il proprio xG** (1.93 atteso, 3 gol reali) — giornata di cinismo sotto porta, non un errore di analisi.

---

## 🗺️ 4. Inventario Fonti Dati — su richiesta esplicita

L'utente ha chiesto un elenco completo delle fonti usate: API-Football (fixture, statistiche, formazioni, infortuni, quote, live odds, eventi — la fonte principale), Flashscore/LiveScore.in (formazioni anticipate), Netwin/Domusbet/Betsson (solo per il piazzamento reale, non più per la ricerca quote). Testate anche fonti mai usate prima:
- **ClubElo**: risultato **non funzionante** — timeout su ogni endpoint dati, root path risponde ma i dati no. Testato anche via browser (300s di timeout) per escludere un problema specifico di rete. Causa non determinabile con certezza (server giù vs blocco rete).
- **The Odds API**: **funziona benissimo**, gratis, chiave già in `.env`. Copre Brazil Serie B e Argentina Primera División. Scoperta la Regola #30 da questo test.
- **TheStatsAPI.com**: legittima ma a pagamento (50$/mese minimo), nessun piano gratuito — scartata, troppa sovrapposizione con API-Football già pagato.
- **Sportmonks**: l'utente ha fatto una prova gratuita — confermato **piano gratuito reale** (solo Danese e Scozzese, 2 leghe), pubblicizzava "expected lineups" ma la documentazione tecnica non conferma questa funzione in modo distinto dalle formazioni normali — non risolve il problema di Flashscore.
- **sources/news.py** (Google News RSS): **funziona**, mai usato in produzione prima di oggi.

---

## 🎯 5. Analisi Approfondita delle Partite di Oggi

L'utente ha chiesto tabelle "molto approfondite" per le partite di Champions League (uomini) e La Liga di stasera. Costruita una prima **Tabella 1** (5 poi 6 selezioni) con forma recente, infortuni, xG, precedenti storici per ogni partita.

**Scoperta principale — Fenerbahçe**: la lista iniziale di API-Football indicava 13 assenti per il Fenerbahçe contro il Lyon. Verificato su **Transfermarkt** (lista tecnica infortuni con date di rientro) e su un **articolo di InfoBetting** incollato dall'utente (formazioni probabili, quote reali, cronaca): solo **4 assenze reali confermate** (Söyüncü, Günok, Aktürkoğlu, Asensio). Controllando i minuti giocati recenti, emerso che Asensio era l'unica assenza fresca (giocava regolarmente, rating 8.0 il 22/08, poi infortunio), gli altri 3 mancavano già da settimane.

**xG dell'andata Lyon-Fenerbahçe**: l'utente ha incollato la pagina statistiche di Flashscore — xG 0.73 (Lyon) contro 0.43 (Fenerbahçe) nonostante il pareggio 1-1, rafforzando ulteriormente la pick su Lyon.

**Falli Totali — pattern notato dall'utente**: tutte e 4 le gare d'andata delle coppe avevano più di 20 falli totali. Verificato contro le quote reali di mercato (linea 25.5-26.5, non 20): solo Lyon-Fenerbahçe (26 falli) era sopra soglia, Viking-Dinamo (22 falli) nettamente sotto — nessun vantaggio automatico su tutte e 4, costruita comunque una Tabella 2 esplorativa con pick differenziate per gara.

**Cartellini**: controllati per tutte e 4 le gare — nessun segnale forte, Lyon e Fenerbahçe risultate tra le squadre più "pulite" del lotto (circa 1 cartellino a partita ciascuna nelle ultime uscite).

---

## 📰 6. Sblocco del Muro Cookie di Google News

L'utente ha chiesto di leggere il contenuto completo di alcuni articoli di rassegna stampa. I link RSS di Google News rimbalzavano su una pagina di consenso cookie che WebFetch non riusciva a superare (loop di redirect). Provate altre strade (UEFA.com diretto: 503; Google Search: stesso muro; DuckDuckGo: CAPTCHA) — tutte fallite, nessuna aggirata (policy: mai bypassare CAPTCHA/protezioni anti-bot).

Su richiesta esplicita dell'utente ("sblocca il muro dei cookie"), chiarito che non si aggirano protezioni ma si può usare il **browser vero**, cliccando "Rifiuta" sui cookie non essenziali come farebbe un utente normale — azione legittima, non un aggiramento. Funzionato: letto l'articolo completo di **Hearts Standard** su Rapid Vienna-Hearts (McCart terzino d'emergenza, Mendy nuovo mediano titolare, McPake uscito zoppicando nell'andata) e due preview di **Sofascore**:
- **Celje-Slovan**: Slovan imbattuto da 11 partite, Celje 4 senza sconfitta
- **Viking-Dinamo Zagabria**: **Dinamo 28 partite senza sconfitta, 5 vittorie di fila, Over 2.5 in 4/5 delle ultime uscite, Over 10.5 Corner in 4/5** — la scoperta più forte della giornata, ha portato all'aggiunta di una pick sui corner (Over 9.5 Corner Totali @1.62) alla Tabella 1
- **AEK-Levski**: confermato quanto già trovato (Levski più pericoloso dell'AEK nell'andata nonostante lo 0-0)

---

## 🔬 7. Audit Completo delle Fonti Dati per Ogni Partita

Su richiesta esplicita ("analizza tutto quello che trovi... indicami i casi dove non trovi informazioni"), fatto un audit sistematico di tutte le 8 (poi 14) partite del giorno nelle leghe ammesse: forma recente, infortuni, xG, classifica, rassegna stampa, H2H andata — con tabella dei buchi reali. Scoperta laterale: **Rapid Vienna-Hearts** aveva dati quote completi mai sfruttati prima; corretti anche due errori di verifica precedenti (Wolfsburg-Inter e PSV-Køge avevano in realtà l'Over/Under disponibile, non solo l'1X2 come detto ieri).

---

## 🚫 8. L'Esperimento "Fuori Regole"

L'utente ha incollato un dump enorme della pagina scommesse di Netwin (palinsesto completo del giorno, decine di campionati) e chiesto di costruire una tabella da zero. Segnalato il conflitto con l'istruzione esplicita di ieri di non cercare più quote su Netwin/Domusbet/Betsson — l'utente ha confermato di volerlo fare comunque.

Tentato prima **Betsson**: bloccato da **Cloudflare** (403, stesso destino di Sofascore, non aggirabile). Proceduto quindi con i dati Netwin incollati dall'utente. Costruita una tabella deliberatamente **fuori dalle regole del progetto** (Regole #5 su leghe minori/opache, #9 su giovanili/riserve), segnalando chiaramente ogni violazione. Su richiesta di verificare il Sesto Senso anche per queste partite, la ricerca di rassegna stampa ha dato **zero risultati editoriali reali** su tutte le 4 partite testate (solo pagine automatiche di statistiche/quote) — conferma diretta e concreta del motivo per cui quelle leghe sono bandite: non è prudenza teorica, è che semplicemente non esiste nessuna informazione verificabile oltre al numero della quota.

---

## 📄 9. Report Finale

Costruito `reports/schedina_26ago.html` con tutte e 4 le tabelle (stile dark coerente con le schedine precedenti del progetto), inclusi orari (richiesta permanente salvata in memoria: includere sempre l'orario in ogni tabella futura), dati d'andata, colonna Sesto Senso per ogni selezione, e avvisi onesti sui limiti di ciascuna tabella.

---

*Sessione salvata su richiesta esplicita dell'utente ("salva tutto anche la conversazione così riprendo da un altro computer") — vedi anche `docs/session_handover_2026_08_26.md` per lo stato tecnico e le istruzioni di ripresa.*
