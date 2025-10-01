"""
Query Builder e Templates para operações comuns no Neo4j
Baseado nos padrões identificados no projeto
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class QueryBuilder:
    """Builder para queries Cypher comuns"""
    
    @staticmethod
    def find_or_create_node(label: str, name: str, properties: Optional[Dict] = None) -> tuple:
        """Query para buscar ou criar nó (evita duplicação)"""
        props = properties or {}
        props['name'] = name
        props['created_at'] = datetime.now().isoformat()
        
        query = f"""
        MERGE (n:{label} {{name: $name}})
        ON CREATE SET n = $props
        ON MATCH SET n.accessed_at = datetime()
        RETURN n
        """
        
        return query, {"name": name, "props": props}
    
    @staticmethod
    def create_relationship(from_label: str, from_name: str, 
                           rel_type: str, 
                           to_label: str, to_name: str,
                           rel_props: Optional[Dict] = None) -> tuple:
        """Cria relacionamento entre nós"""
        query = f"""
        MATCH (from:{from_label} {{name: $from_name}})
        MATCH (to:{to_label} {{name: $to_name}})
        MERGE (from)-[r:{rel_type}]->(to)
        SET r = $rel_props
        RETURN from, r, to
        """
        
        params = {
            "from_name": from_name,
            "to_name": to_name,
            "rel_props": rel_props or {"created_at": datetime.now().isoformat()}
        }
        
        return query, params
    
    @staticmethod
    def batch_create_nodes(label: str, items: List[Dict]) -> tuple:
        """Cria múltiplos nós em batch"""
        query = f"""
        UNWIND $items AS item
        CREATE (n:{label})
        SET n = item
        SET n.created_at = datetime()
        RETURN collect(n) as nodes
        """
        
        return query, {"items": items}
    
    @staticmethod
    def search_nodes(label: str, search_term: str, limit: int = 10) -> tuple:
        """Busca nós por termo"""
        query = f"""
        MATCH (n:{label})
        WHERE n.name CONTAINS $search_term 
           OR n.description CONTAINS $search_term
           OR n.content CONTAINS $search_term
        RETURN n
        ORDER BY n.updated_at DESC, n.created_at DESC
        LIMIT $limit
        """
        
        return query, {"search_term": search_term, "limit": limit}
    
    @staticmethod
    def get_node_with_relationships(label: str, name: str, depth: int = 1) -> tuple:
        """Busca nó com seus relacionamentos"""
        query = f"""
        MATCH (n:{label} {{name: $name}})
        OPTIONAL MATCH path = (n)-[*1..{depth}]-(related)
        RETURN n, collect(DISTINCT related) as related_nodes, 
               collect(DISTINCT relationships(path)) as relationships
        """
        
        return query, {"name": name}
    
    @staticmethod
    def delete_node_cascade(label: str, name: str) -> tuple:
        """Deleta nó e seus relacionamentos"""
        query = f"""
        MATCH (n:{label} {{name: $name}})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        
        return query, {"name": name}
    
    @staticmethod
    def update_node_properties(label: str, name: str, properties: Dict) -> tuple:
        """Atualiza propriedades de um nó"""
        properties['updated_at'] = datetime.now().isoformat()
        
        query = f"""
        MATCH (n:{label} {{name: $name}})
        SET n += $props
        RETURN n
        """
        
        return query, {"name": name, "props": properties}


