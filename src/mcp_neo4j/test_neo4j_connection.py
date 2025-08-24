#!/usr/bin/env python3
"""
Script para testar e salvar informações no Neo4j via Docker
"""
import subprocess
import json
from datetime import datetime

def execute_cypher(query):
    """Executa uma query Cypher no Neo4j via Docker"""
    cmd = [
        'docker', 'exec', '-i', 'terminal-neo4j',
        'cypher-shell', '-u', 'neo4j', '-p', 'password',
        '--format', 'plain', query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar query: {e.stderr}")
        return None

# Testar conexão
print("🔍 Testando conexão com Neo4j...")
test_query = "RETURN 'Conexão bem-sucedida!' as message"
result = execute_cypher(test_query)
if result:
    print(f"✅ {result.strip()}")
else:
    print("❌ Falha na conexão")
    exit(1)

# Criar nó de memória sobre o MCP
print("\n📝 Salvando informação sobre MCP no Neo4j...")
create_memory = """
MERGE (m:Memory {type: 'MCP_Configuration'})
SET m.name = 'MCP Neo4j Agent Memory',
    m.status = 'Configurado via Docker',
    m.container = 'mcp-neo4j-agent',
    m.created_at = datetime(),
    m.updated_at = datetime(),
    m.configuration = '{
        "method": "docker",
        "container_name": "mcp-neo4j-agent",
        "neo4j_container": "terminal-neo4j",
        "credentials": "neo4j/password"
    }'
RETURN m.name as name, m.status as status
"""

result = execute_cypher(create_memory)
if result:
    print(f"✅ Memória salva: {result.strip()}")

# Verificar todas as memórias
print("\n📊 Listando todas as memórias no Neo4j:")
list_query = """
MATCH (n)
RETURN labels(n)[0] as tipo, COUNT(n) as quantidade
ORDER BY quantidade DESC
"""

result = execute_cypher(list_query)
if result:
    print(result)

print("\n✨ Teste concluído com sucesso!")