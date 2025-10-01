"""
Sistema de Batch Operations para Neo4j
Otimizado para operações em massa
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processador de operações em batch"""
    
    def __init__(self, connection_pool, batch_size: int = 1000):
        self.connection_pool = connection_pool
        self.batch_size = batch_size
        self.stats = {
            "total_processed": 0,
            "total_failed": 0,
            "last_batch_time": None,
            "average_batch_time": 0
        }
    
    def process_in_batches(self, items: List[Any], 
                          processor_func: Callable,
                          batch_size: Optional[int] = None) -> Dict:
        """
        Processa items em batches
        
        Args:
            items: Lista de items para processar
            processor_func: Função que recebe um batch e retorna (query, params)
            batch_size: Tamanho do batch (opcional, usa padrão se não especificado)
        
        Returns:
            Estatísticas do processamento
        """
        batch_size = batch_size or self.batch_size
        total_items = len(items)
        processed = 0
        failed = 0
        batch_times = []
        
        logger.info(f"Iniciando processamento de {total_items} items em batches de {batch_size}")
        
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_start = time.time()
            
            try:
                query, params = processor_func(batch)
                self.connection_pool.execute_with_retry(query, params)
                processed += len(batch)
                
                batch_time = time.time() - batch_start
                batch_times.append(batch_time)
                
                # Log de progresso
                progress = (i + len(batch)) / total_items * 100
                logger.info(f"Progresso: {progress:.1f}% ({processed}/{total_items}) - "
                          f"Batch processado em {batch_time:.2f}s")
                
            except Exception as e:
                failed += len(batch)
                logger.error(f"Erro ao processar batch {i//batch_size + 1}: {e}")
        
        # Atualizar estatísticas
        self.stats["total_processed"] += processed
        self.stats["total_failed"] += failed
        if batch_times:
            self.stats["last_batch_time"] = batch_times[-1]
            self.stats["average_batch_time"] = sum(batch_times) / len(batch_times)
        
        return {
            "total_items": total_items,
            "processed": processed,
            "failed": failed,
            "batches": len(batch_times),
            "total_time": sum(batch_times),
            "average_batch_time": self.stats["average_batch_time"]
        }
    
    def batch_create_nodes(self, label: str, nodes_data: List[Dict]) -> Dict:
        """Cria múltiplos nós em batches"""
        def create_batch(batch):
            query = f"""
            UNWIND $batch AS item
            CREATE (n:{label})
            SET n = item
            SET n.batch_created_at = datetime()
            RETURN count(n) as created
            """
            return query, {"batch": batch}
        
        return self.process_in_batches(nodes_data, create_batch)
    
    def batch_create_relationships(self, relationships: List[Dict]) -> Dict:
        """
        Cria múltiplos relacionamentos em batches
        
        Args:
            relationships: Lista de dicts com:
                - from_label, from_name
                - to_label, to_name
                - rel_type
                - properties (opcional)
        """
        def create_batch(batch):
            query = """
            UNWIND $batch AS rel
            MATCH (from) WHERE from.name = rel.from_name AND rel.from_label IN labels(from)
            MATCH (to) WHERE to.name = rel.to_name AND rel.to_label IN labels(to)
            CREATE (from)-[r:RELATED]->(to)
            SET r = rel.properties
            SET r.type = rel.rel_type
            RETURN count(r) as created
            """
            return query, {"batch": batch}
        
        return self.process_in_batches(relationships, create_batch)
    
    def batch_update_nodes(self, label: str, updates: List[Dict]) -> Dict:
        """
        Atualiza múltiplos nós em batches
        
        Args:
            label: Label dos nós
            updates: Lista de dicts com 'name' e 'properties'
        """
        def update_batch(batch):
            query = f"""
            UNWIND $batch AS update
            MATCH (n:{label} {{name: update.name}})
            SET n += update.properties
            SET n.batch_updated_at = datetime()
            RETURN count(n) as updated
            """
            return query, {"batch": batch}
        
        return self.process_in_batches(updates, update_batch)
    
    def batch_delete_nodes(self, label: str, names: List[str]) -> Dict:
        """Deleta múltiplos nós em batches"""
        def delete_batch(batch):
            query = f"""
            MATCH (n:{label})
            WHERE n.name IN $batch
            DETACH DELETE n
            RETURN count(n) as deleted
            """
            return query, {"batch": batch}
        
        return self.process_in_batches(names, delete_batch, batch_size=500)
    
    def batch_merge_nodes(self, label: str, nodes_data: List[Dict]) -> Dict:
        """
        MERGE múltiplos nós (cria se não existe, atualiza se existe)
        """
        def merge_batch(batch):
            query = f"""
            UNWIND $batch AS item
            MERGE (n:{label} {{name: item.name}})
            ON CREATE SET n = item, n.created_at = datetime()
            ON MATCH SET n += item, n.updated_at = datetime()
            RETURN count(n) as merged
            """
            return query, {"batch": batch}
        
        return self.process_in_batches(nodes_data, merge_batch)
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do batch processor"""
        return self.stats


class BulkImporter:
    """Importador em massa para grandes volumes de dados"""
    
    def __init__(self, connection_pool):
        self.connection_pool = connection_pool
        self.batch_processor = BatchProcessor(connection_pool)
    
    def import_csv_data(self, csv_data: List[Dict], 
                       label: str,
                       unique_field: str = "name") -> Dict:
        """
        Importa dados de CSV para Neo4j
        
        Args:
            csv_data: Lista de dicionários do CSV
            label: Label para os nós
            unique_field: Campo único para MERGE
        """
        # Preparar dados
        prepared_data = []
        for row in csv_data:
            # Sanitizar dados
            clean_row = {k: v for k, v in row.items() if v is not None and v != ''}
            if unique_field not in clean_row:
                clean_row[unique_field] = f"{label}_{datetime.now().timestamp()}"
            prepared_data.append(clean_row)
        
        # Importar em batches
        return self.batch_processor.batch_merge_nodes(label, prepared_data)
    
    def import_json_graph(self, nodes: List[Dict], 
                         edges: List[Dict]) -> Dict:
        """
        Importa um grafo completo de JSON
        
        Args:
            nodes: Lista de nós com 'id', 'label', e propriedades
            edges: Lista de arestas com 'source', 'target', 'type'
        """
        stats = {
            "nodes": {},
            "edges": {},
            "total_time": 0
        }
        
        start_time = time.time()
        
        # Importar nós por label
        nodes_by_label = {}
        for node in nodes:
            label = node.get('label', 'Node')
            if label not in nodes_by_label:
                nodes_by_label[label] = []
            nodes_by_label[label].append(node)
        
        # Criar nós
        for label, label_nodes in nodes_by_label.items():
            logger.info(f"Importando {len(label_nodes)} nós do tipo {label}")
            stats["nodes"][label] = self.batch_processor.batch_merge_nodes(
                label, label_nodes
            )
        
        # Criar relacionamentos
        if edges:
            logger.info(f"Importando {len(edges)} relacionamentos")
            stats["edges"] = self.batch_processor.batch_create_relationships(edges)
        
        stats["total_time"] = time.time() - start_time
        logger.info(f"Importação completa em {stats['total_time']:.2f}s")
        
        return stats
    
    def export_subgraph(self, start_node_name: str, 
                       max_depth: int = 2) -> Dict:
        """
        Exporta um subgrafo começando de um nó
        
        Args:
            start_node_name: Nome do nó inicial
            max_depth: Profundidade máxima
        
        Returns:
            Dict com 'nodes' e 'edges'
        """
        query = """
        MATCH path = (start {name: $name})-[*0..""" + str(max_depth) + """]-()
        WITH nodes(path) as nodes, relationships(path) as rels
        UNWIND nodes as node
        WITH collect(DISTINCT {
            id: id(node),
            label: labels(node)[0],
            properties: properties(node)
        }) as all_nodes,
        rels
        UNWIND rels as rel
        WITH all_nodes, collect(DISTINCT {
            source: id(startNode(rel)),
            target: id(endNode(rel)),
            type: type(rel),
            properties: properties(rel)
        }) as all_edges
        RETURN all_nodes as nodes, all_edges as edges
        """
        
        result = self.connection_pool.execute_with_retry(
            query, {"name": start_node_name}
        )
        
        if result:
            return result[0]
        return {"nodes": [], "edges": []}


class TransactionBatcher:
    """Agrupa múltiplas operações em uma única transação"""
    
    def __init__(self, connection_pool):
        self.connection_pool = connection_pool
        self.operations = []
    
    def add_operation(self, query: str, params: Dict):
        """Adiciona operação ao batch"""
        self.operations.append((query, params))
    
    def execute(self) -> List[Any]:
        """Executa todas as operações em uma única transação"""
        if not self.operations:
            return []
        
        results = []
        
        # Executar em uma única sessão/transação
        with self.connection_pool.driver.session(database=self.connection_pool.database) as session:
            with session.begin_transaction() as tx:
                try:
                    for query, params in self.operations:
                        result = tx.run(query, params)
                        results.append([dict(record) for record in result])
                    
                    tx.commit()
                    logger.info(f"Transação com {len(self.operations)} operações commitada com sucesso")
                    
                except Exception as e:
                    tx.rollback()
                    logger.error(f"Erro na transação, rollback executado: {e}")
                    raise
                finally:
                    self.operations.clear()
        
        return results
    
    def clear(self):
        """Limpa operações pendentes"""
        self.operations.clear()