# 📖 RESOCONTO COMPLETO SESSIONE BAGENT (22 AGOSTO 2026)
### 🔄 Handover Ufficiale per Riprendere da Mac / Raspberry Pi

---

## 🎯 1. STATO ATTUALE DEI TICKET & CASSA

### 🛡️ TICKET #15: QUATERNA D'ACCIAIO SERALE (In Gioco Ufficiale su Netwin)
* **Stake**: **20.00 €**
* **Quota Base**: **5.89×**
* **Bonus Netwin**: **+3.53 €**
* **Vincita Potenziale**: **`121.24 €`** 💰
* **Stato**: **In Corso (4/4 aperte)** ⏱️

| # | Orario | Campionato | Partita | Mercato Scelto | Quota | Motivazione Tattica |
|:---:|:---:|:---|:---|:---:|:---:|:---|
| **1** | **18:30** | 🇮🇹 Serie A | **Inter vs Monza** | 🎯 **Lautaro (o Sost.) Segna o Palo/Trav.** | **@1.67** | Perno offensivo a San Siro. Copertura totale Netwin Duo (sostituto + legni). |
| **2** | **18:30** | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League | **Brentford vs Tottenham** | 🚩 **Over 4.5 Corner Brentford (Sq.1)** | **@1.50** | Bees a trazione sui piazzati in casa contro la linea alta Spurs. |
| **3** | **20:45** | 🇫🇷 Ligue 1 | **Tolosa vs Lione** | ⚽ **MultiGol 1-3 Casa (Tolosa)** | **@1.32** | Tolosa a segno da 8 gare interne di fila. Forbice 1-3 protetta al 100%. |
| **4** | **21:30** | 🇪🇸 LaLiga | **Espanyol vs Real Madrid** | 👑 **X2 + Over 2.5 Gol** | **@1.78** | Mbappé e Vinicius devastanti negli spazi. X2 copre qualsiasi pareggio con gol. |

---

## 📊 2. ESITI TICKET PRECEDENTI
* **Ticket #14 (Sestina Overseas - 20€)**: 5 su 6 prese al 100% (Jaguares 1-0 ✅, The Strongest 4-3 ✅, Western Suburbs 3-0 ✅, Tigres 2-0 ✅, Upper Hutt 3-0 ✅). Mancato solo 1 gol su Cashmere 3-0 (Over 3.5).

---

## 📱 3. INFRASTRUTTURA RASPBERRY PI 24/7 ATTIVA:
* **Host**: `pi@100.101.32.5` o `pi@bagent`
* **Demone Live**: `scripts/night_live_daemon.py` configurato con i 4 eventi del Ticket #15.
* **Notifiche Telegram**: Bot `@A502502_bot` (Chat ID: `466378357`) con notifiche live per:
  1. 🟢 Fischio d'inizio (Kickoff)
  2. ⚽ Gol in tempo reale
  3. 🏁 Fischio finale (FT) con calcolo esito pronostico
  4. 📋 Quadro riepilogativo Ticket #15 con vincita potenziale (121.24 €)

---

## 🚀 4. COME AGGIORNARE IL RASPBERRY PI IN 5 SECONDI:
Sul terminale del Raspberry Pi (`pi@bagent:~ $`):
```bash
cd ~/BAgent
git pull origin main
sudo systemctl restart bagent-live
```
