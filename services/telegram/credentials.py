"""
Credenziali Telegram centralizzate — mai token hardcoded nei moduli/script.

Legge solo da environment / .env:
  TELEGRAM_TOKEN
  TELEGRAM_CHAT_ID
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def get_telegram_credentials(
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> Tuple[str, str]:
    """Restituisce (token, chat_id) risolti; stringhe vuote se mancanti."""
    resolved_token = (token or TELEGRAM_TOKEN or "").strip()
    resolved_chat = (chat_id or TELEGRAM_CHAT_ID or "").strip()
    return resolved_token, resolved_chat


def require_telegram_credentials(
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> Tuple[str, str]:
    """Come get_*, ma solleva RuntimeError se token o chat_id mancano."""
    resolved_token, resolved_chat = get_telegram_credentials(token, chat_id)
    if not resolved_token or not resolved_chat:
        raise RuntimeError(
            "TELEGRAM_TOKEN / TELEGRAM_CHAT_ID mancanti. "
            "Impostali in .env (mai in chiaro nel codice)."
        )
    return resolved_token, resolved_chat
