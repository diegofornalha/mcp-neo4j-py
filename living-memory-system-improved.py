#!/usr/bin/env python3
"""
Sistema de Memória Viva para Neo4j - Versão Melhorada
Mantém apenas aprendizados relevantes e atualizados usando conexões e metadados

Melhorias implementadas:
- Type hints completos
- Padrões pythônicos
- Performance otimizada
- Gestão adequada de recursos
- Documentação completa
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from typing import (
    Any, AsyncGenerator, Dict, List, Optional,
    Protocol, Set, Union, Tuple
)
import json
from concurrent.futures import ThreadPoolExecutor

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CleanupAction(Enum):
    """Enum para tipos de ações de limpeza."""
    DELETE = "delete"
    ARCHIVE = "archive"
    MERGE = "merge"
    UPDATE = "update"


class RelevanceFactors(Enum):
    """Fatores que influenciam relevância."""
    AGE = "age"
    CONNECTIONS = "connections"
    ACCESS_COUNT = "access_count"
    CATEGORY = "category"
    IMPORTANCE = "importance"


@dataclass(frozen=True)
class MemoryNode:
    """Representa um nó de memória com todas suas propriedades."""
    id: str
    name: str
    content: str
    category: str = "general"
    importance: str = "medium"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    access_count: int = 0
    connections: int = 0
    relevance_score: Optional[float] = None

    def __post_init__(self) -> None:
        """Validação pós-inicialização."""
        if not self.id or not self.name:
            raise ValueError("ID e name são obrigatórios")


@dataclass
class CleanupCandidate:
    """Candidato para ação de limpeza."""
    node: MemoryNode
    action: CleanupAction
    reason: str
    priority: int = 0
    similarity_target: Optional[str] = None  # Para merge


@dataclass
class CleanupResults:
    """Resultados de um ciclo de limpeza."""
    timestamp: datetime = field(default_factory=datetime.now)
    deleted: int = 0
    archived: int = 0
    merged: int = 0
    refreshed: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def total_actions(self) -> int:
        """Total de ações executadas."""
        return self.deleted + self.archived + self.merged + self.refreshed


@dataclass
class MemoryHealthMetrics:
    """Métricas de saúde da memória."""
    total_nodes: int
    isolated_nodes: int
    stale_nodes: int
    duplicate_pairs: int
    avg_connections: float
    avg_relevance_score: float
    growth_rate_7d: int


class Neo4jConnection(Protocol):
    """Protocol para conexão com Neo4j."""

    async def execute_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Executa query e retorna resultados."""
        ...

    async def close(self) -> None:
        """Fecha conexão."""
        ...


class MemoryAnalyzer(ABC):
    """Interface para analisadores de memória."""

    @abstractmethod
    async def analyze(self, connection: Neo4jConnection) -> MemoryHealthMetrics:
        """Analisa saúde da memória."""
        ...


class RelevanceCalculator(ABC):
    """Interface para calculadores de relevância."""

    @abstractmethod
    def calculate(self, node: MemoryNode) -> float:
        """Calcula score de relevância."""
        ...


class WeightedRelevanceCalculator(RelevanceCalculator):
    """Calculador de relevância baseado em pesos configuráveis."""

    def __init__(self, weights: Optional[Dict[RelevanceFactors, float]] = None):
        self.weights = weights or {
            RelevanceFactors.AGE: 0.3,
            RelevanceFactors.CONNECTIONS: 0.3,
            RelevanceFactors.ACCESS_COUNT: 0.2,
            RelevanceFactors.CATEGORY: 0.1,
            RelevanceFactors.IMPORTANCE: 0.1,
        }

        # Validar que pesos somam 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Pesos devem somar 1.0, atual: {total_weight}")

    @lru_cache(maxsize=1000)
    def calculate(self, node: MemoryNode) -> float:
        """
        Calcula score de relevância baseado em múltiplos fatores.

        Args:
            node: Nó de memória para avaliar

        Returns:
            Score entre 0.0 e 1.0
        """
        score = 0.0

        # Fator idade
        if node.updated_at:
            age_days = (datetime.now() - node.updated_at).days
            age_score = max(0, 1 - (age_days / 365))  # Decai em 1 ano
            score += age_score * self.weights[RelevanceFactors.AGE]

        # Fator conexões
        connection_score = min(1.0, node.connections / 10)
        score += connection_score * self.weights[RelevanceFactors.CONNECTIONS]

        # Fator acesso
        access_score = min(1.0, node.access_count / 50)
        score += access_score * self.weights[RelevanceFactors.ACCESS_COUNT]

        # Bônus categoria
        if node.category == "professional":
            score += self.weights[RelevanceFactors.CATEGORY]

        # Bônus importância
        if node.importance == "high":
            score += self.weights[RelevanceFactors.IMPORTANCE]

        return min(1.0, score)


