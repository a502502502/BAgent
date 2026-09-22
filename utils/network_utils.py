import requests
import time
from functools import wraps
import logging

logger = logging.getLogger("BAgent_Network")

def retry_network_request(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator per ritentare le richieste di rete in caso di fallimenti transitori."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    response = func(*args, **kwargs)
                    response.raise_for_status()
                    return response
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Fallimento rete definitivo dopo {max_retries} tentativi: {e}")
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Tentativo {attempt + 1}/{max_retries} fallito. Attesa {wait_time}s...")
                    time.sleep(wait_time)
        return wrapper
    return decorator
