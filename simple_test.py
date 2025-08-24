#!/usr/bin/env python3
"""
Teste simples das ferramentas MCP
"""

import os
import sys
sys.path.append('src')

from mcp_neo4j.server import get_neo4j_connection, list_memory_labels, search_memories

def test_tools():
    """Testa as ferramentas diretamente"""
    
    print("🧪 Testando ferramentas MCP Neo4j diretamente...")
    
    try:
        # Testar conexão
        print("1. Testando conexão...")
        conn = get_neo4j_connection()
        print("✅ Conexão estabelecida")
        
        # Testar list_memory_labels
        print("\n2. Testando list_memory_labels...")
        labels = list_memory_labels()
        print(f"✅ Labels encontrados: {labels}")
        
        # Testar search_memories
        print("\n3. Testando search_memories...")
        memories = search_memories(query="test", limit=5)
        print(f"✅ Memórias encontradas: {len(memories)}")
        
        print("\n🎉 Todas as ferramentas estão funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tools()
    sys.exit(0 if success else 1)