class OptimizedMemoryAnalyzer(MemoryAnalyzer):
    """Analisador otimizado com queries eficientes."""

    async def analyze(self, connection: Neo4jConnection) -> MemoryHealthMetrics:
        """
        Analisa saúde da memória com queries otimizadas.

        Args:
            connection: Conexão com Neo4j

        Returns:
            Métricas de saúde da memória
        """

        # Query única otimizada para múltiplas métricas
        analysis_query = """
        // Análise completa em uma query
        CALL {
            // Contadores básicos
            MATCH (n:Learning)
            RETURN
                count(n) as total_nodes,
                avg(n.relevance_score) as avg_relevance
        }
        CALL {
            // Nós isolados
            MATCH (n:Learning)
            WHERE NOT EXISTS((n)-[]-())
            RETURN count(n) as isolated_count
        }
        CALL {
            // Nós obsoletos
            MATCH (n:Learning)
            WHERE n.updated_at < datetime() - duration('P90D')
            OR (n.updated_at IS NULL AND n.created_at < datetime() - duration('P90D'))
            RETURN count(n) as stale_count
        }
        CALL {
            // Duplicatas
            MATCH (n1:Learning), (n2:Learning)
            WHERE n1.id < n2.id AND n1.content = n2.content
            RETURN count(*) as duplicate_count
        }
        CALL {
            // Conexões médias
            MATCH (n:Learning)
            OPTIONAL MATCH (n)-[r]-()
            RETURN avg(count(r)) as avg_connections
        }
        CALL {
            // Crescimento últimos 7 dias
            MATCH (n:Learning)
            WHERE n.created_at > datetime() - duration('P7D')
            RETURN count(n) as growth_7d
        }
        RETURN
            total_nodes,
            isolated_count,
            stale_count,
            duplicate_count,
            avg_connections,
            avg_relevance,
            growth_7d
        """

        results = await connection.execute_query(analysis_query)

        if not results:
            raise RuntimeError("Falha ao obter métricas de saúde")

        result = results[0]

        return MemoryHealthMetrics(
            total_nodes=result["total_nodes"],
            isolated_nodes=result["isolated_count"],
            stale_nodes=result["stale_count"],
            duplicate_pairs=result["duplicate_count"],
            avg_connections=result["avg_connections"] or 0.0,
            avg_relevance_score=result["avg_relevance"] or 0.0,
            growth_rate_7d=result["growth_7d"]
        )


