#!/usr/bin/env python3
"""
MCP Neo4j Server Melhorado - Versão 2.0
Com todas as melhorias baseadas nos aprendizados do projeto
"""

import logging
import os
import sys
import asyncio
import threading
from typing import Any, Optional, Dict, List
from datetime import datetime

# Adicionar path para imports locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

# Importar componentes melhorados
from connection_manager import ConnectionPool, QueryCache, cached_query
from query_builder import QueryBuilder, QueryTemplates, SchemaManager
from batch_operations import BatchProcessor, BulkImporter, TransactionBatcher

# Tentar importar componentes existentes
try:
    from self_improve import SelfImprover, get_context_before_action
    from autonomous import AutonomousImprover, activate_autonomous_mode
except ImportError:
    SelfImprover = None
    AutonomousImprover = None

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configurações do Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Criar servidor MCP
mcp = FastMCP("neo4j-memory-v2")

# Pool de conexões global (lazy initialization)
connection_pool = None
batch_processor = None
bulk_importer = None
query_cache = QueryCache(max_size=100, ttl_seconds=300)


def get_connection_pool():
    """Obtém pool de conexões (lazy initialization)"""
    global connection_pool
    if connection_pool is None:
        connection_pool = ConnectionPool(
            uri=NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
            database=NEO4J_DATABASE
        )
        # Agendar warmup em background
        threading.Thread(target=warmup_connection, daemon=True).start()
    return connection_pool


def get_batch_processor():
    """Obtém processador de batch"""
    global batch_processor
    if batch_processor is None:
        batch_processor = BatchProcessor(get_connection_pool())
    return batch_processor


def get_bulk_importer():
    """Obtém importador em massa"""
    global bulk_importer
    if bulk_importer is None:
        bulk_importer = BulkImporter(get_connection_pool())
    return bulk_importer


def warmup_connection():
    """Warmup da conexão em background"""
    try:
        pool = get_connection_pool()
        pool.execute_with_retry("RETURN 1 as test")
        
        # Criar constraints e índices
        schema_mgr = SchemaManager()
        constraints = schema_mgr.create_constraints()
        for query, params in constraints:
            try:
                pool.execute_with_retry(query, params)
            except Exception as e:
                logger.warning(f"Não foi possível criar constraint/index: {e}")
        
        logger.info("Neo4j warmup e schema setup concluídos")
    except Exception as e:
        logger.warning(f"Warmup falhou (não crítico): {e}")


# ============= FERRAMENTAS MCP MELHORADAS =============

@mcp.tool()
@cached_query(ttl=60)  # Cache por 1 minuto
def search_memories_v2(
    query: Optional[str] = None,
    label: Optional[str] = None,
    limit: int = 10,
    use_fulltext: bool = False
) -> List[Dict[str, Any]]:
    """
    Busca memórias com cache e otimizações
    
    Args:
        query: Texto para buscar
        label: Filtrar por label
        limit: Máximo de resultados
        use_fulltext: Usar índice fulltext se disponível
    
    Returns:
        Lista de memórias encontradas
    """
    pool = get_connection_pool()
    
    if query and use_fulltext:
        # Usar índice fulltext se disponível
        cypher = """
        CALL db.index.fulltext.queryNodes('memory_search_index', $query)
        YIELD node, score
        RETURN node as n, labels(node) as labels, score
        ORDER BY score DESC
        LIMIT $limit
        """
        params = {"query": query, "limit": limit}
    else:
        # Query normal
        cypher, params = QueryTemplates.get_recent_memories(limit, label)
        if query:
            cypher, params = QueryBuilder.search_nodes(label or "Memory", query, limit)
    
    results = pool.execute_with_retry(cypher, params)
    
    # Processar resultados
    memories = []
    for record in results:
        node = record.get("n") or record.get("node")
        if node:
            memories.append({
                "labels": record.get("labels", []),
                "properties": dict(node),
                "score": record.get("score", 1.0)
            })
    
    return memories


