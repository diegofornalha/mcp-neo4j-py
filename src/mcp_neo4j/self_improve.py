#!/usr/bin/env python3
"""
Sistema de Auto-Aprimoramento usando Neo4j
Consulta conhecimento armazenado no grafo para melhorar decisões
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class SelfImprover:
    """Sistema que busca conhecimento no Neo4j para auto-aprimoramento"""
    
    def __init__(self, neo4j_conn):
        self.conn = neo4j_conn
    
    def get_project_rules(self) -> List[Dict]:
        """Busca todas as regras do projeto"""
        query = """
        MATCH (r:ProjectRules)-[:HAS_RULE]->(rule)
        RETURN rule.name as name, 
               rule.description as description,
               rule.priority as priority
        ORDER BY rule.priority DESC, rule.created_at DESC
        """
        return self.conn.execute_query(query)
    
    def get_relevant_knowledge(self, context: str) -> List[Dict]:
        """Busca conhecimento relevante baseado no contexto"""
        query = """
        MATCH (n)
        WHERE ANY(prop IN keys(n) WHERE 
            n[prop] IS NOT NULL AND toString(n[prop]) CONTAINS $context)
        RETURN labels(n) as labels, 
               n.name as name,
               n.description as description,
               n.content as content,
               n.useful_code as code
        LIMIT 10
        """
        return self.conn.execute_query(query, {"context": context})
    
    def get_past_decisions(self, topic: str) -> List[Dict]:
        """Busca decisões anteriores sobre um tópico"""
        query = """
        MATCH (d:Decision)
        WHERE d.topic CONTAINS $topic OR d.description CONTAINS $topic
        RETURN d.topic as topic,
               d.decision as decision,
               d.reason as reason,
               d.outcome as outcome,
               d.created_at as date
        ORDER BY d.created_at DESC
        LIMIT 5
        """
        return self.conn.execute_query(query, {"topic": topic})
    
    def save_learning(self, category: str, learning: Dict) -> bool:
        """Salva novo aprendizado no grafo"""
        learning["created_at"] = datetime.now().isoformat()
        learning["category"] = category
        
        query = f"""
        MERGE (l:Learning:{category} {{name: $name}})
        SET l += $props
        RETURN l
        """
        
        result = self.conn.execute_query(
            query, 
            {"name": learning.get("name", f"{category}_{datetime.now().timestamp()}"),
             "props": learning}
        )
        return len(result) > 0
    
    def get_error_patterns(self) -> List[Dict]:
        """Busca padrões de erros conhecidos"""
        query = """
        MATCH (e:Error)
        RETURN e.type as type,
               e.message as message,
               e.solution as solution,
               e.prevention as prevention
        """
        return self.conn.execute_query(query)
    
    def suggest_improvements(self, current_task: str) -> Dict:
        """Sugere melhorias baseadas no conhecimento do grafo"""
        suggestions = {
            "rules": [],
            "relevant_knowledge": [],
            "past_decisions": [],
            "warnings": []
        }
        
        # Buscar regras aplicáveis
        rules = self.get_project_rules()
        suggestions["rules"] = [r for r in rules if r["description"]]
        
        # Buscar conhecimento relevante
        knowledge = self.get_relevant_knowledge(current_task)
        suggestions["relevant_knowledge"] = knowledge
        
        # Buscar decisões anteriores
        decisions = self.get_past_decisions(current_task)
        suggestions["past_decisions"] = decisions
        
        # Verificar padrões de erro
        errors = self.get_error_patterns()
        relevant_errors = [e for e in errors if current_task.lower() in str(e).lower()]
        if relevant_errors:
            suggestions["warnings"] = relevant_errors
        
        return suggestions
    
    def learn_from_execution(self, task: str, result: str, success: bool):
        """Aprende com o resultado de uma execução"""
        learning = {
            "name": f"execution_{datetime.now().timestamp()}",
            "task": task,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            self.save_learning("SuccessfulExecution", learning)
        else:
            self.save_learning("FailedExecution", learning)
            # Salvar como erro para aprender
            error = {
                "name": f"error_{datetime.now().timestamp()}",
                "type": "execution_error",
                "message": result,
                "context": task,
                "prevention": "Verificar contexto antes de executar"
            }
            self.conn.execute_query(
                "CREATE (e:Error $props) RETURN e",
                {"props": error}
            )


def get_context_before_action(neo4j_conn, action_description: str) -> str:
    """Busca contexto completo antes de executar uma ação"""
    improver = SelfImprover(neo4j_conn)
    suggestions = improver.suggest_improvements(action_description)
    
    context = []
    
    # Adicionar regras importantes
    if suggestions["rules"]:
        context.append("🔴 REGRAS IMPORTANTES:")
        for rule in suggestions["rules"][:3]:
            context.append(f"  • {rule['description']}")
    
    # Adicionar conhecimento relevante
    if suggestions["relevant_knowledge"]:
        context.append("\n📚 CONHECIMENTO RELEVANTE:")
        for knowledge in suggestions["relevant_knowledge"][:3]:
            context.append(f"  • {knowledge['name']}: {knowledge.get('description', '')[:100]}")
    
    # Adicionar avisos
    if suggestions["warnings"]:
        context.append("\n⚠️ AVISOS:")
        for warning in suggestions["warnings"]:
            context.append(f"  • {warning['type']}: {warning['solution']}")
    
    return "\n".join(context)


def auto_improve_tool(neo4j_conn):
    """Ferramenta principal de auto-aprimoramento"""
    improver = SelfImprover(neo4j_conn)
    
    # Implementar lógica de melhoria contínua
    print("🧠 Sistema de Auto-Aprimoramento Ativado")
    
    # Buscar e aplicar regras
    rules = improver.get_project_rules()
    print(f"📋 {len(rules)} regras carregadas do Neo4j")
    
    # Retornar instância para uso
    return improver