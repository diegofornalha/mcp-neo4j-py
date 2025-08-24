#!/usr/bin/env python3
"""
Debug das ferramentas MCP
"""

import os
import sys
sys.path.append('src')

def debug_tools():
    """Debuga as ferramentas MCP"""
    
    print("🔍 Debugando ferramentas MCP Neo4j...")
    
    try:
        # Importar o servidor
        from mcp_neo4j.server import mcp
        
        print(f"1. Servidor MCP: {type(mcp)}")
        print(f"   Nome: {mcp.name}")
        
        # Verificar se as ferramentas estão disponíveis
        print("\n2. Verificando ferramentas...")
        
        # Listar todas as funções do módulo
        import mcp_neo4j.server as server_module
        
        print("   Funções disponíveis no módulo:")
        for name in dir(server_module):
            if not name.startswith('_'):
                print(f"     • {name}")
        
        # Verificar se as funções MCP estão definidas
        print("\n3. Verificando funções MCP...")
        
        mcp_functions = [
            'search_memories',
            'create_memory', 
            'create_connection',
            'update_memory',
            'delete_memory',
            'list_memory_labels',
            'get_context_for_task',
            'learn_from_result',
            'suggest_best_approach',
            'get_guidance'
        ]
        
        for func_name in mcp_functions:
            if hasattr(server_module, func_name):
                func = getattr(server_module, func_name)
                print(f"   ✅ {func_name}: {type(func)}")
            else:
                print(f"   ❌ {func_name}: Não encontrada")
        
        # Verificar se o decorator @mcp.tool() foi aplicado
        print("\n4. Verificando decorators...")
        
        for func_name in mcp_functions:
            if hasattr(server_module, func_name):
                func = getattr(server_module, func_name)
                if hasattr(func, '__mcp_tool__'):
                    print(f"   ✅ {func_name}: Decorator MCP aplicado")
                else:
                    print(f"   ❌ {func_name}: Decorator MCP não aplicado")
        
    except Exception as e:
        print(f"❌ Erro ao debugar: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_tools()
