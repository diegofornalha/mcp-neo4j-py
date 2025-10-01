// Queries Cypher para Sistema de Memória Viva Neo4j
// Mantém apenas aprendizados relevantes e atualizados

// ============================================
// 1. ANÁLISE DE SAÚDE DA MEMÓRIA
// ============================================

// Identificar nós isolados (sem conexões)
MATCH (n:Learning)
WHERE NOT EXISTS((n)-[]-())
RETURN n.id as id,
       n.name as name,
       n.created_at as created,
       n.category as category,
       'isolated' as issue
ORDER BY n.created_at;

// Identificar nós obsoletos (> 90 dias sem update)
MATCH (n:Learning)
WHERE (n.updated_at < datetime() - duration('P90D'))
   OR (n.updated_at IS NULL AND n.created_at < datetime() - duration('P90D'))
RETURN n.id as id,
       n.name as name,
       duration.between(coalesce(n.updated_at, n.created_at), datetime()).days as days_old,
       'stale' as issue
ORDER BY days_old DESC;

// Identificar duplicações por conteúdo similar
MATCH (n1:Learning), (n2:Learning)
WHERE n1.id < n2.id
  AND (
    n1.content = n2.content
    OR n1.name = n2.name
    OR (n1.project IS NOT NULL
        AND n1.project = n2.project
        AND n1.category = n2.category)
  )
RETURN n1.id as id1,
       n1.name as name1,
       n2.id as id2,
       n2.name as name2,
       CASE
         WHEN n1.content = n2.content THEN 'exact_duplicate'
         WHEN n1.name = n2.name THEN 'same_name'
         ELSE 'same_project_category'
       END as duplicate_type;

// Calcular score de relevância para cada nó
MATCH (n:Learning)
OPTIONAL MATCH (n)-[r]-()
WITH n, COUNT(DISTINCT r) as connection_count
RETURN n.id as id,
       n.name as name,
       connection_count,
       duration.between(coalesce(n.updated_at, n.created_at), datetime()).days as age_days,
       CASE
         WHEN n.importance = 'high' THEN 0.3
         WHEN n.category = 'professional' THEN 0.2
         ELSE 0.1
       END +
       (toFloat(connection_count) / 10.0) * 0.3 +
       CASE
         WHEN duration.between(coalesce(n.updated_at, n.created_at), datetime()).days < 30 THEN 0.4
         WHEN duration.between(coalesce(n.updated_at, n.created_at), datetime()).days < 90 THEN 0.2
         ELSE 0.0
       END as relevance_score
ORDER BY relevance_score DESC;

// ============================================
// 2. LIMPEZA DE NÓS DUPLICADOS
// ============================================

// Identificar grupos de Best Practices duplicadas do claude-code-sdk-python
MATCH (n:Learning)
WHERE n.evaluation_id IN [
  '5fa8d235-52c9-4445-a237-d8b21108ea67',
  '1602869e-0a01-402a-a603-0b483f8dd829',
  '38681741-6831-446d-9e82-d015b0114527'
]
RETURN n.evaluation_id as evaluation_group,
       COUNT(n) as duplicate_count,
       COLLECT(n.id) as node_ids,
       COLLECT(n.content) as contents
ORDER BY duplicate_count DESC;

// Mesclar duplicatas mantendo o mais recente
MATCH (n:Learning)
WHERE n.evaluation_id = '5fa8d235-52c9-4445-a237-d8b21108ea67'
WITH n ORDER BY n.timestamp DESC
WITH COLLECT(n) as nodes
WITH nodes[0] as keeper, nodes[1..] as duplicates
UNWIND duplicates as dup
DETACH DELETE dup
RETURN keeper.id as kept_node, SIZE(duplicates) as deleted_count;

// ============================================
// 3. ESTABELECER CONEXÕES DE RELEVÂNCIA
// ============================================

// Criar conexões entre aprendizados relacionados
MATCH (n1:Learning), (n2:Learning)
WHERE n1.id < n2.id
  AND n1.category = n2.category
  AND NOT EXISTS((n1)-[:RELATED_TO]-(n2))
  AND (
    n1.project = n2.project
    OR n1.subcategory = n2.subcategory
  )
CREATE (n1)-[:RELATED_TO {
  created_at: datetime(),
  reason: 'same_domain'
}]-(n2)
RETURN COUNT(*) as new_connections;

// Criar conexões SUPERSEDES para versões atualizadas
MATCH (old:Learning), (new:Learning)
WHERE old.name = new.name
  AND old.created_at < new.created_at
  AND NOT EXISTS((new)-[:SUPERSEDES]-(old))
CREATE (new)-[:SUPERSEDES {
  created_at: datetime(),
  version_diff: duration.between(old.created_at, new.created_at).days
}]->(old)
RETURN COUNT(*) as supersede_connections;