class QueryTemplates:
    """Templates para queries específicas do domínio"""
    
    @staticmethod
    def save_memory(memory_type: str, content: str, metadata: Optional[Dict] = None) -> tuple:
        """Salva uma memória no grafo"""
        query, params = QueryBuilder.find_or_create_node(
            label="Memory",
            name=f"memory_{datetime.now().timestamp()}",
            properties={
                "type": memory_type,
                "content": content,
                "metadata": json.dumps(metadata or {})
            }
        )
        return query, params
    
    @staticmethod
    def save_learning(title: str, description: str, tags: List[str] = None) -> tuple:
        """Salva um aprendizado"""
        query = """
        CREATE (l:Learning {
            name: $title,
            description: $description,
            tags: $tags,
            created_at: datetime(),
            importance: 'normal'
        })
        RETURN l
        """
        
        return query, {
            "title": title,
            "description": description,
            "tags": tags or []
        }
    
    @staticmethod
    def save_bug_fix(problem: str, solution: str, affected_components: List[str] = None) -> tuple:
        """Registra um bug fix"""
        query = """
        CREATE (b:BugFix {
            name: $problem,
            problem: $problem,
            solution: $solution,
            components: $components,
            created_at: datetime(),
            resolved: true
        })
        RETURN b
        """
        
        return query, {
            "problem": problem,
            "solution": solution,
            "components": affected_components or []
        }
    
    @staticmethod
    def get_recent_memories(limit: int = 10, memory_type: Optional[str] = None) -> tuple:
        """Busca memórias recentes"""
        if memory_type:
            query = """
            MATCH (m:Memory {type: $memory_type})
            RETURN m
            ORDER BY m.created_at DESC
            LIMIT $limit
            """
            params = {"memory_type": memory_type, "limit": limit}
        else:
            query = """
            MATCH (m:Memory)
            RETURN m
            ORDER BY m.created_at DESC
            LIMIT $limit
            """
            params = {"limit": limit}
        
        return query, params
    
    @staticmethod
    def find_similar_problems(problem_description: str) -> tuple:
        """Busca problemas similares já resolvidos"""
        query = """
        MATCH (b:BugFix)
        WHERE b.problem CONTAINS $search_term
           OR b.solution CONTAINS $search_term
        RETURN b
        ORDER BY b.created_at DESC
        LIMIT 5
        """
        
        return query, {"search_term": problem_description}
    
    @staticmethod
    def get_knowledge_graph_stats() -> tuple:
        """Estatísticas do grafo de conhecimento"""
        query = """
        MATCH (n)
        WITH labels(n) as node_labels
        UNWIND node_labels as label
        WITH label, count(*) as count
        RETURN collect({label: label, count: count}) as node_stats
        
        UNION
        
        MATCH ()-[r]->()
        WITH type(r) as rel_type, count(*) as count
        RETURN collect({type: rel_type, count: count}) as relationship_stats
        """
        
        return query, {}


class SchemaManager:
    """Gerenciador de schema e constraints"""
    
    @staticmethod
    def create_constraints() -> List[tuple]:
        """Cria constraints essenciais"""
        constraints = [
            # Constraint de unicidade para Memory
            ("CREATE CONSTRAINT memory_name_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.name IS UNIQUE", {}),
            
            # Constraint de unicidade para Learning
            ("CREATE CONSTRAINT learning_name_unique IF NOT EXISTS FOR (l:Learning) REQUIRE l.name IS UNIQUE", {}),
            
            # Constraint de unicidade para BugFix
            ("CREATE CONSTRAINT bugfix_name_unique IF NOT EXISTS FOR (b:BugFix) REQUIRE b.name IS UNIQUE", {}),
            
            # Índices para performance
            ("CREATE INDEX memory_type_index IF NOT EXISTS FOR (m:Memory) ON (m.type)", {}),
            ("CREATE INDEX memory_created_index IF NOT EXISTS FOR (m:Memory) ON (m.created_at)", {}),
            ("CREATE INDEX learning_tags_index IF NOT EXISTS FOR (l:Learning) ON (l.tags)", {}),
            ("CREATE FULLTEXT INDEX memory_search_index IF NOT EXISTS FOR (m:Memory) ON EACH [m.content, m.description]", {}),
        ]
        
        return constraints
    
    @staticmethod
    def validate_node_data(label: str, data: Dict) -> Dict:
        """Valida e sanitiza dados antes de inserir"""
        # Remover campos nulos
        cleaned = {k: v for k, v in data.items() if v is not None}
        
        # Adicionar campos obrigatórios
        if 'name' not in cleaned:
            cleaned['name'] = f"{label.lower()}_{datetime.now().timestamp()}"
        
        if 'created_at' not in cleaned:
            cleaned['created_at'] = datetime.now().isoformat()
        
        # Converter listas e dicts para JSON strings se necessário
        for key, value in cleaned.items():
            if isinstance(value, (dict, list)):
                cleaned[key] = json.dumps(value)
        
        return cleaned