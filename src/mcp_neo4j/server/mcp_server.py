"""FastMCP server definition for the Neo4j memory backend."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from ..core.entities import (
    Entity,
    ObservationAddition,
    ObservationDeletion,
    Relation,
)
from ..core.memory import Neo4jMemory
from ..utils.formatting import format_namespace
from ..utils.logging_setup import get_logger
from ..utils.validation import (
    validate_entity_name,
    validate_relation_type,
)

logger = get_logger(__name__)


def _handle_error(message: str, error: Exception) -> ToolError:
    """Log and wrap exceptions in ToolError."""
    logger.exception(message, exc_info=error)
    return ToolError(str(error))


def create_mcp_server(
    memory: Neo4jMemory,
    *,
    namespace: str = "",
    log_level: str = "INFO",
) -> FastMCP:
    """Create and configure a FastMCP instance for Neo4j memory tools."""

    mcp = FastMCP(
        name="mcp-neo4j-memory",
        log_level=log_level,
    )

    prefix = format_namespace(namespace)

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}read_graph",
        title="Read Knowledge Graph",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def read_graph(filter_query: str = "*") -> dict[str, Any]:
        """Read the full knowledge graph with an optional fulltext filter."""

        try:
            graph = await memory.load_graph(filter_query)
            return graph.model_dump()
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao ler grafo de conhecimento", error) from error

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}search_memories",
        title="Search Memories",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def search_memories(query: str) -> dict[str, Any]:
        """Search memories using the Neo4j fulltext index."""

        try:
            graph = await memory.search_memories(query)
            return graph.model_dump()
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao buscar memórias", error) from error

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}find_memories_by_name",
        title="Find Memories By Name",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def find_memories_by_name(names: list[str]) -> dict[str, Any]:
        """Find specific memories by their exact names."""

        try:
            validated_names = [validate_entity_name(name) for name in names]
            graph = await memory.find_memories_by_name(validated_names)
            return graph.model_dump()
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao buscar memórias por nome", error) from error

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}create_entities",
        title="Create Entities",
        annotations=ToolAnnotations(idempotentHint=False, destructiveHint=False),
    )
    async def create_entities(entities: list[Entity]) -> list[dict[str, Any]]:
        """Create or update entities inside the knowledge graph."""

        try:
            created = await memory.create_entities(entities)
            return [entity.model_dump() for entity in created]
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao criar entidades", error) from error

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}create_relations",
        title="Create Relations",
        annotations=ToolAnnotations(idempotentHint=False, destructiveHint=False),
    )
    async def create_relations(relations: list[Relation]) -> list[dict[str, Any]]:
        """Create relations between existing entities."""

        try:
            normalised = [
                relation.model_copy(update={"relationType": validate_relation_type(relation.relationType)})
                for relation in relations
            ]
            created = await memory.create_relations(normalised)
            return [relation.model_dump() for relation in created]
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao criar relações", error) from error

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}add_observations",
        title="Add Observations",
        annotations=ToolAnnotations(idempotentHint=False, destructiveHint=False),
    )
    async def add_observations(
        observations: list[ObservationAddition],
    ) -> list[dict[str, Any]]:
        """Append observations to existing entities."""

        try:
            return await memory.add_observations(observations)
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao adicionar observações", error) from error

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}delete_observations",
        title="Delete Observations",
        annotations=ToolAnnotations(idempotentHint=False, destructiveHint=True),
    )
    async def delete_observations(
        deletions: list[ObservationDeletion],
    ) -> dict[str, Any]:
        """Remove specific observations from entities."""

        try:
            await memory.delete_observations(deletions)
            return {"deleted": len(deletions)}
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao remover observações", error) from error

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}delete_entities",
        title="Delete Entities",
        annotations=ToolAnnotations(idempotentHint=False, destructiveHint=True),
    )
    async def delete_entities(names: list[str]) -> dict[str, Any]:
        """Delete entities and their relationships from the graph."""

        try:
            validated_names = [validate_entity_name(name) for name in names]
            await memory.delete_entities(validated_names)
            return {"deleted": len(validated_names)}
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao deletar entidades", error) from error

    @mcp.tool(  # type: ignore[misc]
        name=f"{prefix}delete_relations",
        title="Delete Relations",
        annotations=ToolAnnotations(idempotentHint=False, destructiveHint=True),
    )
    async def delete_relations(relations: list[Relation]) -> dict[str, Any]:
        """Delete relations between entities."""

        try:
            normalised = [
                relation.model_copy(update={"relationType": validate_relation_type(relation.relationType)})
                for relation in relations
            ]
            await memory.delete_relations(normalised)
            return {"deleted": len(normalised)}
        except Exception as error:  # noqa: BLE001
            raise _handle_error("Falha ao deletar relações", error) from error

    return mcp


__all__ = ["create_mcp_server"]
