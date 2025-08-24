#!/usr/bin/env python3
"""
Teste das ferramentas MCP Neo4j
"""

import json
import subprocess
import time
import sys

def test_mcp_tools():
    """Testa as ferramentas MCP Neo4j"""
    
    print("🧪 Testando ferramentas MCP Neo4j...")
    
    # Configurar variáveis de ambiente
    env = {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password',
        'NEO4J_DATABASE': 'neo4j'
    }
    
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
            ['/home/codable/terminal/mcp-neo4j-py/.venv/bin/python', 'src/mcp_neo4j/server.py'],
            input=input_data,
            capture_output=True,
            text=True,
            env=env,
            cwd='/home/codable/terminal/mcp-neo4j-py'
        )
        
        print("=== RESPOSTAS DO SERVIDOR ===")
        
        # Analisar respostas
        responses = result.stdout.strip().split('\n')
        for i, response in enumerate(responses):
            if response.strip():
                try:
                    data = json.loads(response)
                    print(f"\n📤 Resposta {i+1}:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Verificar se é a resposta de tools/list
                    if i == 1 and 'result' in data and 'tools' in data['result']:
                        tools = data['result']['tools']
                        print(f"\n🛠️ Ferramentas disponíveis ({len(tools)}):")
                        for tool in tools:
                            print(f"   • {tool['name']}")
                            
                except json.JSONDecodeError:
                    print(f"\n📤 Resposta {i+1} (não-JSON):")
                    print(response)
        
        if result.stderr:
            print("\n⚠️ Logs do servidor:")
            print(result.stderr)
        
    except Exception as e:
        print(f"❌ Erro ao executar teste: {e}")
        return False
    
    return True

def test_specific_tool(tool_name, arguments=None):
    """Testa uma ferramenta específica"""
    
    print(f"\n🔧 Testando ferramenta: {tool_name}")
    
    env = {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password',
        'NEO4J_DATABASE': 'neo4j'
    }
    
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
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
    ]
    
    input_data = '\n'.join(json.dumps(cmd) for cmd in commands)
    
    try:
        result = subprocess.run(
            ['/home/codable/terminal/mcp-neo4j-py/.venv/bin/python', 'src/mcp_neo4j/server.py'],
            input=input_data,
            capture_output=True,
            text=True,
            env=env,
            cwd='/home/codable/terminal/mcp-neo4j-py'
        )
        
        responses = result.stdout.strip().split('\n')
        for response in responses:
            if response.strip():
                try:
                    data = json.loads(response)
                    if 'result' in data and 'content' in data['result']:
                        print(f"✅ Resultado: {data['result']['content']}")
                        return True
                except json.JSONDecodeError:
                    continue
        
        print("❌ Ferramenta não retornou resultado válido")
        return False
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TESTES MCP NEO4J")
    print("=" * 50)
    
    # Teste básico
    success = test_mcp_tools()
    
    if success:
        print("\n🎯 TESTANDO FERRAMENTAS ESPECÍFICAS")
        print("-" * 40)
        
        # Testar ferramentas específicas
        test_specific_tool("list_memory_labels")
        test_specific_tool("search_memories", {"query": "test", "limit": 5})
        
        print("\n🎉 Testes concluídos!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. No Cursor Agent, use as ferramentas MCP Neo4j")
        print("   2. Teste: mcp_neo4j-memory_create_memory")
        print("   3. Teste: mcp_neo4j-memory_search_memories")
        print("   4. Explore o grafo de conhecimento!")
        
    else:
        print("\n❌ Testes falharam!")
        sys.exit(1)
