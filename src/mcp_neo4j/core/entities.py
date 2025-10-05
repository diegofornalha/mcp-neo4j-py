"""
Modelos de dados para entidades e relações no grafo de conhecimento.

Baseado no repositório oficial neo4j-contrib/mcp-neo4j com extensões
para suportar features avançadas.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class Entity(BaseModel):
    """
    Representa uma entidade no grafo de conhecimento.

    Uma entidade é um nó no grafo que representa uma pessoa, lugar,
    conceito, evento, etc. Cada entidade tem um nome único, tipo e
    observações associadas.

    Attributes:
        name: Nome único da entidade (identificador)
        type: Tipo da entidade (person, company, location, concept, event, etc)
        observations: Lista de fatos/observações sobre a entidade

    Example:
        {
            "name": "John Smith",
            "type": "person",
            "observations": [
                "Works at Neo4j",
                "Lives in San Francisco",
                "Expert in graph databases"
            ]
        }
    """
    name: str = Field(
        description="Unique identifier/name for the entity. Should be descriptive and specific.",
        min_length=1,
        examples=["John Smith", "Neo4j Inc", "San Francisco"]
    )
    type: str = Field(
        description="Category or classification of the entity. Common types: 'person', 'company', 'location', 'concept', 'event'",
        min_length=1,
        examples=["person", "company", "location", "concept", "event"]
    )
    observations: List[str] = Field(
        description="List of facts, observations, or notes about this entity. Each observation should be a complete, standalone fact.",
        default_factory=list,
        examples=[
            ["Works at Neo4j", "Lives in San Francisco"],
            ["Headquartered in Sweden", "Graph database company"]
        ]
    )


class Relation(BaseModel):
    """
    Representa uma relação entre duas entidades no grafo de conhecimento.

    Uma relação é uma aresta direcionada que conecta duas entidades,
    representando como elas se relacionam.

    Attributes:
        source: Nome da entidade origem (deve existir)
        target: Nome da entidade destino (deve existir)
        relationType: Tipo da relação (WORKS_AT, LIVES_IN, MANAGES, etc)

    Example:
        {
            "source": "John Smith",
            "target": "Neo4j Inc",
            "relationType": "WORKS_AT"
        }
    """
    source: str = Field(
        description="Name of the source entity (must match an existing entity name exactly)",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    target: str = Field(
        description="Name of the target entity (must match an existing entity name exactly)",
        min_length=1,
        examples=["Neo4j Inc", "San Francisco"]
    )
    relationType: str = Field(
        description="Type of relationship between source and target. Use descriptive, uppercase names with underscores.",
        min_length=1,
        examples=["WORKS_AT", "LIVES_IN", "MANAGES", "COLLABORATES_WITH", "LOCATED_IN"]
    )


class KnowledgeGraph(BaseModel):
    """
    Grafo de conhecimento completo contendo entidades e relações.

    Representa uma snapshot completa do grafo de conhecimento,
    incluindo todas as entidades e suas relações.

    Attributes:
        entities: Lista de todas as entidades no grafo
        relations: Lista de todas as relações entre entidades
    """
    entities: List[Entity] = Field(
        description="List of all entities in the knowledge graph",
        default_factory=list
    )
    relations: List[Relation] = Field(
        description="List of all relationships between entities",
        default_factory=list
    )


class ObservationAddition(BaseModel):
    """
    Requisição para adicionar observações a uma entidade existente.

    Usado para adicionar novos fatos/observações a uma entidade
    sem substituir as observações existentes.

    Attributes:
        entityName: Nome exato da entidade existente
        observations: Novas observações a adicionar

    Example:
        {
            "entityName": "John Smith",
            "observations": [
                "Recently promoted to Senior Engineer",
                "Speaks fluent German"
            ]
        }
    """
    entityName: str = Field(
        description="Exact name of the existing entity to add observations to",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    observations: List[str] = Field(
        description="New observations/facts to add to the entity. Each should be unique and informative.",
        min_length=1
    )


class ObservationDeletion(BaseModel):
    """
    Requisição para deletar observações específicas de uma entidade.

    Usado para remover fatos/observações obsoletos ou incorretos
    de uma entidade.

    Attributes:
        entityName: Nome exato da entidade existente
        observations: Observações específicas a remover (deve corresponder exatamente)

    Example:
        {
            "entityName": "John Smith",
            "observations": [
                "Old job title",
                "Outdated contact info"
            ]
        }
    """
    entityName: str = Field(
        description="Exact name of the existing entity to remove observations from",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    observations: List[str] = Field(
        description="Exact observation texts to delete from the entity (must match existing observations exactly)",
        min_length=1
    )


# Modelos adicionais para features avançadas

class MemoryNode(BaseModel):
    """
    Nó de memória no Neo4j (para features avançadas).

    Representa um nó de memória com metadados adicionais
    para features como self-improvement e autonomous learning.

    Attributes:
        id: ID único do nó
        name: Nome da memória
        content: Conteúdo da memória
        category: Categoria da memória
        label: Label Neo4j
        created_at: Data de criação (ISO 8601)
        updated_at: Data de última atualização (ISO 8601)
        properties: Propriedades adicionais
    """
    id: str = Field(description="Unique node ID")
    name: str = Field(description="Memory name")
    content: str = Field(default="", description="Memory content")
    category: str = Field(default="general", description="Memory category")
    label: str = Field(default="Learning", description="Neo4j label")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Update timestamp")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class CleanupCandidate(BaseModel):
    """
    Candidato para limpeza/manutenção do grafo.

    Usado pelo sistema autônomo para identificar nós que
    precisam de atenção (duplicados, obsoletos, isolados, etc).

    Attributes:
        node_id: ID do nó candidato
        reason: Razão para ser candidato (duplicate, stale, isolated, etc)
        action: Ação recomendada (delete, archive, merge, update)
        confidence: Nível de confiança (0.0 - 1.0)
        metadata: Metadados adicionais sobre o candidato
    """
    node_id: str = Field(description="Node ID")
    reason: str = Field(description="Reason for cleanup (duplicate, stale, isolated)")
    action: str = Field(description="Recommended action (delete, archive, merge, update)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
