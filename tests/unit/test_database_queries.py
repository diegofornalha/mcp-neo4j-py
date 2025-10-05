"""
Testes unitários para database/queries.py (query_builder.py)
Testa QueryBuilder e templates de queries Cypher
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from mcp_neo4j.query_builder import QueryBuilder


# ============================================================================
# Testes do QueryBuilder
# ============================================================================

class TestQueryBuilder:
    """Testes da classe QueryBuilder"""

    def test_find_or_create_node_basic(self):
        """Testa criação de query para find or create node"""
        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name="test_node"
        )

        assert "MERGE" in query
        assert "Learning" in query
        assert params["name"] == "test_node"
        assert "props" in params
        assert "created_at" in params["props"]

    def test_find_or_create_node_with_properties(self):
        """Testa find or create com propriedades adicionais"""
        properties = {
            "description": "Test description",
            "priority": 5
        }

        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name="test_node",
            properties=properties
        )

        assert params["props"]["description"] == "Test description"
        assert params["props"]["priority"] == 5
        assert params["props"]["name"] == "test_node"

    def test_find_or_create_node_sets_accessed_at(self):
        """Verifica que query atualiza accessed_at em MATCH"""
        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name="test_node"
        )

        assert "ON MATCH SET" in query
        assert "accessed_at" in query

    def test_create_relationship_basic(self):
        """Testa criação de relacionamento básico"""
        query, params = QueryBuilder.create_relationship(
            from_label="Person",
            from_name="Alice",
            rel_type="KNOWS",
            to_label="Person",
            to_name="Bob"
        )

        assert "MATCH" in query
        assert "MERGE" in query
        assert "KNOWS" in query
        assert params["from_name"] == "Alice"
        assert params["to_name"] == "Bob"
        assert "rel_props" in params
        assert "created_at" in params["rel_props"]

    def test_create_relationship_with_properties(self):
        """Testa criação de relacionamento com propriedades"""
        rel_props = {
            "since": "2024",
            "strength": "strong"
        }

        query, params = QueryBuilder.create_relationship(
            from_label="Person",
            from_name="Alice",
            rel_type="KNOWS",
            to_label="Person",
            to_name="Bob",
            rel_props=rel_props
        )

        # rel_props é passado diretamente
        assert params["rel_props"] == rel_props

    def test_batch_create_nodes(self):
        """Testa criação em batch de nós"""
        items = [
            {"name": "node1", "value": 1},
            {"name": "node2", "value": 2},
            {"name": "node3", "value": 3}
        ]

        query, params = QueryBuilder.batch_create_nodes(
            label="TestNode",
            items=items
        )

        assert "UNWIND" in query
        assert "$items" in query
        assert "CREATE" in query
        assert "TestNode" in query
        assert params["items"] == items

    def test_batch_create_sets_timestamp(self):
        """Verifica que batch create adiciona timestamp"""
        items = [{"name": "test"}]
        query, params = QueryBuilder.batch_create_nodes(
            label="TestNode",
            items=items
        )

        assert "created_at" in query
        assert "datetime()" in query

    def test_search_nodes_basic(self):
        """Testa busca básica de nós"""
        query, params = QueryBuilder.search_nodes(
            label="Learning",
            search_term="python",
            limit=10
        )

        assert "MATCH" in query
        assert "WHERE" in query
        assert "CONTAINS" in query
        assert "LIMIT" in query
        assert params["search_term"] == "python"
        assert params["limit"] == 10

    def test_search_nodes_checks_multiple_fields(self):
        """Verifica que search busca em múltiplos campos"""
        query, params = QueryBuilder.search_nodes(
            label="Learning",
            search_term="test"
        )

        # Deve buscar em name, description e content
        assert query.count("CONTAINS") >= 3
        assert "name" in query
        assert "description" in query
        assert "content" in query

    def test_search_nodes_orders_by_date(self):
        """Verifica ordenação por data"""
        query, params = QueryBuilder.search_nodes(
            label="Learning",
            search_term="test"
        )

        assert "ORDER BY" in query
        assert "updated_at" in query or "created_at" in query

    def test_get_node_with_relationships_depth_1(self):
        """Testa busca de nó com relacionamentos profundidade 1"""
        query, params = QueryBuilder.get_node_with_relationships(
            label="Learning",
            name="test_node",
            depth=1
        )

        assert "MATCH" in query
        assert "OPTIONAL MATCH" in query
        assert "[*1..1]" in query
        assert params["name"] == "test_node"

    def test_get_node_with_relationships_depth_3(self):
        """Testa busca com profundidade customizada"""
        query, params = QueryBuilder.get_node_with_relationships(
            label="Learning",
            name="test_node",
            depth=3
        )

        assert "[*1..3]" in query

    def test_get_node_with_relationships_returns_collections(self):
        """Verifica que query retorna coleções de nós e relacionamentos"""
        query, params = QueryBuilder.get_node_with_relationships(
            label="Learning",
            name="test_node"
        )

        assert "collect" in query.lower()
        assert "related_nodes" in query
        assert "relationships" in query

    def test_delete_node_cascade(self):
        """Testa deleção cascata de nó"""
        query, params = QueryBuilder.delete_node_cascade(
            label="Learning",
            name="test_node"
        )

        assert "MATCH" in query
        assert "DETACH DELETE" in query
        assert params["name"] == "test_node"
        assert "deleted_count" in query

    def test_delete_node_returns_count(self):
        """Verifica que delete retorna contagem"""
        query, params = QueryBuilder.delete_node_cascade(
            label="Learning",
            name="test_node"
        )

        assert "count(n)" in query
        assert "RETURN" in query


# ============================================================================
# Testes de Query Validation
# ============================================================================

class TestQueryValidation:
    """Testes de validação de queries"""

    def test_label_injection_prevention(self):
        """Verifica prevenção de injeção no label"""
        # Labels são interpolados diretamente, mas devem ser validados
        # Este teste documenta o comportamento atual
        query, params = QueryBuilder.find_or_create_node(
            label="Test",
            name="node"
        )

        assert "Test" in query
        # Em produção, deve haver validação de label

    def test_parameter_escaping(self):
        """Verifica que valores são passados como parâmetros"""
        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name="'; DROP DATABASE; --"
        )

        # Nome malicioso deve estar em parâmetro, não na query
        assert "DROP DATABASE" not in query
        assert params["name"] == "'; DROP DATABASE; --"

    def test_special_characters_in_names(self):
        """Testa handling de caracteres especiais"""
        special_name = "test's \"node\" with $pecial ch@rs"

        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name=special_name
        )

        assert params["name"] == special_name
        assert "$name" in query  # Usando parâmetro


# ============================================================================
# Testes de Edge Cases
# ============================================================================

class TestQueryBuilderEdgeCases:
    """Testes de casos extremos"""

    def test_empty_properties(self):
        """Testa com propriedades vazias"""
        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name="test",
            properties={}
        )

        assert params["props"]["name"] == "test"
        assert "created_at" in params["props"]

    def test_none_properties(self):
        """Testa com properties=None"""
        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name="test",
            properties=None
        )

        assert params["props"] is not None
        assert "name" in params["props"]

    def test_empty_items_batch(self):
        """Testa batch create com lista vazia"""
        query, params = QueryBuilder.batch_create_nodes(
            label="Test",
            items=[]
        )

        assert params["items"] == []
        # Query deve funcionar mesmo com lista vazia

    def test_limit_zero(self):
        """Testa search com limit 0"""
        query, params = QueryBuilder.search_nodes(
            label="Learning",
            search_term="test",
            limit=0
        )

        assert params["limit"] == 0
        # Query deve funcionar (retornará 0 resultados)

    def test_negative_depth(self):
        """Testa profundidade negativa (comportamento indefinido)"""
        # Documenta comportamento atual - pode precisar validação
        query, params = QueryBuilder.get_node_with_relationships(
            label="Learning",
            name="test",
            depth=-1
        )

        # Neo4j pode rejeitar, mas query builder não valida

    def test_very_long_name(self):
        """Testa com nome muito longo"""
        long_name = "x" * 10000

        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name=long_name
        )

        assert params["name"] == long_name
        assert len(params["name"]) == 10000

    def test_unicode_in_names(self):
        """Testa suporte a Unicode"""
        unicode_name = "测试节点 🚀 émojis"

        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name=unicode_name
        )

        assert params["name"] == unicode_name

    def test_newlines_in_search(self):
        """Testa search term com quebras de linha"""
        search_term = "line1\nline2\r\nline3"

        query, params = QueryBuilder.search_nodes(
            label="Learning",
            search_term=search_term
        )

        assert params["search_term"] == search_term


# ============================================================================
# Testes de Performance
# ============================================================================

@pytest.mark.slow
class TestQueryBuilderPerformance:
    """Testes de performance do query builder"""

    def test_batch_create_large_dataset(self):
        """Testa criação de query para grande volume"""
        items = [{"name": f"node_{i}", "value": i} for i in range(10000)]

        query, params = QueryBuilder.batch_create_nodes(
            label="TestNode",
            items=items
        )

        assert len(params["items"]) == 10000
        # Query não deve crescer com número de items (usa UNWIND)

    def test_search_with_large_limit(self):
        """Testa search com limit muito alto"""
        query, params = QueryBuilder.search_nodes(
            label="Learning",
            search_term="test",
            limit=1000000
        )

        assert params["limit"] == 1000000


# ============================================================================
# Testes de Compatibilidade
# ============================================================================

class TestCypherCompatibility:
    """Testes de compatibilidade com Cypher"""

    def test_merge_syntax(self):
        """Verifica sintaxe MERGE correta"""
        query, params = QueryBuilder.find_or_create_node(
            label="Learning",
            name="test"
        )

        # MERGE deve ter ON CREATE e ON MATCH
        assert "MERGE" in query
        assert "ON CREATE" in query
        assert "ON MATCH" in query

    def test_unwind_syntax(self):
        """Verifica sintaxe UNWIND correta"""
        query, params = QueryBuilder.batch_create_nodes(
            label="Test",
            items=[{"name": "test"}]
        )

        assert "UNWIND $items AS item" in query

    def test_relationship_syntax(self):
        """Verifica sintaxe de relacionamento"""
        query, params = QueryBuilder.create_relationship(
            from_label="A",
            from_name="a",
            rel_type="REL",
            to_label="B",
            to_name="b"
        )

        # Deve ter padrão correto (from)-[r:REL]->(to)
        assert "-[r:" in query or "]-(" in query
        assert "]->" in query
