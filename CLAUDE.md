# BAgent

Calcio quantitativo. Tennis abolito dal 22 settembre 2026: niente nuove proposte, scansioni o schedine sul tennis. Lo storico dei ticket già giocati resta archivio, non una raccomandazione.

Poisson / Dixon-Coles sui gol, Negative Binomial sui corner. `Edge = (prob × quota) - 1` è solo informativo. Le probabilità vengono dai dati, non dalle quote. L'utente parla in chat: gli script li lancia l'assistente. Dire "selezioni" o "partite", mai "gambe".

Il testo integrale, con le lezioni e lo stato dei task di agosto 2026, è in `docs/archive/claude_full_20260928.md`. Il diario delle sessioni è in `docs/archive/session_log_2026.md`. Qui restano solo i vincoli.

## Operatività

- Sesto Senso ogni giorno, prima dei numeri: Gazzetta, BBC, Marca, Kicker, L'Équipe, MondoPengwin. `scripts/fetch_sports_news.py --home --away --league`.
- FootyStats prima di ogni probabilità: avg gol, Over 2.5%, BTTS%, xG, forma. Stagione in corso, salvo richiesta esplicita dello storico.
- Niente classifica, allenatore, rosa, H2H o forma inventati. Se il feed certificato non c'è, la partita si scarta: "Dati non certificati nel feed ufficiale: partita scartata dal validatore".
- Niente approvazione a parole prima di `scripts/strict_validator.py`. Il verdetto in chat porta lo stato dello script.
- Quota minima 1.20. Verdetto: stella se edge ≥ 5%, occhio se positivo sotto il 5%, croce se negativo. L'edge negativo o sotto +4% genera un avviso di warning informativo e NON boccia la giocata.
- Max 3-4 selezioni per ticket. Max 8% del bankroll a schedina, 5-8% Kelly sul singolo ticket, 15% a sessione. Se un ticket pomeridiano perde, stop: niente recupero serale.
- Partite già iniziate fuori. Kickoff nel futuro. Il minuto live viene da Flashscore (`FlashscoreLiveEngine`), mai da `now - kickoff`.
- Quote di tabella da API-Football e The Odds API. Il numero da giocare si verifica su Netwin: se l'aggio porta l'edge sotto +4%, Gate 6.5 genera un avviso di warning informativo (NETWIN AGGIO TRAP non bloccante). Contare le soglie Over/Under prima di etichettarle (5 o 6 linee). Su Sofascore `"3 | 3 | 0"` non è 3-3.
- Path relativi: `ROOT = Path(__file__).resolve().parent.parent`, database `data/bagent.db`. Prima dell'uso, `PRAGMA wal_checkpoint`. `.env` mai in chat né su git. Codice su GitHub privato `a502502502/BAgent`. Dati su Google Drive. Pi: `pi@bagent.local` / `pi@192.168.1.70`, Tailscale `pi@100.120.216.25`.

## Perimetro

Solo prime divisioni con TV/VAR (Top 5, Portogallo, Olanda, Scozia, Belgio, Danimarca, Norvegia, Svezia, Grecia, Turchia, Svizzera, Brasileirão, Liga Profesional) e coppe UEFA o fasi finali di coppe nazionali tra squadre di prima divisione. Fuori: seconde divisioni, dilettanti, squadre B e giovanili, leghe arabe opache, leghe senza telemetria. Nations League e coppe UEFA maggiori restano calcio, non club di seconda fascia.

Prima giornata di un campionato: niente 1X2, Over o combo sul risultato. Si entra dalla 2ª o 3ª.

## Mercati

