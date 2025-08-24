#!/usr/bin/env python3
"""
MCP Neo4j Agent Memory Server - Python Implementation
Servidor MCP para gerenciamento de memórias no Neo4j usando FastMCP
"""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from neo4j import GraphDatabase
from mcp.server.fastmcp import FastMCP

# Configurar logging para stderr (nunca stdout!)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Por padrão vai para stderr
)
logger = logging.getLogger(__name__)

# Criar servidor MCP
mcp = FastMCP("neo4j-memory")

# Configurações do Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
NEO4J_DATABASE = "neo4j"


class Neo4jConnection:
    """Gerenciador de conexão com Neo4j"""
    
    def __init__(self):
        self.driver = None
        self.connect()
    
    def connect(self):
        """Estabelece conexão com Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
            self.driver.verify_connectivity()
            logger.info("Conectado ao Neo4j com sucesso")
        except Exception:
            logger.exception("Erro ao conectar com Neo4j")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Executa query no Neo4j e retorna resultados"""
        if not self.driver:
            self.connect()
        
        try:
            with self.driver.session(database=NEO4J_DATABASE) as session:
                result = session.run(query, params or {})
                return [dict(record) for record in result]
        except Exception:
            logger.exception("Erro ao executar query")
            raise
    
    def close(self):
        """Fecha conexão com Neo4j"""
        if self.driver:
            self.driver.close()


# Instância global da conexão
neo4j_conn = Neo4jConnection()