// ============================================
// 4. ARQUIVAMENTO E LIMPEZA
// ============================================

// Arquivar nós antigos mas com conexões
MATCH (n:Learning)
WHERE n.created_at < datetime() - duration('P90D')
  AND EXISTS((n)-[]-())
  AND NOT n:Archive
SET n:Archive,
    n.archived_at = datetime(),
    n.archive_reason = 'age_but_connected'
RETURN COUNT(n) as archived_count;

// Deletar nós isolados e muito antigos
MATCH (n:Learning)
WHERE NOT EXISTS((n)-[]-())
  AND n.created_at < datetime() - duration('P180D')
  AND NOT n:Archive
DETACH DELETE n
RETURN COUNT(*) as deleted_count;

// ============================================
// 5. SCORING E RANKING DE RELEVÂNCIA
// ============================================

// Adicionar propriedade de relevance_score
MATCH (n:Learning)
OPTIONAL MATCH (n)-[r]-()
WITH n, COUNT(DISTINCT r) as connections
SET n.relevance_score =
  CASE
    WHEN n.importance = 'high' THEN 0.3
    WHEN n.category = 'professional' THEN 0.2
    ELSE 0.1
  END +
  (toFloat(connections) / 10.0) * 0.3 +
  CASE
    WHEN duration.between(coalesce(n.updated_at, n.created_at), datetime()).days < 30 THEN 0.4
    WHEN duration.between(coalesce(n.updated_at, n.created_at), datetime()).days < 90 THEN 0.2
    ELSE 0.0
  END,
  n.last_relevance_update = datetime()
RETURN COUNT(n) as scored_nodes;

// ============================================
// 6. MONITORAMENTO E MÉTRICAS
// ============================================

// Dashboard de saúde da memória
MATCH (n:Learning)
OPTIONAL MATCH (n)-[r]-()
WITH COUNT(DISTINCT n) as total_nodes,
     COUNT(DISTINCT r) as total_relationships,
     AVG(n.relevance_score) as avg_relevance
MATCH (isolated:Learning)
WHERE NOT EXISTS((isolated)-[]-())
WITH total_nodes, total_relationships, avg_relevance, COUNT(isolated) as isolated_count
MATCH (stale:Learning)
WHERE stale.updated_at < datetime() - duration('P90D')
   OR (stale.updated_at IS NULL AND stale.created_at < datetime() - duration('P90D'))
WITH total_nodes, total_relationships, avg_relevance, isolated_count, COUNT(stale) as stale_count
MATCH (archived:Archive)
RETURN {
  total_nodes: total_nodes,
  total_relationships: total_relationships,
  avg_relevance_score: avg_relevance,
  isolated_nodes: isolated_count,
  stale_nodes: stale_count,
  archived_nodes: COUNT(archived),
  health_score: (1 - (toFloat(isolated_count + stale_count) / total_nodes)) * 100
} as memory_health;

// ============================================
// 7. TRIGGERS AUTOMÁTICOS (Conceitual)
// ============================================

// Aumentar relevância quando nó é acessado
// (Executar após cada query que usa um Learning)
MATCH (n:Learning {id: $accessed_node_id})
SET n.access_count = coalesce(n.access_count, 0) + 1,
    n.last_accessed = datetime(),
    n.relevance_score = n.relevance_score * 1.1  // Boost de 10%
RETURN n;

// Diminuir relevância de nós não acessados
// (Executar periodicamente - diário)
MATCH (n:Learning)
WHERE n.last_accessed < datetime() - duration('P30D')
   OR n.last_accessed IS NULL
SET n.relevance_score = n.relevance_score * 0.9  // Redução de 10%
RETURN COUNT(n) as relevance_decreased;

// ============================================
// 8. CONSOLIDAÇÃO DE APRENDIZADOS SIMILARES
// ============================================

// Mesclar aprendizados com mesmo evaluation_id
MATCH (n:Learning)
WHERE n.evaluation_id IS NOT NULL
WITH n.evaluation_id as eval_id, COLLECT(n) as nodes
WHERE SIZE(nodes) > 1
WITH nodes[0] as main_node, nodes[1..] as duplicates
UNWIND duplicates as dup
// Transferir conexões únicas para o nó principal
OPTIONAL MATCH (dup)-[r]-(other)
WHERE NOT EXISTS((main_node)-[]-(other))
WITH main_node, dup, COLLECT({other: other, type: type(r), props: properties(r)}) as relationships
FOREACH (rel IN relationships |
  CREATE (main_node)-[:MERGED_CONNECTION]-(rel.other)
)
// Preservar conteúdo importante
SET main_node.merged_contents = coalesce(main_node.merged_contents, []) + dup.content,
    main_node.merge_count = coalesce(main_node.merge_count, 0) + 1,
    main_node.updated_at = datetime()
DETACH DELETE dup
RETURN main_node.id as kept_node, COUNT(dup) as merged_count;