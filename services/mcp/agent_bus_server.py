#!/usr/bin/env python3
"""
services/mcp/agent_bus_server.py — MCP Server Standard (JSON-RPC 2.0 via stdio) per Cursor.

Espone ad agenti esterni (incluso l'assistente AI di Cursor) gli strumenti nativi per:
- Ricevere task, direttive e formule matematiche da Antigravity;
- Notificare avanzamento, completamento, modifiche codice e commit Git;
- Chiedere consulenza architetturale o validazione xG in tempo reale;
- Ispezionare lo stato del sistema BAgent (bankroll, quote live, test).

Zero dipendenze esterne: basato sulla libreria standard di Python.
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Assicura encoding UTF-8 su Windows per stdin/stdout/stderr
if sys.platform == "win32":
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Root dir setup
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.mcp.agent_bus_store import AgentBusStore

# Configurazione logging ESCLUSIVAMENTE su stderr o file (stdout è riservato al protocollo JSON-RPC!)
LOG_FILE = ROOT_DIR / "data" / "agent_bus_mcp.log"
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("AgentBusMCP")


class AgentBusMcpServer:
    """Implementazione del server Model Context Protocol (MCP 2024-11-05)."""

    def __init__(self, store: Optional[AgentBusStore] = None):
        self.store = store or AgentBusStore()
        self.server_name = "bagent-bus"
        self.server_version = "1.0.0"
        self.protocol_version = "2024-11-05"

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Restituisce le specifiche dei tool registrati nel server MCP."""
        return [
            {
                "name": "antigravity_get_task",
                "description": (
                    "Recupera l'ultimo task o direttiva inviata da Antigravity a Cursor. "
                    "Include istruzioni dettagliate, file target da modificare, modelli matematici, quote e contesto."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID specifico del task da recuperare (opzionale; se omesso scarica l'ultimo task attivo/aperto)"
                        }
                    }
                }
            },
            {
                "name": "antigravity_report_result",
                "description": (
                    "Invia ad Antigravity il report di esecuzione o stato di un task svolto da Cursor. "
                    "Notifica lo stato (COMPLETED, IN_PROGRESS, BLOCKED, NEEDS_REVIEW), riepilogo delle modifiche, file toccati, hash commit git e note."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID del task a cui fa riferimento il report (opzionale se è il task attivo)"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["COMPLETED", "IN_PROGRESS", "BLOCKED", "NEEDS_REVIEW"],
                            "description": "Stato di avanzamento del task"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Sintesi chiara ed esaustiva di cosa è stato implementato o modificato"
                        },
                        "modified_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista dei percorsi dei file creati o modificati"
                        },
                        "git_commit": {
                            "type": "string",
                            "description": "Hash breve o messaggio del commit Git effettuato (es. '12545f0')"
                        },
                        "notes_for_antigravity": {
                            "type": "string",
                            "description": "Eventuali chiarimenti, dubbi sui modelli o richieste di test aggiuntivi per Antigravity"
                        }
                    },
                    "required": ["status", "summary"]
                }
            },
            {
                "name": "antigravity_ask_guidance",
                "description": (
                    "Pone una domanda diretta ad Antigravity su formule matematiche, xG Poisson, Dixon-Coles, "
                    "gestione mercati Netwin, o architettura del codice."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "La domanda o richiesta di consulenza per Antigravity"
                        },
                        "context": {
                            "type": "string",
                            "description": "Snippet di codice, quota o dettaglio del problema"
                        }
                    },
                    "required": ["question"]
                }
            },
            {
                "name": "bagent_get_system_state",
                "description": (
                    "Ispeziona lo stato reale e aggiornato del sistema BAgent: "
                    "bankroll attuale, numero ticket attivi e riepilogo quote live scaricate da Netwin."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_odds_summary": {
                            "type": "boolean",
                            "description": "Se includere il conteggio e dettaglio delle partite live in cache",
                            "default": True
                        }
                    }
                }
            },
            {
                "name": "debate_status",
                "description": (
                    "Legge lo stato di un dibattito live fra Cursor e Antigravity: "
                    "obiezioni misurate, replica e voto."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "debate_id": {
                            "type": "string",
                            "description": "ID del dibattito (debate_...)"
                        }
                    },
                    "required": ["debate_id"]
                }
            },
            {
                "name": "debate_rebut",
                "description": (
                    "Antigravity replica a una critica di Cursor. "
                    "LEG n: CONCEDE ritira la selezione. "
                    "LEG n: REPLACE market=\"...\" odd=1.40 la rimisura. "
                    "La prosa non cancella le obiezioni."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "debate_id": {"type": "string"},
                        "text": {
                            "type": "string",
                            "description": "Replica con una riga LEG per ogni selezione"
                        }
                    },
                    "required": ["debate_id", "text"]
                }
            },
            {
                "name": "debate_judge",
                "description": (
                    "Cursor vota l'ultima replica. Una selezione passa solo se il validatore "
                    "la firma dopo CONCEDE o REPLACE. Non prenota su Netwin."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "debate_id": {"type": "string"}
                    },
                    "required": ["debate_id"]
                }
            },
            {
                "name": "agent_bus_read_messages",
                "description": (
                    "Legge la cronologia dei messaggi scambiati tra Antigravity e Cursor sul canale di comunicazione."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Numero di messaggi recenti da leggere (default 10)",
                            "default": 10
                        }
                    }
                }
            }
        ]

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> str:
        """Esegue il tool MCP e restituisce il risultato formattato in formato testuale leggibile."""
        if name == "antigravity_get_task":
            task_id = arguments.get("task_id")
            task = self.store.get_task(task_id)
            if not task:
                return "ℹ️ Nessun task pendente trovato sul bus di Antigravity."
            
            lines = [
                f"📋 TASK DA ANTIGRAVITY: [{task.get('task_id')}]",
                f"• Titolo: {task.get('title')}",
                f"• Stato: {task.get('status')} | Inviato il: {task.get('created_at')}",
            ]
            if task.get("target_files"):
                lines.append(f"• File target: {', '.join(task['target_files'])}")
            lines.append("\n--- ISTRUZIONI DI DETTAGLIO ---")
            lines.append(task.get("instructions", "(nessuna istruzione fornita)"))
            return "\n".join(lines)

        elif name == "antigravity_report_result":
            task_id = arguments.get("task_id")
            status = arguments.get("status", "COMPLETED")
            summary = arguments.get("summary", "")
            modified_files = arguments.get("modified_files")
            git_commit = arguments.get("git_commit")
            notes = arguments.get("notes_for_antigravity")

            res = self.store.report_result(
                task_id=task_id,
                status=status,
                summary=summary,
                modified_files=modified_files,
                git_commit=git_commit,
                notes_for_antigravity=notes,
                sender="Cursor"
            )
            return (
                f"✅ Report inviato con successo ad Antigravity!\n"
                f"• Task ID: {res.get('task_id')}\n"
                f"• Stato registrato: {status.upper()}\n"
                f"• Riepilogo: {summary}\n"
                f"Antigravity analizzerà il report e verificherà le modifiche."
            )

        elif name == "antigravity_ask_guidance":
            q = arguments.get("question", "")
            ctx = arguments.get("context", "")
            res = self.store.ask_guidance(q, context=ctx, sender="Cursor")
            return (
                f"📨 Domanda inviata con successo ad Antigravity (ID: {res.get('id')})!\n"
                f"Domanda: {q}\n"
                f"Antigravity risponderà al prossimo turno di elaborazione sul bus."
            )

        elif name == "bagent_get_system_state":
            inc_odds = arguments.get("include_odds_summary", True)
            snapshot = self.store.get_system_snapshot(include_odds_summary=inc_odds)
            return json.dumps(snapshot, indent=2, ensure_ascii=False)

        elif name == "debate_status":
            from services.debate.live_exchange import LiveTicketDebate

            debate_id = arguments.get("debate_id", "")
            debate = LiveTicketDebate(store=self.store).store.get_debate(debate_id)
            if debate is None:
                return f"Nessun dibattito {debate_id} sul bus."
            turns = debate.get("turns") or []
            last = turns[-1]["content"] if turns else ""
            return (
                f"{debate.get('debate_id')} [{debate.get('status')}] {debate.get('title')}\n\n"
                f"{last}"
            )

        elif name == "debate_rebut":
            from services.debate.live_exchange import LiveTicketDebate

            debate = LiveTicketDebate(store=self.store).rebut(
                arguments.get("debate_id", ""),
                arguments.get("text", ""),
            )
            return (
                f"Replica registrata su {debate.get('debate_id')}. "
                f"Stato: {debate.get('status')}. In attesa del voto di Cursor."
            )

        elif name == "debate_judge":
            from services.debate.live_exchange import LiveTicketDebate

            debate = LiveTicketDebate(store=self.store).judge(arguments.get("debate_id", ""))
            turns = debate.get("turns") or []
            return turns[-1]["content"] if turns else debate.get("status", "")

        elif name == "agent_bus_read_messages":
            limit = int(arguments.get("limit", 10))
            msgs = self.store.list_messages(limit=limit)
            if not msgs:
                return "ℹ️ Il bus non contiene ancora messaggi registrati."
            
            lines = [f"📜 ULTIMI {len(msgs)} MESSAGGI SUL BUS TRA ANTIGRAVITY E CURSOR:\n"]
            for m in msgs:
                lines.append(f"[{m.get('timestamp')}] {m.get('sender')} -> {m.get('recipient')} ({m.get('message_type')}):")
                lines.append(f"  {m.get('content')}")
            return "\n".join(lines)

        else:
            raise ValueError(f"Tool sconosciuto: {name}")

    def dispatch(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Elabora un messaggio JSON-RPC 2.0 e restituisce la risposta (o None per le notifiche)."""
        method = request.get("method")
        msg_id = request.get("id")
        params = request.get("params", {})

        # Notifiche: nessuna risposta richiesta
        if method == "notifications/initialized":
            logger.info("Client MCP ha completato l'inizializzazione.")
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": self.server_name,
                        "version": self.server_version
                    }
                }
            }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": self.get_tool_definitions()
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                text_result = self.handle_tool_call(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": text_result
                            }
                        ],
                        "isError": False
                    }
                }
            except Exception as e:
                logger.error(f"Errore esecuzione tool '{tool_name}': {e}", exc_info=True)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ Errore esecuzione tool '{tool_name}': {str(e)}"
                            }
                        ],
                        "isError": True
                    }
                }

        else:
            # Metodo non supportato
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: '{method}'"
                }
            }

    def run_stdio(self):
        """Loop di ascolto continuo su stdio per il protocollo MCP."""
        logger.info("Avvio AgentBusMcpServer in ascolto su stdin/stdout...")
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] AgentBusMcpServer running on stdio (PID: {os.getpid()})\n")
        sys.stderr.flush()

        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError as err:
                logger.error(f"JSON non valido ricevuto: {err}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(err)}"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
                continue

            try:
                response = self.dispatch(request)
                if response is not None:
                    response_json = json.dumps(response, ensure_ascii=False)
                    sys.stdout.write(response_json + "\n")
                    sys.stdout.flush()
            except Exception as err:
                logger.error(f"Errore non gestito in dispatch: {err}", exc_info=True)
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(err)}"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()


def main():
    server = AgentBusMcpServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
