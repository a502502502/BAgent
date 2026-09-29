"""
tests/test_agent_bus.py — Unit test per AgentBusStore e AgentBusMcpServer.

Verifica che il bus di comunicazione tra Antigravity e Cursor funzioni
perfettamente in tutti i casi d'uso (task, report, domande, stato di sistema,
protocollo JSON-RPC 2.0).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.mcp.agent_bus_server import AgentBusMcpServer
from services.mcp.agent_bus_store import AgentBusStore


@pytest.fixture
def bus_store(tmp_path):
    bus_file = tmp_path / "test_agent_bus.json"
    return AgentBusStore(bus_file=bus_file)


@pytest.fixture
def mcp_server(bus_store):
    return AgentBusMcpServer(store=bus_store)


def test_post_and_get_task(bus_store):
    # Nessun task inizialmente
    assert bus_store.get_task() is None

    # Invia task
    task = bus_store.post_task(
        title="Implementa calibrazione Dixon-Coles per 1°T",
        instructions="Usa fattore scala 0.44 sugli xG e testa le quote",
        target_files=["services/analysis/combo_book_search.py"],
        sender="Antigravity",
    )

    assert task["task_id"].startswith("task_")
    assert task["status"] == "PENDING"
    assert task["title"] == "Implementa calibrazione Dixon-Coles per 1°T"

    # Recupera task attivo
    active = bus_store.get_task()
    assert active is not None
    assert active["task_id"] == task["task_id"]
    assert active["instructions"] == "Usa fattore scala 0.44 sugli xG e testa le quote"


def test_report_result_from_cursor(bus_store):
    task = bus_store.post_task(
        title="Aggiungi mercati DNB",
        instructions="Supporta DNB 1 e DNB 2",
        target_files=["services/betting/netwin_cache_reader.py"],
    )

    # Cursor completa il task e manda il report
    rep = bus_store.report_result(
        task_id=task["task_id"],
        status="COMPLETED",
        summary="DNB integrato con fair odds esatte e 3 test aggiunti",
        modified_files=["services/betting/netwin_cache_reader.py", "tests/test_combo_book_search.py"],
        git_commit="12545f0",
        notes_for_antigravity="Verificare la formula di rimborso se pareggio",
        sender="Cursor",
    )

    assert rep["status"] == "COMPLETED"
    assert rep["git_commit"] == "12545f0"

    # Verifica stato aggiornato nel bus
    reloaded = bus_store.get_task(task["task_id"])
    assert reloaded["status"] == "COMPLETED"
    assert reloaded["summary"] == "DNB integrato con fair odds esatte e 3 test aggiunti"

    # Verifica che il messaggio sia presente nel log
    msgs = bus_store.list_messages()
    assert any(m["message_type"] == "REPORT" for m in msgs)


def test_ask_guidance(bus_store):
    res = bus_store.ask_guidance(
        question="Qual è il range di spread per l'aggregata 344 del 1° Tempo?",
        context="h=65541 corrisponde a 0.5 o 1.5?",
        sender="Cursor",
    )
    assert res["message_type"] == "QUESTION"
    assert "344" in res["content"]

    msgs = bus_store.list_messages()
    assert any(m["sender"] == "Cursor" and m["recipient"] == "Antigravity" for m in msgs)


def test_mcp_protocol_initialize_and_tools_list(mcp_server):
    # 1. Initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "cursor", "version": "0.45.0"}
        }
    }
    resp = mcp_server.dispatch(init_req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "bagent-bus"
    assert "tools" in resp["result"]["capabilities"]

    # 2. Notification initialized
    notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    assert mcp_server.dispatch(notif) is None

    # 3. Ping
    ping_resp = mcp_server.dispatch({"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert ping_resp["result"] == {}

    # 4. Tools List
    tools_resp = mcp_server.dispatch({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    tool_names = [t["name"] for t in tools_resp["result"]["tools"]]
    assert "antigravity_get_task" in tool_names
    assert "antigravity_report_result" in tool_names
    assert "antigravity_ask_guidance" in tool_names
    assert "bagent_get_system_state" in tool_names
    assert "agent_bus_read_messages" in tool_names


def test_mcp_tools_call_workflow(mcp_server, bus_store):
    # Antigravity invia un task allo store
    task = bus_store.post_task(
        title="Audit quote Argentina",
        instructions="Controlla Talleres vs Belgrano",
        target_files=["services/betting/netwin_cache_reader.py"],
    )

    # Cursor chiama il tool antigravity_get_task
    call_req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "antigravity_get_task",
            "arguments": {}
        }
    }
    resp = mcp_server.dispatch(call_req)
    text = resp["result"]["content"][0]["text"]
    assert "Audit quote Argentina" in text
    assert task["task_id"] in text

    # Cursor chiama antigravity_report_result
    rep_req = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "antigravity_report_result",
            "arguments": {
                "task_id": task["task_id"],
                "status": "COMPLETED",
                "summary": "Quote verificate, edge reale +6.7%",
                "modified_files": ["services/betting/netwin_cache_reader.py"]
            }
        }
    }
    rep_resp = mcp_server.dispatch(rep_req)
    rep_text = rep_resp["result"]["content"][0]["text"]
    assert "Report inviato con successo" in rep_text

    # Cursor chiama agent_bus_read_messages
    read_req = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {
            "name": "agent_bus_read_messages",
            "arguments": {"limit": 5}
        }
    }
    read_resp = mcp_server.dispatch(read_req)
    read_text = read_resp["result"]["content"][0]["text"]
    assert "MESSAGGI SUL BUS" in read_text


def test_mcp_unknown_method(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 99,
        "method": "non_existent_method"
    }
    resp = mcp_server.dispatch(req)
    assert resp["error"]["code"] == -32601


def test_cmd_wait_for_report_success(bus_store):
    from scripts.agent_bus import cmd_wait_for_report
    import argparse
    task = bus_store.post_task(title="Test wait", instructions="test")
    bus_store.report_result(task_id=task["task_id"], status="COMPLETED", summary="All good")

    args = argparse.Namespace(task_id=task["task_id"], timeout=2, interval=0.1)
    ret = cmd_wait_for_report(args, bus_store)
    assert ret == 0


def test_cmd_wait_for_report_timeout(bus_store):
    from scripts.agent_bus import cmd_wait_for_report
    import argparse
    task = bus_store.post_task(title="Pending task", instructions="wait test")

    args = argparse.Namespace(task_id=task["task_id"], timeout=1, interval=0.2)
    ret = cmd_wait_for_report(args, bus_store)
    assert ret == 1

