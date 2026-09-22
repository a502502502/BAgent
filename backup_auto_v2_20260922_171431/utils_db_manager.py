import sqlite3
import time
from functools import wraps
from typing import Any, Callable

def get_robust_connection(db_path: str) -> sqlite3.Connection:
    """Restituisce una connessione SQLite ottimizzata per la concorrenza e la robustezza."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn

def db_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator per ritentare le operazioni DB con backoff esponenziale."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    raise
        return wrapper
    return decorator
