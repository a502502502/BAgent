# 🚀 BAgent — Session Handover & Complete Checkpoint

**Data Checkpoint**: Martedì 25 Agosto 2026 — Ore ~17:40 (CEST)
**Stato**: Salvato e sincronizzato su GitHub (`origin/main`), ma con **un monitoraggio live attivo solo in questa sessione** — leggi la sezione 5 prima di tutto.

---

## ⚠️ 1. Cosa NON si trasferisce automaticamente aprendo una nuova sessione

Questa sessione ha un **auto-risveglio programmato ogni 10 minuti** (`ScheduleWakeup`) che controlla lo stato live del Ticket #29 e manda aggiornamenti su Telegram. **Questo meccanismo è legato a QUESTA sessione specifica** — se apri una nuova sessione Claude Code su un altro computer, quella nuova sessione NON eredita il monitoraggio automatico.

**Se il Ticket #29 (7 selezioni, kickoff scaglionati 16:00-22:30 UTC) non è ancora concluso quando riprendi**, hai due opzioni:
1. Chiedi alla nuova sessione di rifare `ScheduleWakeup` con lo stesso prompt (vedi `scripts/ticket_watcher.py` + `data/ticket_watch.json`)
2. Attiva il cron sul Raspberry Pi (comandi già pronti più sotto, sezione 6) — più affidabile perché non dipende da nessuna sessione attiva

---

## 📌 2. Riepilogo Esecutivo della Sessione di Oggi (25 Agosto)

Sessione lunghissima, partita da una retrospettiva e finita con due ticket costruiti/piazzati con un flusso di analisi molto più rigoroso e veloce di prima. Ordine cronologico:

1. **Retrospettiva Ticket #22/23/25/26/27** (24-25 agosto) — liquidati via API-Football invece che a mano su Sofascore, molto più veloce. Bilancio: -75€ confermati + Ticket #27 perso (stake non tracciato).
2. **Fix di un conflitto Git irrisolto** in `CLAUDE.md` (marker `<<<<<<< HEAD`/`=======` mai chiusi, ~350 righe duplicate da giorni) — risolto unendo il contenuto unico di entrambi i lati.
3. **Regola #26** recuperata dal lato "perdente" del conflitto (Protocollo di Rigore Matematico).
4. **Scoperta**: API-Football (piano Pro, 7.500 richieste/giorno) copre molto più di quanto pensassimo — xG per squadra, 185 mercati odds da 14 bookmaker incluso "Player Fouls Committed" per singolo giocatore. Aggiunta `player_prop_odds()` e `list_available_markets()` a `collector.py`.
5. **Regola #27**: controllo forma recente via API-Football OBBLIGATORIO prima di ogni tabella, anche senza rassegna stampa — nata da un errore reale (tabella K-League costruita su "reputazione" invece che dati, corretta dopo aver scoperto che Bucheon era la squadra più in forma del lotto).
6. **Ticket #28 — Tripla K League 1** (40€ → pot. 151.20€): costruita con Regola #27 (forma reale + classifica). **Andata in cashout live all'82'** per 10€ (Netto: -30€) — Leg 2 (Under 2.5 Jeju-Pohang) era al limite esatto, Leg 3 (Over Seoul-Bucheon) a rischio con poco tempo residuo.
7. **Sofascore confermato bloccato (403, IP-level)** da questo ambiente — non risolvibile con cookie/header, provato e scartato.
8. **Scoperta LiveScore.in/Flashscore funziona** (`local-global.flashscore.ninja`, non bloccata) — pubblica le formazioni PRIMA di API-Football. Creato `services/football/external/sources/flashscore.py` (lineups/stats/incidents) e aggiornato `scripts/lineup_watcher.py` per usarla come fonte primaria.
9. **Regola #28**: quando la selezione realmente piazzata differisce da quella raccomandata, analizzarla SEMPRE con lo stesso rigore — nata da un caso reale (leg Sabah-Hapoel piazzata come Cartellini invece di Gol).
10. **Ticket #29 — Multipla Serale 7 Eventi** (10€ → pot. 120.56€ con bonus): costruito con xG, classifica, H2H, assenze chiave (Lo Celso/Ezzalzouli out per il Betis). Piazzato su Netwin, **attualmente IN CORSO**.
11. **`scripts/ticket_watcher.py`** creato per monitorare live le gambe di un ticket e avvisare su Telegram solo sui cambiamenti reali.

---

## 🎫 3. Ticket #29 — Stato Live (verificare all'apertura di questa sessione)