class LivingMemorySystem:
    """
    Sistema otimizado de memória viva para Neo4j.

    Features:
    - Análise eficiente de saúde da memória
    - Cálculo cached de relevância
    - Queries otimizadas
    - Gestão adequada de recursos
    - Type safety completo
    """

    def __init__(
        self,
        connection: Neo4jConnection,
        relevance_calculator: Optional[RelevanceCalculator] = None,
        memory_analyzer: Optional[MemoryAnalyzer] = None,
        relevance_threshold: float = 0.3,
        days_until_stale: int = 90,
        min_connections: int = 1
    ):
        self.connection = connection
        self.relevance_calculator = relevance_calculator or WeightedRelevanceCalculator()
        self.memory_analyzer = memory_analyzer or OptimizedMemoryAnalyzer()
        self.relevance_threshold = relevance_threshold
        self.days_until_stale = days_until_stale
        self.min_connections = min_connections

        # Cache para nós analisados
        self._node_cache: Dict[str, MemoryNode] = {}

    async def analyze_memory_health(self) -> MemoryHealthMetrics:
        """
        Analisa saúde geral da memória.

        Returns:
            Métricas detalhadas de saúde
        """
        return await self.memory_analyzer.analyze(self.connection)

    async def identify_cleanup_candidates(self) -> List[CleanupCandidate]:
        """
        Identifica candidatos para limpeza usando estratégias otimizadas.

        Returns:
            Lista de candidatos ordenada por prioridade
        """
        candidates: List[CleanupCandidate] = []

        # Executar queries em paralelo para melhor performance
        tasks = [
            self._find_isolated_nodes(),
            self._find_stale_nodes(),
            self._find_duplicate_nodes(),
            self._find_low_relevance_nodes()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Erro ao identificar candidatos: {result}")
                continue
            candidates.extend(result)

        # Ordenar por prioridade (maior prioridade primeiro)
        candidates.sort(key=lambda x: x.priority, reverse=True)

        return candidates

    async def _find_isolated_nodes(self) -> List[CleanupCandidate]:
        """Encontra nós isolados (sem conexões)."""
        query = """
        MATCH (n:Learning)
        WHERE NOT EXISTS((n)-[]-())
        AND (n.created_at < datetime() - duration('P30D') OR n.created_at IS NULL)
        RETURN n.id as id, n.name as name, n.content as content,
               n.category as category, n.importance as importance,
               n.created_at as created_at, n.updated_at as updated_at,
               n.access_count as access_count, 0 as connections
        LIMIT 100
        """

        results = await self.connection.execute_query(query)
        candidates = []

        for row in results:
            node = self._row_to_memory_node(row)

            # Decisão baseada em idade e importância
            action = (CleanupAction.DELETE if node.importance != "high"
                     else CleanupAction.ARCHIVE)

            candidates.append(CleanupCandidate(
                node=node,
                action=action,
                reason="Nó isolado sem conexões",
                priority=3 if action == CleanupAction.DELETE else 2
            ))

        return candidates

    async def _find_stale_nodes(self) -> List[CleanupCandidate]:
        """Encontra nós obsoletos."""
        query = f"""
        MATCH (n:Learning)
        WHERE n.updated_at < datetime() - duration('P{self.days_until_stale}D')
        OR (n.updated_at IS NULL AND n.created_at < datetime() - duration('P{self.days_until_stale}D'))
        OPTIONAL MATCH (n)-[r]-()
        RETURN n.id as id, n.name as name, n.content as content,
               n.category as category, n.importance as importance,
               n.created_at as created_at, n.updated_at as updated_at,
               n.access_count as access_count, count(r) as connections
        LIMIT 100
        """

        results = await self.connection.execute_query(query)
        candidates = []

        for row in results:
            node = self._row_to_memory_node(row)

            # Estratégia baseada em conexões e relevância
            relevance = self.relevance_calculator.calculate(node)

            if relevance < self.relevance_threshold:
                action = CleanupAction.DELETE
                priority = 4
            else:
                action = CleanupAction.ARCHIVE
                priority = 1

            candidates.append(CleanupCandidate(
                node=node,
                action=action,
                reason=f"Nó obsoleto (relevância: {relevance:.2f})",
                priority=priority
            ))

        return candidates

    async def _find_duplicate_nodes(self) -> List[CleanupCandidate]:
        """Encontra nós duplicados usando hash de conteúdo."""
        query = """
        MATCH (n:Learning)
        WITH n.content as content, collect(n) as nodes
        WHERE size(nodes) > 1
        UNWIND nodes as node
        WITH content, nodes, node
        ORDER BY node.updated_at DESC, node.access_count DESC
        WITH content, collect(node)[1..] as duplicates, collect(node)[0] as keeper
        UNWIND duplicates as dup
        RETURN dup.id as id, dup.name as name, dup.content as content,
               dup.category as category, dup.importance as importance,
               dup.created_at as created_at, dup.updated_at as updated_at,
               dup.access_count as access_count, 0 as connections,
               keeper.id as target_id
        LIMIT 50
        """

        results = await self.connection.execute_query(query)
        candidates = []

        for row in results:
            node = self._row_to_memory_node(row)

            candidates.append(CleanupCandidate(
                node=node,
                action=CleanupAction.MERGE,
                reason="Conteúdo duplicado detectado",
                priority=3,
                similarity_target=row["target_id"]
            ))

        return candidates

    async def _find_low_relevance_nodes(self) -> List[CleanupCandidate]:
        """Encontra nós com baixa relevância."""
        query = """
        MATCH (n:Learning)
        OPTIONAL MATCH (n)-[r]-()
        WITH n, count(r) as connections
        WHERE connections < $min_connections
        RETURN n.id as id, n.name as name, n.content as content,
               n.category as category, n.importance as importance,
               n.created_at as created_at, n.updated_at as updated_at,
               n.access_count as access_count, connections
        LIMIT 100
        """

        results = await self.connection.execute_query(
            query,
            {"min_connections": self.min_connections}
        )

        candidates = []

        for row in results:
            node = self._row_to_memory_node(row)
            relevance = self.relevance_calculator.calculate(node)

            if relevance < self.relevance_threshold:
                candidates.append(CleanupCandidate(
                    node=node,
                    action=CleanupAction.DELETE,
                    reason=f"Baixa relevância ({relevance:.2f})",
                    priority=2
                ))

        return candidates

    def _row_to_memory_node(self, row: Dict[str, Any]) -> MemoryNode:
        """Converte row do Neo4j para MemoryNode."""
        return MemoryNode(
            id=row["id"],
            name=row["name"],
            content=row["content"] or "",
            category=row.get("category", "general"),
            importance=row.get("importance", "medium"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            access_count=row.get("access_count", 0),
            connections=row.get("connections", 0)
        )

    async def apply_cleanup_actions(self, candidates: List[CleanupCandidate]) -> CleanupResults:
        """
        Aplica ações de limpeza com controle de erros.

        Args:
            candidates: Lista de candidatos para limpeza

        Returns:
            Resultados detalhados da limpeza
        """
        results = CleanupResults()

        # Agrupar por tipo de ação para otimizar
        actions_map: Dict[CleanupAction, List[CleanupCandidate]] = {}
        for candidate in candidates:
            if candidate.action not in actions_map:
                actions_map[candidate.action] = []
            actions_map[candidate.action].append(candidate)

        # Executar cada tipo de ação
        for action, action_candidates in actions_map.items():
            try:
                if action == CleanupAction.DELETE:
                    count = await self._delete_nodes(action_candidates)
                    results.deleted = count
                elif action == CleanupAction.ARCHIVE:
                    count = await self._archive_nodes(action_candidates)
                    results.archived = count
                elif action == CleanupAction.MERGE:
                    count = await self._merge_nodes(action_candidates)
                    results.merged = count
                elif action == CleanupAction.UPDATE:
                    count = await self._update_nodes(action_candidates)
                    results.refreshed = count

            except Exception as e:
                error_msg = f"Erro ao executar {action.value}: {e}"
                logger.error(error_msg)
                results.errors.append(error_msg)

        return results

    async def _delete_nodes(self, candidates: List[CleanupCandidate]) -> int:
        """Deleta nós irrelevantes."""
        if not candidates:
            return 0

        node_ids = [c.node.id for c in candidates]

        query = """
        MATCH (n:Learning)
        WHERE n.id IN $node_ids
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """

        results = await self.connection.execute_query(query, {"node_ids": node_ids})
        return results[0]["deleted_count"] if results else 0

    async def _archive_nodes(self, candidates: List[CleanupCandidate]) -> int:
        """Arquiva nós antigos mas potencialmente úteis."""
        if not candidates:
            return 0

        node_ids = [c.node.id for c in candidates]

        query = """
        MATCH (n:Learning)
        WHERE n.id IN $node_ids
        SET n:Archive, n.archived_at = datetime()
        REMOVE n:Learning
        RETURN count(n) as archived_count
        """

        results = await self.connection.execute_query(query, {"node_ids": node_ids})
        return results[0]["archived_count"] if results else 0

    async def _merge_nodes(self, candidates: List[CleanupCandidate]) -> int:
        """Mescla nós duplicados."""
        merged_count = 0

        for candidate in candidates:
            if not candidate.similarity_target:
                continue

            query = """
            MATCH (source:Learning {id: $source_id}), (target:Learning {id: $target_id})
            // Transferir conexões únicas
            MATCH (source)-[r]-(other)
            WHERE NOT (target)-[]-(other)
            CREATE (target)-[r2]-(other)
            SET r2 = properties(r)
            // Mesclar metadados
            SET target.merged_content = coalesce(target.merged_content, []) + [source.content]
            SET target.updated_at = datetime()
            SET target.access_count = target.access_count + source.access_count
            // Deletar source
            DETACH DELETE source
            RETURN 1 as merged
            """

            try:
                results = await self.connection.execute_query(query, {
                    "source_id": candidate.node.id,
                    "target_id": candidate.similarity_target
                })

                if results and results[0]["merged"]:
                    merged_count += 1

            except Exception as e:
                logger.error(f"Erro ao mesclar {candidate.node.id}: {e}")

        return merged_count

    async def _update_nodes(self, candidates: List[CleanupCandidate]) -> int:
        """Atualiza timestamp de nós acessados."""
        if not candidates:
            return 0

        node_ids = [c.node.id for c in candidates]

        query = """
        MATCH (n:Learning)
        WHERE n.id IN $node_ids
        SET n.last_accessed = datetime(),
            n.access_count = coalesce(n.access_count, 0) + 1,
            n.updated_at = datetime()
        RETURN count(n) as updated_count
        """

        results = await self.connection.execute_query(query, {"node_ids": node_ids})
        return results[0]["updated_count"] if results else 0


class AutoCleanupScheduler:
    """
    Agendador automático otimizado para limpeza periódica.

    Features:
    - Controle de concorrência
    - Logging detalhado
    - Métricas de performance
    - Tratamento robusto de erros
    """

    def __init__(
        self,
        memory_system: LivingMemorySystem,
        cleanup_interval: int = 24 * 3600,  # 24 horas
        max_candidates_per_cycle: int = 1000
    ):
        self.memory_system = memory_system
        self.cleanup_interval = cleanup_interval
        self.max_candidates_per_cycle = max_candidates_per_cycle
        self.last_cleanup: Optional[datetime] = None
        self._is_running = False

    async def run_cleanup_cycle(self) -> CleanupResults:
        """
        Executa ciclo completo de limpeza com logging detalhado.

        Returns:
            Resultados detalhados do ciclo
        """
        if self._is_running:
            raise RuntimeError("Ciclo de limpeza já em execução")

        self._is_running = True
        start_time = datetime.now()

        try:
            logger.info("🔄 Iniciando ciclo de limpeza da memória viva...")

            # 1. Analisar saúde atual
            logger.info("📊 Analisando saúde atual da memória...")
            health_before = await self.memory_system.analyze_memory_health()

            logger.info(f"📈 Estado atual: {health_before.total_nodes} nós, "
                       f"{health_before.isolated_nodes} isolados, "
                       f"relevância média: {health_before.avg_relevance_score:.2f}")

            # 2. Identificar candidatos
            logger.info("🎯 Identificando candidatos para limpeza...")
            candidates = await self.memory_system.identify_cleanup_candidates()

            # Limitar número de candidatos por ciclo
            if len(candidates) > self.max_candidates_per_cycle:
                logger.warning(f"⚠️ Limitando candidatos de {len(candidates)} para {self.max_candidates_per_cycle}")
                candidates = candidates[:self.max_candidates_per_cycle]

            # Log estatísticas dos candidatos
            action_counts = {}
            for candidate in candidates:
                action = candidate.action.value
                action_counts[action] = action_counts.get(action, 0) + 1

            for action, count in action_counts.items():
                logger.info(f"  📋 {action}: {count} candidatos")

            # 3. Aplicar limpeza
            if candidates:
                logger.info("🧹 Aplicando ações de limpeza...")
                results = await self.memory_system.apply_cleanup_actions(candidates)

                # Log resultados
                if results.deleted > 0:
                    logger.info(f"  🗑️ Deletados: {results.deleted} nós")
                if results.archived > 0:
                    logger.info(f"  📦 Arquivados: {results.archived} nós")
                if results.merged > 0:
                    logger.info(f"  🔀 Mesclados: {results.merged} pares")
                if results.refreshed > 0:
                    logger.info(f"  🔄 Atualizados: {results.refreshed} nós")

                if results.errors:
                    logger.error(f"❌ Erros durante limpeza: {len(results.errors)}")
                    for error in results.errors:
                        logger.error(f"  {error}")

            else:
                logger.info("✨ Nenhuma ação de limpeza necessária")
                results = CleanupResults()

            # 4. Analisar saúde após limpeza
            health_after = await self.memory_system.analyze_memory_health()

            duration = datetime.now() - start_time
            logger.info(f"✅ Ciclo completado em {duration.total_seconds():.1f}s - "
                       f"{results.total_actions} ações executadas")

            # 5. Registrar métricas
            await self._log_cleanup_metrics(results, health_before, health_after, duration)

            self.last_cleanup = datetime.now()
            return results

        finally:
            self._is_running = False

    async def _log_cleanup_metrics(
        self,
        results: CleanupResults,
        health_before: MemoryHealthMetrics,
        health_after: MemoryHealthMetrics,
        duration: timedelta
    ) -> None:
        """Registra métricas detalhadas do ciclo."""

        improvement_metrics = {
            "nodes_removed": health_before.total_nodes - health_after.total_nodes,
            "isolated_reduction": health_before.isolated_nodes - health_after.isolated_nodes,
            "relevance_improvement": health_after.avg_relevance_score - health_before.avg_relevance_score,
            "duration_seconds": duration.total_seconds()
        }

        logger.info(f"📊 Métricas de melhoria: {improvement_metrics}")

        # Em produção, salvar no Neo4j
        cleanup_log_query = """
        CREATE (log:CleanupLog {
            timestamp: datetime(),
            duration_seconds: $duration,
            deleted_count: $deleted,
            archived_count: $archived,
            merged_count: $merged,
            refreshed_count: $refreshed,
            total_actions: $total_actions,
            nodes_before: $nodes_before,
            nodes_after: $nodes_after,
            relevance_improvement: $relevance_improvement
        })
        RETURN log.timestamp as logged_at
        """

        try:
            await self.memory_system.connection.execute_query(cleanup_log_query, {
                "duration": duration.total_seconds(),
                "deleted": results.deleted,
                "archived": results.archived,
                "merged": results.merged,
                "refreshed": results.refreshed,
                "total_actions": results.total_actions,
                "nodes_before": health_before.total_nodes,
                "nodes_after": health_after.total_nodes,
                "relevance_improvement": improvement_metrics["relevance_improvement"]
            })

            logger.info("📝 Métricas registradas no Neo4j")

        except Exception as e:
            logger.error(f"Erro ao registrar métricas: {e}")


# Mock connection para demonstração
class MockNeo4jConnection:
    """Conexão mock para testes e demonstração."""

    async def execute_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Simula execução de query."""
        # Em produção, usar driver real do Neo4j
        logger.debug(f"Executando query: {query[:100]}...")

        # Retornar dados mock baseados no tipo de query
        if "total_nodes" in query:
            return [{
                "total_nodes": 150,
                "isolated_count": 15,
                "stale_count": 25,
                "duplicate_count": 5,
                "avg_connections": 3.2,
                "avg_relevance": 0.65,
                "growth_7d": 12
            }]
        elif "DETACH DELETE" in query:
            return [{"deleted_count": len(parameters.get("node_ids", []))}]
        elif "archived_count" in query:
            return [{"archived_count": len(parameters.get("node_ids", []))}]
        else:
            return []

    async def close(self) -> None:
        """Mock close."""
        logger.debug("Conexão mock fechada")


async def main() -> None:
    """
    Demonstração completa do sistema melhorado.
    """

    print("=" * 60)
    print("🧠 SISTEMA DE MEMÓRIA VIVA PARA NEO4J - VERSÃO MELHORADA")
    print("=" * 60)

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Criar conexão mock (em produção usar driver real)
    connection = MockNeo4jConnection()

    try:
        # Configurar sistema com parâmetros customizados
        relevance_calc = WeightedRelevanceCalculator({
            RelevanceFactors.AGE: 0.25,
            RelevanceFactors.CONNECTIONS: 0.35,
            RelevanceFactors.ACCESS_COUNT: 0.25,
            RelevanceFactors.CATEGORY: 0.10,
            RelevanceFactors.IMPORTANCE: 0.05,
        })

        memory_system = LivingMemorySystem(
            connection=connection,
            relevance_calculator=relevance_calc,
            relevance_threshold=0.4,
            days_until_stale=60
        )

        scheduler = AutoCleanupScheduler(
            memory_system=memory_system,
            max_candidates_per_cycle=500
        )

        # Executar análise completa
        print("\n📊 Analisando saúde da memória...")
        health = await memory_system.analyze_memory_health()

        print(f"  Total de nós: {health.total_nodes}")
        print(f"  Nós isolados: {health.isolated_nodes}")
        print(f"  Nós obsoletos: {health.stale_nodes}")
        print(f"  Duplicatas: {health.duplicate_pairs}")
        print(f"  Conexões médias: {health.avg_connections:.1f}")
        print(f"  Relevância média: {health.avg_relevance_score:.2f}")
        print(f"  Crescimento 7d: {health.growth_rate_7d}")

        # Executar ciclo de limpeza
        print("\n🧹 Executando ciclo de limpeza...")
        results = await scheduler.run_cleanup_cycle()

        print(f"\n📈 Resultados do ciclo:")
        print(f"  ✅ Ações totais: {results.total_actions}")
        print(f"  🗑️ Deletados: {results.deleted}")
        print(f"  📦 Arquivados: {results.archived}")
        print(f"  🔀 Mesclados: {results.merged}")
        print(f"  🔄 Atualizados: {results.refreshed}")

        if results.errors:
            print(f"  ❌ Erros: {len(results.errors)}")

    finally:
        await connection.close()

    print("\n" + "=" * 60)
    print("✨ Demonstração completa!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())