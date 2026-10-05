"""Avvia il server MCP Sportmicro. La chiave si legge da .env."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def main() -> int:
    key = os.getenv("SPORTMICRO_API_KEY", "").strip()
    if not key:
        print("SPORTMICRO_API_KEY assente in .env", file=sys.stderr)
        return 1
    npx = shutil.which("npx")
    if npx is None:
        print("npx non trovato", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["SPORTMICRO_API_KEY"] = key
    return subprocess.call([npx, "-y", "@sportmicro/sportmicro-mcp-server"], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
