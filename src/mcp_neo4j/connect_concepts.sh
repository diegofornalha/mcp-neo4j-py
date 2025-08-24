#!/bin/bash

# Conectar conceitos fundamentais

curl -s -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'neo4j:Cancela@1' | base64)" \
  -d @- <<'EOF'
{
  "statements": [
    {
      "statement": "MATCH (gdb:CoreConcept {name: 'Graph Database Fundamentals'}), (nodes:GraphElement {name: 'Nodes (Nós)'}) MERGE (gdb)-[:COMPOSED_OF]->(nodes) RETURN count(*)"
    },
    {
      "statement": "MATCH (gdb:CoreConcept {name: 'Graph Database Fundamentals'}), (rels:GraphElement {name: 'Relationships (Relacionamentos)'}) MERGE (gdb)-[:COMPOSED_OF]->(rels) RETURN count(*)"
    },
    {
      "statement": "MATCH (nodes:GraphElement {name: 'Nodes (Nós)'}), (rels:GraphElement {name: 'Relationships (Relacionamentos)'}) MERGE (nodes)-[:CONNECTS_WITH]->(rels) RETURN count(*)"
    },
    {
      "statement": "MATCH (gdb:CoreConcept {name: 'Graph Database Fundamentals'}), (adv:Benefits {name: 'Vantagens dos Bancos de Dados de Grafo'}) MERGE (gdb)-[:PROVIDES]->(adv) RETURN count(*)"
    },
    {
      "statement": "MATCH (gdb:CoreConcept {name: 'Graph Database Fundamentals'}), (use:Applications {name: 'Casos de Uso de Grafos'}) MERGE (gdb)-[:ENABLES]->(use) RETURN count(*)"
    },
    {
      "statement": "MATCH (gdb:CoreConcept {name: 'Graph Database Fundamentals'}), (model:DataModel {name: 'Modelagem de Dados em Grafo'}) MERGE (gdb)-[:IMPLEMENTS]->(model) RETURN count(*)"
    },
    {
      "statement": "MATCH (neo4j:CoreConcept {name: 'Neo4j Core Architecture'}), (gdb:CoreConcept {name: 'Graph Database Fundamentals'}) MERGE (neo4j)-[:IS_IMPLEMENTATION_OF]->(gdb) RETURN count(*)"
    },
    {
      "statement": "MATCH (ind:Adoption {name: 'Adoção Industrial do Neo4j'}), (use:Applications {name: 'Casos de Uso de Grafos'}) MERGE (ind)-[:APPLIES]->(use) RETURN count(*)"
    }
  ]
}
EOF

echo "Conceitos conectados!"