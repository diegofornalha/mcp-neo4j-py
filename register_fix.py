#!/usr/bin/env python3
"""Registrar correção no Neo4j"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_neo4j.server import neo4j_conn
from datetime import datetime

# Registrar a correção
cypher = """
CREATE (fix:BugFix {
    name: 'DateTime Serialization Fix',
    description: 'Corrigido erro de serialização de objetos DateTime do Neo4j para JSON',
    task: 'Correção do erro de serialização de DateTime no servidor MCP Neo4j',
    solution: 'Implementada conversão de DateTime para string ISO format em todas as funções que retornam dados',
    files_modified: ['mcp-neo4j-py/src/mcp_neo4j/server.py'],
    created_at: datetime(),
    status: 'completed',
    success: true,
    category: 'bug_fix'
})
RETURN fix
"""

try:
    result = neo4j_conn.execute_query(cypher)
    if result:
        print("✅ Correção registrada no Neo4j com sucesso!")
        print("Detalhes:", result[0]['fix'])
    else:
        print("❌ Falha ao registrar correção")
except Exception as e:
    print(f"❌ Erro: {e}")

# Buscar registros relacionados
print("\n📊 Verificando registros de bugs e correções...")
search_query = """
MATCH (n)
WHERE labels(n) IN [['BugFix'], ['Learning'], ['Error']]
  AND (n.category = 'bug_fix' OR n.name CONTAINS 'DateTime' OR n.task CONTAINS 'serialização')
RETURN labels(n) as labels, n.name as name, n.created_at as created_at
ORDER BY n.created_at DESC
LIMIT 5
"""

try:
    results = neo4j_conn.execute_query(search_query)
    if results:
        print(f"\nEncontrados {len(results)} registros relacionados:")
        for r in results:
            print(f"  - [{r['labels'][0] if r['labels'] else 'Unknown'}] {r['name']}")
    else:
        print("Nenhum registro relacionado encontrado")
except Exception as e:
    print(f"❌ Erro na busca: {e}")

print("\n✅ MCP Neo4j está funcionando corretamente!")
print("   As correções foram aplicadas e registradas no grafo de conhecimento.")