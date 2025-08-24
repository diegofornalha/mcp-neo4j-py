#!/usr/bin/env python3
"""
Teste das funções MCP Neo4j
"""

import json
import subprocess
import time
import sys

def test_mcp_function(function_name, arguments=None):
    """Testa uma função MCP específica"""
    
    print(f"\n🔧 Testando: {function_name}")
    print("-" * 40)
    
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
            "method": "tools/call",
            "params": {
                "name": function_name,
                "arguments": arguments or {}
            }
        }
    ]
    
    # Converter comandos para JSON
    input_data = '\n'.join(json.dumps(cmd) for cmd in commands)
    
    try:
        # Executar servidor MCP
        result = subprocess.run(
            ['/home/codable/terminal/mcp-neo4j-py/.venv/bin/python', '/home/codable/terminal/mcp-neo4j-py/src/mcp_neo4j/server.py'],
            input=input_data,
            capture_output=True,
            text=True,
            env=env,
            cwd='/home/codable/terminal/mcp-neo4j-py'
        )
        
        # Analisar respostas
        responses = result.stdout.strip().split('\n')
        
        # Procurar pela resposta da função
        for response in responses:
            if response.strip():
                try:
                    data = json.loads(response)
                    if 'result' in data and 'content' in data['result']:
                        print(f"✅ Resultado: {data['result']['content']}")
                        return True
                    elif 'error' in data:
                        print(f"❌ Erro: {data['error']['message']}")
                        return False
                except json.JSONDecodeError:
                    continue
        
        print("⚠️ Resposta não encontrada ou inválida")
        return False
        
    except Exception as e:
        print(f"❌ Erro de execução: {e}")
        return False

def test_all_functions():
    """Testa todas as funções MCP"""
    
    print("🚀 TESTANDO TODAS AS FUNÇÕES MCP NEO4J")
    print("=" * 50)
    
    # Lista de funções para testar
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
        time.sleep(0.5)  # Pequena pausa entre testes
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 30)
    
    for func_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {func_name}")
    
    success_count = sum(results.values())
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