@mcp.tool()
def search_memories(
    query: Optional[str] = None,
    label: Optional[str] = None,
    limit: int = 10,
    depth: int = 1,
    since_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca memórias no grafo de conhecimento
    
    Args:
        query: Texto para buscar em qualquer propriedade
        label: Filtrar por label da memória
        limit: Máximo de resultados (padrão 10, max 200)
        depth: Profundidade de relacionamentos (padrão 1)
        since_date: Data ISO para filtrar memórias criadas após
    
    Returns:
        Lista de memórias encontradas com suas propriedades
    """
    limit = min(limit, 200)
    
    # Construir query Cypher
    where_clauses = []
    params = {"limit": limit}
    
    if label:
        cypher = f"MATCH (n:{label})"
    else:
        cypher = "MATCH (n)"
    
    if query:
        where_clauses.append(
            "ANY(prop IN keys(n) WHERE "
            "toString(n[prop]) CONTAINS $query)"
        )
        params["query"] = query
    
    if since_date:
        where_clauses.append("n.created_at >= datetime($since_date)")
        params["since_date"] = since_date
    
    if where_clauses:
        cypher += " WHERE " + " AND ".join(where_clauses)
    
    cypher += " RETURN n, labels(n) as labels LIMIT $limit"
    
    results = neo4j_conn.execute_query(cypher, params)
    
    memories = []
    for record in results:
        node = record["n"]
        memory = {
            "id": node.element_id if hasattr(node, 'element_id') else node.id,
            "labels": record["labels"],
            "properties": dict(node)
        }
        memories.append(memory)
    
    return memories


@mcp.tool()
def create_memory(
    label: str,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Cria uma nova memória no grafo
    
    Args:
        label: Label da memória (ex: person, project, idea)
        properties: Propriedades da memória (deve incluir 'name')
    
    Returns:
        Memória criada com ID e propriedades
    """
    if "name" not in properties:
        raise ValueError("Propriedade 'name' é obrigatória")
    
    # Adicionar timestamps
    properties["created_at"] = datetime.now().isoformat()
    properties["updated_at"] = datetime.now().isoformat()
    
    cypher = f"""
    CREATE (n:{label} $props)
    RETURN n, labels(n) as labels, elementId(n) as id
    """
    
    results = neo4j_conn.execute_query(cypher, {"props": properties})
    
    if results:
        record = results[0]
        return {
            "id": record["id"],
            "labels": record["labels"],
            "properties": dict(record["n"])
        }
    
    raise Exception("Falha ao criar memória")


@mcp.tool()
def create_connection(
    from_memory_id: str,
    to_memory_id: str,
    connection_type: str,
    properties: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Cria conexão entre duas memórias
    
    Args:
        from_memory_id: ID da memória origem
        to_memory_id: ID da memória destino
        connection_type: Tipo do relacionamento (ex: KNOWS, WORKS_ON)
        properties: Propriedades opcionais do relacionamento
    
    Returns:
        Informações sobre a conexão criada
    """
    props = properties or {}
    props["created_at"] = datetime.now().isoformat()
    
    cypher = f"""
    MATCH (a), (b)
    WHERE elementId(a) = $from_id AND elementId(b) = $to_id
    CREATE (a)-[r:{connection_type} $props]->(b)
    RETURN r, type(r) as type
    """
    
    params = {
        "from_id": from_memory_id,
        "to_id": to_memory_id,
        "props": props
    }
    
    results = neo4j_conn.execute_query(cypher, params)
    
    if results:
        return {
            "type": results[0]["type"],
            "properties": dict(results[0]["r"]),
            "from": from_memory_id,
            "to": to_memory_id
        }
    
    raise Exception("Falha ao criar conexão")


@mcp.tool()
def update_memory(
    node_id: str,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Atualiza propriedades de uma memória existente
    
    Args:
        node_id: ID da memória a atualizar
        properties: Propriedades para atualizar/adicionar
    
    Returns:
        Memória atualizada
    """
    properties["updated_at"] = datetime.now().isoformat()
    
    cypher = """
    MATCH (n)
    WHERE elementId(n) = $node_id
    SET n += $props
    RETURN n, labels(n) as labels
    """
    
    results = neo4j_conn.execute_query(
        cypher, 
        {"node_id": node_id, "props": properties}
    )
    
    if results:
        record = results[0]
        return {
            "id": node_id,
            "labels": record["labels"],
            "properties": dict(record["n"])
        }
    
    raise Exception("Memória não encontrada")


@mcp.tool()
def delete_memory(node_id: str) -> Dict[str, str]:
    """
    Deleta uma memória e todos seus relacionamentos
    
    Args:
        node_id: ID da memória a deletar
    
    Returns:
        Confirmação da exclusão
    """
    cypher = """
    MATCH (n)
    WHERE elementId(n) = $node_id
    DETACH DELETE n
    RETURN count(n) as deleted
    """
    
    results = neo4j_conn.execute_query(cypher, {"node_id": node_id})
    
    if results and results[0]["deleted"] > 0:
        return {"status": "success", "message": f"Memória {node_id} deletada"}
    
    raise Exception("Memória não encontrada")


@mcp.tool()
def list_memory_labels() -> List[Dict[str, Any]]:
    """
    Lista todos os labels únicos de memória com suas contagens
    
    Returns:
        Lista de labels com contagem de nós
    """
    cypher = """
    MATCH (n)
    WITH labels(n) as node_labels
    UNWIND node_labels as label
    RETURN label, COUNT(*) as count
    ORDER BY count DESC
    """
    
    results = neo4j_conn.execute_query(cypher)
    
    return [
        {"label": r["label"], "count": r["count"]} 
        for r in results
    ]


@mcp.tool()
def get_guidance(topic: Optional[str] = None) -> str:
    """
    Obtém orientações sobre uso das ferramentas de memória
    
    Args:
        topic: Tópico específico (connections, labels, relationships, best-practices)
    
    Returns:
        Texto com orientações
    """
    guidance = {
        "connections": """
        CONEXÕES E RELACIONAMENTOS:
        - Use create_connection para ligar memórias
        - Tipos comuns: KNOWS, WORKS_ON, LIVES_IN, HAS_SKILL
        - Adicione propriedades como 'since', 'role', 'status'
        - Exemplo: pessoa KNOWS pessoa, pessoa WORKS_ON projeto
        """,
        "labels": """
        LABELS RECOMENDADOS:
        - person: Pessoas e contatos
        - project: Projetos e iniciativas
        - organization: Empresas e organizações
        - skill: Habilidades e competências
        - event: Eventos e reuniões
        - idea: Ideias e conceitos
        - task: Tarefas e atividades
        """,
        "best-practices": """
        MELHORES PRÁTICAS:
        - Sempre use 'name' como identificador principal
        - Adicione timestamps com created_at/updated_at
        - Conecte memórias relacionadas
        - Use labels descritivos e consistentes
        - Evite duplicação: busque antes de criar
        """,
        "default": """
        SISTEMA DE MEMÓRIA NEO4J:
        
        Ferramentas disponíveis:
        - search_memories: Buscar memórias existentes
        - create_memory: Criar nova memória
        - create_connection: Conectar memórias
        - update_memory: Atualizar propriedades
        - delete_memory: Remover memória
        - list_memory_labels: Ver todos os labels
        
        Use get_guidance(topic) para mais detalhes sobre:
        - connections: Como criar conexões
        - labels: Labels recomendados
        - best-practices: Melhores práticas
        """
    }
    
    if topic and topic in guidance:
        return guidance[topic]
    
    return guidance["default"]


# Executar servidor
if __name__ == "__main__":
    try:
        logger.info("Iniciando servidor MCP Neo4j Memory...")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception:
        logger.exception("Erro fatal no servidor")
    finally:
        neo4j_conn.close()
        logger.info("Servidor encerrado")