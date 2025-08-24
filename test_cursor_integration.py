#!/usr/bin/env python3
"""
Teste de integração com Cursor Agent MCP
"""

import json
import subprocess
import sys

def test_cursor_mcp_integration():
    """Testa se o Cursor está reconhecendo o servidor MCP"""
    
    print("🔍 Testando integração MCP com Cursor Agent...")
    
    # Verificar se o arquivo de configuração existe
    config_file = "/home/codable/.cursor/mcp.json"
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            print("✅ Arquivo de configuração MCP encontrado")
            print(f"   Servidor: {list(config['mcpServers'].keys())[0]}")
    except Exception as e:
        print(f"❌ Erro ao ler configuração: {e}")
        return False
    
    # Verificar se o Neo4j está rodando
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=terminal-neo4j', '--format', '{{.Status}}'],
            capture_output=True,
            text=True
        )
        if 'Up' in result.stdout:
            print("✅ Neo4j está rodando")
        else:
            print("❌ Neo4j não está rodando")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar Neo4j: {e}")
        return False
    
    # Testar conexão com o servidor MCP
    try:
        env = {
            'NEO4J_URI': 'bolt://localhost:7687',
            'NEO4J_USERNAME': 'neo4j',
            'NEO4J_PASSWORD': 'password',
            'NEO4J_DATABASE': 'neo4j'
        }
        
        result = subprocess.run(
            ['/home/codable/terminal/mcp-neo4j-py/.venv/bin/python', 'src/mcp_neo4j/server.py'],
            input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}',
            capture_output=True,
            text=True,
            env=env,
            cwd='/home/codable/terminal/mcp-neo4j-py'
        )
        
        if 'neo4j-memory' in result.stdout:
            print("✅ Servidor MCP Neo4j respondendo")
        else:
            print("❌ Servidor MCP não está respondendo")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar servidor MCP: {e}")
        return False
    
    print("\n🎯 STATUS DA INTEGRAÇÃO:")
    print("   ✅ Configuração MCP: OK")
    print("   ✅ Neo4j: Rodando")
    print("   ✅ Servidor MCP: Respondendo")
    print("   🔄 Cursor Agent: Deve estar carregando ferramentas")
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("   1. No Cursor Agent, procure por ferramentas com prefixo 'mcp_neo4j-memory_'")
    print("   2. Teste uma ferramenta como 'search_memories'")
    print("   3. Verifique se consegue criar e buscar memórias")
    
    return True

if __name__ == "__main__":
    success = test_cursor_mcp_integration()
    
    if success:
        print("\n🎉 Integração MCP configurada com sucesso!")
        print("   As ferramentas devem estar disponíveis no Cursor Agent")
    else:
        print("\n❌ Há problemas na configuração MCP")
        sys.exit(1)
