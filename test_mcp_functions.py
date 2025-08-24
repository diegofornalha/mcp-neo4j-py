#!/usr/bin/env python3
"""
Teste das funções MCP Neo4j
"""

import json
import subprocess
import time
import sys
import os
from typing import Optional, Dict, Any


def _read_one_json_line(proc: subprocess.Popen, timeout: float = 5.0) -> Optional[dict]:
    """Read a single JSON line from proc.stdout with a timeout."""
    start = time.time()
    buffer = ""
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.05)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            buffer += line
            # keep reading
    return None


def _write_json(proc: subprocess.Popen, obj: Dict[str, Any]) -> None:
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def test_mcp_function(function_name: str, arguments: Optional[Dict[str, Any]] = None) -> bool:
    """Testa uma função MCP específica com handshake adequado."""

    print(f"\n🔧 Testando: {function_name}")
    print("-" * 40)

    env = os.environ.copy()
    env.update({
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password',
        'NEO4J_DATABASE': 'neo4j'
    })

    server_path = os.path.join(os.path.dirname(__file__), 'src', 'mcp_neo4j', 'server.py')

    try:
        proc = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=os.path.dirname(__file__),
            bufsize=1,
        )

        # initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            }
        }
        _write_json(proc, init_req)
        init_resp = _read_one_json_line(proc, timeout=5.0)
        if not init_resp or init_resp.get("id") != 1:
            print("⚠️ Resposta de initialize não recebida ou inválida:", init_resp)
            proc.kill()
            return False

        # send notifications/initialized
        initialized_note = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": None,
        }
        _write_json(proc, initialized_note)

        # call tool
        call_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": function_name,
                "arguments": arguments or {}
            }
        }
        _write_json(proc, call_req)
        call_resp = _read_one_json_line(proc, timeout=10.0)

        # Print stderr for debugging if present
        stderr_output = proc.stderr.read() if proc.stderr and not proc.poll() else ""
        if stderr_output:
            print("[stderr]", stderr_output)

        # Terminate the process
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

        if not call_resp:
            print("⚠️ Resposta não encontrada ou inválida")
            return False

        if 'result' in call_resp and 'content' in call_resp['result']:
            print(f"✅ Resultado: {call_resp['result']['content']}")
            return True
        elif 'error' in call_resp:
            print(f"❌ Erro: {call_resp['error'].get('message')}")
            return False

        print("⚠️ Resposta inesperada:", call_resp)
        return False

    except Exception as e:
        print(f"❌ Erro de execução: {e}")
        return False


def test_all_functions() -> bool:
    """Testa todas as funções MCP"""

    print("🚀 TESTANDO TODAS AS FUNÇÕES MCP NEO4J")
    print("=" * 50)

    functions = [
        ("list_memory_labels", {}),
        ("search_memories", {"query": "test", "limit": 5}),
        ("get_guidance", {"topic": "default"}),
        ("create_memory", {"label": "test", "properties": {"name": "Teste MCP", "description": "Teste de função"}}),
        ("search_memories", {"query": "Teste MCP", "limit": 5}),
        ("get_context_for_task", {"task_description": "Testar funções MCP"}),
        ("suggest_best_approach", {"current_task": "Testar integração MCP"}),
        ("learn_from_result", {"task": "Teste MCP", "result": "Funções funcionando", "success": True}),
    ]

    results = {}

    for func_name, args in functions:
        success = test_mcp_function(func_name, args)
        results[func_name] = success
        time.sleep(0.2)

    print("\n📊 RESUMO DOS TESTES")
    print("=" * 30)

    for func_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {func_name}")

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"\n🎯 Resultado: {success_count}/{total_count} funções funcionando")

    if success_count == total_count:
        print("🎉 TODAS AS FUNÇÕES MCP ESTÃO FUNCIONANDO!")
    else:
        print("⚠️ Algumas funções precisam de ajustes")

    return success_count == total_count


if __name__ == "__main__":
    success = test_all_functions()
    sys.exit(0 if success else 1)
