"""Runtime utilities to bootstrap the MCP Neo4j server."""

from __future__ import annotations

from contextlib import suppress
from typing import Tuple

from ..core.config import MemoryConfig, Neo4jConfig, ServerConfig
from ..core.memory import Neo4jMemory
from ..database.connection import Neo4jConnection
from ..utils.logging_setup import get_logger, setup_logging
from .mcp_server import create_mcp_server

logger = get_logger(__name__)


async def _prepare_memory(
    connection: Neo4jConnection,
    memory_config: MemoryConfig,
) -> Neo4jMemory:
    """Establish connection and prepare the Neo4j memory layer."""

    await connection.connect()
    memory = Neo4jMemory(connection.driver)

    if memory_config.enable_fulltext_index:
        logger.debug("Garantindo índice fulltext")
        with suppress(Exception):
            await memory.create_fulltext_index()

    return memory


async def _initialise(
    neo4j_config: Neo4jConfig,
    memory_config: MemoryConfig,
) -> Tuple[Neo4jConnection, Neo4jMemory]:
    connection = Neo4jConnection(neo4j_config)
    memory = await _prepare_memory(connection, memory_config)
    return connection, memory


def run_server() -> None:
    """Bootstrap FastMCP and start the server using configuration from the environment."""

    server_config = ServerConfig.from_env()
    setup_logging(server_config.log_level)
    logger.info("Iniciando servidor MCP Neo4j (namespace=%s)", server_config.namespace or "default")

    neo4j_config = Neo4jConfig.from_env()
    memory_config = MemoryConfig.from_env()

    # Lazy wrapper for memory - will be initialized on first use within event loop
    class LazyMemory:
        def __init__(self):
            self._memory = None
            self._connection = None
            self._initialized = False

        async def _ensure_init(self):
            if not self._initialized:
                self._connection, self._memory = await _initialise(neo4j_config, memory_config)
                self._initialized = True
            return self._memory

        def __getattr__(self, name):
            # Create coroutine wrapper for async methods
            async def async_wrapper(*args, **kwargs):
                memory = await self._ensure_init()
                method = getattr(memory, name)
                return await method(*args, **kwargs)
            return async_wrapper

    lazy_memory = LazyMemory()

    mcp = create_mcp_server(
        lazy_memory,
        namespace=server_config.namespace,
        log_level=server_config.log_level,
    )

    transport = server_config.transport
    mount_path = None

    if transport == "http":
        transport = "streamable-http"
    if transport == "sse":
        mount_path = server_config.path

    logger.info("Executando FastMCP com transporte %s", transport)
    mcp.run(transport=transport, mount_path=mount_path)


def main() -> None:
    """Entry point compatible with ``python -m mcp_neo4j``."""

    run_server()


__all__ = ["main", "run_server"]
