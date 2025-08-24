#!/usr/bin/env python3
"""Teste de conexão e serialização do Neo4j"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_neo4j.server import neo4j_conn
from datetime import datetime
import json

def serialize_value(value):
    """Converter valor do Neo4j para formato serializável"""
    if hasattr(value, 'iso_format'):
        return value.iso_format()
    elif hasattr(value, 'isoformat'):
        return value.isoformat()
    elif isinstance(value, (str, int, float, bool, type(None))):
        return value
    elif isinstance(value, (list, tuple)):
        return [serialize_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    else:
        return str(value)

print("Testando conexão com Neo4j...")

try:
    # Buscar um nó
    result = neo4j_conn.execute_query('MATCH (n) RETURN n, labels(n) as labels LIMIT 1')
    
    if result:
        print("\n✅ Conexão bem-sucedida!")
        node = result[0]['n']
        labels = result[0]['labels']
        
        print(f"\nLabels do nó: {labels}")
        print(f"Tipo do nó: {type(node)}")
        print("\nPropriedades originais:")
        
        for key, value in dict(node).items():
            print(f"  {key}: {type(value).__name__} = {value}")
        
        # Tentar serializar
        print("\nPropriedades serializadas:")
        serialized = {}
        for key, value in dict(node).items():
            serialized[key] = serialize_value(value)
            print(f"  {key}: {serialized[key]}")
        
        # Testar conversão para JSON
        print("\nTeste JSON:")
        json_str = json.dumps(serialized, indent=2)
        print(json_str[:200] + "..." if len(json_str) > 200 else json_str)
        
    else:
        print("❌ Nenhum nó encontrado no banco")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()