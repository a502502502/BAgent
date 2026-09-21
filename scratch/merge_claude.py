import subprocess

# Read remote CLAUDE.md
res = subprocess.run(['git', 'show', 'origin/main:CLAUDE.md'], stdout=subprocess.PIPE)
remote_text = res.stdout.decode('utf-8', errors='ignore')

# Read local additions from our previous commit or diff
local_ticket_and_rules = """
---

### 🎯 TICKET #91 — IL CAPOLAVORO STORICO DEL POMERIGGIO: EN PLEIN 7 SU 7 (18 SETTEMBRE 2026)
* **Piattaforma**: Netwin | **Stato**: 🏆 **VINTA AL 100% (EN PLEIN 7 SU 7)**
* **Identificativo Ticket**: `TICKET_CASSAFORTE_23EUR_18SET`
* **Importo Puntato**: **`23.00 €`** | **Quota Totale**: **`7.79×`** | **Bonus Multipla**: **`+10.74 €`** | **Vincita Incassata**: **`189.86 €`**
* **Profitto Netto**: **`+166.86 €`** | **Bankroll Salito a**: **`204.18 €`** (da 37.32 € iniziali)

| # | Evento & Torneo | Mercato | Quota | Risultato Finale | Esito |
|---|---|:---:|:---:|:---:|:---:|
| 1 | 🇺🇦 **FC Chernomorets Odessa vs FC Obolon Kyiv** *(UPL)* | `1X + Under 4.5` | 1.45 | **1 - 1** | 🏆 **WON** |
| 2 | 🌏 **Arabia Saudita U23 vs Qatar U23** *(Giochi Asiatici)* | `1 (Esito Finale)` | 1.48 | **2 - 0** | 🏆 **WON** |
| 3 | 🇮🇱 **Maccabi Yavne vs Hapoel Herzelia FC** *(Liga Alef South)* | `Under 3.5` | 1.33 | **0 - 0** | 🏆 **WON** |
| 4 | 🇨🇳 **Zhejiang FC vs Wuhan Three Towns FC** *(Super League)* | `1X + Over 1.5` | 1.42 | **4 - 1** | 🏆 **WON** |
| 5 | 🇺🇦 **FC Polissya Zhytomyr vs FC Kryvbas Kriviy Rih** *(UPL)* | `1 (Esito Finale)` | 1.23 | **1 - 0** | 🏆 **WON** |
| 6 | 🇮🇱 **Hapoel Tel Aviv FC vs Hapoel Petah Tikva FC** *(Premier)* | `Doppia Chance 1X` | 1.07 | **3 - 0** | 🏆 **WON** |
| 7 | 🇿🇦 **Highbury FC vs Gomora United** *(Championship)* | `1X + Under 3.5` | 1.46 | **0 - 0** | 🏆 **WON** |

---

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

---

*Ultimo aggiornamento: 21 settembre 2026 ore 09:30 — BAgent (Bankroll Ufficiale: 164.18 € | Riconciliato con Mac: Ticket 90/91 e Telegram Mini App)*
"""

merged_claude = remote_text.rstrip() + "\n\n" + local_ticket_and_rules.strip() + "\n"

with open('CLAUDE.md', 'w', encoding='utf-8') as f:
    f.write(merged_claude)

print("Merged CLAUDE.md successfully! Total length:", len(merged_claude))
