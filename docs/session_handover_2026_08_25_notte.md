# 🚀 BAgent — Session Handover & Complete Checkpoint (Notte 25-26 Agosto)

**Data Checkpoint**: Notte tra Martedì 25 e Mercoledì 26 Agosto 2026 — Ore ~22:55 (CEST)
**Stato**: Salvato e sincronizzato su GitHub (`origin/main`). Sessione aperta su un **secondo Mac** — vedi sezione 1 per il setup ambiente specifico di questa macchina.

---

## 🖥️ 1. Setup Ambiente — Specifico per questo (nuovo) Mac

Su questo computer `data/` non era collegata a Google Drive. Risolto con symlink individuali (NON una cartella intera, per non toccare `historical/` e `netwin_session/` già locali):

```bash
cd /Users/flashmac/Projects/BAgent/data
DRIVE="/Users/flashmac/Google Drive/My Drive/B-Agent/BAgent/data"
for f in bagent.db bagent.db-journal matches.db csv_import football cache predictions \
  brazil-serie-a-league-2026-to-2026-stats.csv brazil-serie-a-matches-2026-to-2026-stats.csv \
  brazil-serie-a-players-2026-to-2026-stats.csv brazil-serie-a-teams-2026-to-2026-stats.csv \
  netherlands-eredivisie-league-2026-to-2027-stats.csv netherlands-eredivisie-matches-2026-to-2027-stats.csv \
  netherlands-eredivisie-players-2026-to-2027-stats.csv netherlands-eredivisie-teams-2026-to-2027-stats.csv; do
  ln -s "$DRIVE/$f" "$f"
done
```

Poi eseguito checkpoint del DB (journal file presente = stato dirty):
```python
import sqlite3
conn = sqlite3.connect('data/bagent.db')
conn.execute('PRAGMA wal_checkpoint;')
conn.commit()
```

**Se riapri su un Mac dove `data/` risulta vuota (solo `historical/`/`netwin_session/`), rifai questi due passaggi prima di qualunque query.** `.env` e `.venv` su questo Mac erano già presenti e funzionanti — se mancano, vedi sezione 7 (come sempre) per copiarli da Google Drive.

**Nota**: `venv` usa Python 3.9 con un warning innocuo su LibreSSL/urllib3 (`NotOpenSSLWarning`) — ignorabile, non blocca nulla.

---

## 🎫 2. Ticket #29 — CHIUSO, PERSO (5/7 prese)

Bruciato dalla leg 5 (Bodø Glimt Over 8.5 Corner Totali — arrivati solo a 6 corner totali nonostante 3-0 finale e 10 uomini avversari dal 3'). Le leg 6 e 7 (Juventude-CRB, Goianiense-Botafogo, kickoff 00:30) erano ancora da giocare al momento della chiusura di questo checkpoint ma **irrilevanti**: il ticket aveva già perso sulla leg 5. Dettaglio completo con tutti gli esiti in `CLAUDE.md`, sezione Ticket #29.

---

## 🎫 3. Ticket di Recupero — IN CORSO al momento del checkpoint

File HTML: `reports/schedina_recupero_notte_25ago.html`. Stake 20€, quota 3.43×, potenziale 68.55€.

| # | Partita | Fixture ID | Orario | Pick | Quota |
|---|---|---|---|---|---|
| 1 | Deportivo Madryn - Godoy Cruz | 1498659 | 26/08 00:00 IT | Under 2.5 Gol | @1.42 |
| 2 | Juventude RS - CRB | 1520835 | 26/08 00:30 IT | Under 2.5 Gol | @1.62 |
| 3 | Atlético Goianiense - Botafogo SP | 1520831 | 26/08 00:30 IT | Under 2.5 Gol | @1.49 |

**Per controllare lo stato al volo**:
```python
from dotenv import load_dotenv; load_dotenv('.env')
from services.football.external.collector import FootballExternalCollector
c = FootballExternalCollector()
for fid in [1498659, 1520835, 1520831]:
    fx = c.fixture(fid)['response'][0]
    print(fx['teams']['home']['name'], fx['goals']['home'], '-', fx['goals']['away'], fx['teams']['away']['name'], fx['fixture']['status'])
```

**Nessuna delle 3 partite era ancora iniziata quando questo checkpoint è stato scritto** (~22:55, kickoff alle 00:00 e 00:30). Se riprendi dopo che sono finite, verifica subito i punteggi con lo snippet sopra e aggiorna il Registro Cassa in `CLAUDE.md`.

---

## 🏆 4. Tris Live Già Concluso e Vinto (per contesto, non richiede azione)

Su Betsson, in-play, formazioni verificate: **Bodø Glimt Over 2.5 Gol** (3-0 FT), **Birmingham-Brentford Over 5.5 Gol** (1-6 FT), **Doncaster-Middlesbrough Over 2.5 Gol** (1-3 FT). Tutte e tre vinte, confermato dall'utente. Non serve nessuna azione di follow-up, solo per contesto se l'utente ne parla.

---

## 📋 5. Come Riprendere la Sessione su un Altro Computer

```bash
cd BAgent
git pull origin main
```

Poi verifica subito lo stato delle 3 partite del ticket di recupero con lo snippet della sezione 3, e collega/verifica `data/` come da sezione 1 se necessario.

Messaggio suggerito per la nuova sessione:
> *"Ho riaperto BAgent su un altro computer, ho letto `docs/session_handover_2026_08_25_notte.md` e `CLAUDE.md`. Il ticket di recupero da 3 selezioni (Madryn-Godoy Cruz, Juventude-CRB, Goianiense-Botafogo, tutte Under 2.5) era in corso quando ho chiuso — controlla lo stato attuale e aggiorniamo il Registro Cassa."*

---

## 🛠️ 6. Nota Tecnica — Ricerca su Betsson (desktop)

Il campo di ricerca nella sidebar sinistra (`betsson.it/scommesse`) a volte non riceve il testo digitato se si clicca subito dopo una `navigate` — il click sembra andare a segno ma il campo resta vuoto. **Soluzione**: fare un secondo click esplicito sul campo prima di digitare (usare `find` per ottenere il `ref` esatto se le coordinate falliscono per via dello scroll/reflow della pagina).

---

## 📋 7. Se serve rifare il setup completo da zero

```bash
git clone https://github.com/a502502502/BAgent.git
# collegare data/ da Google Drive (vedi sezione 1 per i symlink esatti)
# copiare .env dalla cartella Google Drive B-Agent/BAgent/.env nella root del progetto
pip install -r requirements.txt
```

---
*Tutto salvato, committato e pushato. Nessun monitoraggio automatico (ScheduleWakeup) attivo su questa sessione al momento del checkpoint — il ticket di recupero va controllato manualmente o riattivato esplicitamente nella nuova sessione.*
