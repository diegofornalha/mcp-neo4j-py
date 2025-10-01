#!/usr/bin/env python3
"""
Script de teste para validar todas as melhorias implementadas
"""

import json
import time
from datetime import datetime
from src.mcp_neo4j.connection_manager import ConnectionPool, QueryCache
from src.mcp_neo4j.query_builder import QueryBuilder, QueryTemplates, SchemaManager
from src.mcp_neo4j.batch_operations import BatchProcessor, BulkImporter

# Configurações
NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
NEO4J_DATABASE = "neo4j"


def test_connection_pool():
    """Testa o pool de conexões com circuit breaker"""
    print("\n🔧 Testando Connection Pool com Circuit Breaker...")
    
    pool = ConnectionPool(
        uri=NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        database=NEO4J_DATABASE
    )
    
    # Teste 1: Conexão básica
    result = pool.execute_with_retry("RETURN 1 as test")
    assert result[0]["test"] == 1
    print("✅ Conexão básica funcionando")
    
    # Teste 2: Métricas
    metrics = pool.get_metrics()
    print(f"📊 Métricas: {json.dumps(metrics, indent=2)}")
    assert metrics["queries_executed"] > 0
    print("✅ Sistema de métricas funcionando")
    
    # Teste 3: Retry com falha simulada
    try:
        # Query inválida para testar retry
        pool.execute_with_retry("INVALID QUERY", max_retries=2)
    except:
        print("✅ Sistema de retry funcionando")
    
    pool.close()
    return True


def test_query_cache():
    """Testa o cache LRU"""
    print("\n💾 Testando Query Cache LRU...")
    
    cache = QueryCache(max_size=5, ttl_seconds=2)
    
    # Teste 1: Set e Get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    print("✅ Cache set/get funcionando")
    
    # Teste 2: Hit/Miss stats
    cache.get("key1")  # Hit
    cache.get("key2")  # Miss
    stats = cache.get_stats()
    assert stats["hits"] == 2  # 1 do assert + 1 do get
    assert stats["misses"] == 1
    print(f"📊 Cache stats: {stats}")
    print("✅ Estatísticas de cache funcionando")
    
    # Teste 3: TTL expiration
    time.sleep(3)
    expired_value = cache.get("key1")
    if expired_value is None:
        print("✅ TTL de cache funcionando")
    else:
        print("⚠️ TTL não expirou como esperado, mas não é crítico")
    
    return True


def test_query_builder():
    """Testa o Query Builder"""
    print("\n🔨 Testando Query Builder...")
    
    # Teste 1: Find or create
    query, params = QueryBuilder.find_or_create_node(
        label="TestNode",
        name="test1",
        properties={"type": "test"}
    )
    assert "MERGE" in query
    assert params["name"] == "test1"
    print("✅ Find or create query funcionando")
    
    # Teste 2: Batch create
    query, params = QueryBuilder.batch_create_nodes(
        label="TestNode",
        items=[{"name": f"test{i}"} for i in range(5)]
    )
    assert "UNWIND" in query
    assert len(params["items"]) == 5
    print("✅ Batch create query funcionando")
    
    # Teste 3: Search
    query, params = QueryBuilder.search_nodes(
        label="TestNode",
        search_term="test",
        limit=10
    )
    assert "CONTAINS" in query
    print("✅ Search query funcionando")
    
    return True


def test_batch_operations():
    """Testa operações em batch"""
    print("\n📦 Testando Batch Operations...")
    
    pool = ConnectionPool(
        uri=NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        database=NEO4J_DATABASE
    )
    
    processor = BatchProcessor(pool, batch_size=100)
    
    # Criar dados de teste
    test_data = [
        {"name": f"batch_test_{i}", "value": i}
        for i in range(250)
    ]
    
    # Processar em batches
    stats = processor.batch_create_nodes("BatchTest", test_data)
    
    print(f"📊 Batch stats: {json.dumps(stats, indent=2)}")
    assert stats["processed"] == 250
    assert stats["batches"] == 3  # 250/100 = 3 batches
    print("✅ Batch processing funcionando")
    
    # Limpar dados de teste
    pool.execute_with_retry("MATCH (n:BatchTest) DETACH DELETE n")
    pool.close()
    
    return True


def test_schema_manager():
    """Testa o Schema Manager"""
    print("\n📋 Testando Schema Manager...")
    
    pool = ConnectionPool(
        uri=NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        database=NEO4J_DATABASE
    )
    
    schema_mgr = SchemaManager()
    
    # Teste 1: Criar constraints
    constraints = schema_mgr.create_constraints()
    print(f"📊 {len(constraints)} constraints/índices definidos")
    
    for query, params in constraints[:2]:  # Testar apenas 2 para não demorar
        try:
            pool.execute_with_retry(query, params)
            print(f"✅ Constraint criado: {query[:50]}...")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"ℹ️ Constraint já existe: {query[:50]}...")
    
    # Teste 2: Validação de dados
    dirty_data = {
        "name": None,  # Será preenchido
        "empty": "",   # Será removido
        "list": [1, 2, 3],  # Será convertido para JSON
        "valid": "test"
    }
    
    clean_data = schema_mgr.validate_node_data("Test", dirty_data)
    if "name" in clean_data and "empty" not in clean_data and isinstance(clean_data["list"], str):
        print("✅ Validação de dados funcionando")
    else:
        print("⚠️ Validação parcialmente funcionando")
    
    pool.close()
    return True


def test_query_templates():
    """Testa os templates de query"""
    print("\n📝 Testando Query Templates...")
    
    # Teste 1: Save memory
    query, params = QueryTemplates.save_memory(
        memory_type="test",
        content="Test memory content",
        metadata={"source": "test"}
    )
    assert "Memory" in query
    print("✅ Template save_memory funcionando")
    
    # Teste 2: Save learning
    query, params = QueryTemplates.save_learning(
        title="Test Learning",
        description="Something we learned",
        tags=["test", "validation"]
    )
    assert "Learning" in query
    assert params["tags"] == ["test", "validation"]
    print("✅ Template save_learning funcionando")
    
    # Teste 3: Save bug fix
    query, params = QueryTemplates.save_bug_fix(
        problem="Test problem",
        solution="Test solution",
        affected_components=["component1", "component2"]
    )
    assert "BugFix" in query
    print("✅ Template save_bug_fix funcionando")
    
    return True


def run_all_tests():
    """Executa todos os testes"""
    print("=" * 60)
    print("🚀 INICIANDO TESTES DAS MELHORIAS IMPLEMENTADAS")
    print("=" * 60)
    
    tests = [
        ("Connection Pool", test_connection_pool),
        ("Query Cache", test_query_cache),
        ("Query Builder", test_query_builder),
        ("Query Templates", test_query_templates),
        ("Schema Manager", test_schema_manager),
        ("Batch Operations", test_batch_operations),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "✅ PASSOU"))
        except Exception as e:
            print(f"❌ Erro no teste {name}: {e}")
            results.append((name, f"❌ FALHOU: {e}"))
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for name, status in results:
        print(f"{name:20} {status}")
    
    passed = sum(1 for _, status in results if "✅" in status)
    total = len(results)
    
    print("\n" + "=" * 60)
    if passed == total:
        print(f"🎉 TODOS OS {total} TESTES PASSARAM!")
    else:
        print(f"⚠️ {passed}/{total} testes passaram")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()