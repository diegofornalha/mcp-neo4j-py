"""
Gerenciador de conexão melhorado com circuit breaker e retry logic
Baseado nos aprendizados reais do projeto
"""

import logging
import time
import threading
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired
from functools import lru_cache
import asyncio

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit Breaker para evitar retry storms"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Executa função com proteção de circuit breaker"""
        with self._lock:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise ServiceUnavailable("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar resetar o circuit"""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)
    
    def _on_success(self):
        """Reset ao sucesso"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Incrementa falhas e pode abrir o circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPEN após {self.failure_count} falhas")


class ConnectionPool:
    """Pool de conexões com reconnect automático"""
    
    def __init__(self, uri: str, auth: tuple, database: str):
        self.uri = uri
        self.auth = auth
        self.database = database
        self.driver = None
        self._connected = False
        self._lock = threading.Lock()
        self.circuit_breaker = CircuitBreaker()
        
        # Métricas
        self.metrics = {
            "queries_executed": 0,
            "queries_failed": 0,
            "reconnections": 0,
            "last_query_time": None,
            "slow_queries": []
        }
    
    def ensure_connected(self):
        """Garante que está conectado (lazy + auto-reconnect)"""
        if not self._connected or not self._verify_connection():
            self._reconnect()
    
    def _verify_connection(self) -> bool:
        """Verifica se conexão está viva (não bloqueante)"""
        if not self.driver:
            return False
        
        try:
            # Timeout curto para não bloquear
            self.driver.verify_connectivity(timeout=0.5)
            return True
        except:
            return False
    
    def _reconnect(self):
        """Reconecta ao Neo4j"""
        with self._lock:
            try:
                if self.driver:
                    self.driver.close()
                
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=self.auth,
                    encrypted=False,
                    connection_timeout=2.0,
                    max_connection_pool_size=10,
                    max_transaction_retry_time=1.0
                )
                
                self._connected = True
                self.metrics["reconnections"] += 1
                logger.info("Reconectado ao Neo4j com sucesso")
                
            except Exception as e:
                self._connected = False
                logger.error(f"Falha ao reconectar: {e}")
                raise
    
    def execute_with_retry(self, query: str, params: Optional[Dict] = None, 
                          max_retries: int = 3) -> List[Dict]:
        """Executa query com retry automático"""
        
        def _execute():
            self.ensure_connected()
            
            start_time = time.time()
            try:
                with self.driver.session(database=self.database) as session:
                    result = session.run(query, params or {})
                    data = [dict(record) for record in result]
                    
                    # Métricas
                    elapsed = time.time() - start_time
                    self.metrics["queries_executed"] += 1
                    self.metrics["last_query_time"] = elapsed
                    
                    # Registrar queries lentas (> 1 segundo)
                    if elapsed > 1.0:
                        self.metrics["slow_queries"].append({
                            "query": query[:100],
                            "time": elapsed,
                            "timestamp": datetime.now().isoformat()
                        })
                        # Manter apenas últimas 10 queries lentas
                        self.metrics["slow_queries"] = self.metrics["slow_queries"][-10:]
                    
                    return data
                    
            except (ServiceUnavailable, SessionExpired) as e:
                self._connected = False
                raise
            except Exception as e:
                self.metrics["queries_failed"] += 1
                raise
        
        # Usar circuit breaker para evitar retry storms
        for attempt in range(max_retries):
            try:
                return self.circuit_breaker.call(_execute)
            except ServiceUnavailable:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return []
    
    def get_metrics(self) -> Dict:
        """Retorna métricas da conexão"""
        return {
            **self.metrics,
            "circuit_breaker_state": self.circuit_breaker.state,
            "is_connected": self._connected
        }
    
    def close(self):
        """Fecha conexão"""
        if self.driver:
            self.driver.close()
            self._connected = False


class QueryCache:
    """Cache LRU para queries frequentes"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.Lock()
        
        # Métricas de cache
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Busca no cache"""
        with self._lock:
            if key in self._cache:
                # Verificar TTL
                if time.time() - self._timestamps[key] < self.ttl_seconds:
                    self.hits += 1
                    return self._cache[key]
                else:
                    # Expirou
                    del self._cache[key]
                    del self._timestamps[key]
            
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any):
        """Adiciona ao cache"""
        with self._lock:
            # LRU: remover mais antigo se atingiu limite
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest = min(self._timestamps, key=self._timestamps.get)
                del self._cache[oldest]
                del self._timestamps[oldest]
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def clear(self):
        """Limpa o cache"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self._cache),
            "max_size": self.max_size
        }


# Cache global para queries frequentes
query_cache = QueryCache()


def cached_query(ttl: int = 300):
    """Decorator para cachear queries"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Criar chave do cache
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Tentar buscar do cache
            cached = query_cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Executar e cachear
            result = func(*args, **kwargs)
            query_cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator