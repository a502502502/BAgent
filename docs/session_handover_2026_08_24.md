# 🚀 BAgent — Session Handover & Complete Checkpoint
**Data Checkpoint**: Lunedì 24 Agosto 2026 — Ore 07:50 (CEST)
**Stato**: Sincronizzato e Salvato al 100% su GitHub (`origin/main`)

---

## 📌 1. Riepilogo Esecutivo & Stato del Progetto

Questo documento serve a trasferire istantaneamente e senza perdita di contesto l'intera sessione di lavoro su un altro computer o dispositivo. 

Tutti i file sorgente, il database SQLite con **3.049 giocatori**, le regole operative e i ticket sono stati versionati e caricati su **GitHub**:
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
# Esempi di utilizzo:
python scripts/query_player.py "Guimaraes"
python scripts/query_player.py "Yildiz"
python scripts/query_player.py --team "Juventus" --pos "Attacker"
python scripts/query_player.py --league "Bundesliga" --pos "Midfielder"
```

### 3. Monitor Live Zero-Latenza Flashscore (`scripts/night_live_daemon.py`)
Motore di tracciamento istantaneo per corner, cartellini e falli collegato direttamente ai feed `https://local-global.flashscore.ninja/2/x/feed/` per aggiornamenti Telegram senza ritardi.

---

## 🛡️ 3. Il Decalogo delle 16 Regole Inviolabili di BetGuard

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
15. **DIVIETO ASSOLUTO DI DUPLICAZIONE DELLA STESSA SELEZIONE SU PIÙ TICKET (DECOUPLING 100%)**:
    * MAI inserire lo stesso identico pronostico in 2 o più schedine contemporanee nella stessa sessione.
    * Ogni schedina deve essere statisticamente e operativamente INDIPENDENTE per azzerare il Single-Point-of-Failure.
16. **AUDIT PREVENTIVO SULL'INTEGRITÀ DELLA ROSA (PRE-MATCH SQUAD INTEGRITY FILTER)**:
    * MAI affidarsi alle sole statistiche della passata stagione.
    * Eseguire 60 minuti prima:
      1. *Talisman Check*: Presenza del capocannoniere (es. Watkins escluso per mercato).
      2. *Spine Check*: Presenza di portiere titolare (Dibu Martinez vs Bizot), mediano di rottura (Onana) e centrali.
      3. *Youth Emergency Check*: Se la squadra schiera debuttanti U19 d'emergenza (es. 18enne Hemmings), scatta il BAN IMMEDIATO da mercati a favore e si punta invece SULL'AVVERSARIO!

---

## 📋 4. Come Riprendere la Sessione sul Nuovo Computer

Sul nuovo computer, basta eseguire i seguenti comandi da terminale:

```bash
# 1. Clonare o aggiornare la repository
git clone https://github.com/a502502502/BAgent.git
cd BAgent
git pull origin main

# 2. Attivare il virtualenv e verificare le dipendenze
source .venv/bin/activate  # (o ricrearlo con requirements.txt)

# 3. Testare la presenza del Database Giocatori
python scripts/query_player.py "Yildiz"
```

Nel nuovo prompt, ti basterà dire:
> *"Ho riaperto BAgent sul nuovo computer, ho letto il checkpoint in `docs/session_handover_2026_08_24.md` e `CLAUDE.md`. Continuiamo da qui!"*

---
*Tutto salvato, committato e pushato con successo.* 🚀🔒
