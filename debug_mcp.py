#!/usr/bin/env python3
"""
Debug do servidor MCP Neo4j
"""

import os
import sys
sys.path.append('src')

from mcp_neo4j.server import mcp

def debug_mcp():
    """Debuga o servidor MCP"""
    
    print("🔍 Debugando servidor MCP Neo4j...")
    
    # Verificar se o servidor MCP foi criado
    print(f"1. Servidor MCP criado: {mcp is not None}")
    
    # Verificar ferramentas registradas
    print(f"2. Servidor MCP: {type(mcp)}")
    print(f"   Nome: {mcp.name}")
    
    # Verificar se há problemas com as ferramentas
    print("\n3. Verificando ferramentas...")
    
    try:
        # Testar se as ferramentas podem ser chamadas
        from mcp_neo4j.server import list_memory_labels, search_memories
        
        print("   ✅ list_memory_labels: Disponível")
        print("   ✅ search_memories: Disponível")
        
    except Exception as e:
        print(f"   ❌ Erro ao importar ferramentas: {e}")
    
    print("\n4. Verificando configuração Neo4j...")
    print(f"   URI: {os.getenv('NEO4J_URI', 'não definido')}")
    print(f"   Username: {os.getenv('NEO4J_USERNAME', 'não definido')}")
    print(f"   Password: {os.getenv('NEO4J_PASSWORD', 'não definido')}")
    print(f"   Database: {os.getenv('NEO4J_DATABASE', 'não definido')}")

if __name__ == "__main__":
    debug_mcp()
