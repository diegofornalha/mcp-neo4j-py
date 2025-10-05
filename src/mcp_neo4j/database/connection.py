"""
Gerenciamento de conexão com Neo4j usando AsyncDriver.
"""
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession, RoutingControl
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError
import asyncio

from ..core.config import Neo4jConfig
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


class Neo4jConnection:
    """
    Gerenciador de conexão assíncrona com Neo4j.

    Esta classe gerencia o pool de conexões com o Neo4j usando AsyncDriver,
    implementa retry logic, health checks e fornece interface simples
    para execução de queries.

    Attributes:
        config: Configuração de conexão
        driver: Driver Neo4j (inicializado ao conectar)
    """

    def __init__(self, config: Neo4jConfig):
        """
        Inicializa gerenciador de conexão.

        Args:
            config: Configuração de conexão Neo4j
        """
        self.config = config
        self._driver: Optional[AsyncDriver] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Estabelece conexão com Neo4j.

        Cria o driver e verifica conectividade. Usa configurações
        do Neo4jConfig para pool de conexões e timeouts.

        Raises:
            AuthError: Se credenciais forem inválidas
            ServiceUnavailable: Se Neo4j estiver indisponível
        """
        if self._connected and self._driver:
            logger.debug("Conexão já estabelecida")
            return

        try:
            self._driver = AsyncGraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                encrypted=self.config.encrypted,
                max_connection_lifetime=3600,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_acquisition_timeout=self.config.connection_timeout,
            )

            # Verificar conectividade
            await self._driver.verify_connectivity()
            self._connected = True

            logger.info(
                "Conectado ao Neo4j (uri=%s, database=%s)",
                self.config.uri,
                self.config.database,
            )

        except AuthError as e:
            logger.error("Erro de autenticação Neo4j: %s", e)
            raise

        except ServiceUnavailable as e:
            logger.error("Neo4j indisponível: %s", e)
            raise

        except Exception as e:  # noqa: BLE001
            logger.error("Erro ao conectar ao Neo4j: %s", e)
            raise

    async def close(self) -> None:
        """
        Fecha conexão com Neo4j.

        Fecha o driver e limpa recursos. Safe para chamar múltiplas vezes.
        """
        if self._driver:
            await self._driver.close()
            self._connected = False
            logger.info("Conexão Neo4j fechada")

    @property
    def driver(self) -> AsyncDriver:
        """Retorna o driver Neo4j inicializado."""
        if not self._driver:
            raise RuntimeError(
                "Driver não inicializado. Chame connect() antes de acessar o driver."
            )
        return self._driver

    @asynccontextmanager
    async def session(self) -> AsyncSession:
        """
        Context manager para sessão Neo4j.

        Yields:
            AsyncSession configurada com o database correto

        Raises:
            RuntimeError: Se driver não estiver inicializado

        Example:
            async with connection.session() as session:
                result = await session.run("RETURN 1")
        """
        if not self._driver:
            raise RuntimeError(
                "Driver não inicializado. Chame connect() primeiro."
            )

        async with self._driver.session(database=self.config.database) as session:
            yield session

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        routing_control: RoutingControl = RoutingControl.WRITE,
        retry_count: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Executa query Cypher e retorna resultados.

        Usa execute_query do driver para gerenciamento automático de transações
        e retry logic. Suporta routing control para reads/writes.

        Args:
            query: Query Cypher a executar
            parameters: Parâmetros da query
            routing_control: Controle de roteamento (READ ou WRITE)
            retry_count: Número de tentativas em caso de erro

        Returns:
            Lista de registros como dicionários

        Raises:
            RuntimeError: Se driver não estiver inicializado
            Neo4jError: Se query falhar após todas as tentativas

        Example:
            results = await connection.execute_query(
                "MATCH (n:Person) WHERE n.name = $name RETURN n",
                {"name": "Alice"},
                routing_control=RoutingControl.READ
            )
        """
        if not self._driver:
            raise RuntimeError(
                "Driver não inicializado. Chame connect() primeiro."
            )

        last_error = None

        for attempt in range(retry_count):
            try:
                result = await self._driver.execute_query(
                    query,
                    parameters or {},
                    routing_control=routing_control,
                    database_=self.config.database,
                )

                # Converter records para lista de dicionários
                records = [dict(record) for record in result.records]

                truncated_query = query[:100]
                logger.debug(
                    "Query executada com sucesso (query=%s, records=%d, attempt=%d)",
                    truncated_query,
                    len(records),
                    attempt + 1,
                )

                return records

            except ServiceUnavailable as e:
                last_error = e
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "Neo4j indisponível, tentando novamente em %ss (tentativa %d): %s",
                        wait_time,
                        attempt + 1,
                        e,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        "Neo4j indisponível após %d tentativas: %s",
                        retry_count,
                        e,
                    )

            except Neo4jError as e:
                logger.error(
                    "Erro ao executar query Neo4j (query=%s): %s",
                    query[:100],
                    e,
                )
                raise

            except Exception as e:  # noqa: BLE001
                logger.error(
                    "Erro inesperado ao executar query (query=%s): %s",
                    query[:100],
                    e,
                )
                raise

        # Se chegou aqui, todas as tentativas falharam
        raise last_error or RuntimeError("Query falhou após todas as tentativas")

    async def health_check(self) -> bool:
        """
        Verifica saúde da conexão.

        Executa query simples para verificar se conexão está funcionando.

        Returns:
            True se conexão está saudável, False caso contrário
        """
        try:
            await self.execute_query(
                "RETURN 1 as health",
                routing_control=RoutingControl.READ
            )
            return True

        except Exception as e:  # noqa: BLE001
            logger.error("Health check falhou: %s", e)
            return False

    async def get_database_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o database.

        Returns:
            Dicionário com informações do database

        Example:
            info = await connection.get_database_info()
            print(f"Neo4j version: {info['version']}")
        """
        try:
            # Query para obter informações do database
            result = await self.execute_query(
                """
                CALL dbms.components() YIELD name, versions, edition
                RETURN name, versions, edition
                """,
                routing_control=RoutingControl.READ
            )

            if result:
                return {
                    "name": result[0].get("name"),
                    "version": result[0].get("versions", [None])[0],
                    "edition": result[0].get("edition"),
                    "database": self.config.database,
                }

            return {"database": self.config.database}

        except Exception as e:  # noqa: BLE001
            logger.warning("Não foi possível obter informações do database: %s", e)
            return {"database": self.config.database, "error": str(e)}

    @property
    def is_connected(self) -> bool:
        """
        Verifica se está conectado.

        Returns:
            True se conectado, False caso contrário
        """
        return self._connected and self._driver is not None
