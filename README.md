# BAgent

**Quantitative sports betting system focused on football (calcio).**

BAgent is an AI-first, rule-driven engine for bankroll management and value betting.  
It prioritises data (Poisson / Dixon-Coles, xG, certified rosters) over gut feeling and bookmaker traps.

> Tennis was abolished on 22 September 2026. Only football remains in scope.

---

## Core principles

- **No rigid 1X2** — pure match result or rigid "1 + Over" combos are forbidden.  
  Preference for flow markets that absorb variance: MultiGol tempi, Chance Mix, Over 0.5 both halves, open MultiGol (1-5 / 2-5).
- **Core-Satellite portfolio (70/30)**  
  - 70% bankroll → low-risk "Cassaforte" tickets (target odds ~2.40–3.20x)  
  - 30% → props, gems and higher-odds satellites
- **Strict bankroll rules** — max 8% per ticket, 5–8% fractional Kelly, max 15% session risk. No loss chasing.
- **Reality Gate** — every player, coach and squad must be verified against the current 2026/27 season. Stale memory is forbidden.
- **Edge is informative** — probabilities come from data, never from odds alone. Negative / low edge is a warning, not an automatic skip.

**Rules index:** [`docs/RULES.md`](docs/RULES.md)  
**Full operational constraints:** `CLAUDE.md` and `.cursorrules`

---

## Quick start

```bash
# 1. Clone & install
git clone https://github.com/a502502502/BAgent.git
cd BAgent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure secrets (never commit .env)
cp .env.example .env        # if present, or create your own
# Fill API keys, Telegram token, etc.

# 3. Entry points
python main.py              # lightweight entry / pipeline hint
python run_bagent_full.py   # controller (DB + scanner + live + Telegram wiring)
```

Certificate a ticket before playing:

```bash
python scripts/strict_validator.py --demo
```

---

## Repository layout (high level)

| Path | Role |
|------|------|
| `analyzer/` | OFP engine (Oddspedia / Forebet / Pengwin convergence) |
| `application/` | Use-cases, analyzers, factors, validation |
| `domain/` | Core domain models |
| `services/` | Football engines, live, betting pipeline, notifications, data loaders |
| `scripts/` | Operational scripts (scanner, validator, reality gate, Telegram…) |
| `data/` | Runtime data (mostly gitignored; some mirrors kept) |
| `storage/` | SQLite ledger and persistence |
| `portal/` / `web_mobile/` | Live ticket portal |
| `docs/` | Rules index, architecture, handovers, archive |
| `tests/` | Unit / property / harness tests |
| `harness/` | Contracts, HTTP replay, calibration |

---

## Key operational scripts

- `scripts/strict_validator.py` — mandatory certificate before any ticket is considered playable
- `scripts/build_verified_ticket.py` — full pipeline (roster → injuries → lineups → probability → edge → Kelly)
- Reality Gate & roster hygiene under `scripts/` and `services/football/`
- Telegram daemon / alerts

See [`docs/RULES.md`](docs/RULES.md) for the numbered rules index and `CLAUDE.md` for the full text.

---

## Development notes

- Database path: `data/bagent.db` (WAL mode). Run `PRAGMA wal_checkpoint` before heavy use.
- Odds snapshot sources: `data/netwin_live_odds.json` and related caches.
- Never commit `.env` or real secrets.
- Prefer path-relative imports from project root.
- Do not hard-code match slates or squads: always use certified feeds (Reality Gate).

---

## License

MIT — see `LICENSE`.
