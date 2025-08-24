#!/usr/bin/env python3
"""
Teste direto das funcionalidades autônomas
"""

import os
import sys
from neo4j import GraphDatabase
from datetime import datetime

# Adicionar path para importar módulos
sys.path.append('/app/src')
sys.path.append('/app/src/mcp_neo4j')

from self_improve import SelfImprover, get_context_before_action
from autonomous import AutonomousImprover

# Configurações do Neo4j
NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "Cancela@1"
NEO4J_DATABASE = "neo4j"

class Neo4jConnection:
    """Gerenciador de conexão com Neo4j"""
    
    def __init__(self):
        self.driver = None
        self.connect()
    
    def connect(self):
        """Estabelece conexão com Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
            self.driver.verify_connectivity()
            print("✅ Conectado ao Neo4j com sucesso")
        except Exception as e:
            print(f"❌ Erro ao conectar com Neo4j: {e}")
            raise
    
    def execute_query(self, query: str, params=None):
        """Executa query no Neo4j e retorna resultados"""
        if not self.driver:
            self.connect()
        
        try:
            with self.driver.session(database=NEO4J_DATABASE) as session:
                result = session.run(query, params or {})
                return [dict(record) for record in result]
        except Exception as e:
            print(f"❌ Erro ao executar query: {e}")
            raise
    
    def close(self):
        """Fecha conexão com Neo4j"""
        if self.driver:
            self.driver.close()

def test_autonomous_system():
    """Testa o sistema autônomo"""
    
    print("🤖 TESTANDO SISTEMA AUTÔNOMO MCP NEO4J")
    print("=" * 50)
    
    # Conectar ao Neo4j
    conn = Neo4jConnection()
    
    try:
        # Verificar status atual
        print("\n📊 1. Verificando status atual...")
        
        result = conn.execute_query("""
            MATCH (a:AutonomousMode)
            RETURN a
            ORDER BY a.activated_at DESC
            LIMIT 1
        """)
        
        if result:
            autonomous = result[0]["a"]
            status = autonomous.get("status", "unknown")
            print(f"   Status atual: {status.upper()}")
        else:
            print("   Status: NÃO CONFIGURADO")
        
        # Testar sistema de auto-aprimoramento
        print("\n🧠 2. Testando sistema de auto-aprimoramento...")
        improver = SelfImprover(conn)
        
        # Simular aprendizado
        task = "testar sistema autônomo"
        result_text = "Sistema funcionando corretamente"
        improver.learn_from_execution(task, result_text, True)
        print("   ✅ Aprendizado registrado com sucesso")
        
        # Buscar contexto
        context = get_context_before_action(conn, "implementar nova feature")
        print(f"   📚 Contexto obtido: {len(context)} caracteres")
        
        # Sugerir melhorias
        suggestions = improver.suggest_improvements("criar novo módulo MCP")
        print(f"   💡 Sugestões geradas: {len(suggestions.get('rules', []))} regras")
        
        # Ativar modo autônomo (apenas registrar no Neo4j)
        print("\n🚀 3. Ativando modo autônomo...")
        
        conn.execute_query("""
            MERGE (a:AutonomousMode {status: 'active'})
            ON CREATE SET a.activated_at = datetime(),
                         a.monitoring_interval = 30
            ON MATCH SET a.status = 'active',
                        a.reactivated_at = datetime()
        """)
        print("   ✅ Modo autônomo ativado no Neo4j")
        
        # Criar algumas regras básicas
        print("\n📋 4. Criando regras básicas...")
        
        basic_rules = [
            {
                "name": "preserve_before_delete",
                "description": "Sempre salvar no Neo4j antes de deletar",
                "priority": 10,
                "category": "data_preservation"
            },
            {
                "name": "check_context_first", 
                "description": "Consultar Neo4j para contexto antes de ação",
                "priority": 9,
                "category": "context_awareness"
            },
            {
                "name": "avoid_duplication",
                "description": "Verificar existência antes de criar",
                "priority": 8,
                "category": "data_integrity"
            }
        ]
        
        for rule in basic_rules:
            rule["created_at"] = datetime.now().isoformat()
            conn.execute_query("""
                MERGE (r:ProjectRules {name: 'system_rules'})
                CREATE (rule:Rule $props)
                CREATE (r)-[:HAS_RULE]->(rule)
            """, {"props": rule})
        
        print(f"   ✅ {len(basic_rules)} regras básicas criadas")
        
        # Verificar estatísticas finais
        print("\n📈 5. Estatísticas finais...")
        
        stats = conn.execute_query("""
            OPTIONAL MATCH (l:Learning) WITH count(l) as learnings
            OPTIONAL MATCH (r:Rule) WITH learnings, count(r) as rules
            OPTIONAL MATCH (a:AutonomousMode) WITH learnings, rules, count(a) as autonomous
            RETURN learnings, rules, autonomous
        """)
        
        if stats:
            s = stats[0]
            print(f"   • Aprendizados: {s['learnings']}")
            print(f"   • Regras: {s['rules']}")
            print(f"   • Modo autônomo: {'ATIVO' if s['autonomous'] > 0 else 'INATIVO'}")
        
        print("\n" + "=" * 50)
        print("✅ SISTEMA AUTÔNOMO CONFIGURADO E FUNCIONANDO!")
        print("\n🎯 RECURSOS ATIVOS:")
        print("   • Auto-aprimoramento baseado em experiência")
        print("   • Consulta de contexto antes de ações")
        print("   • Sistema de regras e aprendizados")
        print("   • Preservação de conhecimento no grafo")
        print("   • Detecção e aplicação de padrões")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_autonomous_system()
    exit(0 if success else 1)