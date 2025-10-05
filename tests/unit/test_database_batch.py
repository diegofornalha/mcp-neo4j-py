"""
Testes unitários para database/batch.py (batch_operations.py)
Testa BatchProcessor e operações em lote
"""

import pytest
import time
from unittest.mock import Mock, patch, call

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from mcp_neo4j.batch_operations import BatchProcessor


# ============================================================================
# Testes do BatchProcessor
# ============================================================================

class TestBatchProcessor:
    """Testes da classe BatchProcessor"""

    @pytest.fixture
    def mock_connection_pool(self):
        """Mock do connection pool"""
        pool = Mock()
        pool.execute_with_retry = Mock(return_value=[{"created": 100}])
        return pool

    @pytest.fixture
    def batch_processor(self, mock_connection_pool):
        """Fixture de BatchProcessor"""
        return BatchProcessor(mock_connection_pool, batch_size=100)

    def test_initialization(self, batch_processor):
        """Testa inicialização do batch processor"""
        assert batch_processor.batch_size == 100
        assert batch_processor.stats["total_processed"] == 0
        assert batch_processor.stats["total_failed"] == 0

    def test_process_in_batches_basic(self, batch_processor, mock_connection_pool):
        """Testa processamento básico em batches"""
        items = [{"name": f"item_{i}"} for i in range(250)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = batch_processor.process_in_batches(items, processor_func)

        # Deve processar 250 items em 3 batches (100, 100, 50)
        assert result["total_items"] == 250
        assert result["processed"] == 250
        assert result["failed"] == 0
        assert result["batches"] == 3

    def test_process_in_batches_calls_connection_pool(self, batch_processor, mock_connection_pool):
        """Verifica que batch processor chama connection pool"""
        items = [{"name": "test"}]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        batch_processor.process_in_batches(items, processor_func)

        mock_connection_pool.execute_with_retry.assert_called_once()

    def test_process_in_batches_handles_errors(self, batch_processor, mock_connection_pool):
        """Testa handling de erros durante processamento"""
        mock_connection_pool.execute_with_retry.side_effect = Exception("Database error")

        items = [{"name": f"item_{i}"} for i in range(150)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = batch_processor.process_in_batches(items, processor_func)

        # Todos os batches falharam
        assert result["failed"] == 150
        assert result["processed"] == 0

    def test_process_in_batches_partial_failure(self, batch_processor, mock_connection_pool):
        """Testa processamento com falhas parciais"""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Segundo batch falha
                raise Exception("Batch 2 failed")
            return [{"created": 100}]

        mock_connection_pool.execute_with_retry.side_effect = side_effect

        items = [{"name": f"item_{i}"} for i in range(250)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = batch_processor.process_in_batches(items, processor_func)

        # 2 batches sucesso (200 items), 1 falha (100 items) = 50 restantes
        assert result["processed"] == 200
        assert result["failed"] == 50

    def test_custom_batch_size(self, batch_processor):
        """Testa processamento com batch size customizado"""
        items = [{"name": f"item_{i}"} for i in range(150)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = batch_processor.process_in_batches(
            items,
            processor_func,
            batch_size=50  # Override default
        )

        # 150 items / 50 per batch = 3 batches
        assert result["batches"] == 3

    def test_stats_accumulation(self, batch_processor):
        """Testa acumulação de estatísticas"""
        items1 = [{"name": "item"}]
        items2 = [{"name": "item"}]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        batch_processor.process_in_batches(items1, processor_func)
        batch_processor.process_in_batches(items2, processor_func)

        # Stats devem acumular
        assert batch_processor.stats["total_processed"] == 2

    def test_batch_timing_metrics(self, batch_processor):
        """Testa métricas de tempo de processamento"""
        items = [{"name": f"item_{i}"} for i in range(50)]

        def processor_func(batch):
            time.sleep(0.01)  # Simular processamento
            return "CREATE (n:Test)", {"batch": batch}

        result = batch_processor.process_in_batches(items, processor_func)

        assert result["total_time"] > 0
        assert result["average_batch_time"] > 0
        assert batch_processor.stats["last_batch_time"] is not None

    def test_empty_items_list(self, batch_processor):
        """Testa processamento de lista vazia"""
        items = []

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = batch_processor.process_in_batches(items, processor_func)

        assert result["total_items"] == 0
        assert result["processed"] == 0
        assert result["batches"] == 0

    def test_single_item(self, batch_processor):
        """Testa processamento de item único"""
        items = [{"name": "single"}]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = batch_processor.process_in_batches(items, processor_func)

        assert result["total_items"] == 1
        assert result["processed"] == 1
        assert result["batches"] == 1


# ============================================================================
# Testes dos Métodos Específicos
# ============================================================================

class TestBatchProcessorMethods:
    """Testes dos métodos específicos de batch operations"""

    @pytest.fixture
    def mock_connection_pool(self):
        """Mock do connection pool"""
        pool = Mock()
        pool.execute_with_retry = Mock(return_value=[{"created": 100}])
        return pool

    @pytest.fixture
    def batch_processor(self, mock_connection_pool):
        """Fixture de BatchProcessor"""
        return BatchProcessor(mock_connection_pool, batch_size=100)

    def test_batch_create_nodes(self, batch_processor, mock_connection_pool):
        """Testa criação em batch de nós"""
        nodes_data = [
            {"name": "node1", "value": 1},
            {"name": "node2", "value": 2}
        ]

        result = batch_processor.batch_create_nodes("TestLabel", nodes_data)

        assert result["total_items"] == 2
        assert result["processed"] == 2

        # Verificar que query foi chamada
        mock_connection_pool.execute_with_retry.assert_called()

        # Verificar estrutura da query
        call_args = mock_connection_pool.execute_with_retry.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "UNWIND" in query
        assert "TestLabel" in query
        assert "batch" in params

    def test_batch_create_nodes_large_dataset(self, batch_processor):
        """Testa criação de muitos nós"""
        nodes_data = [{"name": f"node_{i}"} for i in range(500)]

        result = batch_processor.batch_create_nodes("TestLabel", nodes_data)

        assert result["total_items"] == 500
        assert result["batches"] == 5  # 500 / 100 = 5 batches

    def test_batch_create_relationships(self, batch_processor, mock_connection_pool):
        """Testa criação em batch de relacionamentos"""
        relationships = [
            {"from": "node1", "to": "node2", "type": "RELATES_TO"},
            {"from": "node2", "to": "node3", "type": "RELATES_TO"}
        ]

        result = batch_processor.batch_create_relationships(relationships)

        assert result["total_items"] == 2
        mock_connection_pool.execute_with_retry.assert_called()


# ============================================================================
# Testes de Performance
# ============================================================================

@pytest.mark.slow
class TestBatchProcessorPerformance:
    """Testes de performance do batch processor"""

    def test_large_batch_processing(self, mock_connection_pool):
        """Testa processamento de grande volume"""
        processor = BatchProcessor(mock_connection_pool, batch_size=1000)

        items = [{"name": f"item_{i}"} for i in range(10000)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        start_time = time.time()
        result = processor.process_in_batches(items, processor_func)
        elapsed = time.time() - start_time

        assert result["total_items"] == 10000
        assert result["batches"] == 10
        assert elapsed < 5  # Deve ser rápido (mock)

    def test_optimal_batch_size(self, mock_connection_pool):
        """Testa diferentes batch sizes"""
        items = [{"name": f"item_{i}"} for i in range(1000)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        # Testar diferentes sizes
        for batch_size in [10, 100, 500, 1000]:
            processor = BatchProcessor(mock_connection_pool, batch_size=batch_size)
            result = processor.process_in_batches(items, processor_func)

            expected_batches = (1000 + batch_size - 1) // batch_size
            assert result["batches"] == expected_batches


# ============================================================================
# Testes de Error Recovery
# ============================================================================

class TestBatchProcessorErrorRecovery:
    """Testes de recuperação de erros"""

    def test_continue_after_batch_failure(self):
        """Verifica que processamento continua após falha de um batch"""
        pool = Mock()

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Batch 2 failed")
            return [{"created": 100}]

        pool.execute_with_retry.side_effect = side_effect

        processor = BatchProcessor(pool, batch_size=100)
        items = [{"name": f"item_{i}"} for i in range(300)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = processor.process_in_batches(items, processor_func)

        # Deve ter processado batches 1 e 3, mas não o 2
        assert result["processed"] == 200
        assert result["failed"] == 100
        assert result["batches"] == 3

    def test_all_batches_fail(self):
        """Testa quando todos os batches falham"""
        pool = Mock()
        pool.execute_with_retry.side_effect = Exception("All failed")

        processor = BatchProcessor(pool, batch_size=100)
        items = [{"name": f"item_{i}"} for i in range(250)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = processor.process_in_batches(items, processor_func)

        assert result["processed"] == 0
        assert result["failed"] == 250


# ============================================================================
# Testes de Edge Cases
# ============================================================================

class TestBatchProcessorEdgeCases:
    """Testes de casos extremos"""

    def test_batch_size_larger_than_items(self):
        """Testa batch size maior que número de items"""
        pool = Mock()
        pool.execute_with_retry.return_value = []

        processor = BatchProcessor(pool, batch_size=1000)
        items = [{"name": "item"}]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = processor.process_in_batches(items, processor_func)

        assert result["batches"] == 1
        assert result["processed"] == 1

    def test_batch_size_one(self):
        """Testa batch size de 1 (sem batching real)"""
        pool = Mock()
        pool.execute_with_retry.return_value = []

        processor = BatchProcessor(pool, batch_size=1)
        items = [{"name": f"item_{i}"} for i in range(5)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        result = processor.process_in_batches(items, processor_func)

        assert result["batches"] == 5  # Um batch por item

    def test_processor_func_returns_none(self):
        """Testa quando processor_func retorna valores inválidos"""
        pool = Mock()
        pool.execute_with_retry.return_value = []

        processor = BatchProcessor(pool)
        items = [{"name": "item"}]

        def bad_processor_func(batch):
            return None, None  # Invalid

        # Deve falhar ou tratar gracefully
        # Documenta comportamento atual
        with pytest.raises(Exception):
            processor.process_in_batches(items, bad_processor_func)


# ============================================================================
# Testes de Logging
# ============================================================================

class TestBatchProcessorLogging:
    """Testes de logging do batch processor"""

    def test_progress_logging(self, mock_connection_pool, caplog):
        """Verifica que progresso é logado"""
        import logging

        processor = BatchProcessor(mock_connection_pool, batch_size=100)
        items = [{"name": f"item_{i}"} for i in range(250)]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        with caplog.at_level(logging.INFO):
            processor.process_in_batches(items, processor_func)

        # Deve ter logs de progresso
        assert any("Progresso" in record.message for record in caplog.records)

    def test_error_logging(self, caplog):
        """Verifica que erros são logados"""
        import logging

        pool = Mock()
        pool.execute_with_retry.side_effect = Exception("Test error")

        processor = BatchProcessor(pool)
        items = [{"name": "item"}]

        def processor_func(batch):
            return "CREATE (n:Test)", {"batch": batch}

        with caplog.at_level(logging.ERROR):
            processor.process_in_batches(items, processor_func)

        # Deve ter log de erro
        assert any("Erro ao processar batch" in record.message for record in caplog.records)
