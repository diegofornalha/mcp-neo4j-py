#!/bin/bash

# Script para adicionar conhecimento sobre composição de queries grandes

curl -s -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'neo4j:Cancela@1' | base64)" \
  -d @- <<'EOF'
{
  "statements": [
    {
      "statement": "CREATE (union:Documentation:CypherComposition {name: 'UNION Clause', description: 'Combina resultados de duas queries com mesma estrutura', syntax: 'UNION [ALL] entre queries', requirement: 'Colunas devem ter mesmos aliases em todas sub-cláusulas', union_all: 'UNION ALL mantém duplicatas, UNION remove', use_case: 'Combinar resultados de padrões diferentes', example: 'MATCH actors RETURN name UNION MATCH directors RETURN name', alternative: 'Pode usar | para múltiplos tipos: [:ACTED_IN|DIRECTED]', updated_at: datetime()}) RETURN union"
    },
    {
      "statement": "CREATE (with:Documentation:CypherComposition {name: 'WITH Clause Fundamentals', description: 'Encadeia fragmentos de queries como pipeline de dados', purpose: 'Cada fragmento trabalha com output do anterior', similarity: 'Similar ao RETURN mas não finaliza a query', difference: 'Prepara input para próxima parte da query', requirement: 'Todas colunas devem ter alias', features: ['Expressões', 'Agregações', 'Ordenação', 'Paginação'], control_flow: 'Apenas colunas declaradas no WITH ficam disponíveis', updated_at: datetime()}) RETURN with"
    },
    {
      "statement": "CREATE (pipeline:Documentation:CypherComposition {name: 'Data Pipeline Pattern', description: 'WITH permite criar pipelines de transformação de dados', workflow: 'MATCH -> WITH (transform) -> WHERE -> WITH (aggregate) -> RETURN', intermediate_calc: 'Permite cálculos intermediários dentro da query', variable_passing: 'Passa valores entre seções da query', example: 'WITH person, count(*) AS appearances WHERE appearances > 1', flexibility: 'Cada estágio pode filtrar, agregar ou transformar', updated_at: datetime()}) RETURN pipeline"
    },
    {
      "statement": "CREATE (params:Documentation:CypherComposition {name: 'WITH for Parameters', description: 'WITH útil para configurar parâmetros antes da query', use_cases: ['Parameter keys', 'URL strings', 'Query variables', 'Import configurations'], example: 'WITH 2 AS min, 6 AS max MATCH (p) WHERE min <= p.value <= max', benefits: 'Código mais limpo e reutilizável', performance: 'Parâmetros calculados uma vez', updated_at: datetime()}) RETURN params"
    },
    {
      "statement": "CREATE (composition:Documentation:CypherAdvanced {name: 'Query Composition Best Practices', modular: 'Quebrar queries complexas em partes com WITH', readable: 'Cada WITH deve ter propósito claro', performance_tip: 'Filtrar cedo para reduzir dados passados', aggregation_tip: 'Agregar antes de passar com WITH', naming: 'Usar aliases descritivos', debugging: 'WITH facilita debug de queries complexas', updated_at: datetime()}) RETURN composition"
    },
    {
      "statement": "CREATE (collect:Documentation:CypherComposition {name: 'Collect and Filter Pattern', description: 'Padrão comum: coletar dados e filtrar baseado em agregação', pattern: 'MATCH -> WITH collect() -> WHERE condition on collection', example: 'WITH person, collect(movies) AS movies WHERE size(movies) > 1', power: 'Combina agregação com filtragem', use_case: 'Encontrar padrões baseados em contagens ou coleções', updated_at: datetime()}) RETURN collect"
    },
    {
      "statement": "CREATE (chaining:Documentation:CypherComposition {name: 'Query Chaining', description: 'Encadear múltiplas operações em sequência', stages: ['Busca inicial', 'Transformação', 'Agregação', 'Filtragem', 'Projeção final'], variable_scope: 'Variáveis só existem após WITH que as declara', memory: 'Cada WITH pode reduzir memória filtrando dados', example_flow: 'MATCH (a)-[r]-(b) WITH a, collect(b) AS related WITH a, size(related) AS count RETURN a, count', updated_at: datetime()}) RETURN chaining"
    }
  ]
}
EOF

echo "Conhecimento sobre composição de queries adicionado!"