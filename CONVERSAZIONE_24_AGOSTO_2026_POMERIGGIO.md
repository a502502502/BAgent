# 📋 CONVERSAZIONE COMPLETA — 24 AGOSTO 2026 (POMERIGGIO/SERA)

> Sessione di continuazione da `CONVERSAZIONE_24_AGOSTO_2026.md` (mattina). Obiettivo: verificare sul campo tutte le quote e le tabelle prodotte al mattino prima di piazzare qualsiasi ticket.

---

## 🎯 1. Punto di partenza

Ripresa la sessione leggendo `CONVERSAZIONE_24_AGOSTO_2026.md` e `docs/session_handover_2026_08_24.md`. Il branch locale era **21 commit indietro** rispetto a GitHub (sessione Mac di stamattina non ancora pullata). Sincronizzazione fatta con stash/pull/merge, risolto un conflitto su `scripts/night_live_daemon.py` mantenendo la versione remota (v4.0 corner tracker) più recente.

**Feedback dell'utente**: workflow multi-macchina — GitHub è la fonte di verità, i file locali non committati sono bozze usa-e-getta. Non serve preservarli con cura in caso di conflitto: vince sempre la versione più recente pushata da un'altra sessione.

---

## 🔍 2. Verifica Quote — Metodo e Risultati

Richiesta esplicita dell'utente: **"non considerare più le quote originali ma solo quelle che hai verificato adesso"**. Da qui in poi ogni numero citato doveva avere una fonte verificata in sessione (Netwin loggato, più Domusbet come secondo riscontro).

### Discrepanze trovate rispetto alla tabella mattutina
- **Corner Bologna/Roma**: la tabella mattutina parlava di "Over 7.5 Corner Totali" @1.24-1.25. La soglia reale su Netwin è **8.5**, non 7.5, con Over quotato @1.76 (Bologna) e @1.69 (Roma) — molto più alto del previsto.
- **Cartellini Fulham-Chelsea**: soglia reale **4.5**, non 3.5. Over 4.5 @1.86 (Netwin) / @1.91 (Domusbet).
- **Osasuna DC 1X**: quota reale @1.21 (handover diceva @1.18, sotto la quota minima di regolamento 1.20).
- **Duelli 1v1 (Falli per giocatore)**: mercato trovato sotto la tab **"Falli"**, non "Sanzioni" come inizialmente cercato. Risultati contrastanti:
  - Zaccagni 2+ Falli Subiti: reale @1.20 (più sicuro del previsto @1.40)
  - Dybala 2+ Falli Subiti: reale @1.40 (identica su Netwin e Domusbet — doppia conferma)
  - Palmer 2+ Falli Subiti: reale @1.80 (molto meno sicuro del previsto @1.50)
  - Berge 1+ Falli Commessi: reale @1.20 (quasi identica)

### FootyStats — limiti e scoperte
- Rate-limit gratuito di FootyStats: solo 3 partite consultabili prima di un blocco di 4 ore.
- Dati Corner/Cartellini dietro paywall Premium — solo dati Gol/BTTS disponibili gratis.
- **Scoperta importante**: nella lineup più recente di Osasuna, **Budimir risultava in panchina** (titolare Raúl García), smentendo la narrativa "Budimir bomber" della tabella mattutina. Confermato titolare solo più tardi nelle probabili formazioni Sofascore.

---

## 🧠 3. Stress-Test delle Ipotesi Tattiche (Sesto Senso Rinforzato)

L'utente ha proposto due ipotesi tattiche indipendenti, entrambe verificate contro i dati di mercato reali invece di essere accettate per fede:

1. **"Fulham ha la difesa rimaneggiata (Andersen squalificato, Cairney infortunato) → partita con molti falli"**
   → Verificato il mercato Falli Totali Match Fulham-Chelsea: linea **22.5**, quote quasi alla pari (Under 1.87/Over 1.83). **Nessuna conferma** — il mercato non prezza questa gara come anomala per falli. Ipotesi scartata, ma i singoli picks Berge/Caicedo restano validi di per sé.

