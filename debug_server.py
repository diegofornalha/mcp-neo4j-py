#!/usr/bin/env python3
"""
Debug do servidor MCP Neo4j
"""

import subprocess
import json
import time

def debug_server():
    print("🔍 Debug do servidor MCP Neo4j...\n")
    
    # Iniciar servidor
    process = subprocess.Popen(
        ["uv", "run", "python", "src/mcp_neo4j/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Aguardar inicialização
        time.sleep(2)
        
        # Enviar initialize
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            }
        }
        
        print("📤 Enviando initialize...")
        process.stdin.write(json.dumps(init_msg) + "\n")
        process.stdin.flush()
        
        # Ler resposta
        response = process.stdout.readline()
        print(f"📥 Resposta: {response.strip()}")
        
        # Aguardar
        time.sleep(1)
        
        # Enviar tools/list com formato diferente
        tools_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("\n📤 Enviando tools/list...")
        process.stdin.write(json.dumps(tools_msg) + "\n")
        process.stdin.flush()
        
        # Ler resposta
        response = process.stdout.readline()
        print(f"📥 Resposta: {response.strip()}")
        
        # Aguardar
        time.sleep(1)
        
        # Tentar com método diferente
        print("\n📤 Tentando list_tools...")
        list_tools_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "list_tools",
            "params": {}
        }
        
        process.stdin.write(json.dumps(list_tools_msg) + "\n")
        process.stdin.flush()
        
        # Ler resposta
        response = process.stdout.readline()
        print(f"📥 Resposta: {response.strip()}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    debug_server()
