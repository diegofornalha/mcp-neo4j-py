#!/usr/bin/env python3
"""
Exemplos práticos de uso do Neo4j com Python
Salvando conhecimento no grafo para referência futura
"""

import subprocess
import json
from datetime import datetime

def execute_cypher(query):
    """Executa query Cypher via Docker"""
    cmd = [
        'docker', 'exec', '-i', 'terminal-neo4j',
        'cypher-shell', '-u', 'neo4j', '-p', 'Cancela@1',
        '--format', 'plain', query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e.stderr}")
        return None

# Salvar exemplos práticos no Neo4j
print("📚 Salvando Exemplos Práticos de Python + Neo4j...")

# 1. Exemplo de CRUD completo
crud_example = """
// Criar exemplo de CRUD Python
CREATE (ex:PythonExample {
  type: 'CRUD_Operations',
  name: 'Operações CRUD com Neo4j Python',
  created_at: datetime(),
  description: 'Exemplo completo de Create, Read, Update, Delete'
})

// Código Create
CREATE (create:CodeSnippet {
  operation: 'CREATE',
  code: 'driver.execute_query(
    "CREATE (p:Person {name: $name, age: $age}) RETURN p",
    name="João", age=30
)',
  description: 'Criar novo nó Person'
})

// Código Read
CREATE (read:CodeSnippet {
  operation: 'READ',
  code: 'driver.execute_query(
    "MATCH (p:Person) WHERE p.age > $min_age RETURN p.name, p.age",
    min_age=25
)',
  description: 'Buscar pessoas por idade'
})

// Código Update
CREATE (update:CodeSnippet {
  operation: 'UPDATE',
  code: 'driver.execute_query(
    "MATCH (p:Person {name: $name}) SET p.age = $new_age RETURN p",
    name="João", new_age=31
)',
  description: 'Atualizar idade da pessoa'
})

// Código Delete
CREATE (delete:CodeSnippet {
  operation: 'DELETE',
  code: 'driver.execute_query(
    "MATCH (p:Person {name: $name}) DETACH DELETE p",
    name="João"
)',
  description: 'Deletar pessoa e seus relacionamentos'
})

// Relacionar exemplos
CREATE (ex)-[:HAS_SNIPPET]->(create)
CREATE (ex)-[:HAS_SNIPPET]->(read)
CREATE (ex)-[:HAS_SNIPPET]->(update)
CREATE (ex)-[:HAS_SNIPPET]->(delete)

RETURN ex.name as exemplo, COUNT{(ex)-[:HAS_SNIPPET]->()} as snippets
"""

result = execute_cypher(crud_example)
if result:
    print(f"✅ CRUD Example: {result.strip()}")

# 2. Exemplo de Transações
transaction_example = """
CREATE (ex:PythonExample {
  type: 'Transactions',
  name: 'Transações com Neo4j Python',
  created_at: datetime(),
  code: 'def transfer_funds(driver, from_account, to_account, amount):
    with driver.session() as session:
        def transaction_function(tx):
            # Debitar
            tx.run("MATCH (a:Account {id: $id}) SET a.balance = a.balance - $amount",
                   id=from_account, amount=amount)
            # Creditar
            tx.run("MATCH (a:Account {id: $id}) SET a.balance = a.balance + $amount",
                   id=to_account, amount=amount)
            # Registrar transação
            tx.run("CREATE (t:Transaction {from: $from, to: $to, amount: $amount, date: datetime()})",
                   from=from_account, to=to_account, amount=amount)
        
        session.execute_write(transaction_function)',
  description: 'Transação atômica para transferência bancária'
})
RETURN ex.name as exemplo
"""

result = execute_cypher(transaction_example)
if result:
    print(f"✅ Transaction Example: {result.strip()}")

# 3. Exemplo de Índices e Constraints
index_example = """
CREATE (ex:PythonExample {
  type: 'Indexes_Constraints',
  name: 'Índices e Constraints Python',
  created_at: datetime(),
  commands: [
    'CREATE INDEX person_name FOR (p:Person) ON (p.name)',
    'CREATE CONSTRAINT unique_email FOR (p:Person) REQUIRE p.email IS UNIQUE',
    'CREATE INDEX composite_index FOR (p:Person) ON (p.name, p.age)'
  ],
  python_code: 'driver.execute_query("CREATE INDEX person_name FOR (p:Person) ON (p.name)")',
  description: 'Criar índices para melhorar performance de queries'
})
RETURN ex.name as exemplo
"""

result = execute_cypher(index_example)
if result:
    print(f"✅ Index Example: {result.strip()}")

# 4. Exemplo de Agregações
aggregation_example = """
CREATE (ex:PythonExample {
  type: 'Aggregations',
  name: 'Agregações e Estatísticas',
  created_at: datetime(),
  queries: [
    'MATCH (p:Person) RETURN COUNT(p) as total',
    'MATCH (p:Person) RETURN AVG(p.age) as idade_media',
    'MATCH (p:Person)-[r:KNOWS]->(friend) RETURN p.name, COUNT(friend) as amigos ORDER BY amigos DESC',
    'MATCH (p:Person) RETURN p.city, COUNT(p) as pessoas GROUP BY p.city'
  ],
  python_code: 'result = driver.execute_query(
    "MATCH (p:Person) RETURN p.city, COUNT(p) as total, AVG(p.age) as avg_age"
)',
  description: 'Usar funções de agregação para análises'
})
RETURN ex.name as exemplo
"""

result = execute_cypher(aggregation_example)
if result:
    print(f"✅ Aggregation Example: {result.strip()}")

# 5. Padrões de Modelagem
modeling_patterns = """
CREATE (pat:ModelingPattern {
  type: 'Graph_Patterns',
  name: 'Padrões de Modelagem de Grafos',
  created_at: datetime(),
  patterns: [
    'Rede Social: (Person)-[:FOLLOWS]->(Person)',
    'E-commerce: (Customer)-[:PURCHASED]->(Product)',
    'Conhecimento: (Topic)-[:RELATED_TO]->(Topic)',
    'Hierarquia: (Employee)-[:REPORTS_TO]->(Manager)',
    'Timeline: (Event)-[:PRECEDED_BY]->(Event)'
  ],
  best_practices: [
    'Use nós para entidades',
    'Use relacionamentos para conectar entidades',
    'Propriedades devem ser valores primitivos',
    'Evite arrays grandes em propriedades',
    'Use labels descritivos e no singular'
  ]
})
RETURN pat.name as padrao
"""

result = execute_cypher(modeling_patterns)
if result:
    print(f"✅ Modeling Pattern: {result.strip()}")

# Verificar total de conhecimento salvo
print("\n📊 Resumo do Conhecimento Salvo:")
summary = """
MATCH (n)
WHERE n.created_at > datetime() - duration('PT1H')
RETURN labels(n)[0] as tipo, COUNT(n) as quantidade
ORDER BY quantidade DESC
"""

result = execute_cypher(summary)
if result:
    print(result)

print("\n✨ Conhecimento Neo4j + Python salvo com sucesso no grafo!")