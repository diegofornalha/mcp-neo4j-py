"""
Configuração de logging estruturado para o sistema MCP Neo4j.
"""
import logging
import sys
from typing import Any


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configura logging estruturado para o sistema.

    Args:
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configurar formato de logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configurar handler para stderr (nunca stdout para não interferir com MCP)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(log_format))

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(handler)

    # Configurar logger específico do módulo
    logger = logging.getLogger("mcp_neo4j")
    logger.setLevel(getattr(logging, log_level.upper()))


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger configurado para o módulo especificado.

    Args:
        name: Nome do módulo (geralmente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(f"mcp_neo4j.{name}")
