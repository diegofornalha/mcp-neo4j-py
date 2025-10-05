"""
Testes unitários para database/connection.py
Testa ConnectionPool, CircuitBreaker e QueryCache
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from neo4j.exceptions import ServiceUnavailable, SessionExpired

# Import do módulo a ser testado
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from mcp_neo4j.connection_manager import (
    CircuitBreaker,
    ConnectionPool,
    QueryCache,
    cached_query
)


# ============================================================================
# Testes do CircuitBreaker
# ============================================================================

class TestCircuitBreaker:
    """Testes da classe CircuitBreaker"""

    def test_circuit_breaker_initial_state(self):
        """Verifica estado inicial do circuit breaker"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    def test_circuit_breaker_success(self):
        """Testa chamada bem-sucedida"""
        cb = CircuitBreaker()

        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_circuit_breaker_opens_after_failures(self):
        """Testa abertura do circuit após falhas"""
        cb = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise ServiceUnavailable("Connection failed")

        # Simular falhas até atingir threshold
        for i in range(3):
            with pytest.raises(ServiceUnavailable):
                cb.call(failing_func)

        assert cb.state == "OPEN"
        assert cb.failure_count == 3

    def test_circuit_breaker_blocks_when_open(self):
        """Testa bloqueio quando circuit está aberto"""
        cb = CircuitBreaker(failure_threshold=1)

        def failing_func():
            raise ServiceUnavailable("Connection failed")

        # Abrir o circuit
        with pytest.raises(ServiceUnavailable):
            cb.call(failing_func)

        assert cb.state == "OPEN"

        # Tentar novamente - deve ser bloqueado
        with pytest.raises(ServiceUnavailable) as exc_info:
            cb.call(lambda: "test")

        assert "Circuit breaker is OPEN" in str(exc_info.value)

    def test_circuit_breaker_half_open_after_timeout(self):
        """Testa transição para HALF_OPEN após timeout"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        def failing_func():
            raise ServiceUnavailable("Connection failed")

        # Abrir o circuit
        with pytest.raises(ServiceUnavailable):
            cb.call(failing_func)

        assert cb.state == "OPEN"

        # Aguardar timeout
        time.sleep(0.2)

        # Próxima tentativa deve ir para HALF_OPEN
        def success_func():
            return "recovered"

        result = cb.call(success_func)
        assert result == "recovered"
        assert cb.state == "CLOSED"

    def test_circuit_breaker_reset_on_success(self):
        """Testa reset do contador ao ter sucesso"""
        cb = CircuitBreaker(failure_threshold=5)

        def sometimes_fails(should_fail):
            if should_fail:
                raise Exception("Failed")
            return "success"

        # Algumas falhas
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(sometimes_fails, True)

        assert cb.failure_count == 2

        # Sucesso - deve resetar contador
        result = cb.call(sometimes_fails, False)
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"


# ============================================================================
# Testes do ConnectionPool
# ============================================================================

class TestConnectionPool:
    """Testes da classe ConnectionPool"""

    @pytest.fixture
    def mock_driver(self):
        """Mock do driver Neo4j"""
        driver = Mock()
        driver.verify_connectivity = Mock(return_value=True)
        return driver

    @pytest.fixture
    def connection_pool(self, mock_driver, neo4j_config):
        """Fixture de ConnectionPool com mocks"""
        with patch('mcp_neo4j.connection_manager.GraphDatabase.driver', return_value=mock_driver):
            pool = ConnectionPool(
                uri=neo4j_config["uri"],
                auth=(neo4j_config["username"], neo4j_config["password"]),
                database=neo4j_config["database"]
            )
            return pool

    def test_connection_pool_initialization(self, connection_pool):
        """Testa inicialização do pool"""
        assert connection_pool.driver is None
        assert connection_pool._connected is False
        assert connection_pool.circuit_breaker is not None
        assert "queries_executed" in connection_pool.metrics

    def test_ensure_connected_lazy_initialization(self, connection_pool, mock_driver):
        """Testa lazy initialization da conexão"""
        with patch('mcp_neo4j.connection_manager.GraphDatabase.driver', return_value=mock_driver):
            connection_pool.ensure_connected()
            assert connection_pool._connected is True
            assert connection_pool.driver is not None

    def test_verify_connection_success(self, connection_pool, mock_driver):
        """Testa verificação de conexão bem-sucedida"""
        connection_pool.driver = mock_driver
        result = connection_pool._verify_connection()
        assert result is True

    def test_verify_connection_failure(self, connection_pool, mock_driver):
        """Testa verificação de conexão com falha"""
        connection_pool.driver = mock_driver
        mock_driver.verify_connectivity.side_effect = Exception("Connection lost")
        result = connection_pool._verify_connection()
        assert result is False

    def test_reconnect_on_connection_loss(self, connection_pool, mock_driver):
        """Testa reconexão automática"""
        with patch('mcp_neo4j.connection_manager.GraphDatabase.driver', return_value=mock_driver):
            connection_pool._reconnect()
            assert connection_pool._connected is True
            assert connection_pool.metrics["reconnections"] == 1

    def test_execute_with_retry_success(self, connection_pool, mock_driver):
        """Testa execução de query com sucesso"""
        # Setup mock session
        mock_session = Mock()
        mock_result = Mock()
        mock_record = {"name": "test", "value": 123}
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))

        mock_session.run.return_value = mock_result
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_session

        connection_pool.driver = mock_driver
        connection_pool._connected = True

        # Executar query
        result = connection_pool.execute_with_retry("MATCH (n) RETURN n", {})

        assert len(result) == 1
        assert connection_pool.metrics["queries_executed"] == 1

    def test_execute_with_retry_handles_service_unavailable(self, connection_pool, mock_driver):
        """Testa retry ao encontrar ServiceUnavailable"""
        mock_session = Mock()
        mock_session.run.side_effect = ServiceUnavailable("Connection lost")
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_session

        connection_pool.driver = mock_driver
        connection_pool._connected = True

        with pytest.raises(ServiceUnavailable):
            connection_pool.execute_with_retry("MATCH (n) RETURN n", {}, max_retries=2)

        assert connection_pool.metrics["queries_failed"] > 0

    def test_slow_query_tracking(self, connection_pool, mock_driver):
        """Testa rastreamento de queries lentas"""
        # Simular query lenta
        mock_session = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))

        def slow_run(*args, **kwargs):
            time.sleep(1.1)  # Mais de 1 segundo
            return mock_result

        mock_session.run = slow_run
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_session

        connection_pool.driver = mock_driver
        connection_pool._connected = True

        connection_pool.execute_with_retry("MATCH (n) RETURN n")

        # Verificar que query lenta foi registrada
        assert len(connection_pool.metrics["slow_queries"]) > 0
        assert connection_pool.metrics["slow_queries"][0]["time"] > 1.0

    def test_get_metrics(self, connection_pool):
        """Testa obtenção de métricas"""
        metrics = connection_pool.get_metrics()

        assert "queries_executed" in metrics
        assert "queries_failed" in metrics
        assert "reconnections" in metrics
        assert "circuit_breaker_state" in metrics
        assert "is_connected" in metrics

    def test_close_connection(self, connection_pool, mock_driver):
        """Testa fechamento de conexão"""
        connection_pool.driver = mock_driver
        connection_pool._connected = True

        connection_pool.close()

        mock_driver.close.assert_called_once()
        assert connection_pool._connected is False


# ============================================================================
# Testes do QueryCache
# ============================================================================

class TestQueryCache:
    """Testes da classe QueryCache"""

    def test_cache_initialization(self):
        """Testa inicialização do cache"""
        cache = QueryCache(max_size=50, ttl_seconds=300)
        assert cache.max_size == 50
        assert cache.ttl_seconds == 300
        assert cache.hits == 0
        assert cache.misses == 0

    def test_cache_set_and_get(self):
        """Testa set e get básico"""
        cache = QueryCache()
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"
        assert cache.hits == 1

    def test_cache_miss(self):
        """Testa cache miss"""
        cache = QueryCache()
        result = cache.get("nonexistent")

        assert result is None
        assert cache.misses == 1

    def test_cache_ttl_expiration(self):
        """Testa expiração por TTL"""
        cache = QueryCache(ttl_seconds=0.1)
        cache.set("key1", "value1")

        # Buscar imediatamente - deve encontrar
        result1 = cache.get("key1")
        assert result1 == "value1"

        # Aguardar expiração
        time.sleep(0.2)

        # Buscar novamente - deve estar expirado
        result2 = cache.get("key1")
        assert result2 is None

    def test_cache_lru_eviction(self):
        """Testa remoção LRU quando atinge limite"""
        cache = QueryCache(max_size=3)

        # Adicionar 3 items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Adicionar 4º item - deve remover o mais antigo
        cache.set("key4", "value4")

        # key1 deve ter sido removido
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_cache_update_existing_key(self):
        """Testa atualização de chave existente"""
        cache = QueryCache()
        cache.set("key1", "value1")
        cache.set("key1", "value2")

        result = cache.get("key1")
        assert result == "value2"

    def test_cache_clear(self):
        """Testa limpeza do cache"""
        cache = QueryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(cache._cache) == 0

    def test_cache_statistics(self):
        """Testa estatísticas do cache"""
        cache = QueryCache()

        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert "hit_rate" in stats

    def test_cache_hit_rate_calculation(self):
        """Testa cálculo de hit rate"""
        cache = QueryCache()

        cache.set("key1", "value1")

        # 2 hits, 1 miss = 66.7%
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key2")  # miss

        stats = cache.get_stats()
        assert "66" in stats["hit_rate"]


# ============================================================================
# Testes do Decorator cached_query
# ============================================================================

class TestCachedQueryDecorator:
    """Testes do decorator @cached_query"""

    def test_cached_query_decorator(self):
        """Testa funcionamento básico do decorator"""
        call_count = 0

        @cached_query(ttl=300)
        def expensive_query(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"

        # Primeira chamada - deve executar
        result1 = expensive_query("test")
        assert result1 == "result_test"
        assert call_count == 1

        # Segunda chamada - deve usar cache
        result2 = expensive_query("test")
        assert result2 == "result_test"
        assert call_count == 1  # Não incrementou

        # Chamada com parâmetro diferente - deve executar
        result3 = expensive_query("other")
        assert result3 == "result_other"
        assert call_count == 2


# ============================================================================
# Testes de Integração Connection Manager
# ============================================================================

@pytest.mark.integration
class TestConnectionManagerIntegration:
    """Testes de integração do gerenciador de conexão"""

    def test_connection_pool_with_circuit_breaker(self, neo4j_config):
        """Testa integração entre ConnectionPool e CircuitBreaker"""
        # Este teste requer Neo4j rodando
        pytest.skip("Requer Neo4j em execução")

    def test_connection_pool_retry_logic(self, neo4j_config):
        """Testa lógica de retry completa"""
        # Este teste requer Neo4j rodando
        pytest.skip("Requer Neo4j em execução")
