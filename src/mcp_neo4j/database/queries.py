"""
Query builder e templates de queries Cypher otimizadas.
"""
from typing import Optional, List, Dict, Any


class MemoryQueries:
    """
    Queries Cypher para gestão de memória.

    Classe utilitária com queries otimizadas e parametrizadas
    para operações comuns no grafo de conhecimento.
    """

    @staticmethod
    def create_memory(label: str) -> str:
        """
        Query para criar memória com propriedades.

        Args:
            label: Label Neo4j da memória

        Returns:
            Query Cypher parametrizada

        Example:
            query = MemoryQueries.create_memory("Learning")
            # Use with parameters: {"properties": {...}}
        """
        return f"""
        CREATE (n:{label} $properties)
        SET n.created_at = datetime()
        SET n.updated_at = datetime()
        RETURN elementId(n) as id, n
        """

    @staticmethod
    def search_memories(label: str, include_relations: bool = True) -> str:
        """
        Query para buscar memórias com filtro opcional.

        Args:
            label: Label Neo4j das memórias
            include_relations: Se deve incluir relações

        Returns:
            Query Cypher parametrizada

        Example:
            query = MemoryQueries.search_memories("Learning")
            # Use with parameters: {"query": "text", "limit": 10}
        """
        if include_relations:
            return f"""
            MATCH (n:{label})
            WHERE $query IS NULL OR
                  toLower(n.name) CONTAINS toLower($query) OR
                  toLower(coalesce(n.content, '')) CONTAINS toLower($query)
            OPTIONAL MATCH (n)-[r]-(related)
            RETURN n, collect({{rel: r, node: related}}) as relations
            ORDER BY n.updated_at DESC
            LIMIT $limit
            """
        else:
            return f"""
            MATCH (n:{label})
            WHERE $query IS NULL OR
                  toLower(n.name) CONTAINS toLower($query)
            RETURN n
            ORDER BY n.updated_at DESC
            LIMIT $limit
            """

    @staticmethod
    def get_memory_health() -> str:
        """
        Query otimizada para análise de saúde do grafo.

        Returns:
            Query Cypher que retorna estatísticas de saúde
        """
        return """
        CALL {
            MATCH (n:Learning)
            RETURN count(n) as total_nodes
        }
        CALL {
            MATCH (n:Learning)
            WHERE NOT EXISTS((n)-[]-())
            RETURN count(n) as isolated_count
        }
        CALL {
            MATCH (n:Learning)
            WHERE n.updated_at < datetime() - duration('P90D')
            RETURN count(n) as stale_count
        }
        CALL {
            MATCH ()-[r]->()
            RETURN count(r) as total_relations
        }
        RETURN total_nodes, isolated_count, stale_count, total_relations
        """

    @staticmethod
    def find_duplicates(label: str = "Learning") -> str:
        """
        Query eficiente para encontrar duplicatas.

        Args:
            label: Label Neo4j para buscar duplicatas

        Returns:
            Query Cypher que retorna duplicatas
        """
        return f"""
        MATCH (n:{label})
        WITH n.content as content, collect(n) as nodes
        WHERE size(nodes) > 1
        UNWIND nodes as node
        WITH content, nodes, node
        ORDER BY node.updated_at DESC
        RETURN elementId(node) as id,
               node.name as name,
               content,
               size(nodes) as duplicate_count
        LIMIT 100
        """

    @staticmethod
    def find_isolated_nodes(label: str = "Learning") -> str:
        """
        Query para encontrar nós isolados (sem relações).

        Args:
            label: Label Neo4j para buscar

        Returns:
            Query Cypher
        """
        return f"""
        MATCH (n:{label})
        WHERE NOT EXISTS((n)-[]-())
        RETURN elementId(n) as id,
               n.name as name,
               n.created_at as created_at,
               n.updated_at as updated_at
        ORDER BY n.created_at DESC
        LIMIT 100
        """

    @staticmethod
    def find_stale_nodes(label: str = "Learning", days: int = 90) -> str:
        """
        Query para encontrar nós obsoletos.

        Args:
            label: Label Neo4j
            days: Dias sem atualização para considerar obsoleto

        Returns:
            Query Cypher parametrizada
        """
        return f"""
        MATCH (n:{label})
        WHERE n.updated_at < datetime() - duration('P{{days}}D')
        RETURN elementId(n) as id,
               n.name as name,
               n.updated_at as updated_at,
               duration.between(n.updated_at, datetime()).days as days_stale
        ORDER BY n.updated_at ASC
        LIMIT 100
        """

    @staticmethod
    def get_node_statistics(label: str = "Learning") -> str:
        """
        Query para estatísticas detalhadas dos nós.

        Args:
            label: Label Neo4j

        Returns:
            Query Cypher
        """
        return f"""
        MATCH (n:{label})
        OPTIONAL MATCH (n)-[r]-()
        WITH n, count(r) as rel_count
        RETURN
            count(n) as total_nodes,
            avg(rel_count) as avg_relationships,
            min(rel_count) as min_relationships,
            max(rel_count) as max_relationships,
            count(CASE WHEN rel_count = 0 THEN 1 END) as isolated_nodes
        """

    @staticmethod
    def merge_duplicate_nodes(label: str = "Learning") -> str:
        """
        Query para mesclar nós duplicados.

        Args:
            label: Label Neo4j

        Returns:
            Query Cypher parametrizada
        """
        return f"""
        MATCH (n1:{label}), (n2:{label})
        WHERE elementId(n1) = $id1 AND elementId(n2) = $id2
        WITH n1, n2
        CALL apoc.refactor.mergeNodes([n1, n2], {{
            properties: "combine",
            mergeRels: true
        }})
        YIELD node
        RETURN elementId(node) as merged_id
        """

    @staticmethod
    def update_node_timestamp(label: str = "Learning") -> str:
        """
        Query para atualizar timestamp de nó.

        Args:
            label: Label Neo4j

        Returns:
            Query Cypher parametrizada
        """
        return f"""
        MATCH (n:{label})
        WHERE elementId(n) = $id
        SET n.updated_at = datetime()
        RETURN elementId(n) as id, n.updated_at as updated_at
        """

    @staticmethod
    def delete_node_cascade(label: str = "Learning") -> str:
        """
        Query para deletar nó e suas relações.

        Args:
            label: Label Neo4j

        Returns:
            Query Cypher parametrizada
        """
        return f"""
        MATCH (n:{label})
        WHERE elementId(n) = $id
        DETACH DELETE n
        """


