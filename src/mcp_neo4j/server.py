#!/usr/bin/env python3
"""
MCP Neo4j Agent Memory Server - Python Implementation
Servidor MCP para gerenciamento de memórias no Neo4j usando FastMCP
"""

import logging
import os
from typing import Any, Optional, Dict, List
from datetime import datetime
from neo4j import GraphDatabase
from mcp.server.fastmcp import FastMCP
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from .self_improve import SelfImprover, get_context_before_action
    from .autonomous import AutonomousImprover, activate_autonomous_mode
except ImportError:
    # Para execução direta do script
    from self_improve import SelfImprover, get_context_before_action
    from autonomous import AutonomousImprover, activate_autonomous_mode

import asyncio
import threading

# Configurar logging para stderr (nunca stdout!)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Por padrão vai para stderr
)
logger = logging.getLogger(__name__)

# Criar servidor MCP
mcp = FastMCP("neo4j-memory")

# Configurações do Neo4j (usando variáveis de ambiente ou padrões)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Cancela@1")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


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

# Instância global do sistema autônomo
autonomous_system = None
autonomous_thread = None


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
            "n[prop] IS NOT NULL AND toString(n[prop]) CONTAINS $query)"
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
        # Converter propriedades para formato serializável
        props = {}
        for key, value in dict(node).items():
            # Converter DateTime do Neo4j para string
            if hasattr(value, 'iso_format'):
                props[key] = value.iso_format()
            elif hasattr(value, 'isoformat'):
                props[key] = value.isoformat()
            else:
                props[key] = value
        
        memory = {
            "id": node.element_id if hasattr(node, 'element_id') else node.id,
            "labels": record["labels"],
            "properties": props
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
        node = record["n"]
        # Converter propriedades para formato serializável
        props = {}
        for key, value in dict(node).items():
            if hasattr(value, 'iso_format'):
                props[key] = value.iso_format()
            elif hasattr(value, 'isoformat'):
                props[key] = value.isoformat()
            else:
                props[key] = value
        
        return {
            "id": record["id"],
            "labels": record["labels"],
            "properties": props
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
        rel = results[0]["r"]
        # Converter propriedades para formato serializável
        props = {}
        for key, value in dict(rel).items():
            if hasattr(value, 'iso_format'):
                props[key] = value.iso_format()
            elif hasattr(value, 'isoformat'):
                props[key] = value.isoformat()
            else:
                props[key] = value
        
        return {
            "type": results[0]["type"],
            "properties": props,
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
        node = record["n"]
        # Converter propriedades para formato serializável
        props = {}
        for key, value in dict(node).items():
            if hasattr(value, 'iso_format'):
                props[key] = value.iso_format()
            elif hasattr(value, 'isoformat'):
                props[key] = value.isoformat()
            else:
                props[key] = value
        
        return {
            "id": node_id,
            "labels": record["labels"],
            "properties": props
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
def update_connection(
    from_memory_id: str,
    to_memory_id: str,
    connection_type: str,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Atualiza propriedades de uma conexão existente
    
    Args:
        from_memory_id: ID da memória origem
        to_memory_id: ID da memória destino
        connection_type: Tipo do relacionamento
        properties: Propriedades para atualizar
    
    Returns:
        Conexão atualizada
    """
    props = properties or {}
    props["updated_at"] = datetime.now().isoformat()
    
    cypher = f"""
    MATCH (a)-[r:{connection_type}]->(b)
    WHERE elementId(a) = $from_id AND elementId(b) = $to_id
    SET r += $props
    RETURN r, type(r) as type
    """
    
    params = {
        "from_id": from_memory_id,
        "to_id": to_memory_id,
        "props": props
    }
    
    results = neo4j_conn.execute_query(cypher, params)
    
    if results:
        rel = results[0]["r"]
        # Converter propriedades para formato serializável
        props = {}
        for key, value in dict(rel).items():
            if hasattr(value, 'iso_format'):
                props[key] = value.iso_format()
            elif hasattr(value, 'isoformat'):
                props[key] = value.isoformat()
            else:
                props[key] = value
        
        return {
            "type": results[0]["type"],
            "properties": props,
            "from": from_memory_id,
            "to": to_memory_id
        }
    
    raise Exception("Conexão não encontrada")


@mcp.tool()
def delete_connection(
    from_memory_id: str,
    to_memory_id: str,
    connection_type: str
) -> Dict[str, str]:
    """
    Deleta uma conexão específica entre duas memórias
    
    Args:
        from_memory_id: ID da memória origem
        to_memory_id: ID da memória destino
        connection_type: Tipo do relacionamento
    
    Returns:
        Confirmação da exclusão
    """
    cypher = f"""
    MATCH (a)-[r:{connection_type}]->(b)
    WHERE elementId(a) = $from_id AND elementId(b) = $to_id
    DELETE r
    RETURN count(r) as deleted
    """
    
    params = {
        "from_id": from_memory_id,
        "to_id": to_memory_id
    }
    
    results = neo4j_conn.execute_query(cypher, params)
    
    if results and results[0]["deleted"] > 0:
        return {"status": "success", "message": "Conexão deletada"}
    
    raise Exception("Conexão não encontrada")


@mcp.tool()
def get_context_for_task(task_description: str) -> str:
    """
    Busca contexto e conhecimento relevante antes de executar uma tarefa
    
    Args:
        task_description: Descrição da tarefa a ser executada
    
    Returns:
        Contexto relevante incluindo regras, conhecimento e avisos
    """
    return get_context_before_action(neo4j_conn, task_description)


@mcp.tool()
def learn_from_result(
    task: str,
    result: str,
    success: bool = True,
    category: Optional[str] = None
) -> Dict[str, str]:
    """
    Registra aprendizado de uma execução no grafo
    
    Args:
        task: Tarefa executada
        result: Resultado obtido
        success: Se foi bem-sucedido
        category: Categoria do aprendizado (opcional)
    
    Returns:
        Confirmação do aprendizado salvo
    """
    improver = SelfImprover(neo4j_conn)
    improver.learn_from_execution(task, result, success)
    
    if category:
        learning = {
            "name": f"{category}_{datetime.now().timestamp()}",
            "task": task,
            "result": result,
            "success": success
        }
        improver.save_learning(category, learning)
    
    return {
        "status": "learned",
        "message": f"Aprendizado {'positivo' if success else 'de erro'} registrado"
    }


@mcp.tool()
def suggest_best_approach(current_task: str) -> Dict[str, Any]:
    """
    Sugere a melhor abordagem baseada no conhecimento do grafo
    
    Args:
        current_task: Descrição da tarefa atual
    
    Returns:
        Sugestões incluindo regras, conhecimento relevante e decisões passadas
    """
    improver = SelfImprover(neo4j_conn)
    suggestions = improver.suggest_improvements(current_task)
    
    # Formatar resposta
    response = {
        "task": current_task,
        "suggestions": []
    }
    
    # Adicionar regras mais importantes
    if suggestions["rules"]:
        response["important_rules"] = [
            r["description"] for r in suggestions["rules"][:3]
            if r.get("description")
        ]
    
    # Adicionar conhecimento relevante
    if suggestions["relevant_knowledge"]:
        response["relevant_knowledge"] = [
            {
                "type": k["labels"][0] if k.get("labels") else "unknown",
                "name": k.get("name", ""),
                "info": k.get("description", k.get("content", ""))[:100]
            }
            for k in suggestions["relevant_knowledge"][:3]
        ]
    
    # Adicionar decisões passadas
    if suggestions["past_decisions"]:
        response["past_decisions"] = [
            {
                "topic": d.get("topic"),
                "decision": d.get("decision"),
                "outcome": d.get("outcome")
            }
            for d in suggestions["past_decisions"][:2]
        ]
    
    # Adicionar avisos
    if suggestions["warnings"]:
        response["warnings"] = [
            f"{w.get('type', '')}: {w.get('solution', '')}"
            for w in suggestions["warnings"]
        ]
    
    return response


@mcp.tool()
def activate_autonomous() -> Dict[str, str]:
    """
    Ativa o modo autônomo de auto-aprimoramento
    
    O sistema irá:
    - Monitorar continuamente o Neo4j
    - Aprender com novos dados automaticamente
    - Detectar e salvar padrões
    - Aplicar aprendizados
    - Consolidar conhecimento
    
    Returns:
        Status da ativação
    """
    global autonomous_system, autonomous_thread
    
    if autonomous_system and autonomous_system.running:
        return {
            "status": "already_active",
            "message": "Sistema autônomo já está ativo"
        }
    
    try:
        # Criar instância do sistema autônomo
        improver = SelfImprover(neo4j_conn)
        autonomous_system = AutonomousImprover(neo4j_conn, improver)
        
        # Executar em thread separada
        def run_autonomous():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(autonomous_system.start())
        
        autonomous_thread = threading.Thread(target=run_autonomous, daemon=True)
        autonomous_thread.start()
        
        # Salvar estado no Neo4j
        neo4j_conn.execute_query("""
            CREATE (a:AutonomousMode {
                activated_at: datetime(),
                status: 'active',
                monitoring_interval: 30
            })
        """)
        
        logger.info("🤖 Modo autônomo ativado com sucesso")
        
        return {
            "status": "activated",
            "message": "Sistema autônomo ativado - monitorando e aprendendo continuamente",
            "features": [
                "Monitoramento contínuo a cada 30 segundos",
                "Aplicação automática de aprendizados",
                "Detecção de padrões",
                "Consolidação de conhecimento",
                "Limpeza automática de dados obsoletos"
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro ao ativar modo autônomo: {e}")
        return {
            "status": "error",
            "message": f"Erro ao ativar: {str(e)}"
        }


@mcp.tool()
def deactivate_autonomous() -> Dict[str, str]:
    """
    Desativa o modo autônomo
    
    Returns:
        Status da desativação
    """
    global autonomous_system
    
    if not autonomous_system or not autonomous_system.running:
        return {
            "status": "not_active",
            "message": "Sistema autônomo não está ativo"
        }
    
    try:
        autonomous_system.stop()
        
        # Atualizar estado no Neo4j
        neo4j_conn.execute_query("""
            MATCH (a:AutonomousMode {status: 'active'})
            SET a.status = 'inactive',
                a.deactivated_at = datetime()
        """)
        
        logger.info("🛑 Modo autônomo desativado")
        
        return {
            "status": "deactivated",
            "message": "Sistema autônomo desativado com sucesso"
        }
        
    except Exception as e:
        logger.error(f"Erro ao desativar modo autônomo: {e}")
        return {
            "status": "error",
            "message": f"Erro ao desativar: {str(e)}"
        }


@mcp.tool()
def autonomous_status() -> Dict[str, Any]:
    """
    Verifica o status do sistema autônomo
    
    Returns:
        Status detalhado do sistema
    """
    global autonomous_system
    
    # Buscar status no Neo4j
    result = neo4j_conn.execute_query("""
        MATCH (a:AutonomousMode)
        RETURN a
        ORDER BY a.activated_at DESC
        LIMIT 1
    """)
    
    neo4j_status = result[0]["a"] if result else None
    
    response = {
        "active": autonomous_system and autonomous_system.running,
        "monitoring_interval": autonomous_system.monitoring_interval if autonomous_system else None,
        "last_check": autonomous_system.last_check.isoformat() if autonomous_system and hasattr(autonomous_system, 'last_check') else None
    }
    
    if neo4j_status:
        # Converter DateTime para string
        activated_at = neo4j_status.get("activated_at")
        deactivated_at = neo4j_status.get("deactivated_at")
        
        if hasattr(activated_at, 'iso_format'):
            activated_at = activated_at.iso_format()
        elif hasattr(activated_at, 'isoformat'):
            activated_at = activated_at.isoformat()
        
        if hasattr(deactivated_at, 'iso_format'):
            deactivated_at = deactivated_at.iso_format()
        elif hasattr(deactivated_at, 'isoformat'):
            deactivated_at = deactivated_at.isoformat()
        
        response["neo4j_status"] = {
            "status": neo4j_status.get("status"),
            "activated_at": activated_at,
            "deactivated_at": deactivated_at
        }
    
    # Buscar estatísticas
    stats = neo4j_conn.execute_query("""
        MATCH (l:Learning)
        WITH count(l) as total_learnings,
             sum(CASE WHEN l.applied = true THEN 1 ELSE 0 END) as applied_learnings
        MATCH (p:Pattern)
        WITH total_learnings, applied_learnings, count(p) as patterns_detected
        MATCH (e:Error)
        WITH total_learnings, applied_learnings, patterns_detected, count(e) as errors_logged
        RETURN total_learnings, applied_learnings, patterns_detected, errors_logged
    """)
    
    if stats:
        response["statistics"] = {
            "total_learnings": stats[0].get("total_learnings", 0),
            "applied_learnings": stats[0].get("applied_learnings", 0),
            "patterns_detected": stats[0].get("patterns_detected", 0),
            "errors_logged": stats[0].get("errors_logged", 0)
        }
    
    return response


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
        - document: Documentos e arquivos
        - location: Lugares e endereços
        """,
        "relationships": """
        TIPOS DE RELACIONAMENTOS:
        - KNOWS: Entre pessoas
        - WORKS_ON: Pessoa -> Projeto
        - WORKS_AT: Pessoa -> Organização
        - MANAGES: Pessoa -> Pessoa/Projeto
        - LOCATED_IN: Qualquer -> Location
        - RELATED_TO: Conexão genérica
        - CREATED_BY: Qualquer -> Pessoa
        - PART_OF: Componente -> Todo
        """,
        "best-practices": """
        MELHORES PRÁTICAS:
        - Sempre use 'name' como identificador principal
        - Adicione timestamps com created_at/updated_at
        - Conecte memórias relacionadas
        - Use labels descritivos e consistentes
        - Evite duplicação: busque antes de criar
        - Mantenha propriedades simples e relevantes
        - Use relacionamentos para expressar contexto
        """,
        "examples": """
        EXEMPLOS DE USO:
        
        1. Criar pessoa:
        create_memory("person", {"name": "João Silva", "email": "joao@example.com"})
        
        2. Criar projeto:
        create_memory("project", {"name": "MCP Neo4j", "status": "active"})
        
        3. Conectar pessoa a projeto:
        create_connection(person_id, project_id, "WORKS_ON", {"role": "developer"})
        
        4. Buscar memórias:
        search_memories(query="Python", label="skill", limit=5)
        """,
        "default": """
        SISTEMA DE MEMÓRIA NEO4J - GUIA COMPLETO
        
        📚 FERRAMENTAS DISPONÍVEIS:
        - search_memories: Buscar memórias existentes
        - create_memory: Criar nova memória
        - create_connection: Conectar memórias
        - update_memory: Atualizar propriedades
        - update_connection: Atualizar conexão
        - delete_memory: Remover memória
        - delete_connection: Remover conexão
        - list_memory_labels: Ver todos os labels
        - get_guidance: Obter ajuda
        
        📖 TÓPICOS DE AJUDA:
        Use get_guidance(topic) para mais detalhes:
        - "connections": Como criar e gerenciar conexões
        - "labels": Labels recomendados para memórias
        - "relationships": Tipos de relacionamentos
        - "best-practices": Melhores práticas
        - "examples": Exemplos práticos
        
        💡 DICA: Sempre busque antes de criar para evitar duplicatas!
        """
    }
    
    if topic and topic in guidance:
        return guidance[topic]
    
    return guidance["default"]


def main():
    """Função principal para executar o servidor"""
    try:
        logger.info("Iniciando servidor MCP Neo4j Memory (Python)...")
        logger.info(f"Neo4j URI: {NEO4J_URI}")
        logger.info(f"Database: {NEO4J_DATABASE}")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception:
        logger.exception("Erro fatal no servidor")
    finally:
        neo4j_conn.close()
        logger.info("Servidor encerrado")


# Executar servidor
if __name__ == "__main__":
    main()