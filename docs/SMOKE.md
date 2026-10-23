# 🛡️ BAgent Smoke Checks (Protocollo di Verifica Pre-Volo 2026/27)

Verifica locale rapida dopo ogni pull o all'inizio di ogni sessione operativa.
Tutti e quattro i comandi devono restituire esito positivo (`exit code 0`).

```bash
# 1. Verifica integrità Downloader Netwin (>20 KB, import pulito)
python -c "from services.betting.netwin_odds_downloader import NetwinOddsDownloader; print('Downloader OK')"

# 2. Strict Validator Demo (Audit dei casi limite e hard gates)
python scripts/strict_validator.py --demo

# 3. Esportazione Snapshot Certificato da bagent.db
python scripts/export_certified_snapshot.py

# 4. Pipeline Giornaliera Unificata (Esecuzione completa deterministica)
python scripts/run_today.py --skip-download
```

### 📌 Note Operative
* **Live Loop:** Il loop background di `run_bagent_full.py` deve rimanere **spento** finché non sarà integrato un feed live reale autenticato.
* **Refertazione:** A fine partite, eseguire `python scripts/post_match_settlement.py` per registrare gli esiti in `bet_leg_ledger` e monitorare l'hit rate.
* Se un comando fallisce, correggere l'errore prima di proporre qualsiasi schedina.
