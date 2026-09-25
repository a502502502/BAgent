"""Pubblica l'archivio su GitHub Pages quando le schedine cambiano.

La pagina online ricontrolla schedine.json ogni 30 secondi. Questo script
riscrive quel file e, con --watch, ripete il controllo allo stesso ritmo.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.portal.slip_archive import (  # noqa: E402
    CHECK_SECONDS,
    PUBLIC_SITE,
    archive_payload,
    load_slips,
    write_slip_archive,
)


def _now() -> datetime:
    return datetime.now(ZoneInfo("Europe/Rome"))


def _body(payload: dict) -> dict:
    body = dict(payload)
    body.pop("generated_at", None)
    return body


def publish_once() -> str:
    if not (PUBLIC_SITE / ".git").exists():
        raise SystemExit(f"Sito pubblico assente: {PUBLIC_SITE}")
    fresh = _body(archive_payload(load_slips(), _now()))
    current_json = PUBLIC_SITE / "schedine.json"
    current_html = PUBLIC_SITE / "index.html"
    same_data = False
    if current_json.exists():
        old = json.loads(current_json.read_text(encoding="utf-8"))
        same_data = _body(old) == fresh
    shell = current_html.read_text(encoding="utf-8") if current_html.exists() else ""
    same_shell = "Chiedi schedina" in shell and "schedine.json?t=" in shell
    if same_data and same_shell:
        return "invariato"
    write_slip_archive(PUBLIC_SITE / "index.html")
    write_slip_archive()
    _git("add", "index.html", "schedine.json")
    if _git("diff", "--cached", "--quiet") == 0:
        return "invariato"
    message = PUBLIC_SITE / "_commit_msg.txt"
    message.write_text("Aggiorna presenti, future e passate.\n", encoding="utf-8")
    try:
        committed = _git("commit", "-F", str(message))
    finally:
        message.unlink(missing_ok=True)
    if committed != 0:
        raise SystemExit("commit non riuscito")
    if _git("push", "origin", "HEAD") != 0:
        raise SystemExit("push non riuscito")
    return "pubblicato"


def _git(*args: str) -> int:
    result = subprocess.run(["git", *args], cwd=PUBLIC_SITE)
    return result.returncode


def main() -> None:
    watch = "--watch" in sys.argv
    while True:
        try:
            print(publish_once(), flush=True)
        except SystemExit:
            raise
        if not watch:
            return
        time.sleep(CHECK_SECONDS)


if __name__ == "__main__":
    main()