2. **"Roma-Fiorentina, livello tecnico alto e partita bilanciata → molti falli"**
   → Verificato il mercato Falli Totali Match: linea **25.5**, Over @1.70 (leggero sbilanciamento verso l'Over, diversamente da Fulham-Chelsea). Segnale che sembrava confermare l'ipotesi.
   → **Controllo empirico aggiuntivo**: statistiche reali delle 4 partite di Serie A giocate il 23/08 (giornata 1): Frosinone-Juventus 33 falli (outlier), le altre 3 tutte ≤19 falli. **Solo 1 partita su 4 ha superato quota 25.** Il campione reale ha smentito l'ipotesi nonostante fosse logicamente sensata. **Ticket Over 25.5 Falli Totali scartato.**

**Lezione chiave**: un ragionamento tattico valido non basta — va sempre confrontato sia con il prezzo di mercato sia, quando possibile, con un campione reale di partite già giocate nello stesso turno.

---

## 🎫 4. Evoluzione della Schedina — Dalla Prima Bozza alla Versione Finale

Percorso iterativo di costruzione, guidato da domande e correzioni dell'utente:

1. **Prima proposta**: 4 selezioni Gol/DC (Osasuna DC1X, Chelsea X2, Dybala, Roma Over1.5) — quota ~1.89×, troppo bassa per il target "Super Sicura" (3.50-5.50×).
2. **Aggiunta Sesto Senso in tabella** (richiesta esplicita, Regola #11) con motivazioni tattiche per ogni pick.
3. **Ricalcolo per centrare il target**: sostituito un pick debole con Palmer @1.80 → quota ~3.75×, dentro il range.
4. **Verifica se ci fossero partite Liga/Ligue1 dimenticate**: Ligue 1 zero partite quel giorno; Liga aveva anche Malaga-Deportivo, analizzato ma scartato per mancanza di Sesto Senso approfondibile in tempi ragionevoli.
5. **Richiesta di una schedina "Alta Quota" solo Falli (≥10×)**: costruita prima a 5 selezioni Over 1.5 (~10.25×), poi convertita su richiesta a **Over 0.5 con più giocatori** (10 selezioni, ~13.67×), con nota onesta che il rischio aggregato è comparabile, non inferiore, nonostante quote singole più basse.
6. **Cross-check con le formazioni confermate**: analizzati TUTTI i titolari delle 3 partite per trovare i migliori pick reali di Falli Commessi/Subiti, non solo quelli già scelti. Individuato un miglioramento (Dovbyk al posto di Marušić).
7. **Upgrade Kean**: l'utente ha notato che Kean aveva la quota più bassa di tutte (@1.12 su Over 0.5) — segnale di "calamita da falli" — quindi spostato a **Over 1.5 @1.55** per sfruttare meglio il suo profilo, portando la quota finale da 13.59× a **18.80×**.

### Le 3 Schedine Finali (salvate in `reports/schedina_24ago.html`)

**🎲 Alta Quota — Falli Commessi/Subiti (9 selezioni, ~18.80×)**
| Giocatore | Partita | Mercato | Quota |
|---|---|---|---|
| Zaccagni | Bologna-Lazio | Over 1.5 Falli Subiti | @1.20 |
| Palmer | Fulham-Chelsea | Over 1.5 Falli Subiti | @1.80 |
| Caicedo | Fulham-Chelsea | Over 1.5 Falli Commessi | @1.55 |
| Berge | Fulham-Chelsea | Over 0.5 Falli Commessi | @1.20 |
| Soulé | Roma-Fiorentina | Over 0.5 Falli Subiti | @1.15 |
| Dybala | Roma-Fiorentina | Over 1.5 Falli Subiti | @1.40 |
| Kean | Roma-Fiorentina | Over 1.5 Falli Subiti | @1.55 |
| Frattesi | Bologna-Lazio | Over 0.5 Falli Commessi | @1.25 |
| Dovbyk | Bologna-Lazio | Over 0.5 Falli Subiti | @1.50 |

**🛡️ Super Sicura — Gol & Doppia Chance (4 selezioni, ~3.75×)**
Osasuna DC1X @1.21 · Chelsea X2 @1.23 · Dybala O1.5 Subiti @1.40 · Palmer O1.5 Subiti @1.80

**🚩 Corner & Sanzioni Totali Match (3 selezioni, ~3.60×)**
Bologna Over 8.5 Corner @1.76 · Roma Over 8.5 Corner @1.69 · Osasuna DC1X @1.21
*(Nota: la versione con Fulham-Chelsea Cartellini è stata scartata su richiesta dell'utente — violava la Regola #8, i Cartellini vanno giocati solo in ambienti "caldi" e Fulham-Chelsea non lo è davvero nonostante sia un derby.)*

---

## ✅ 5. Verifica Formazioni Probabili

Controllate su Sofascore le probabili formazioni di tutte e 3 le partite prima di finalizzare. **Tutti e 9 i giocatori della schedina Alta Quota risultano titolari.** Bonus: tra gli assenti Fulham compaiono **Joachim Andersen (cartellino rosso/squalificato)** e **Tom Cairney (infortunato)** — confermando la narrativa "difesa Fulham rimaneggiata" della tabella mattutina.

---

## ⚠️ 6. Tentativo di Automazione su Netwin — Fallito, Documentato

Richiesta dell'utente di creare e prenotare le 3 schedine direttamente sul carrello Netwin. Dopo ~10 tentativi di click automatizzato sui mercati "Falli per giocatore" (liste virtualizzate molto lunghe, centinaia di righe per partita), solo 1 click ha funzionato — e per errore, su un mercato sbagliato (poi rimosso con "Svuota"). I pannelli compatti (1X2/DC/Corner con poche righe) invece rispondono bene ai click.

**Decisione presa**: non insistere con l'automazione a rischio di costruire una schedina con selezioni sbagliate senza accorgersene. L'HTML di riferimento (`reports/schedina_24ago.html`) resta la checklist per il piazzamento manuale.

---

## 📌 7. Prossimi Passi
1. Attendere le formazioni ufficiali definitive (~1h prima di ogni fischio d'inizio: 18:30 Bologna-Lazio, 19:30 Osasuna-Levante, 20:45 Roma-Fiorentina, 21:00 Fulham-Chelsea).
2. Piazzare manualmente le 3 schedine su Netwin usando `reports/schedina_24ago.html` come riferimento.
3. Le nuove Regole Inviolabili #23, #24, #25 sono state aggiunte a `CLAUDE.md` per le sessioni future.

---

*Sessione conclusa — file salvato su richiesta esplicita dell'utente ("salva tutto compreso la conversazione").*
