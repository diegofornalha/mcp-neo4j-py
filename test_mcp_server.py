#!/usr/bin/env python3
"""
Script de teste para o servidor MCP Neo4j
"""

import json
import subprocess
import sys
import os

def test_mcp_server():
    """Testa o servidor MCP Neo4j"""
    
    # Configurar variáveis de ambiente
    env = os.environ.copy()
    env.update({
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password',
        'NEO4J_DATABASE': 'neo4j'
    })
    
    # Comandos para testar
    commands = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
    ]
    
    # Converter comandos para JSON
    input_data = '\n'.join(json.dumps(cmd) for cmd in commands)
    
    try:
        # Executar servidor MCP
        result = subprocess.run(
            ['uv', 'run', 'python', 'src/mcp_neo4j/server.py'],
            input=input_data,
            capture_output=True,
            text=True,
            env=env,
            cwd='/home/codable/terminal/mcp-neo4j-py'
        )
        
        print("=== SAÍDA DO SERVIDOR ===")
        print(result.stdout)
        
        if result.stderr:
            print("\n=== ERROS ===")
            print(result.stderr)
        
        # Analisar respostas
        responses = result.stdout.strip().split('\n')
        for i, response in enumerate(responses):
            if response.strip():
                try:
                    data = json.loads(response)
                    print(f"\n=== RESPOSTA {i+1} ===")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print(f"\n=== RESPOSTA {i+1} (não-JSON) ===")
                    print(response)
        
    except Exception as e:
        print(f"Erro ao executar teste: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testando servidor MCP Neo4j...")
    success = test_mcp_server()
    
    if success:
        print("\n✅ Teste concluído!")
    else:
        print("\n❌ Teste falhou!")
        sys.exit(1)