@mcp.tool()
def create_memory_v2(
    label: str,
    properties: Dict[str, Any],
    connect_to: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Cria memória com validação e conexões opcionais
    
    Args:
        label: Label da memória
        properties: Propriedades (name é obrigatório)
        connect_to: Lista de IDs para conectar
    
    Returns:
        Memória criada
    """
    pool = get_connection_pool()
    
    # Validar e sanitizar dados
    schema_mgr = SchemaManager()
    properties = schema_mgr.validate_node_data(label, properties)
    
    # Usar query builder
    query, params = QueryBuilder.find_or_create_node(
        label=label,
        name=properties.get("name"),
        properties=properties
    )
    
    results = pool.execute_with_retry(query, params)
    
    if results:
        created_node = results[0]["n"]
        
        # Criar conexões se especificadas
        if connect_to:
            for target_id in connect_to:
                try:
                    rel_query = """
                    MATCH (from), (to)
                    WHERE elementId(from) = $from_id AND elementId(to) = $to_id
                    CREATE (from)-[:RELATED {created_at: datetime()}]->(to)
                    """
                    pool.execute_with_retry(rel_query, {
                        "from_id": created_node.element_id,
                        "to_id": target_id
                    })
                except Exception as e:
                    logger.warning(f"Não foi possível criar conexão com {target_id}: {e}")
        
        return {
            "id": created_node.element_id,
            "labels": list(created_node.labels),
            "properties": dict(created_node)
        }
    
    raise Exception("Falha ao criar memória")


@mcp.tool()
def batch_create_memories(
    memories: List[Dict[str, Any]],
    label: str = "Memory",
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Cria múltiplas memórias em batch
    
    Args:
        memories: Lista de memórias para criar
        label: Label para todas as memórias
        batch_size: Tamanho do batch
    
    Returns:
        Estatísticas da operação
    """
    processor = get_batch_processor()
    
    # Validar dados
    schema_mgr = SchemaManager()
    validated = [
        schema_mgr.validate_node_data(label, mem) 
        for mem in memories
    ]
    
    # Processar em batches
    stats = processor.batch_merge_nodes(label, validated)
    
    # Limpar cache após operação em massa
    query_cache.clear()
    
    return stats


@mcp.tool()
def save_learning(
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    related_to: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Salva um aprendizado no grafo
    
    Args:
        title: Título do aprendizado
        description: Descrição detalhada
        tags: Tags para categorização
        related_to: IDs de memórias relacionadas
    
    Returns:
        Aprendizado criado
    """
    pool = get_connection_pool()
    
    query, params = QueryTemplates.save_learning(title, description, tags)
    results = pool.execute_with_retry(query, params)
    
    if results:
        learning = results[0]["l"]
        
        # Conectar a memórias relacionadas
        if related_to:
            for memory_id in related_to:
                try:
                    rel_query = """
                    MATCH (l:Learning {name: $title}), (m)
                    WHERE elementId(m) = $memory_id
                    CREATE (l)-[:RELATES_TO {created_at: datetime()}]->(m)
                    """
                    pool.execute_with_retry(rel_query, {
                        "title": title,
                        "memory_id": memory_id
                    })
                except Exception as e:
                    logger.warning(f"Não foi possível conectar ao ID {memory_id}: {e}")
        
        return {
            "id": learning.element_id,
            "properties": dict(learning)
        }
    
    raise Exception("Falha ao salvar aprendizado")


@mcp.tool()
def save_bug_fix(
    problem: str,
    solution: str,
    components: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Registra um bug fix no grafo
    
    Args:
        problem: Descrição do problema
        solution: Solução implementada
        components: Componentes afetados
    
    Returns:
        Bug fix registrado
    """
    pool = get_connection_pool()
    
    # Buscar problemas similares primeiro
    similar_query, similar_params = QueryTemplates.find_similar_problems(problem)
    similar = pool.execute_with_retry(similar_query, similar_params)
    
    # Salvar novo bug fix
    query, params = QueryTemplates.save_bug_fix(problem, solution, components)
    results = pool.execute_with_retry(query, params)
    
    if results:
        bug_fix = results[0]["b"]
        
        # Conectar a problemas similares se encontrados
        if similar:
            for sim_bug in similar:
                try:
                    rel_query = """
                    MATCH (b1:BugFix {name: $new_problem}), 
                          (b2:BugFix {name: $similar_problem})
                    CREATE (b1)-[:SIMILAR_TO {similarity: 'high'}]->(b2)
                    """
                    pool.execute_with_retry(rel_query, {
                        "new_problem": problem,
                        "similar_problem": sim_bug["b"]["name"]
                    })
                except Exception:
                    pass  # Não crítico
        
        response = {
            "id": bug_fix.element_id,
            "properties": dict(bug_fix)
        }
        
        if similar:
            response["similar_problems"] = [
                {"problem": s["b"]["problem"], "solution": s["b"]["solution"]}
                for s in similar[:3]
            ]
        
        return response
    
    raise Exception("Falha ao registrar bug fix")


@mcp.tool()
def get_graph_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do grafo e métricas de performance
    
    Returns:
        Estatísticas completas
    """
    pool = get_connection_pool()
    
    # Estatísticas do grafo
    graph_query = """
    MATCH (n)
    WITH count(n) as total_nodes, collect(DISTINCT labels(n)) as all_labels
    MATCH ()-[r]->()
    WITH total_nodes, all_labels, count(r) as total_relationships, 
         collect(DISTINCT type(r)) as all_types
    RETURN {
        nodes: total_nodes,
        relationships: total_relationships,
        labels: all_labels,
        relationship_types: all_types
    } as graph_stats
    """
    
    graph_results = pool.execute_with_retry(graph_query)
    
    # Combinar com métricas do sistema
    stats = {
        "graph": graph_results[0]["graph_stats"] if graph_results else {},
        "connection": pool.get_metrics(),
        "cache": query_cache.get_stats(),
        "batch_processor": get_batch_processor().get_stats() if batch_processor else {}
    }
    
    return stats


@mcp.tool()
def import_data(
    data_type: str,
    data: List[Dict[str, Any]],
    label: Optional[str] = None
) -> Dict[str, Any]:
    """
    Importa dados em massa
    
    Args:
        data_type: Tipo de dados ('csv', 'json_graph')
        data: Dados para importar
        label: Label para os nós (se aplicável)
    
    Returns:
        Estatísticas da importação
    """
    importer = get_bulk_importer()
    
    if data_type == "csv":
        if not label:
            raise ValueError("Label é obrigatório para importação CSV")
        return importer.import_csv_data(data, label)
    
    elif data_type == "json_graph":
        # Espera formato: {"nodes": [...], "edges": [...]}
        if not isinstance(data, dict) or "nodes" not in data:
            raise ValueError("Formato inválido para json_graph")
        return importer.import_json_graph(
            data.get("nodes", []),
            data.get("edges", [])
        )
    
    else:
        raise ValueError(f"Tipo de dados não suportado: {data_type}")


@mcp.tool()
def execute_transaction(
    operations: List[Dict[str, Any]]
) -> List[Any]:
    """
    Executa múltiplas operações em uma única transação
    
    Args:
        operations: Lista de operações com 'query' e 'params'
    
    Returns:
        Resultados de cada operação
    """
    pool = get_connection_pool()
    batcher = TransactionBatcher(pool)
    
    for op in operations:
        if "query" not in op:
            raise ValueError("Cada operação deve ter um 'query'")
        batcher.add_operation(op["query"], op.get("params", {}))
    
    return batcher.execute()


# ============= FERRAMENTAS DE AUTO-MELHORIA =============

if SelfImprover:
    @mcp.tool()
    def self_improve(
        aspect: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sistema de auto-melhoria baseado em aprendizados
        
        Args:
            aspect: Aspecto para melhorar
            context: Contexto adicional
        
        Returns:
            Sugestões de melhoria
        """
        pool = get_connection_pool()
        improver = SelfImprover(pool)
        
        if context:
            full_context = get_context_before_action(pool, context)
        else:
            full_context = {}
        
        return improver.suggest_improvement(aspect, full_context)


if AutonomousImprover:
    @mcp.tool()
    def activate_autonomous(
        interval_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Ativa modo autônomo de melhoria
        
        Args:
            interval_seconds: Intervalo entre melhorias
        
        Returns:
            Status da ativação
        """
        pool = get_connection_pool()
        
        # Ativar em thread separada
        thread = threading.Thread(
            target=activate_autonomous_mode,
            args=(pool, interval_seconds),
            daemon=True
        )
        thread.start()
        
        return {
            "status": "activated",
            "interval": interval_seconds,
            "thread_id": thread.ident
        }


# ============= MAIN =============

def main():
    """Função principal"""
    logger.info("Iniciando servidor MCP Neo4j Memory v2.0...")
    logger.info(f"Neo4j URI: {NEO4J_URI}")
    logger.info(f"Database: {NEO4J_DATABASE}")
    
    # Iniciar warmup em background
    threading.Thread(target=warmup_connection, daemon=True).start()
    
    logger.info("Starting MCP server on stdio transport...")
    
    # Rodar servidor
    mcp.run()
    
    # Cleanup ao sair
    if connection_pool:
        connection_pool.close()
    
    logger.info("Servidor encerrado")


if __name__ == "__main__":
    main()