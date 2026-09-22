"""Path e costanti di progetto — unica fonte per ROOT/DATA/sessioni."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "data"
OUTPUT = ROOT / "output"
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports"
CACHE = DATA / "cache"

# DB: preferire bagent.db (ledger ufficiale); matches.db resta legacy
DATABASE = DATA / "bagent.db"
MATCHES_DB = DATA / "matches.db"

# Profilo Chromium persistente Netwin (login ADM)
NETWIN_SESSION_DIR = DATA / "netwin_session"
NETWIN_URL = "https://www.netwin.it/scommesse"
NETWIN_RECEIPTS_DIR = REPORTS / "receipts"

TIMEOUT = 20

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/138.0 Safari/537.36"
)

# Sport ammesso (Regola Suprema 22/09/2026)
ALLOWED_SPORT = "football"
TENNIS_BANNED = True
