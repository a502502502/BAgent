# BAgent architecture (short)

Active scope: **football only**.

## Layers

| Layer | Role |
|-------|------|
| `domain/` | Core models |
| `application/` | Use-cases, factors, historical validation |
| `services/football/` | Probability, ratings, Reality Gate, loaders |
| `services/betting/` | Strict ticket pipeline |
| `analyzer/` | OFP convergence structure (Oddspedia / Forebet / Pengwin) |
| `scripts/` | Operational entry scripts (validator, scanners, Telegram) |
| `storage/` + `data/` | SQLite ledger and runtime snapshots |
| `portal/` | Public ticket view |

## Rules of the road

- Source of truth for rules: `GEMINI.md`
- Navigable index: `docs/RULES.md`
- No rigid 1X2. Prefer flow markets.
- Every playable ticket must pass `scripts/strict_validator.py`.
- No hard-coded match slates or squads. Reality Gate only.

## Entry points

- `python main.py` — lightweight hint
- `python run_bagent_full.py` — controller (DB + scanner + live + Telegram wiring)
- `python scripts/strict_validator.py --demo` — certificate demo

## Checks

See `docs/SMOKE.md` for local smoke commands.
