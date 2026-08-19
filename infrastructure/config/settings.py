from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "data"

OUTPUT = ROOT / "output"

LOGS = ROOT / "logs"

CACHE = DATA / "cache"

DATABASE = DATA / "matches.db"

TIMEOUT = 20

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/138.0 Safari/537.36"
)