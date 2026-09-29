"""
services/mcp/agent_bus_store.py — Storage e stato condiviso per il Bus di Comunicazione Agent-to-Agent.

Funge da repository persistente e thread/process-safe per:
- Task e direttive da Antigravity per Cursor;
- Report di esecuzione, commit git e stato modifiche da Cursor ad Antigravity;
- Richieste di chiarimento matematico/tattico (guidance);
- Snapshot di sistema (bankroll, quote live, test).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
BUS_FILE = DATA_DIR / "agent_bus.json"
BANKROLL_HISTORY_FILE = DATA_DIR / "bankroll_history.json"
LIVE_ODDS_FILE = DATA_DIR / "netwin_live_odds.json"
TICKETS_FILE = DATA_DIR / "active_user_tickets.json"


@dataclass
class BusMessage:
    id: str
    timestamp: str
    sender: str  # "Antigravity" | "Cursor" | "User"
    recipient: str  # "Cursor" | "Antigravity" | "All"
    message_type: str  # "TASK", "REPORT", "QUESTION", "ANSWER", "UPDATE"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTask:
    task_id: str
    created_at: str
    sender: str
    title: str
    instructions: str
    target_files: List[str] = field(default_factory=list)
    status: str = "PENDING"  # "PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED", "NEEDS_REVIEW"
    summary: str = ""
    modified_files: List[str] = field(default_factory=list)
    git_commit: str = ""
    notes_for_antigravity: str = ""
    updated_at: str = ""


class AgentBusStore:
    """Gestione atomica e persistente del file agent_bus.json."""

    def __init__(self, bus_file: Optional[Path] = None):
        self.bus_file = bus_file or BUS_FILE
        self.bus_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.bus_file.exists():
            self._save_raw({
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "active_task_id": None,
                "tasks": [],
                "messages": []
            })

    def _read_raw(self) -> Dict[str, Any]:
        """Legge lo stato raw dal JSON con retry per concorrenza."""
        for attempt in range(5):
            try:
                if not self.bus_file.exists():
                    return {"version": "1.0", "updated_at": datetime.now().isoformat(), "active_task_id": None, "tasks": [], "messages": []}
                with open(self.bus_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        return {"version": "1.0", "updated_at": datetime.now().isoformat(), "active_task_id": None, "tasks": [], "messages": []}
                    return json.loads(content)
            except (json.JSONDecodeError, OSError):
                time.sleep(0.05 * (attempt + 1))
        return {"version": "1.0", "updated_at": datetime.now().isoformat(), "active_task_id": None, "tasks": [], "messages": []}

    def _save_raw(self, data: Dict[str, Any]) -> None:
        """Scrittura atomica tramite file temporaneo per evitare corruzioni da processi concorrenti."""
        data["updated_at"] = datetime.now().isoformat()
        parent = self.bus_file.parent
        parent.mkdir(parents=True, exist_ok=True)
        
        # Scrivi prima su file temporaneo nella stessa cartella
        temp_file = parent / f".agent_bus_tmp_{os.getpid()}_{time.time_ns()}.json"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Rinomina atomica
            os.replace(temp_file, self.bus_file)
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    # --- TASK API ---

    def post_task(
        self,
        title: str,
        instructions: str,
        target_files: Optional[List[str]] = None,
        sender: str = "Antigravity",
    ) -> Dict[str, Any]:
        """Crea e imposta un nuovo task attivo per Cursor."""
        raw = self._read_raw()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        new_task = {
            "task_id": task_id,
            "created_at": now,
            "sender": sender,
            "title": title.strip(),
            "instructions": instructions.strip(),
            "target_files": target_files or [],
            "status": "PENDING",
            "summary": "",
            "modified_files": [],
            "git_commit": "",
            "notes_for_antigravity": "",
            "updated_at": now,
        }

        raw["tasks"].insert(0, new_task)
        raw["active_task_id"] = task_id

        # Aggiungi anche come messaggio sul bus
        msg_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]}"
        raw["messages"].append({
            "id": msg_id,
            "timestamp": now,
            "sender": sender,
            "recipient": "Cursor",
            "message_type": "TASK",
            "content": f"Nuovo task [{task_id}]: {title}",
            "metadata": {"task_id": task_id, "target_files": target_files or []}
        })

        self._save_raw(raw)
        return new_task

    def get_task(self, task_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Recupera un task specifico o l'ultimo task attivo/aperto."""
        raw = self._read_raw()
        tasks = raw.get("tasks", [])
        if not tasks:
            return None

        if task_id:
            for t in tasks:
                if t.get("task_id") == task_id:
                    return t
            return None

        # Cerca il task attivo esplicito
        active_id = raw.get("active_task_id")
        if active_id:
            for t in tasks:
                if t.get("task_id") == active_id:
                    return t

        # Altrimenti il primo non completato, oppure l'ultimo inserito
        for t in tasks:
            if t.get("status") in ("PENDING", "IN_PROGRESS", "NEEDS_REVIEW"):
                return t

        return tasks[0] if tasks else None

    def report_result(
        self,
        task_id: Optional[str],
        status: str,
        summary: str,
        modified_files: Optional[List[str]] = None,
        git_commit: Optional[str] = None,
        notes_for_antigravity: Optional[str] = None,
        sender: str = "Cursor",
    ) -> Dict[str, Any]:
        """Invia il report di completamento o aggiornamento di un task da Cursor ad Antigravity."""
        raw = self._read_raw()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_task = None

        if task_id:
            for t in raw.get("tasks", []):
                if t.get("task_id") == task_id:
                    target_task = t
                    break
        elif raw.get("active_task_id"):
            active_id = raw.get("active_task_id")
            for t in raw.get("tasks", []):
                if t.get("task_id") == active_id:
                    target_task = t
                    break

        if not target_task and raw.get("tasks"):
            target_task = raw["tasks"][0]

        if target_task:
            target_task["status"] = status.upper().strip()
            target_task["summary"] = summary.strip()
            if modified_files is not None:
                target_task["modified_files"] = modified_files
            if git_commit is not None:
                target_task["git_commit"] = git_commit.strip()
            if notes_for_antigravity is not None:
                target_task["notes_for_antigravity"] = notes_for_antigravity.strip()
            target_task["updated_at"] = now
            task_ref = target_task.get("task_id", "sconosciuto")
        else:
            task_ref = task_id or "generico"

        # Registra il messaggio sul bus
        msg_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]}"
        raw["messages"].append({
            "id": msg_id,
            "timestamp": now,
            "sender": sender,
            "recipient": "Antigravity",
            "message_type": "REPORT",
            "content": f"Report task [{task_ref}] - Stato: {status.upper()} | {summary}",
            "metadata": {
                "task_id": task_ref,
                "status": status.upper(),
                "modified_files": modified_files or [],
                "git_commit": git_commit or "",
                "notes": notes_for_antigravity or ""
            }
        })

        self._save_raw(raw)
        return target_task or {"task_id": task_ref, "status": status, "summary": summary}

    # --- GUIDANCE / MESSAGING API ---

    def ask_guidance(self, question: str, context: Optional[str] = None, sender: str = "Cursor") -> Dict[str, Any]:
        """Cursor pone una domanda matematica o architetturale ad Antigravity."""
        raw = self._read_raw()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]}"

        entry = {
            "id": msg_id,
            "timestamp": now,
            "sender": sender,
            "recipient": "Antigravity",
            "message_type": "QUESTION",
            "content": question.strip(),
            "metadata": {"context": (context or "").strip()}
        }
        raw["messages"].append(entry)
        self._save_raw(raw)
        return entry

    def post_message(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Invia un messaggio generico sul bus tra agenti."""
        raw = self._read_raw()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]}"

        entry = {
            "id": msg_id,
            "timestamp": now,
            "sender": sender,
            "recipient": recipient,
            "message_type": message_type.upper(),
            "content": content.strip(),
            "metadata": metadata or {}
        }
        raw["messages"].append(entry)
        self._save_raw(raw)
        return entry

    def list_messages(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Recupera gli ultimi N messaggi dal bus cronologico."""
        raw = self._read_raw()
        msgs = raw.get("messages", [])
        return msgs[-limit:]

    # --- SYSTEM SNAPSHOT API ---

    def get_system_snapshot(self, include_odds_summary: bool = True) -> Dict[str, Any]:
        """Fornisce a Cursor l'istantanea dello stato di BAgent."""
        snapshot: Dict[str, Any] = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "root_dir": str(ROOT_DIR),
            "bankroll": None,
            "active_tickets_count": 0,
            "live_odds_summary": {}
        }

        # 1. Bankroll reale da SQLite (PerformanceTracker)
        try:
            from services.database.performance_tracker import PerformanceTracker
            tracker = PerformanceTracker()
            snapshot["bankroll"] = {
                "balance_eur": tracker.get_current_bankroll(),
                "currency": "EUR"
            }
        except Exception:
            if BANKROLL_HISTORY_FILE.exists():
                try:
                    with open(BANKROLL_HISTORY_FILE, "r", encoding="utf-8") as f:
                        history = json.load(f)
                        if isinstance(history, list) and history:
                            snapshot["bankroll"] = history[-1]
                except Exception:
                    pass

        # 2. Ticket attivi
        if TICKETS_FILE.exists():
            try:
                with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                    t_data = json.load(f)
                    t_list = t_data.get("tickets", []) if isinstance(t_data, dict) else t_data
                    snapshot["active_tickets_count"] = len(t_list)
            except Exception:
                pass

        # 3. Live Odds
        if include_odds_summary and LIVE_ODDS_FILE.exists():
            try:
                with open(LIVE_ODDS_FILE, "r", encoding="utf-8") as f:
                    odds_data = json.load(f)
                    matches = odds_data.get("matches", [])
                    tournaments = {}
                    for m in matches:
                        t = m.get("tournament", "Altro")
                        tournaments[t] = tournaments.get(t, 0) + 1
                    snapshot["live_odds_summary"] = {
                        "timestamp": odds_data.get("timestamp"),
                        "total_matches": len(matches),
                        "tournaments": tournaments
                    }
            except Exception:
                pass

        return snapshot