| # | Partita | Orario UTC | Pick | Quota |
|---|---|---|---|---|
| 1 | SK Brann - FK Austria Wien | 16:00 | Over 2.5 Gol | @1.37 |
| 2 | Sabah Masazir - Hapoel Beer Sheva | 16:45 | Over 1.5 Cartellini Squadra 1 (Sabah) | @1.39 |
| 3 | Valencia - Real Betis | 19:00 | Under 2.5 Gol | @1.66 |
| 4 | LASK Linz - Celtic | 19:00 | Over 1.5 Gol | @1.14 |
| 5 | Bodo Glimt - Nijmegen | 19:00 | Over 8.5 Corner Totali | @1.37 |
| 6 | Juventude RS - CRB | 26/08 00:30 | Under 2.5 Gol | @1.48 |
| 7 | Goianiense GO - Botafogo SP | 26/08 00:30 | Under 2.5 Gol | @1.50 |

Stake 10€, quota totale con bonus 10.96×, potenziale 120.56€.

**Nota critica sulla gamba 2 (Sabah cartellini)**: è la più debole del ticket. Dati leg d'andata (Hapoel 2-1 Sabah): Hapoel (67% possesso) ha fatto 12 falli/3 gialli contro i 6 falli/0 gialli di Sabah — l'ipotesi "Sabah dovrà fare falli per fermare il gioco" NON regge sui dati reali (conferma Regola #18: chi ha il possesso fa più falli).

**Fixture ID per controllo rapido**: 1623459, 1622626, 1570342, 1610924, 1622627, 1520835, 1520831 (usa `FootballExternalCollector.fixture(id)` per lo stato live).

---

## 🛠️ 4. Nuovi Strumenti Creati Oggi

### `scripts/lineup_watcher.py` (aggiornato)
Controlla formazioni per fixture tracciate in `data/tracked_fixtures.json`, fonte primaria Flashscore (`services/football/external/sources/flashscore.py`), fallback API-Football. Segnala anomalie contro infortuni noti su Telegram.

### `services/football/external/sources/flashscore.py` (nuovo)
Client per il feed non ufficiale di LiveScore.in/Flashscore (`local-global.flashscore.ninja`). Metodi: `lineups(match_id)`, `stats(match_id)`, `incidents_raw(match_id)` (quest'ultimo non ancora parsato in eventi strutturati — va calibrato su una partita realmente in corso).
**Limite noto**: non c'è un endpoint di ricerca affidabile per trovare il `match_id` (mid) di una partita — va recuperato una volta a mano da livescore.in (il link della partita contiene `?mid=XXXXXXXX`) e poi riusato.

### `scripts/ticket_watcher.py` (nuovo)
Monitora live le gambe di un ticket tracciato in `data/ticket_watch.json`, invia riepilogo su Telegram solo sui cambiamenti. Valuta automaticamente solo i mercati "Gol" (Over/Under); per corner/cartellini mostra il punteggio ma non un verdetto (servirebbe leggere le stats live, non incluso per restare veloce).

### `collector.py` — nuovi metodi
`player_prop_odds(fixture_id, market, bookmaker=None)` e `list_available_markets(fixture_id)` — estraggono le quote prop-giocatore (es. "Player Fouls Committed") dai 14 bookmaker coperti da API-Football.

---

## 🛡️ 5. Le 28 Regole Inviolabili — solo le nuove di oggi (26, 27, 28)

Vedi `CLAUDE.md` per il testo completo. In sintesi:
- **#26**: Massimo 3-4 eventi per schedina sui mercati player-prop, mai disperdere in multiple lunghe.
- **#27**: Controllo forma recente via API-Football OBBLIGATORIO prima di ogni tabella, anche senza rassegna stampa — non bastano mai le sole quote o la reputazione generica.
- **#28**: Quando la selezione realmente piazzata differisce dalla raccomandazione, analizzarla SEMPRE con lo stesso rigore prima di consegnare l'esito — mai "non l'ho controllata" se i dati erano raggiungibili.

---

## 📋 6. Deploy sul Raspberry Pi (se serve monitoraggio indipendente dalla sessione)

```bash
ssh pi@100.120.216.25
cd ~/BAgent && git pull origin main
# poi ricrea data/ticket_watch.json (vedi contenuto in sezione 3, o copia da questo computer)
python3 scripts/ticket_watcher.py   # test manuale, deve mandare un Telegram
(crontab -l 2>/dev/null; echo "*/10 * * * * cd ~/BAgent && python3 scripts/ticket_watcher.py >> /tmp/ticket_watcher.log 2>&1") | crontab -
```

---

## 📋 7. Come Riprendere la Sessione sul Nuovo Computer

```bash
cd BAgent
git pull origin main
```

Poi:
> *"Ho riaperto BAgent su un altro computer, ho letto il checkpoint in `docs/session_handover_2026_08_25.md` e `CLAUDE.md`. Il Ticket #29 era ancora in corso quando ho chiuso — controlla lo stato attuale delle 7 partite e riprendiamo da lì."*

---
*Tutto salvato, committato e pushato. Il monitoraggio automatico via ScheduleWakeup resta attivo SOLO nella sessione originale finché non viene chiusa/scade.*
