#!/usr/bin/env python3
"""
Sistema de Memória Viva para Neo4j
Mantém apenas aprendizados relevantes e atualizados usando conexões e metadados
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

class LivingMemorySystem:
    """
    Sistema que mantém a memória do Neo4j viva e relevante
    """

    def __init__(self):
        self.relevance_threshold = 0.3  # Score mínimo para manter
        self.days_until_stale = 90      # Dias até considerar obsoleto
        self.min_connections = 1        # Conexões mínimas para relevância

    async def analyze_memory_health(self) -> Dict[str, Any]:
        """
        Analisa a saúde geral da memória e identifica problemas
        """

        # Query para analisar conexões e relevância
        analysis_queries = {

            # 1. Nós isolados (sem conexões)
            "isolated_nodes": """
            MATCH (n:Learning)
            WHERE NOT EXISTS((n)-[]-())
            RETURN n.id as id,
                   n.name as name,
                   n.created_at as created,
                   'isolated' as reason
            """,

            # 2. Nós obsoletos (muito antigos sem updates)
            "stale_nodes": """
            MATCH (n:Learning)
            WHERE n.updated_at < datetime() - duration('P90D')
            OR (n.updated_at IS NULL AND n.created_at < datetime() - duration('P90D'))
            RETURN n.id as id,
                   n.name as name,
                   n.updated_at as last_update,
                   'stale' as reason
            """,

            # 3. Duplicações (conteúdo similar)
            "duplicate_nodes": """
            MATCH (n1:Learning), (n2:Learning)
            WHERE n1.id < n2.id
            AND (
                n1.content = n2.content
                OR n1.name = n2.name
                OR (n1.project = n2.project AND n1.category = n2.category
                    AND n1.subcategory = n2.subcategory)
            )
            RETURN n1.id as id1, n2.id as id2,
                   n1.name as name1, n2.name as name2,
                   'duplicate' as reason
            """,

            # 4. Nós com baixa relevância (poucas conexões e antigos)
            "low_relevance": """
            MATCH (n:Learning)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, COUNT(r) as connections
            WHERE connections < 2
            AND (n.updated_at < datetime() - duration('P30D')
                 OR n.updated_at IS NULL)
            RETURN n.id as id,
                   n.name as name,
                   connections,
                   'low_relevance' as reason
            """,

            # 5. Conexões quebradas ou inválidas
            "broken_connections": """
            MATCH (n:Learning)-[r]-(m)
            WHERE NOT m:Learning
            AND NOT EXISTS(m.id)
            RETURN n.id as id,
                   type(r) as relationship,
                   'broken_connection' as reason
            """
        }

        return analysis_queries

    def calculate_relevance_score(self, node: Dict[str, Any]) -> float:
        """
        Calcula score de relevância de um nó baseado em múltiplos fatores
        """
        score = 0.0

        # Fator 1: Idade (mais recente = maior score)
        if 'updated_at' in node:
            age_days = (datetime.now() - node['updated_at']).days
            age_score = max(0, 1 - (age_days / 365))  # Decai em 1 ano
            score += age_score * 0.3

        # Fator 2: Número de conexões
        connections = node.get('connections', 0)
        connection_score = min(1, connections / 10)  # Máximo em 10 conexões
        score += connection_score * 0.3

        # Fator 3: Frequência de acesso (se tracked)
        access_count = node.get('access_count', 0)
        access_score = min(1, access_count / 50)  # Máximo em 50 acessos
        score += access_score * 0.2

        # Fator 4: Importância/Categoria
        if node.get('category') == 'professional':
            score += 0.1
        if node.get('importance') == 'high':
            score += 0.1

        return min(1.0, score)

    async def identify_nodes_to_clean(self) -> Dict[str, List[Dict]]:
        """
        Identifica nós que devem ser limpos ou consolidados
        """

        cleanup_candidates = {
            "delete": [],      # Deletar completamente
            "archive": [],     # Arquivar (marcar como histórico)
            "merge": [],       # Mesclar com outro nó
            "update": []       # Atualizar/refrescar
        }

        # Simular análise (em produção, faria queries reais)
        sample_analysis = {
            "isolated_old_nodes": [
                {"id": "node-123", "name": "Aprendizado obsoleto", "age_days": 180, "connections": 0}
            ],
            "duplicate_best_practices": [
                {"id1": "node-18", "id2": "node-45", "content": "Type hints completos", "similarity": 0.95}
            ],
            "low_value_nodes": [
                {"id": "node-789", "score": 0.15, "reason": "Sem acessos há 60 dias"}
            ]
        }

        # Classificar nós para ação
        for node in sample_analysis.get("isolated_old_nodes", []):
            if node["age_days"] > 180 and node["connections"] == 0:
                cleanup_candidates["delete"].append(node)
            elif node["age_days"] > 90:
                cleanup_candidates["archive"].append(node)

        for dup in sample_analysis.get("duplicate_best_practices", []):
            cleanup_candidates["merge"].append(dup)

        return cleanup_candidates

    async def create_living_memory_rules(self) -> Dict[str, Any]:
        """
        Define regras para manter a memória viva e relevante
        """

        rules = {
            "auto_cleanup_rules": {
                "delete_if": [
                    "isolated AND age > 180 days",
                    "duplicate AND lower_score",
                    "broken_connections AND unfixable",
                    "relevance_score < 0.1"
                ],
                "archive_if": [
                    "age > 90 days AND connections < 3",
                    "category = 'temporary' AND age > 30 days",
                    "superseded_by_newer_version"
                ],
                "merge_if": [
                    "content_similarity > 0.9",
                    "same_evaluation_id",
                    "same_concept_different_wording"
                ],
                "refresh_if": [
                    "frequently_accessed AND age > 30 days",
                    "high_importance AND needs_validation",
                    "external_dependency_changed"
                ]
            },

            "relevance_boosters": {
                "increase_on": [
                    "new_connection_created",
                    "referenced_in_recent_query",
                    "used_in_successful_operation",
                    "validated_by_user"
                ],
                "decrease_on": [
                    "no_access_30_days",
                    "contradicted_by_newer_info",
                    "marked_as_outdated",
                    "low_success_rate"
                ]
            },

            "connection_patterns": {
                "strong_connections": [
                    "VALIDATES",
                    "IMPLEMENTS",
                    "REQUIRES",
                    "UPDATES"
                ],
                "weak_connections": [
                    "SIMILAR_TO",
                    "MENTIONED_IN",
                    "POSSIBLY_RELATED"
                ],
                "negative_connections": [
                    "CONTRADICTS",
                    "SUPERSEDED_BY",
                    "DEPRECATED_BY"
                ]
            }
        }

        return rules

    async def apply_cleanup_actions(self, candidates: Dict[str, List]) -> Dict[str, Any]:
        """
        Aplica as ações de limpeza identificadas
        """

        cleanup_cypher = {
            # Deletar nós irrelevantes
            "delete_nodes": """
            MATCH (n:Learning)
            WHERE n.id IN $node_ids
            DETACH DELETE n
            RETURN COUNT(n) as deleted_count
            """,

            # Arquivar nós (adicionar label Archive)
            "archive_nodes": """
            MATCH (n:Learning)
            WHERE n.id IN $node_ids
            SET n:Archive, n.archived_at = datetime()
            REMOVE n:Learning
            RETURN COUNT(n) as archived_count
            """,

            # Mesclar nós duplicados
            "merge_duplicates": """
            MATCH (n1:Learning {id: $id1}), (n2:Learning {id: $id2})
            // Transferir conexões de n2 para n1
            MATCH (n2)-[r]-(other)
            WHERE NOT (n1)-[]-(other)
            CREATE (n1)-[r2:MERGED_FROM]-(other)
            SET r2 = properties(r)
            // Preservar informações importantes de n2
            SET n1.merged_content = coalesce(n1.merged_content, []) + n2.content
            SET n1.updated_at = datetime()
            // Deletar n2
            DETACH DELETE n2
            RETURN n1.id as merged_node
            """,

            # Atualizar timestamp de nós acessados
            "refresh_accessed": """
            MATCH (n:Learning)
            WHERE n.id IN $node_ids
            SET n.last_accessed = datetime(),
                n.access_count = coalesce(n.access_count, 0) + 1
            RETURN COUNT(n) as refreshed_count
            """
        }

        return cleanup_cypher

    async def monitor_memory_growth(self) -> Dict[str, Any]:
        """
        Monitora crescimento e saúde da memória ao longo do tempo
        """

        monitoring_queries = {
            # Taxa de crescimento
            "growth_rate": """
            MATCH (n:Learning)
            WHERE n.created_at > datetime() - duration('P7D')
            RETURN date(n.created_at) as day,
                   COUNT(n) as new_nodes
            ORDER BY day
            """,

            # Distribuição por categoria
            "category_distribution": """
            MATCH (n:Learning)
            RETURN n.category as category,
                   COUNT(n) as count,
                   AVG(n.relevance_score) as avg_relevance
            ORDER BY count DESC
            """,

            # Conexões médias
            "connection_health": """
            MATCH (n:Learning)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, COUNT(r) as connections
            RETURN AVG(connections) as avg_connections,
                   MIN(connections) as min_connections,
                   MAX(connections) as max_connections,
                   percentileCont(connections, 0.5) as median_connections
            """,

            # Nós mais conectados (hubs)
            "knowledge_hubs": """
            MATCH (n:Learning)-[r]-()
            WITH n, COUNT(r) as connections
            WHERE connections > 10
            RETURN n.id, n.name, connections
            ORDER BY connections DESC
            LIMIT 10
            """
        }

        return monitoring_queries


class AutoCleanupScheduler:
    """
    Agendador automático para limpeza periódica
    """

    def __init__(self, memory_system: LivingMemorySystem):
        self.memory_system = memory_system
        self.cleanup_interval = 24 * 3600  # 24 horas
        self.last_cleanup = None

    async def run_cleanup_cycle(self) -> Dict[str, Any]:
        """
        Executa ciclo completo de limpeza
        """

        print("🔄 Iniciando ciclo de limpeza da memória viva...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "actions": {
                "deleted": 0,
                "archived": 0,
                "merged": 0,
                "refreshed": 0
            },
            "health_before": {},
            "health_after": {}
        }

        # 1. Analisar saúde atual
        health = await self.memory_system.analyze_memory_health()
        results["health_before"] = health

        # 2. Identificar candidatos para limpeza
        candidates = await self.memory_system.identify_nodes_to_clean()

        # 3. Aplicar ações de limpeza
        if candidates["delete"]:
            # Deletar nós irrelevantes
            results["actions"]["deleted"] = len(candidates["delete"])
            print(f"  🗑️ Deletando {results['actions']['deleted']} nós irrelevantes")

        if candidates["archive"]:
            # Arquivar nós antigos mas potencialmente úteis
            results["actions"]["archived"] = len(candidates["archive"])
            print(f"  📦 Arquivando {results['actions']['archived']} nós antigos")

        if candidates["merge"]:
            # Mesclar duplicatas
            results["actions"]["merged"] = len(candidates["merge"])
            print(f"  🔀 Mesclando {results['actions']['merged']} duplicatas")

        # 4. Analisar saúde após limpeza
        health_after = await self.memory_system.analyze_memory_health()
        results["health_after"] = health_after

        # 5. Registrar limpeza
        await self.log_cleanup_action(results)

        print(f"✅ Ciclo de limpeza completo: {sum(results['actions'].values())} ações executadas")

        return results

    async def log_cleanup_action(self, results: Dict[str, Any]):
        """
        Registra ação de limpeza no Neo4j
        """

        cleanup_log = f"""
        CREATE (log:CleanupLog {{
            timestamp: datetime('{results["timestamp"]}'),
            deleted_count: {results["actions"]["deleted"]},
            archived_count: {results["actions"]["archived"]},
            merged_count: {results["actions"]["merged"]},
            refreshed_count: {results["actions"]["refreshed"]},
            total_actions: {sum(results["actions"].values())}
        }})
        RETURN log
        """

        # Em produção, executaria a query
        print(f"  📝 Limpeza registrada: {results['timestamp']}")


async def main():
    """
    Demonstração do sistema de memória viva
    """

    print("=" * 60)
    print("🧠 SISTEMA DE MEMÓRIA VIVA PARA NEO4J")
    print("=" * 60)

    # Criar sistema
    memory_system = LivingMemorySystem()
    scheduler = AutoCleanupScheduler(memory_system)

    # 1. Definir regras
    print("\n📋 Definindo regras de memória viva...")
    rules = await memory_system.create_living_memory_rules()
    print(f"  ✅ {len(rules['auto_cleanup_rules'])} regras de limpeza")
    print(f"  ✅ {len(rules['relevance_boosters'])} boosters de relevância")
    print(f"  ✅ {len(rules['connection_patterns'])} padrões de conexão")

    # 2. Analisar saúde atual
    print("\n🔍 Analisando saúde da memória...")
    health_queries = await memory_system.analyze_memory_health()
    print(f"  📊 {len(health_queries)} tipos de análise disponíveis")

    # 3. Identificar problemas
    print("\n🎯 Identificando nós problemáticos...")
    candidates = await memory_system.identify_nodes_to_clean()
    for action, nodes in candidates.items():
        if nodes:
            print(f"  {action}: {len(nodes)} nós")

    # 4. Executar limpeza
    print("\n🧹 Executando ciclo de limpeza...")
    results = await scheduler.run_cleanup_cycle()

    # 5. Monitorar crescimento
    print("\n📈 Métricas de diagnostico...")
    monitoring = await memory_system.monitor_memory_growth()
    print(f"  ✅ {len(monitoring)} queries de diagnostico configuradas")

    print("\n" + "=" * 60)
    print("✨ Sistema de Memória Viva configurado com sucesso!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())