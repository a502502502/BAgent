#!/usr/bin/env python3
"""
scripts/sync_to_drive_supervisor.py — Ponte di Sincronizzazione Google Drive (Architettura 1).

Copia in tempo reale i file chiave di stato e configurazione di BAgent nella cartella
'BAgent_Supervisor' su Google Drive, consentendo ai supervisori AI esterni (Claude,
Gemini, ChatGPT) di leggere direttamente i file in chiaro a Zero Costo & Zero Token Drain.

File sincronizzati:
- portal/schedine.json
- SNAPSHOT_OGGI.json
- data/daily_reality_snapshot.json
- data/active_user_tickets.json
- CLAUDE.md
- sync_manifest.json (metadati e timestamp)
"""

import os
import sys
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent

CANDIDATE_DRIVE_ROOTS = [
    Path("G:/My Drive"),
    Path("C:/Users/demarj/Google Drive"),
    Path("C:/Users/demarj/Google Drive/BAgent"),
]

ENV_DRIVE_PATH = os.getenv("GOOGLE_DRIVE_PATH")
if ENV_DRIVE_PATH:
    CANDIDATE_DRIVE_ROOTS.insert(0, Path(ENV_DRIVE_PATH))

FILES_TO_SYNC: List[Tuple[str, str]] = [
    ("portal/schedine.json", "schedine.json"),
    ("portal/schedine.html", "schedine.html"),
    ("portal/android.html", "android.html"),
    ("SNAPSHOT_OGGI.json", "SNAPSHOT_OGGI.json"),
    ("data/daily_reality_snapshot.json", "daily_reality_snapshot.json"),
    ("data/active_user_tickets.json", "active_user_tickets.json"),
    ("CLAUDE.md", "CLAUDE.md"),
]


def compute_file_hash(path: Path) -> str:
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_target_directories() -> List[Path]:
    targets = []
    seen = set()
    for root in CANDIDATE_DRIVE_ROOTS:
        if root.exists():
            resolved = root.resolve()
            # Se siamo su G:/My Drive creiamo G:/My Drive/BAgent_Supervisor
            target_dir = resolved / "BAgent_Supervisor"
            if str(target_dir) not in seen:
                seen.add(str(target_dir))
                targets.append(target_dir)
    return targets


def sync_files():
    targets = find_target_directories()
    if not targets:
        print("[AVVISO] Nessun percorso Google Drive trovato tra quelli configurati.")
        return False

    now_iso = datetime.now().isoformat()
    manifest_data = {
        "sync_time": now_iso,
        "files": {},
        "status": "SYNCED"
    }

    synced_any = False
    for target_dir in targets:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"[SYNC] Destinazione Drive: {target_dir}")

        for rel_src, dest_name in FILES_TO_SYNC:
            src_path = ROOT / rel_src
            dest_path = target_dir / dest_name

            if src_path.exists():
                shutil.copy2(src_path, dest_path)
                file_hash = compute_file_hash(dest_path)
                file_size = dest_path.stat().st_size
                manifest_data["files"][dest_name] = {
                    "source": rel_src,
                    "size_bytes": file_size,
                    "md5": file_hash,
                    "last_modified": datetime.fromtimestamp(dest_path.stat().st_mtime).isoformat()
                }
                print(f"  -> Copiato: {dest_name} ({file_size} bytes)")
                synced_any = True
            else:
                print(f"  [OMESSO] File sorgente assente: {rel_src}")

        manifest_file = target_dir / "sync_manifest.json"
        manifest_file.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  -> Scritto manifest: {manifest_file.name}")

    return synced_any


def main():
    print("=" * 80)
    print("BAGENT — SINCRONIZZAZIONE GOOGLE DRIVE PER SUPERVISORE ESTERNO")
    print("=" * 80)
    success = sync_files()
    if success:
        print("\nSincronizzazione completata con successo.")
        sys.exit(0)
    else:
        print("\nNessun file sincronizzato.")
        sys.exit(1)


if __name__ == "__main__":
    main()
