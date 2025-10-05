"""
Configuração global de fixtures para testes pytest
Fornece mocks reutilizáveis para Neo4j, MCP e outros componentes
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, List, Any
from datetime import datetime


# ============================================================================
# Fixtures de Configuração
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Event loop para testes assíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def neo4j_config():
    """Configuração padrão do Neo4j para testes"""
    return {
        "uri": "bolt://localhost:7687",
        "username": "neo4j",
        "password": "testpassword",
        "database": "neo4j"
    }


# ============================================================================
# Fixtures de Mock Neo4j
# ============================================================================

@pytest.fixture
def mock_neo4j_driver():
    """Mock completo do driver Neo4j"""
    driver = Mock()
    session = Mock()
    result = Mock()

    # Configurar comportamento padrão
    result.data.return_value = []
    session.run.return_value = result
    session.__enter__.return_value = session
    session.__exit__.return_value = None

    driver.session.return_value = session
    driver.verify_connectivity.return_value = True

    return driver


@pytest.fixture
def mock_neo4j_session():
    """Mock de sessão Neo4j"""
    session = Mock()
    result = Mock()

    result.data.return_value = []
    result.__iter__.return_value = iter([])
    session.run.return_value = result
    session.__enter__.return_value = session
    session.__exit__.return_value = None

    return session


@pytest.fixture
def mock_neo4j_connection(mock_neo4j_driver):
    """Mock da classe Neo4jConnection"""
    conn = Mock()
    conn.driver = mock_neo4j_driver
    conn.execute_query = Mock(return_value=[])
    conn.close = Mock()
    return conn


# ============================================================================
# Fixtures de Dados de Teste
# ============================================================================

@pytest.fixture
def sample_memory_data():
    """Dados de memória de exemplo para testes"""
    return {
        "label": "Learning",
        "name": "test_memory",
        "properties": {
            "description": "Test memory description",
            "content": "Test content",
            "created_at": datetime.now().isoformat()
        }
    }


@pytest.fixture
def sample_entity_data():
    """Dados de entidade de exemplo"""
    return {
        "name": "test_entity",
        "entityType": "person",
        "observations": ["First observation", "Second observation"]
    }


@pytest.fixture
def sample_relation_data():
    """Dados de relação de exemplo"""
    return {
        "from": "entity1",
        "to": "entity2",
        "relationType": "KNOWS"
    }


@pytest.fixture
def sample_knowledge_graph():
    """Grafo de conhecimento completo para testes"""
    return {
        "entities": [
            {
                "name": "Alice",
                "entityType": "person",
                "observations": ["Works at TechCorp", "Likes Python"]
            },
            {
                "name": "Bob",
                "entityType": "person",
                "observations": ["Team lead", "Expert in Neo4j"]
            }
        ],
        "relations": [
            {
                "from": "Alice",
                "to": "Bob",
                "relationType": "WORKS_WITH"
            }
        ]
    }


@pytest.fixture
def sample_batch_nodes():
    """Lote de nós para testes de batch"""
    return [
        {"name": f"node_{i}", "value": i, "type": "test"}
        for i in range(100)
    ]


# ============================================================================
# Fixtures de Mock MCP
# ============================================================================

@pytest.fixture
def mock_mcp_server():
    """Mock do servidor FastMCP"""
    server = Mock()
    server.tool = Mock(return_value=lambda f: f)  # Decorator mock
    server.run = AsyncMock()
    return server


@pytest.fixture
def mock_mcp_context():
    """Mock do contexto MCP para tools"""
    context = Mock()
    context.request_context = {
        "user": "test_user",
        "timestamp": datetime.now().isoformat()
    }
    return context


# ============================================================================
# Fixtures de Connection Manager
# ============================================================================

@pytest.fixture
def mock_connection_pool(mock_neo4j_driver):
    """Mock do ConnectionPool"""
    pool = Mock()
    pool.driver = mock_neo4j_driver
    pool.ensure_connected = Mock()
    pool.execute_with_retry = Mock(return_value=[])
    pool.get_metrics = Mock(return_value={
        "queries_executed": 0,
        "queries_failed": 0,
        "reconnections": 0,
        "is_connected": True
    })
    pool.close = Mock()
    return pool


@pytest.fixture
def mock_circuit_breaker():
    """Mock do CircuitBreaker"""
    breaker = Mock()
    breaker.state = "CLOSED"
    breaker.failure_count = 0
    breaker.call = Mock(side_effect=lambda f, *args, **kwargs: f(*args, **kwargs))
    return breaker


# ============================================================================
# Fixtures de Query Builder
# ============================================================================

@pytest.fixture
def sample_cypher_queries():
    """Queries Cypher de exemplo para testes"""
    return {
        "create_node": "CREATE (n:Test {name: $name}) RETURN n",
        "match_node": "MATCH (n:Test {name: $name}) RETURN n",
        "create_relation": "MATCH (a:Test), (b:Test) WHERE a.name = $from AND b.name = $to CREATE (a)-[r:RELATES_TO]->(b) RETURN r",
        "search": "MATCH (n:Test) WHERE n.name CONTAINS $term RETURN n LIMIT 10"
    }


# ============================================================================
# Fixtures de Autonomous System
# ============================================================================

@pytest.fixture
def mock_autonomous_improver(mock_neo4j_connection):
    """Mock do AutonomousImprover"""
    improver = Mock()
    improver.is_active = False
    improver.start = AsyncMock()
    improver.stop = AsyncMock()
    improver.get_status = Mock(return_value={
        "active": False,
        "cycles_completed": 0,
        "patterns_detected": 0
    })
    return improver


@pytest.fixture
def mock_self_improver(mock_neo4j_connection):
    """Mock do SelfImprover"""
    improver = Mock()
    improver.get_project_rules = Mock(return_value=[])
    improver.get_relevant_knowledge = Mock(return_value=[])
    improver.get_past_decisions = Mock(return_value=[])
    improver.suggest_improvements = Mock(return_value={
        "rules": [],
        "relevant_knowledge": [],
        "past_decisions": [],
        "warnings": []
    })
    improver.learn_from_execution = Mock()
    return improver


# ============================================================================
# Fixtures de Utilities
# ============================================================================

@pytest.fixture
def mock_logger():
    """Mock do logger"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def temp_test_dir(tmp_path):
    """Diretório temporário para testes de arquivo"""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


# ============================================================================
# Fixtures de Performance Testing
# ============================================================================

@pytest.fixture
def performance_metrics():
    """Fixture para coletar métricas de performance"""
    metrics = {
        "start_time": None,
        "end_time": None,
        "duration": None,
        "memory_usage": None
    }
    return metrics


# ============================================================================
# Fixtures de Error Simulation
# ============================================================================

@pytest.fixture
def simulate_connection_error():
    """Simula erro de conexão Neo4j"""
    from neo4j.exceptions import ServiceUnavailable
    return ServiceUnavailable("Connection refused")


@pytest.fixture
def simulate_query_error():
    """Simula erro de query"""
    from neo4j.exceptions import CypherSyntaxError
    return CypherSyntaxError("Invalid syntax")


# ============================================================================
# Hooks do Pytest
# ============================================================================

def pytest_configure(config):
    """Configuração customizada do pytest"""
    config.addinivalue_line(
        "markers", "slow: marca testes lentos (deselecionar com '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "async_test: marca testes assíncronos"
    )