- Scansionare tutti i mercati (`scripts/scan_omni_markets.py`). Si gioca il migliore per probabilità, quota e respiro a 90 minuti. Nessun mercato è escluso per abitudine.
- Sweet spot: probabilità reale 72-88%, quota 1.28-1.65 (fino a 1.85 sulle combo a doppia chance), edge ≥ +5%. Sotto 1.22 è una trappola. Mercati 1° Tempo (MultiGol 0-1 1°T, Under 1.5 1°T, 1X 1°T) ammessi e prezzati con precisione via Poisson (xG × 0.45).
- 1 o 2 secco sotto 1.65 è vietato. Sostituire con 1X, 1X + Over 1.5, DNB o MultiGol 1-3 squadra. Niente 2 fisso in trasferta di coppa.
- Δ punti ≤ 3: niente Over 2.5 forzato. Over 1.5 o doppia chance.
- "Prima contro ultima" non è una base sicura. Niente `1 + Over 1.5` o `1 + Under 3.5` sotto 1.65. Usare `1X + MultiGol 1-4` o `MultiGol 1-3 Casa`, e controllare gli H2H della stagione.
- Attacco dominante contro difesa fragile (Barça, Bayern, City, Real): vietati MultiGol 1-2, 1-3 e Under 2.5. Usare mercati aperti: `1/2 + Over 1.5`, Over 1.5 squadra, MultiGol 2-5.
- Corto muso (Allegri al Napoli, Simeone): vietati `1X + Over 1.5`, `1 + Over 1.5`, Over 1.5 squadra. Usare `1X + MultiGol 1-5`, `1X + Under 3.5`, DNB se la quota del 1 è ≥ 1.65, o MultiGol 1-3 squadra.
- Mercati preferiti quando il campione li regge: MultiGol 1-5, `1X/X2 + MultiGol 1-4/1-5`, MultiGol 1-3 squadra, MultiGol tempi (`0-2` o `1-3` nel primo tempo e `1-3` o `1-4` nel secondo), Chance Mix (`1X o Over 1.5` perde solo sullo 0-1; `X2 o Over 1.5` perde solo sull'1-0). Over 0.5 primo tempo sotto 1.40 è vietato.
- Corner solo con ≥ 18-20 tiri totali e ≥ 6-7 tiri in porta della favorita, e un avversario che ne concede 15-18 da blocco basso. Favorita a quota ≤ 1.35: niente Over corner di squadra ≥ 6.5. Se è sotto o bloccata, le linee alte hanno senso; se ha già dilagato, no.
- Cartellini Over solo in Grecia, Turchia, Balcani, Sudamerica, derby e partite tese. Vietati in Norvegia e nelle partite nordiche o austriache pulite.
- Nelle coppe UEFA, niente 2, X2 o `X2 + MultiGol` in trasferta in Turchia, Grecia o nei Balcani. Solo mercati neutri, gol o cartellini.
- Giocatori: prima `verify_squad_control.py` sulla rosa 2026/27, poi la distinta ufficiale. Senza titolare confermato, solo mercati di squadra. Prima dei 60-75 minuti dal calcio d'inizio, niente props individuali e niente titolarità data per certa.
- Niente allenatore, modulo o giocatore citato a memoria. Il tecnico viene da `/coachs` o dalle formazioni. L'assenza di una punta non autorizza a giocare contro la big.
- Calendario UEFA solo da API della stagione corrente. Non ricostruire i turni a memoria.
- Paracadute: singola secca a 1.85-2.40 che copre lo stake del ticket principale, mai una multipla. Backup a quota ≥ 4.50 con `S2 = ceil(S_tot / Q2)` e `S1 = S_tot - S2`, via `scripts/build_backup_ticket.py`.
- Combo nei campionati maggiori: se esiste una combo a 1.75-2.50 con edge ≥ 0, non proporre il 1X2 a 1.20-1.35. Motore: `scripts/boost_match_combos.py`.

## DNA campionato

Verificare con `scripts/audit_match_dna.py`. Il semaforo rosso boccia.

- Argentina, Brasile, Colombia, Uruguay: Under 3.0 asiatico o Under 3.5, DNB, Over 4.5/5.5 cartellini. Vietati Over 0.5, Over corner > 7.5, Over 2.5.
- MLS, Bundesliga, Eredivisie, Scandinavia, Austria: Over 6.5/7.5 corner, Chance Mix, DNB in trasferta, Over 1.5. Vietati gli Under stretti, il 2 secco compresso e il No Gol.
- Dominante contro blocco basso: corner squadra Over 3.5/4.5, `1X o Over 1.5`. Vietati il 1 sotto 1.65 e il MultiGol 1-3 squadra.
- Corto muso: come il filtro Allegri/Simeone sopra.
- Brasile: `1X + MultiGol 1-5` o `1X + Under 3.5`. Niente 2 esterno compresso.
- Olanda: mercati aperti, niente Under 2.5.
- Norvegia: Over 2.5, Gol, corner. Niente Over cartellini.

## Live

Minuto e punteggio solo dal feed Flashscore. Trigger: assedio se la sfavorita (favorita pre-match ≤ 1.60) passa avanti tra il 12' e il 78' (corner, cartellini, tiri della favorita, 1X/X2 live); pressione 68'-85'; 0-0 all'intervallo con tanto volume; gol precoce 15'-30'; quattro cartellini già usciti tra il 55' e il 78'. Notifica Telegram. Stake live max 3% del bankroll.

## Pipeline

`scripts/build_verified_ticket.py`, in ordine: rosa, infortuni, distinta, probabilità composta, calcolo edge (warning se < +4%), Kelly. Poi il validatore (`scripts/strict_validator.py`).
- **Regola #75 (Audit Obbligatorio Cloud AI Pre-Emissione)**: Ogni volta che viene generata o validata una schedina, deve essere eseguito l'audit online indipendente via Groq Cloud (`services/debate/groq_auditor.py` con modello 120B a 0€). L'esito dell'audit (EV, scenari di perdita e verdetto) viene allegato al ticket per smascherare trappole bookmaker prima della proposta finale. Senza validatore e audit non si propone la schedina come giocabile. Una lettura di solo Sesto Senso, chiesta espressamente, si dichiara come tale e non è un certificato.
- **Regola #76 (Data e Ora Obbligatorie per Ogni Partita / Selezione)**: In ogni schedina, ticket JSON, report terminale, alert Telegram o pagina web, la **data e l'ora di inizio** della partita (`kickoff_time`) devono essere SEMPRE presenti ed esplicitate (es. `2026-10-09 00:30 CEST` o `04/10/2026 ore 19:30`). È severamente vietato proporre partite o selezioni prive di data e orario o con indicazioni generiche. Il validatore (`StrictTicketPipeline` Gate 0.05 e `scripts/strict_validator.py`) deve bloccare le selezioni prive di data e ora complete.
- **Regola #77 (Ciclo Dialettico Obbligatorio Pre-Costruzione Schedina - Debate & Re-Audit Loop)**: Questa regola deve essere tassativamente eseguita prima di costruire qualsiasi schedina. L'Auditor (Groq 120B) fa l'avvocato del diavolo e trova la trappola (*"Perché questa leg rischia di saltare?"*). Il Modellista Quantitativo (Antigravity) accoglie l'obiezione, torna sul palinsesto Netwin e ristruttura le giocate con mercati protetti (MultiGol 1° Tempo, Chance Mix, Under 3.5) o eliminando le quote compresse e i derby ingannevoli. Re-Audit: la schedina rettificata viene risottomessa a Groq finché non si raggiunge il consenso unanime (🟢 APPROVATA con valore atteso positivo). Nessuna schedina può essere proposta o pubblicata senza aver completato questo ciclo di convergenza dialettica.