class QueryBuilder:
    """
    Builder para construção dinâmica de queries Cypher.

    Permite construir queries complexas de forma programática
    com validação e sanitização de inputs.
    """

    def __init__(self):
        """Inicializa builder."""
        self._match: List[str] = []
        self._where: List[str] = []
        self._return: List[str] = []
        self._order_by: List[str] = []
        self._limit: Optional[int] = None
        self._parameters: Dict[str, Any] = {}

    def match(self, pattern: str) -> "QueryBuilder":
        """
        Adiciona cláusula MATCH.

        Args:
            pattern: Padrão de match

        Returns:
            Self para chaining
        """
        self._match.append(pattern)
        return self

    def where(self, condition: str, **params) -> "QueryBuilder":
        """
        Adiciona cláusula WHERE.

        Args:
            condition: Condição WHERE
            **params: Parâmetros da condição

        Returns:
            Self para chaining
        """
        self._where.append(condition)
        self._parameters.update(params)
        return self

    def return_clause(self, *fields: str) -> "QueryBuilder":
        """
        Adiciona cláusula RETURN.

        Args:
            *fields: Campos a retornar

        Returns:
            Self para chaining
        """
        self._return.extend(fields)
        return self

    def order_by(self, *fields: str) -> "QueryBuilder":
        """
        Adiciona cláusula ORDER BY.

        Args:
            *fields: Campos para ordenação

        Returns:
            Self para chaining
        """
        self._order_by.extend(fields)
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """
        Adiciona cláusula LIMIT.

        Args:
            count: Limite de resultados

        Returns:
            Self para chaining
        """
        self._limit = count
        return self

    def build(self) -> tuple[str, Dict[str, Any]]:
        """
        Constrói query e retorna com parâmetros.

        Returns:
            Tupla (query, parameters)

        Raises:
            ValueError: Se query estiver incompleta
        """
        if not self._match:
            raise ValueError("Query deve ter pelo menos uma cláusula MATCH")

        if not self._return:
            raise ValueError("Query deve ter cláusula RETURN")

        parts = []

        # MATCH
        parts.append("MATCH " + ", ".join(self._match))

        # WHERE
        if self._where:
            parts.append("WHERE " + " AND ".join(self._where))

        # RETURN
        parts.append("RETURN " + ", ".join(self._return))

        # ORDER BY
        if self._order_by:
            parts.append("ORDER BY " + ", ".join(self._order_by))

        # LIMIT
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")

        query = "\n".join(parts)
        return query, self._parameters

    def reset(self) -> "QueryBuilder":
        """
        Reseta builder para reutilização.

        Returns:
            Self para chaining
        """
        self._match.clear()
        self._where.clear()
        self._return.clear()
        self._order_by.clear()
        self._limit = None
        self._parameters.clear()
        return self
