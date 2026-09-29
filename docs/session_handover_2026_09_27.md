# Session Handover — Domenica 27 Settembre 2026 (Pre-Match)

## 1. Bankroll
- **Saldo ledger** (26/09 22:42): **€149.19**
- Max stake ticket (Gate 8, 8%): **≈ €11.90**
- Max sessione 15%: ≈ €22.40
- Ieri 26/09: **NO BET** corretto (Under/Over a edge negativo su Netwin). Capitale preservato.

## 2. Perno Certificato (audit 26/09 19:06)
| Match | KO | Mercato | Netwin | P motore | Fair | Edge | Gate |
|---|---|---|---|---|---|---|---|
| **Serbia vs Olanda** | 18:00 | **X2** | **1.37** (2@1.41) | **88.5%** | 1.13 | **+21.3%** | 🟢 CERTIFICATO |

- File: `data/tickets/nl_sun27_audit.json`
- xG Dixon-Coles (OddsAPI 1X2+O2.5): **0.80 – 2.25**
- Gate 0: 2 fisso @ 1.41 **vietato**; si gioca solo X2.
- Anteprima lunedì già ok in lab: Belgio–Francia X2 @ 1.82 (P 73.1%, Edge +33.1%) — **non mescolare** con ticket di domenica.

## 3. Compagni — NON certificati (vietato appendere a braccio)
Scan 26/09 ha **bocciato** le linee convenzionali:

| Match | Mercato Netwin | Edge motore | Motivo |
|---|---|---|---|
| Germania–Grecia | 1 @ 1.40 | — | Gate 0 |
| Germania–Grecia | Over 2.5 @ 1.46 | −7.1% | Gate 6 |
| Germania–Grecia | Under 3.5 @ 1.63 | −4.3% / P 58.7% | Gate 6 + floor 72% |
| Norvegia–Portogallo | Gol @ 1.43 | −6.0% | Gate 6 |
| Norvegia–Portogallo | Over 2.5 @ 1.48 | −5.4% | Gate 6 |
| Norvegia–Portogallo | 1X @ 1.45 | −10.0% | Gate 6 |
| Danimarca–Galles | 1 @ 1.48 | — | Gate 0 |
| Danimarca–Galles | Over 1.5 @ 1.23 | −3.9% | Gate 6 |
| Austria–Kosovo | Over 1.5 @ 1.24 | −5.2% | Gate 6 |

**Obiettivo mattina**: OmniMarketScanner + Netwin refresh su GER/NOR/DEN/AUT. Solo mercati con Edge ≥ +4% e P ≥ 72%. Se nessuno passa → **singola secca** Serbia–Olanda X2.

## 4. Protocollo Mattina (ordine ferreo)
1. `download_netwin_odds.py` su Nations League (quote possono muoversi).
2. Se X2 Olanda scende e Edge < +4% → **abort** o ricalibra.
3. `scan_omni_markets` / StrictTicketPipeline su 2–3 candidati compagni (max 3 selezioni totali).
4. `strict_validator.py --ticket-json` → solo se 🟢 CERTIFICATO ED APPROVATO.
5. Target quota combinata **1.85–2.40×** solo se i compagni sono certificati; altrimenti singola @ 1.37.
6. Zero player props (Regola #37/#49). Zero citazioni nominative non auditate.
7. Telegram: token ancora da refresh BotFather se serve push.

## 5. Cosa NON fare
- Non giocare 1 fisso Germania/Danimarca/Austria.
- Non forzare Over/BTTS su Norvegia–Portogallo a quote Netwin attuali.
- Non costruire tripla “narrativa” senza certificato.
