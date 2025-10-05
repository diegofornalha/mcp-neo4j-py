"""
Configurações centralizadas para o sistema MCP Neo4j.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Neo4jConfig:
    """
    Configuração de conexão com Neo4j.

    Attributes:
        uri: URI de conexão (ex: bolt://localhost:7687)
        username: Nome de usuário
        password: Senha
        database: Nome do banco de dados (padrão: neo4j)
        encrypted: Se deve usar conexão criptografada
        max_connection_pool_size: Tamanho máximo do pool de conexões
        connection_timeout: Timeout de conexão em segundos
    """
    uri: str
    username: str
    password: str
    database: str = "neo4j"
    encrypted: bool = False
    max_connection_pool_size: int = 50
    connection_timeout: float = 10.0

    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """
        Cria configuração a partir de variáveis de ambiente.

        Variáveis de ambiente:
            NEO4J_URI: URI de conexão (padrão: bolt://127.0.0.1:7687)
            NEO4J_USERNAME: Nome de usuário (padrão: neo4j)
            NEO4J_PASSWORD: Senha (obrigatório)
            NEO4J_DATABASE: Nome do banco (padrão: neo4j)
            NEO4J_ENCRYPTED: Se deve usar criptografia (padrão: false)
            NEO4J_MAX_POOL_SIZE: Tamanho do pool (padrão: 50)
            NEO4J_TIMEOUT: Timeout em segundos (padrão: 10.0)

        Returns:
            Configuração criada

        Raises:
            ValueError: Se NEO4J_PASSWORD não estiver configurado
        """
        password = os.getenv("NEO4J_PASSWORD")
        if not password:
            raise ValueError(
                "NEO4J_PASSWORD não configurado. "
                "Configure a variável de ambiente NEO4J_PASSWORD."
            )

        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=password,
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
            encrypted=os.getenv("NEO4J_ENCRYPTED", "false").lower() == "true",
            max_connection_pool_size=int(os.getenv("NEO4J_MAX_POOL_SIZE", "50")),
            connection_timeout=float(os.getenv("NEO4J_TIMEOUT", "10.0")),
        )


@dataclass(frozen=True)
class ServerConfig:
    """
    Configuração do servidor MCP.

    Attributes:
        namespace: Namespace para prefixar nomes de tools
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        transport: Tipo de transporte (stdio, http, sse)
        host: Host para servidor HTTP/SSE
        port: Porta para servidor HTTP/SSE
        path: Path para servidor HTTP/SSE
        allow_origins: Origens permitidas para CORS (lista separada por vírgula)
        allowed_hosts: Hosts permitidos (lista separada por vírgula)
    """
    namespace: str = ""
    log_level: str = "INFO"
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp/"
    allow_origins: str = "*"
    allowed_hosts: str = "*"

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """
        Cria configuração a partir de variáveis de ambiente.

        Variáveis de ambiente:
            MCP_NAMESPACE: Namespace (padrão: "")
            MCP_LOG_LEVEL: Nível de log (padrão: INFO)
            MCP_TRANSPORT: Tipo de transporte (padrão: stdio)
            MCP_HOST: Host (padrão: 127.0.0.1)
            MCP_PORT: Porta (padrão: 8000)
            MCP_PATH: Path (padrão: /mcp/)
            MCP_ALLOW_ORIGINS: Origens CORS (padrão: *)
            MCP_ALLOWED_HOSTS: Hosts permitidos (padrão: *)

        Returns:
            Configuração criada
        """
        return cls(
            namespace=os.getenv("MCP_NAMESPACE", ""),
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
            transport=os.getenv("MCP_TRANSPORT", "stdio"),
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
            path=os.getenv("MCP_PATH", "/mcp/"),
            allow_origins=os.getenv("MCP_ALLOW_ORIGINS", "*"),
            allowed_hosts=os.getenv("MCP_ALLOWED_HOSTS", "*"),
        )


@dataclass(frozen=True)
class MemoryConfig:
    """
    Configuração do sistema de memória.

    Attributes:
        relevance_threshold: Threshold de relevância para busca (0.0 - 1.0)
        days_until_stale: Dias até memória ser considerada obsoleta
        min_connections: Mínimo de conexões para não ser considerado isolado
        max_cache_size: Tamanho máximo do cache LRU
        enable_fulltext_index: Se deve criar índice fulltext automaticamente
    """
    relevance_threshold: float = 0.3
    days_until_stale: int = 90
    min_connections: int = 1
    max_cache_size: int = 1000
    enable_fulltext_index: bool = True

    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """
        Cria configuração a partir de variáveis de ambiente.

        Variáveis de ambiente:
            MEMORY_RELEVANCE_THRESHOLD: Threshold de relevância (padrão: 0.3)
            MEMORY_DAYS_UNTIL_STALE: Dias até obsoleto (padrão: 90)
            MEMORY_MIN_CONNECTIONS: Mínimo de conexões (padrão: 1)
            MEMORY_MAX_CACHE_SIZE: Tamanho do cache (padrão: 1000)
            MEMORY_ENABLE_FULLTEXT: Criar índice fulltext (padrão: true)

        Returns:
            Configuração criada
        """
        return cls(
            relevance_threshold=float(os.getenv("MEMORY_RELEVANCE_THRESHOLD", "0.3")),
            days_until_stale=int(os.getenv("MEMORY_DAYS_UNTIL_STALE", "90")),
            min_connections=int(os.getenv("MEMORY_MIN_CONNECTIONS", "1")),
            max_cache_size=int(os.getenv("MEMORY_MAX_CACHE_SIZE", "1000")),
            enable_fulltext_index=os.getenv("MEMORY_ENABLE_FULLTEXT", "true").lower() == "true",
        )
