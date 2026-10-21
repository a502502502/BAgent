# Smoke checks

Quick local verification after a pull or before a session.

```bash
# 1. Dependencies
pip install -r requirements.txt
# optional: pip install -e ".[dev]"

# 2. Import smoke
python -c "from services.betting.strict_ticket_pipeline import StrictTicketPipeline; print('ok')"

# 3. Validator demo (no live bets)
python scripts/strict_validator.py --demo

# 4. Tests (subset already ignored in pytest.ini)
pytest tests/ -q --tb=no
```

If any step fails, fix before proposing tickets.
