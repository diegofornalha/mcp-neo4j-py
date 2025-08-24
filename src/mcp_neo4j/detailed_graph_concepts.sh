#!/bin/bash

# Script para adicionar conceitos detalhados sobre grafos

curl -s -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'neo4j:Cancela@1' | base64)" \
  -d @- <<'EOF'
{
  "statements": [
    {
      "statement": "MERGE (pgm:Documentation:GraphModel {name: 'Property Graph Model'}) SET pgm.description = 'Modelo de banco de dados de grafo usado pelo Neo4j consistindo de nós, relacionamentos e propriedades', pgm.components = ['Nodes (vértices/pontos)', 'Relationships (arestas/links)', 'Properties (pares chave-valor)', 'Labels (classificadores)'], pgm.mathematical_foundation = 'Teoria dos Grafos', pgm.updated_at = datetime() RETURN pgm"
    },
    {
      "statement": "MERGE (nodeDetail:Documentation:NodeConcept {name: 'Node Details'}) SET nodeDetail.description = 'Nós descrevem entidades (objetos discretos) de um domínio', nodeDetail.labels_info = 'Zero ou mais labels para classificar o tipo de nó', nodeDetail.properties_info = 'Pares chave-valor para descrever o nó', nodeDetail.minimal_graph = 'Um único nó sem relacionamentos é o grafo mais simples possível', nodeDetail.terminology = ['Também chamados de vértices ou pontos'], nodeDetail.updated_at = datetime() RETURN nodeDetail"
    },
    {
      "statement": "MERGE (labels:Documentation:LabelConcept {name: 'Node Labels Concept'}) SET labels.purpose = 'Moldam o domínio agrupando nós em conjuntos', labels.runtime_flexibility = 'Podem ser adicionados/removidos durante execução', labels.use_cases = ['Agrupar usuários com label User', 'Marcar estados temporários (Suspended)', 'Indicar sazonalidade (Seasonal)'], labels.cardinality = 'Um nó pode ter zero a muitos labels', labels.updated_at = datetime() RETURN labels"
    },
    {
      "statement": "MERGE (relDetail:Documentation:RelationshipConcept {name: 'Relationship Details'}) SET relDetail.requirements = ['Conecta nó fonte e nó alvo', 'Tem uma direção', 'Deve ter exatamente um tipo', 'Pode ter propriedades'], relDetail.self_relationships = 'Um nó pode ter relacionamento consigo mesmo', relDetail.direction_flexibility = 'Direção pode ser ignorada quando não útil', relDetail.structures_enabled = ['Listas', 'Árvores', 'Mapas', 'Entidades compostas'], relDetail.updated_at = datetime() RETURN relDetail"
    },
    {
      "statement": "MERGE (props:Documentation:PropertyConcept {name: 'Properties System'}) SET props.description = 'Pares chave-valor para armazenar dados em nós e relacionamentos', props.data_types = ['Number (integer, float)', 'String', 'Boolean', 'Arrays homogêneos'], props.array_examples = ['[1, 2, 3]', '[2.71, 3.14]', '[\"abc\", \"example\"]', '[true, false]'], props.updated_at = datetime() RETURN props"
    },
    {
      "statement": "MERGE (trav:Documentation:TraversalConcept {name: 'Graph Traversals'}) SET trav.description = 'Como consultar um grafo para encontrar respostas', trav.definition = 'Visitar nós seguindo relacionamentos de acordo com regras', trav.typical_behavior = 'Geralmente apenas um subconjunto do grafo é visitado', trav.path_concept = 'Resultado pode ser retornado como um caminho', trav.path_length_zero = 'Caminho mais curto tem comprimento zero (um nó, sem relacionamentos)', trav.updated_at = datetime() RETURN trav"
    },
    {
      "statement": "MERGE (schema:Documentation:SchemaConcept {name: 'Neo4j Schema'}) SET schema.components = ['Indexes', 'Constraints'], schema.philosophy = 'Schema opcional - não necessário criar antes dos dados', schema.indexes_purpose = 'Aumentar performance', schema.constraints_purpose = 'Garantir que dados aderem às regras do domínio', schema.flexibility = 'Podem ser introduzidos quando desejado', schema.updated_at = datetime() RETURN schema"
    },
    {
      "statement": "MERGE (naming:Documentation:NamingConventions {name: 'Neo4j Naming Conventions'}) SET naming.case_sensitive = true, naming.node_labels = 'CamelCase começando com maiúscula (:VehicleOwner)', naming.relationship_types = 'UPPER_CASE com underscore (:OWNS_VEHICLE)', naming.properties = 'lowerCamelCase começando com minúscula (firstName)', naming.updated_at = datetime() RETURN naming"
    },
    {
      "statement": "MERGE (cyExample:Documentation:CypherExample {name: 'Tom Hanks Graph Example'}) SET cyExample.create_node = 'CREATE (:Person:Actor {name: \"Tom Hanks\", born: 1956})', cyExample.create_relationship = 'CREATE ()-[:ACTED_IN {roles: [\"Forrest\"]}]->()', cyExample.full_example = 'CREATE (:Person:Actor {name: \"Tom Hanks\", born: 1956})-[:ACTED_IN {roles: [\"Forrest\"]}]->(:Movie {title: \"Forrest Gump\", released: 1994})<-[:DIRECTED]-(:Person {name: \"Robert Zemeckis\", born: 1951})', cyExample.query_example = 'Find movies Tom Hanks acted in', cyExample.updated_at = datetime() RETURN cyExample"
    }
  ]
}
EOF

echo "Conceitos detalhados adicionados!"