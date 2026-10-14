# BAgent: Quantitative Sports Betting & Autonomous Portfolio Engine
## Master Project Context & Deep Reasoning Audit Pack (for Gemini 4 Argon)

> **Document Purpose**: This single consolidated master file encapsulates the entire architecture, quantitative methodology, operational betting manifesto (Rules 1 to 85), historical ledger, and live slate for the BAgent autonomous project. Designed specifically for ingestion and deep-reasoning audit by **Gemini 4 Argon** (`gemini-4-argon`).

---

## 1. Executive Summary & System Mission

**BAgent** is an AI-first, quantitative sports betting system and bankroll management agent designed to eliminate human cognitive bias, emotional chasing, and bookmaker traps. 

### Core Operational Principles
- **No Gut Feelings, Pure Math & Reality**: Probabilities are derived from data (Poisson distribution, Dixon-Coles models, empirical xG distributions), never from bookmaker odds alone.
- **Asymmetric Hedging & Flow Markets**: Rigid 1X2 match betting is banned. The system prioritizes high-coverage flow markets that absorb match volatility (Chance Mix, MultiGol intervals, Team totals, Player Props).
- **Core-Satellite Portfolio (70/30 Rule)**:
  - **70% of Bankroll**: Allocated to low-risk, high-probability "Core / Cassaforte" slips (target odds 2.40x to 3.20x).
  - **30% of Bankroll**: Allocated to "Satellite" slips (Props, hidden gems, or asymmetric high-odds combos).
