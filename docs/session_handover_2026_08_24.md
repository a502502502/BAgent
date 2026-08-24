# 🚀 BAgent — Session Handover & Complete Checkpoint
**Data Checkpoint**: Lunedì 24 Agosto 2026 — Ore 23:05 (CEST)
**Stato**: Sincronizzato e Salvato al 100% su GitHub (`origin/main`)

---

## 📌 1. Riepilogo Esecutivo & Stato del Progetto

Questo documento serve a trasferire istantaneamente e senza perdita di contesto l'intera sessione di lavoro su un altro computer o dispositivo. 

Tutti i file sorgente, il database SQLite con **3.049 giocatori**, le 17 regole operative e i ticket sono stati versionati e caricati su **GitHub**:
👉 **Repository**: `https://github.com/a502502502/BAgent`
👉 **Branch**: `main`

---

## 🗄️ 2. Database e Strumenti Creati nella Sessione

### 1. Database Giocatori BAgent (`storage/database/bagent.db`)
Popolato con i roster ufficiali completi della stagione **2026/2027**:
* 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League**: 20 squadre, **674 giocatori**
* 🇮🇹 **Serie A**: 20 squadre, **647 giocatori**
* 🇩🇪 **Bundesliga**: 18 squadre, **571 giocatori**
* 🇪🇸 **La Liga**: 20 squadre, **631 giocatori**
* 🇫🇷 **Ligue 1**: 18 squadre, **526 giocatori**
* **TOTALE**: **96 squadre censite, 3.049 giocatori** con età, numero di maglia, ruolo e foto.

### 2. Strumento CLI di Ricerca Giocatori (`scripts/query_player.py`)
Ricerca immediata con normalizzazione automatica di accenti e caratteri speciali:
```bash
python scripts/query_player.py "Yildiz"
python scripts/query_player.py --team "Juventus" --pos "Attacker"
```

### 3. Downloader Dati LiveScore (`scripts/download_livescore.py`)
Estrae istantaneamente xG, tiri, formazioni, duelli, falli e corner da qualsiasi link o Match ID di LiveScore.in:
```bash
python scripts/download_livescore.py "OCgNUQYH"
```

---

## 🛡️ 3. Il Decalogo delle 17 Regole Inviolabili di BetGuard

1. **Analisi Profonda Assenze & Referti Medici**: Verificare sempre infortuni e formazioni ufficiali.
2. **Quota Combinata Target**: $\ge 3.50\times$ (Super Sicure) e $\ge 100\times$ (Lotto Matematico).
3. **Validazione Visiva Live & Cashout**: Usare il cashout per blindare i profitti.
4. **Sesto Senso & Pressione Ambientale**: No 1X2 in trasferta nelle coppe secche o campi ostili.
5. **BAN PERMANENTE CAMPIONATI ARABI E LEGHE OPACHE**: Solo leghe regolamentate con feed live garantiti.
6. **Strategia a 3-4 Eventi d'Acciaio**: Preferire ticket compatti e consistenti.
7. **Trappola del Segno 2 Fisso nelle Coppe**: Usare sempre la Doppia Chance X2 o linee Gol.
8. **Profilo Geografico dei Cartellini**: Over solo su derby e stadi caldi (Grecia, Turchia, Sudamerica).
9. **Leghe Giovanili / Riserve / Squadre B**: Giocare sempre e solo Over/Under Gol, MAI l'1X2 secco.
10. **La Trappola delle Prime 1-3 Giornate (N ≤ 3)**: Solo Doppie Chance di protezione o Gol protetti.
11. **Obbligo Colonna 'Motivazione Tattica & Sesto Senso' in tutte le tabelle**.
12. **La Trappola della Partita 'Troppo Pulita'**: No sanzioni/falli in gare a senso unico.
13. **L'Arsenal Corner Engine & Asimmetria dei Corner**: Corner come arma sistematica in casa.
14. **Filtro Distacco in Classifica ($\Delta \le 3$) in Sudamerica/Leghe Minori**: Ban sui segni secchi.
15. **DIVIETO ASSOLUTO DI DUPLICAZIONE DELLA STESSA SELEZIONE SU PIÙ TICKET (DECOUPLING 100%)**: Zero sovrapposizioni tra ticket contemporanei per evitare il single-point-of-failure.
16. **AUDIT PREVENTIVO SULL'INTEGRITÀ DELLA ROSA (PRE-MATCH SQUAD INTEGRITY FILTER)**:
    * Eseguire 60 minuti prima:
      1. *Talisman Check*: Presenza del capocannoniere (es. Watkins escluso per mercato).
      2. *Spine Check*: Presenza di portiere titolare (Dibu Martinez vs Bizot), mediano di rottura (Onana) e centrali.
      3. *Youth Emergency Check*: Se la squadra schiera debuttanti U19 d'emergenza (es. 18enne Hemmings), scatta il BAN IMMEDIATO da mercati a favore e si punta invece SULL'AVVERSARIO!
17. **PROTOCOLLO DI RIGORE MATEMATICO (STOP ALLA DISPERSIONE DEI MICRO-PROPS & RITORNO A 3-4 EVENTI D'ACCIAIO)**:
    * I mercati sui singoli giocatori (Falli Giocatore / Duelli 1v1) soffrono di una varianza individuale troppo alta per essere concatenati in multiple lunghe.
    * Massimo 3 o 4 Eventi per Schedina (Quota target $3.50\times - 5.50\times$ con Bonus): Ritorno al modello matematico vincente del 19 Agosto.
    * Priorità a Mercati di Squadra e Linee Protette: Doppie Chance con Gol (1X + Over 1.5), Corner di Squadra Asimmetrici, MultiGol 1-3.

---

## 🌙 4. Ticket Attivo per la Notte (Ticket #27 - Quota 10.00× / con Bonus ~12.50×)
1. 🇺🇸 **Charleston Battery vs Miami FC** ➔ `Over 2.5 Gol` @1.50
2. 🇧🇷 **Sc Recife Pe vs America Mg** ➔ `1 (Sport Recife)` @1.63
3. 🇦🇷 **Tigre vs Central Cordoba** ➔ `Under 2.5 Gol` @1.45
4. 🇨🇴 **Boyaca Patriotas vs Atletico Fc** ➔ `1 (Boyaca Patriotas)` @1.34
5. 🇧🇷 **Botafogo vs Athletico Paranaense** ➔ `1X (Botafogo)` @1.40
6. 🇧🇷 **Athletic Club vs Novorizontino** ➔ `Under 2.5 Gol` @1.50

---

## 📋 5. Come Riprendere la Sessione sul Nuovo Computer

Sul nuovo computer, basta eseguire i seguenti comandi da terminale:

```bash
# 1. Aggiornare la repository
cd BAgent
git pull origin main

# 2. Verificare l'ambiente
source .venv/bin/activate
python scripts/query_player.py "Yildiz"
```

Nel nuovo prompt, ti basterà dire:
> *"Ho riaperto BAgent sul nuovo computer, ho letto il checkpoint in `docs/session_handover_2026_08_24.md` e `CLAUDE.md`. Continuiamo da qui!"*

---
*Tutto salvato, committato e pushato con successo.* 🚀🔒
