"""
Sistema de memória Neo4j baseado no repositório oficial neo4j-contrib/mcp-neo4j.

Este módulo implementa a classe Neo4jMemory que gerencia entidades e relações
no grafo de conhecimento usando AsyncDriver do Neo4j.
"""
import logging
from typing import Any, Dict, List

from neo4j import AsyncDriver, RoutingControl

from .entities import (
    Entity,
    Relation,
    KnowledgeGraph,
    ObservationAddition,
    ObservationDeletion,
)
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


class Neo4jMemory:
    """
    Sistema de memória viva no Neo4j.

    Esta classe fornece interface de alto nível para gerenciar entidades,
    relações e observações no grafo de conhecimento. Baseada na implementação
    oficial do neo4j-contrib/mcp-neo4j com extensões para features avançadas.

    Attributes:
        driver: AsyncDriver do Neo4j
    """

    def __init__(self, neo4j_driver: AsyncDriver):
        """
        Inicializa sistema de memória.

        Args:
            neo4j_driver: Driver assíncrono do Neo4j
        """
        self.driver = neo4j_driver

    async def create_fulltext_index(self) -> None:
        """
        Cria índice fulltext para busca em entidades.

        O índice permite busca eficiente por nome, tipo e observações.
        É safe chamar múltiplas vezes (usa IF NOT EXISTS).

        Raises:
            Exception: Se houver erro ao criar índice
        """
        try:
            query = """
            CREATE FULLTEXT INDEX search IF NOT EXISTS
            FOR (m:Memory)
            ON EACH [m.name, m.type, m.observations]
            """
            await self.driver.execute_query(
                query,
                routing_control=RoutingControl.WRITE
            )
            logger.info("Índice fulltext criado/verificado")

        except Exception as e:
            # Index pode já existir, o que é ok
            logger.debug(f"Criação de índice fulltext: {e}")

    async def load_graph(self, filter_query: str = "*") -> KnowledgeGraph:
        """
        Carrega grafo de conhecimento do Neo4j.

        Args:
            filter_query: Query de filtro para busca fulltext (padrão: "*" para tudo)

        Returns:
            KnowledgeGraph com entidades e relações

        Example:
            # Carregar tudo
            graph = await memory.load_graph()

            # Buscar específico
            graph = await memory.load_graph("John Smith")
        """
        logger.info("Carregando grafo de conhecimento do Neo4j")

        query = """
            CALL db.index.fulltext.queryNodes('search', $filter)
            YIELD node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct {
                name: entity.name,
                type: entity.type,
                observations: entity.observations
            }) as nodes,
            collect(distinct {
                source: startNode(r).name,
                target: endNode(r).name,
                relationType: type(r)
            }) as relations
        """

        result = await self.driver.execute_query(
            query,
            {"filter": filter_query},
            routing_control=RoutingControl.READ
        )

        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])

        record = result.records[0]
        nodes = record.get('nodes', [])
        rels = record.get('relations', [])

        # Converter para modelos Pydantic
        entities = [
            Entity(
                name=node['name'],
                type=node['type'],
                observations=node.get('observations', [])
            )
            for node in nodes if node.get('name')
        ]

        relations = [
            Relation(
                source=rel['source'],
                target=rel['target'],
                relationType=rel['relationType']
            )
            for rel in rels if rel.get('relationType')
        ]

        logger.debug(f"Carregadas {len(entities)} entidades e {len(relations)} relações")

        return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Cria múltiplas entidades no grafo.

        Args:
            entities: Lista de entidades a criar

        Returns:
            Lista de entidades criadas

        Example:
            entities = [
                Entity(name="Alice", type="person", observations=["Developer"]),
                Entity(name="Bob", type="person", observations=["Designer"])
            ]
            created = await memory.create_entities(entities)
        """
        logger.info(f"Criando {len(entities)} entidades")

        for entity in entities:
            query = f"""
            WITH $entity as entity
            MERGE (e:Memory {{ name: entity.name }})
            SET e += entity {{ .type, .observations }}
            SET e:`{entity.type}`
            """
            await self.driver.execute_query(
                query,
                {"entity": entity.model_dump()},
                routing_control=RoutingControl.WRITE
            )

        logger.info(f"Criadas {len(entities)} entidades com sucesso")
        return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        """
        Cria múltiplas relações entre entidades.

        Args:
            relations: Lista de relações a criar

        Returns:
            Lista de relações criadas

        Example:
            relations = [
                Relation(source="Alice", target="Bob", relationType="KNOWS"),
                Relation(source="Alice", target="Neo4j", relationType="WORKS_AT")
            ]
            created = await memory.create_relations(relations)
        """
        logger.info(f"Criando {len(relations)} relações")

        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (from:Memory), (to:Memory)
            WHERE from.name = relation.source
            AND to.name = relation.target
            MERGE (from)-[r:`{relation.relationType}`]->(to)
            """

            await self.driver.execute_query(
                query,
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )

        logger.info(f"Criadas {len(relations)} relações com sucesso")
        return relations

    async def add_observations(
        self,
        observations: List[ObservationAddition]
    ) -> List[Dict[str, Any]]:
        """
        Adiciona observações a entidades existentes.

        Args:
            observations: Lista de observações a adicionar

        Returns:
            Lista de resultados com observações adicionadas

        Example:
            additions = [
                ObservationAddition(
                    entityName="Alice",
                    observations=["Promoted to Senior Developer"]
                )
            ]
            results = await memory.add_observations(additions)
        """
        logger.info(f"Adicionando observações a {len(observations)} entidades")

        query = """
        UNWIND $observations as obs
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.observations WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations, []) + new
        RETURN e.name as name, new
        """

        result = await self.driver.execute_query(
            query,
            {"observations": [obs.model_dump() for obs in observations]},
            routing_control=RoutingControl.WRITE
        )

        results = [
            {
                "entityName": record.get("name"),
                "addedObservations": record.get("new")
            }
            for record in result.records
        ]

        logger.info(f"Observações adicionadas com sucesso")
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        """
        Deleta múltiplas entidades e suas relações associadas.

        Args:
            entity_names: Lista de nomes de entidades a deletar

        Example:
            await memory.delete_entities(["Alice", "Bob"])
        """
        logger.info(f"Deletando {len(entity_names)} entidades")

        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """

        await self.driver.execute_query(
            query,
            {"entities": entity_names},
            routing_control=RoutingControl.WRITE
        )

        logger.info(f"Deletadas {len(entity_names)} entidades com sucesso")

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        """
        Deleta observações específicas de entidades.

        Args:
            deletions: Lista de observações a deletar

        Example:
            deletions = [
                ObservationDeletion(
                    entityName="Alice",
                    observations=["Old job title"]
                )
            ]
            await memory.delete_observations(deletions)
        """
        logger.info(f"Deletando observações de {len(deletions)} entidades")

        query = """
        UNWIND $deletions as d
        MATCH (e:Memory { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations, []) WHERE NOT o IN d.observations]
        """

        await self.driver.execute_query(
            query,
            {"deletions": [deletion.model_dump() for deletion in deletions]},
            routing_control=RoutingControl.WRITE
        )

        logger.info(f"Observações deletadas com sucesso")

    async def delete_relations(self, relations: List[Relation]) -> None:
        """
        Deleta múltiplas relações do grafo.

        Args:
            relations: Lista de relações a deletar

        Example:
            relations = [
                Relation(source="Alice", target="Bob", relationType="KNOWS")
            ]
            await memory.delete_relations(relations)
        """
        logger.info(f"Deletando {len(relations)} relações")

        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (source:Memory)-[r:`{relation.relationType}`]->(target:Memory)
            WHERE source.name = relation.source
            AND target.name = relation.target
            DELETE r
            """

            await self.driver.execute_query(
                query,
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )

        logger.info(f"Deletadas {len(relations)} relações com sucesso")

    async def read_graph(self) -> KnowledgeGraph:
        """
        Lê grafo de conhecimento completo.

        Returns:
            KnowledgeGraph com todas entidades e relações
        """
        return await self.load_graph()

    async def search_memories(self, query: str) -> KnowledgeGraph:
        """
        Busca memórias usando busca fulltext.

        Args:
            query: Query de busca

        Returns:
            KnowledgeGraph com resultados

        Example:
            results = await memory.search_memories("developer")
        """
        logger.info(f"Buscando memórias com query: '{query}'")
        return await self.load_graph(query)

    async def find_memories_by_name(self, names: List[str]) -> KnowledgeGraph:
        """
        Busca memórias específicas por nome.

        Não usa busca fulltext - busca exata por nome.

        Args:
            names: Lista de nomes a buscar

        Returns:
            KnowledgeGraph com entidades encontradas

        Example:
            graph = await memory.find_memories_by_name(["Alice", "Bob"])
        """
        logger.info(f"Buscando {len(names)} memórias por nome")

        query = """
        MATCH (e:Memory)
        WHERE e.name IN $names
        RETURN e.name as name,
               e.type as type,
               e.observations as observations
        """

        result_nodes = await self.driver.execute_query(
            query,
            {"names": names},
            routing_control=RoutingControl.READ
        )

        entities: List[Entity] = []
        for record in result_nodes.records:
            entities.append(Entity(
                name=record['name'],
                type=record['type'],
                observations=record.get('observations', [])
            ))

        # Buscar relações para entidades encontradas
        relations: List[Relation] = []
        if entities:
            query = """
            MATCH (source:Memory)-[r]->(target:Memory)
            WHERE source.name IN $names OR target.name IN $names
            RETURN source.name as source,
                   target.name as target,
                   type(r) as relationType
            """

            result_relations = await self.driver.execute_query(
                query,
                {"names": names},
                routing_control=RoutingControl.READ
            )

            for record in result_relations.records:
                relations.append(Relation(
                    source=record["source"],
                    target=record["target"],
                    relationType=record["relationType"]
                ))

        logger.info(f"Encontradas {len(entities)} entidades e {len(relations)} relações")
        return KnowledgeGraph(entities=entities, relations=relations)