- **Strict Anti-Hallucination & Reality Gate (Rule #85)**: Every player, squad, manager, injury, and schedule is verified against official 2026/27 registries. Outdated memory, simulated games, or fantasy rosters are strictly forbidden.

---

## 2. System Architecture & Technical Stack

```
   +-------------------------------------------------------------------+
   |                     BAgent Autonomous Pipeline                    |
   +-------------------------------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|  Tri-Convergence OFP  |                       |  Strict Betting Rules |
|   Statistical Engine  |                       |   Engine (Rules 1-85) |
| (Oddspedia/Forebet/P) |                       | (CLAUDE.md/.cursor)   |
+-----------------------+                       +-----------------------+
            |                                               |
            +-----------------------+-----------------------+
                                    |
                                    v
            +-----------------------------------------------+
            |    Execution, Tracking & Portfolio Ledger     |
            |   (SQLite database: storage/database/bagent.db|
            |     active ledger: data/active_user_tickets)  |
            +-----------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|   Live Web Portal     |                       |  Telegram Sentinel    |
| (portal/schedine.json |                       |   Daemon & Alerts     |
|  & bagent-schedine)   |                       | (scripts/telegram...) |
+-----------------------+                       +-----------------------+
```

### Key Modules:
1. **`analyzer/ofp_engine.py`**: The three-pillar convergence engine:
   - **O (Oddspedia)**: Market consensus, dropping odds, bookmaker sentiment.
   - **F (Forebet / Mathematical Models)**: Poisson probability distributions, xG predictions, score projections.
   - **P (MondoPengwin / Qualitative Flow)**: Specialist markets, card pressure, tactical match narratives.
2. **`storage/database/bagent.db`**: SQLite ledger tracking `ticket_ledger` (tickets, stakes, odds, status, P&L) and `bet_leg_ledger` (individual match selections, estimated probabilities, and edges).
3. **`data/active_user_tickets.json`**: Real-time JSON mirror maintaining all historical and active user slips.
4. **`portal/schedine.json` & `bagent-schedine/`**: Public live portal updating active (`present`), upcoming (`future`), and settled (`past`) slips with dynamic P&L calculation.

---

## 3. The Betting Manifesto & Inviolable Rules

### A. General Governance & Bankroll Discipline
- **Max Stake**: Max 8% of total bankroll per ticket; 5-8% fractional Kelly Criterion on single edges. Max 15% daily session risk.
- **No Loss Chasing**: If a day or early ticket loses, revenge/chasing betting is strictly prohibited.
- **Odds Sweet Spot**: Individual legs must have odds between 1.25 and 1.85 (target 1.35 - 1.55). Outright traps below 1.20 are flagged as unplayable.

### B. Abolition of Rigid 1X2 Match Outcomes
- **Rule**: Pure "1" or "2" outright wins or rigid combos like "1 + Over 1.5" or "2 + Over 2.5" are prohibited on favorites.
- **Alternative**: Use Asymmetric Double Chance combos (`1X + Over 1.5`, `X2 + Under 4.5`), Chance Mix (`1X o Over 1.5`), or MultiGol intervals.

### C. Player Props Protocol
- **Offensive Props (Shots on Target)**: Must be placed ONLY on confirmed starting center-forwards or primary penalty takers who consistently play 80+ minutes in top-tier fixtures.
- **Defensive Discipline Prohibition**: Individual defender foul counts are volatile and subject to match disruption (e.g., teammate red cards, referee bias). Discipline bets must only target **total match card/foul lines**, never isolated defenders.
- **Goalkeeper Saves Asymmetry**: Goalkeepers facing high shot-volume opponents (e.g. teams averaging > 20 shots / > 8 on target) offer massive positive EV on low save lines (Over 3.5 saves).

### D. Regola #85: Reality Gate & Anti-Fantasy Bias
- Strict verification of 2026/27 transfers and rosters:
  - Inter Milan: Coach Cristian Chivu (Akanji, Stones, Bastoni, Lautaro, Thuram).
  - Napoli: Coach Massimiliano Allegri (Kevin De Bruyne, McTominay, Rasmus Højlund).
  - AS Roma: Coach Gian Piero Gasperini (Artem Dovbyk, Paulo Dybala).
  - Manchester City: Coach Enzo Maresca (Erling Haaland, Rayan Cherki, Phil Foden).
  - Liverpool: Coach Arne Slot (Mohamed Salah, Cody Gakpo, Alexis Mac Allister).
  - Real Madrid: Coach Carlo Ancelotti (Kylian Mbappé, Vinícius Júnior, Jude Bellingham).

---

## 4. Current Ledger, Performance & Retrospective

### Financial Ledger Snapshot (October 2026)
- **Monday, Oct 12**:
  - `TICKET_USER_MULTIPLA4_PENGWIN_15EUR_12OTT` (@ 5.60x): **WON (+86.61 EUR)**.
  - Overall Oct 12 Net Balance: **+41.61 EUR**.
- **Tuesday, Oct 13 (UCL Matchday 3 - Night 1)**:
  - 4 tickets placed (Total stake: 35.00 EUR).
  - Outcome: 0/4 won (Net: -35.00 EUR).
  - **Net Cumulative Bankroll**: **+6.61 EUR (In Positive Territory)**.

### Detailed Retrospective of October 13:
1. **Ticket 3 (Tripla Gemme Props @ 4.94x) — Heartbreak by 1 Single Stat**:
   - **Leg 1**: *Rasmus Højlund Almeno 1 Tiro in Porta*: **WON** (Shot on target saved at 81' by Luiz Júnior).
   - **Leg 2**: *Yann Sommer Over 3.5 Parate*: **WON (Monumental)**. Sommer recorded **9 saves** against Inter's 12 shots on target. The model's +22.2% EV prediction was validated.
   - **Leg 3**: *Lisandro Martínez Cartellino o >=2 Falli*: **LOST by 1 foul**. Martínez committed 1 foul at 26' and 0 cards. Teammate Leny Yoro received a straight red card at 74', freezing United's defensive aggression.
2. **Ticket 2 (Multipla 6 Top Match UCL @ 9.22x) — 4/6 Hits**:
   - *Hits*: Villarreal-Napoli Gol (3-1), Arsenal Over 15.5 Shots (21 shots, 3-0), Atletico 1X+Over 1.5 (2-0), Gala-Barca Gol (1-4).
   - *Misses*: Leipzig vs PSV (Goal arrived at 75', failing 1st-half goal bet), Inter vs Brugge MultiGol (2nd half featured 5 goals, bursting MultiGol 1-4).

---

## 5. Today's Live Slate: Wednesday, 14 October 2026 (UCL Matchday 3 - Night 2)

### The 9 Official UEFA Champions League Fixtures:
1. **Feyenoord vs Como** *(18:45 CEST, De Kuip)*: Cesc Fàbregas's Como faces Dutch intensity in Rotterdam.
2. **LASK vs Liverpool** *(18:45 CEST, Raiffeisen Arena)*: Arne Slot's Reds (Salah, Díaz, Mac Allister) heavily favored away.
3. **Manchester City vs Paris Saint-Germain** *(21:00 CEST, Etihad Stadium)*: Heavyweight clash. Haaland & Cherki vs Dembélé & Kvaratskhelia.
4. **AS Roma vs Real Madrid** *(21:00 CEST, Stadio Olimpico)*: Gian Piero Gasperini's Roma (Dovbyk, Dybala) vs Carlo Ancelotti's Real Madrid (Mbappé, Vinícius Jr).
5. **Aston Villa vs Fenerbahçe** *(21:00 CEST, Villa Park)*: Unai Emery vs José Mourinho tactical duel.
6. **Bodø/Glimt vs Borussia Dortmund** *(21:00 CEST, Aspmyra Stadion)*: Arctic artificial pitch. Serhou Guirassy leading Dortmund's attack.
7. **Slovan Bratislava vs VfB Stuttgart** *(21:00 CEST)*: Sebastian Hoeneß's Stuttgart facing a fragile Slovan defense.
8. **Real Betis vs FC Porto** *(21:00 CEST, Benito Villamarín)*: Open, high-tempo Iberian clash.
9. **Shakhtar Donetsk vs AEK Athens** *(21:00 CEST, Neutral ground Gelsenkirchen)*: Balanced European encounter.

---

## 6. The Three Working Proposals for Today

### Ticket A: "La Cassaforte Raddoppio" (Core Portfolio @ 2.74x)
- **LASK vs Liverpool (18:45)**: `2 + Over 1.5` (@ 1.42)
- **Feyenoord vs Como (18:45)**: `1X + Over 1.5` (@ 1.38)
- **AS Roma vs Real Madrid (21:00)**: `X2 + Under 4.5` (@ 1.40)
- *Total Odds*: **2.74x** · *Stake*: 15.00 EUR · *Potential Win*: **41.10 EUR**

### Ticket B: "Gemme Props & Parate Portiere" (Props Model @ 4.80x)
- **LASK vs Liverpool (18:45)**: `Portiere LASK (Lawal/Siebenhandl) Over 3.5 Parate` (@ 1.55) *(Sommer model replica)*
- **Manchester City vs PSG (21:00)**: `Haaland, Erling Almeno 1 Tiro in Porta` (@ 1.32)
- **Bodø/Glimt vs Dortmund (21:00)**: `Guirassy, Serhou Almeno 1 Tiro in Porta` (@ 1.45)
- **Aston Villa vs Fenerbahçe (21:00)**: `U/O Cartellini Totali Match Over 4.5` (@ 1.62) *(Emery vs Mourinho)*
- *Total Odds*: **4.80x** · *Stake*: 10.00 EUR · *Potential Win*: **48.00 EUR**

### Ticket C: "Satellite Top Match UCL" (High Multiplier @ 11.56x)
- **Manchester City vs PSG (21:00)**: `Gol (Entrambe a Segno)` (@ 1.52)
- **AS Roma vs Real Madrid (21:00)**: `Gol` (@ 1.62)
- **Bodø/Glimt vs Dortmund (21:00)**: `Over 2.5` (@ 1.55)
- **Slovan Bratislava vs Stoccarda (21:00)**: `2 (Stoccarda)` (@ 1.45)
- **Aston Villa vs Fenerbahçe (21:00)**: `1X + Over 1.5` (@ 1.40)
- **Real Betis vs FC Porto (21:00)**: `MultiGol 2-4` (@ 1.50)
- *Total Odds*: **11.56x** · *Stake*: 5.00 EUR · *Potential Win*: **57.80 EUR**

---

## 7. Prompts to Copy-Paste into Gemini 4 Argon

When uploading this file to Gemini 4 Argon (`gemini-4-argon`), you can use any of the following prompts to trigger its frontier deep reasoning:

### Prompt 1: Comprehensive Strategic Audit
> "Ho caricato il file Master di BAgent, il nostro sistema quantitativo di scommesse sportive e gestione del bankroll. Analizza l'intera architettura, il manifesto delle regole (inclusa la Regola #85 Reality Gate) e la retrospettiva delle partite di ieri. Quali sono i 3 punti di maggiore debolezza matematica della nostra strategia e come ottimizzeresti il bilanciamento tra Ticket A (Cassaforte), Ticket B (Props) e Ticket C (Satellite) per le 9 partite di Champions League di stasera?"

### Prompt 2: Deep Dive on Goalkeeper Saves & Player Props
> "Esamina specificamente il nostro modello sulle Player Props. Ieri abbiamo fatto cassa piena su Sommer Over 3.5 Parate (9 parate reali) e su Hojlund 1 Tiro in Porta, ma abbiamo perso per 1 solo fallo su Lisandro Martinez. Analizza la proposta per stasera con il portiere del LASK Over 3.5 parate contro il Liverpool e Haaland/Guirassy almeno 1 tiro in porta. Qual è la probabilità teorica stimata di questa quadrupla e come dovremmo dimensionare lo stake rispetto al nostro bankroll attuale?"

### Prompt 3: Real Madrid vs Roma & City vs PSG Tactical Engine
> "Esegui un'analisi tattica approfondita su Manchester City vs PSG e AS Roma vs Real Madrid di stasera tenendo conto degli assetti reali (Gasperini alla Roma, Maresca al City, Luis Enrique al PSG, Ancelotti al Real). Quali mercati asimmetrici (fuori dal classico 1X2) offrono il più alto Expected Value e come possono essere integrati senza generare correlazioni negative?"
