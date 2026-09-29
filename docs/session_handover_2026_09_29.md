# Session Handover — Martedì 29 Settembre 2026

## 1. Stato del Bankroll & Sessioni Recenti
- **Bankroll Attuale**: **€182.18** (partito da €100.00).
- **Sessione Domenica 27/09**:
  - Audit quote live Netwin: smascherate le quote compresse sulle doppie chance (es. Olanda X2 @ 1.09, Germania 1X @ 1.10).
  - Giocate live sui 2° tempi (Intervallo): Germania Segna Prossimo Gol / 1 Fisso Live (@ 1.50/1.60) e Norvegia-Portogallo Over 2.5 / Gol Live (@ 1.60/1.35 con trigger Assedio Regola #50).
- **Sessione Lunedì 28/09 (UEFA Nations League)**:
  - Schedina Tripla di Continuità certificata a quota **@ 2.51** (Lettonia 1X @ 1.43, Romania 1X @ 1.32, Svezia 1X @ 1.33).
  - File HTML interattivo: `reports/schedina_28set.html`.
- **Sessione Sudamerica (Argentina & Brasile)**:
  - Schedina Tripla di Continuità Sudamericana certificata a quota **@ 2.20** (Independiente 1X @ 1.32, Atletico Mineiro 1X @ 1.30, Internacional 1X @ 1.28).
  - File HTML interattivo: `reports/schedina_sudamerica.html`.

## 2. Infrastruttura & Canale Dual-Agent (MCP Team Bus)
- **Database**: `storage/database/team_bus.db` (`team_chat_bus` table con 15 messaggi totali registrati).
- **Mirror Markdown**: `docs/SHARED_CHAT.md` sincronizzato al 100%.
- **Messaggi recenti in attesa di ACK da Cursor**:
  - #12: Rettifica ufficiale quote reali Netwin.
  - #13: Proposta Schedina Nations League Lunedì 28/09.
  - #14: Azione Live 2° Tempi Domenica 27/09.
  - #15: Proposta Schedina Sudamerica (Argentina Liga Profesional & Brasileirão Série A).
- **Server Locale Attivo**: Porta 8080 (`http://localhost:8080/reports/`).

## 3. Direttive Operative
- Max 3-4 selezioni per ticket (Protocollo Continuità).
- Stake Kelly Frazionario max 5-8% del bankroll per singola schedina.
- Controllo rigoroso quote reali direttamente da Netwin (zero memoria parametrica o allucinazioni).
