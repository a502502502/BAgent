#!/usr/bin/env python3
"""
scripts/agent_bus.py — CLI per il Bus di Comunicazione tra Antigravity e Cursor.

Uso:
    # 1. Antigravity posta un nuovo task per Cursor:
    python scripts/agent_bus.py post-task --title "Refactoring parser mercati" --instructions "Aggiungi supporto a DNB" --files "services/betting/netwin_cache_reader.py"

    # 2. Mostra lo stato del task attivo:
    python scripts/agent_bus.py get-task

    # 3. Cursor (o script) invia un report di completamento:
    python scripts/agent_bus.py report --status COMPLETED --summary "Mercati DNB integrati e test superati" --commit "12545f0"

    # 4. Mostra lo storico dei messaggi sul bus:
    python scripts/agent_bus.py log

    # 5. Invia un messaggio/domanda sul bus:
    python scripts/agent_bus.py send-message --from Antigravity --to Cursor --text "Qual è lo status del commit?"

    # 6. Mostra lo snapshot di sistema di BAgent:
    python scripts/agent_bus.py system-state
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# UTF-8 su Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.mcp.agent_bus_store import AgentBusStore


def cmd_post_task(args, store: AgentBusStore):
    files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else []
    task = store.post_task(
        title=args.title,
        instructions=args.instructions,
        target_files=files,
        sender=args.sender,
    )
    print("=" * 75)
    print(f"🚀 TASK PUBBLICATO SUL BUS! [ID: {task['task_id']}]")
    print("=" * 75)
    print(f"• Titolo: {task['title']}")
    print(f"• Mittente: {task['sender']}")
    print(f"• Data: {task['created_at']}")
    if files:
        print(f"• File target: {', '.join(files)}")
    print("\n--- ISTRUZIONI PER CURSOR ---")
    print(task['instructions'])
    print("=" * 75)

    if getattr(args, "wait", False):
        cmd_wait_for_report(args, store, task_id=task['task_id'])


def cmd_wait_for_report(args, store: AgentBusStore, task_id: Optional[str] = None):
    target_id = task_id or getattr(args, "task_id", None)
    timeout = getattr(args, "timeout", 120)
    interval = getattr(args, "interval", 2)
    start_t = time.time()

    label = f"sul task [{target_id}]" if target_id else "sull'ultimo task attivo"
    print(f"\n⏳ Attesa sincrona della verifica da Cursor via MCP {label} (timeout: {timeout}s)...")

    while time.time() - start_t < timeout:
        task = store.get_task(task_id=target_id)
        if task and task.get("status") in ["COMPLETED", "BLOCKED", "NEEDS_REVIEW", "REJECTED"]:
            print("\n" + "=" * 75)
            print(f"🎯 VERIFICA RICEVUTA DA CURSOR! [Stato: {task.get('status')}]")
            print("=" * 75)
            print(f"• Summary: {task.get('summary')}")
            if task.get("git_commit"):
                print(f"• Commit Git: {task.get('git_commit')}")
            if task.get("notes_for_antigravity"):
                print(f"• Note per Antigravity: {task.get('notes_for_antigravity')}")
            print("=" * 75)
            return 0
        time.sleep(interval)

    print(f"\n⏱️ TIMEOUT ({timeout}s): Cursor non ha ancora inviato un report di verifica.")
    print("Il task rimane salvato sul bus in stato PENDING per essere letto con 'antigravity_get_task'.")
    return 1


def cmd_get_task(args, store: AgentBusStore):
    task = store.get_task(task_id=args.task_id)
    if not task:
        print("ℹ️ Nessun task pendente trovato nel bus.")
        return

    print("=" * 75)
    print(f"📋 DETTAGLIO TASK: [{task.get('task_id')}]")
    print("=" * 75)
    print(f"• Titolo: {task.get('title')}")
    print(f"• Stato: {task.get('status')} | Mittente: {task.get('sender')}")
    print(f"• Creato il: {task.get('created_at')} | Aggiornato: {task.get('updated_at')}")
    if task.get("target_files"):
        print(f"• File target: {', '.join(task['target_files'])}")
    if task.get("summary"):
        print(f"• Ultimo report ({task.get('status')}): {task['summary']}")
    if task.get("git_commit"):
        print(f"• Git commit: {task['git_commit']}")
    if task.get("notes_for_antigravity"):
        print(f"• Note per Antigravity: {task['notes_for_antigravity']}")
    print("\n--- ISTRUZIONI ---")
    print(task.get("instructions", ""))
    print("=" * 75)


def cmd_report(args, store: AgentBusStore):
    files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else None
    res = store.report_result(
        task_id=args.task_id,
        status=args.status,
        summary=args.summary,
        modified_files=files,
        git_commit=args.commit,
        notes_for_antigravity=args.notes,
        sender=args.sender,
    )
    print("=" * 75)
    print(f"✅ REPORT REGISTRATO SUL BUS! [Task ID: {res.get('task_id')}]")
    print("=" * 75)
    print(f"• Stato: {res.get('status')}")
    print(f"• Riepilogo: {res.get('summary')}")
    if res.get("git_commit"):
        print(f"• Git commit: {res.get('git_commit')}")
    if res.get("modified_files"):
        print(f"• File modificati: {', '.join(res.get('modified_files'))}")
    if res.get("notes_for_antigravity"):
        print(f"• Note: {res.get('notes_for_antigravity')}")
    print("=" * 75)


def cmd_log(args, store: AgentBusStore):
    msgs = store.list_messages(limit=args.limit)
    print("=" * 75)
    print(f"📜 CRONOLOGIA BUS AGENTI ({len(msgs)} messaggi recenti)")
    print("=" * 75)
    if not msgs:
        print("ℹ️ Nessun messaggio registrato.")
        return

    for m in msgs:
        sender = m.get("sender", "?")
        recipient = m.get("recipient", "?")
        m_type = m.get("message_type", "MSG")
        ts = m.get("timestamp", "")
        print(f"[{ts}] {sender} ➔ {recipient} ({m_type}):")
        print(f"  {m.get('content')}")
        if m.get("metadata"):
            meta_str = ", ".join([f"{k}: {v}" for k, v in m["metadata"].items() if v])
            if meta_str:
                print(f"  ↳ [meta] {meta_str}")
        print("-" * 75)


def cmd_send_message(args, store: AgentBusStore):
    entry = store.post_message(
        sender=args.sender,
        recipient=args.to,
        message_type=args.type,
        content=args.text,
    )
    print(f"📨 Messaggio registrato sul bus (ID: {entry['id']}): {args.sender} -> {args.to}")


def cmd_system_state(args, store: AgentBusStore):
    snapshot = store.get_system_snapshot(include_odds_summary=True)
    print("=" * 75)
    print("📊 STATO ATTUALE DEL SISTEMA BAGENT")
    print("=" * 75)
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Agent Bus CLI (Antigravity ↔ Cursor)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # post-task
    p_task = subparsers.add_parser("post-task", help="Invia un task per Cursor")
    p_task.add_argument("--title", required=True, type=str, help="Titolo del task")
    p_task.add_argument("--instructions", required=True, type=str, help="Istruzioni dettagliate")
    p_task.add_argument("--files", type=str, default="", help="File target separati da virgola")
    p_task.add_argument("--sender", type=str, default="Antigravity", help="Mittente del task")
    p_task.add_argument("--wait", action="store_true", help="Attende sincronicamente il report di verifica di Cursor")
    p_task.add_argument("--timeout", type=int, default=120, help="Secondi massimi di attesa in modalità sincrona (default: 120)")
    p_task.add_argument("--interval", type=int, default=2, help="Secondi tra un polling e l'altro (default: 2)")

    # wait-for-report
    p_wait = subparsers.add_parser("wait-for-report", help="Attende il report di Cursor su un task")
    p_wait.add_argument("--task-id", type=str, default=None, help="ID specifico del task (default: ultimo attivo)")
    p_wait.add_argument("--timeout", type=int, default=120, help="Secondi massimi di attesa (default: 120)")
    p_wait.add_argument("--interval", type=int, default=2, help="Secondi tra i controlli (default: 2)")

    # get-task
    p_get = subparsers.add_parser("get-task", help="Mostra l'ultimo task attivo")
    p_get.add_argument("--task-id", type=str, default=None, help="ID specifico del task")

    # report
    p_rep = subparsers.add_parser("report", help="Invia un report di avanzamento o completamento")
    p_rep.add_argument("--status", required=True, type=str, choices=["COMPLETED", "IN_PROGRESS", "BLOCKED", "NEEDS_REVIEW"])
    p_rep.add_argument("--summary", required=True, type=str, help="Riepilogo delle modifiche")
    p_rep.add_argument("--task-id", type=str, default=None, help="ID del task")
    p_rep.add_argument("--files", type=str, default="", help="File modificati separati da virgola")
    p_rep.add_argument("--commit", type=str, default="", help="Hash o messaggio del commit Git")
    p_rep.add_argument("--notes", type=str, default="", help="Note per Antigravity")
    p_rep.add_argument("--sender", type=str, default="Cursor", help="Mittente del report")

    # log
    p_log = subparsers.add_parser("log", help="Mostra lo storico dei messaggi sul bus")
    p_log.add_argument("--limit", type=int, default=15, help="Limite messaggi")

    # send-message
    p_msg = subparsers.add_parser("send-message", help="Invia un messaggio generico sul bus")
    p_msg.add_argument("--sender", "--from", dest="sender", default="Antigravity", help="Mittente")
    p_msg.add_argument("--to", default="Cursor", help="Destinatario")
    p_msg.add_argument("--type", default="UPDATE", help="Tipo messaggio (TASK, REPORT, QUESTION, UPDATE)")
    p_msg.add_argument("--text", required=True, help="Testo del messaggio")

    # system-state
    subparsers.add_parser("system-state", help="Mostra lo snapshot del sistema BAgent")

    args = parser.parse_args()
    store = AgentBusStore()

    if args.command == "post-task":
        cmd_post_task(args, store)
    elif args.command == "get-task":
        cmd_get_task(args, store)
    elif args.command == "report":
        cmd_report(args, store)
    elif args.command == "wait-for-report":
        cmd_wait_for_report(args, store)
    elif args.command == "log":
        cmd_log(args, store)
    elif args.command == "send-message":
        cmd_send_message(args, store)
    elif args.command == "system-state":
        cmd_system_state(args, store)


if __name__ == "__main__":
    main()
