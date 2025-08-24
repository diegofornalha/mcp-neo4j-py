#!/usr/bin/env python3
"""
Teste direto do FastMCP
"""

import json
import subprocess
import tempfile
import os
import sys
import time
from typing import Optional


def _read_one_json_line(proc: subprocess.Popen, timeout: float = 5.0) -> Optional[dict]:
    start = time.time()
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
            continue
    return None


def _pick_python() -> str:
    # Allow override
    override = os.environ.get("MCP_PYTHON")
    if override:
        return override
    # Prefer project venv if exists
    venv_python = "/workspace/venv/bin/python"
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable


def _child_env() -> dict:
    env = os.environ.copy()
    venv_site = "/workspace/venv/lib/python3.11/site-packages"
    env["PYTHONPATH"] = (
        (venv_site + os.pathsep + env["PYTHONPATH"]) if env.get("PYTHONPATH") else venv_site
    )
    return env


def test_direct_mcp():
    """Testa o FastMCP diretamente"""

    print("🧪 Testando FastMCP diretamente...")

    # Criar um servidor MCP simples
    mcp_code = '''
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP

# Criar servidor MCP
mcp = FastMCP("test-server")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Função de teste"""
    return f"Hello, {name}!"

@mcp.tool()
def add(a: int, b: int) -> int:
    """Soma dois números"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="stdio")
'''

    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(mcp_code)
        temp_file = f.name

    try:
        print(f"1. Arquivo temporário criado: {temp_file}")

        python_exec = _pick_python()
        print(f"Usando interpretador: {python_exec}")

        # Start the server as a persistent process
        proc = subprocess.Popen(
            [python_exec, temp_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=_child_env(),
        )

        # Initialize
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
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        init_resp = _read_one_json_line(proc, timeout=5.0)
        print("2. Resposta initialize:", init_resp)

        # Send notifications/initialized
        initialized_note = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": None,
        }
        proc.stdin.write(json.dumps(initialized_note) + "\n")
        proc.stdin.flush()

        # List tools
        list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        proc.stdin.write(json.dumps(list_req) + "\n")
        proc.stdin.flush()
        list_resp = _read_one_json_line(proc, timeout=5.0)
        print("3. Resposta tools/list:", list_resp)

        if list_resp and 'result' in list_resp:
            print("✅ Ferramentas foram listadas!")
        else:
            print("❌ Ferramentas não foram listadas")

        # Call tool
        call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "hello",
                "arguments": {"name": "Test"}
            }
        }
        proc.stdin.write(json.dumps(call_req) + "\n")
        proc.stdin.flush()
        call_resp = _read_one_json_line(proc, timeout=5.0)
        print("4. Resposta tools/call:", call_resp)

        if call_resp and 'result' in call_resp and 'content' in call_resp['result']:
            print("✅ Chamada de ferramenta bem-sucedida!")
        else:
            print("❌ Falha na chamada de ferramenta")

        # Print stderr if any
        try:
            stderr_output = proc.stderr.read(4096)
            if stderr_output:
                print("[stderr]", stderr_output)
        except Exception:
            pass

        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

    except subprocess.TimeoutExpired:
        print("❌ Timeout ao executar servidor")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        # Limpar arquivo temporário
        try:
            os.unlink(temp_file)
            print(f"8. Arquivo temporário removido: {temp_file}")
        except Exception:
            pass


if __name__ == "__main__":
    test_direct_mcp()
