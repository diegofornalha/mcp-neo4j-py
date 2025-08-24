#!/usr/bin/env python3
"""
Script para verificar e ativar o sistema autônomo
"""

import os
from neo4j import GraphDatabase
from datetime import datetime

# Configurações do Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Neo4j@1992")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

def check_autonomous_status():
    """Verifica o status do sistema autônomo no Neo4j"""
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            # Verificar se há modo autônomo ativo
            result = session.run("""
                MATCH (a:AutonomousMode)
                RETURN a
                ORDER BY a.activated_at DESC
                LIMIT 1
            """)
            
            autonomous_record = result.single()
            
            print("🤖 SISTEMA AUTÔNOMO - STATUS ATUAL")
            print("=" * 50)
            
            if autonomous_record:
                autonomous = autonomous_record["a"]
                status = autonomous.get("status", "unknown")
                activated_at = autonomous.get("activated_at")
                deactivated_at = autonomous.get("deactivated_at")
                
                print(f"Status: {status.upper()}")
                print(f"Ativado em: {activated_at}")
                if deactivated_at:
                    print(f"Desativado em: {deactivated_at}")
                print(f"Intervalo de monitoramento: {autonomous.get('monitoring_interval', 'N/A')} segundos")
            else:
                print("Status: NÃO CONFIGURADO")
                print("Modo autônomo nunca foi ativado")
            
            # Estatísticas do sistema
            print("\n📊 ESTATÍSTICAS DO SISTEMA")
            print("=" * 30)
            
            stats_result = session.run("""
                OPTIONAL MATCH (l:Learning)
                WITH count(l) as total_learnings,
                     sum(CASE WHEN l.applied = true THEN 1 ELSE 0 END) as applied_learnings
                OPTIONAL MATCH (p:Pattern)
                WITH total_learnings, applied_learnings, count(p) as patterns_detected
                OPTIONAL MATCH (e:Error)
                WITH total_learnings, applied_learnings, patterns_detected, count(e) as errors_logged
                OPTIONAL MATCH (d:Documentation)
                WITH total_learnings, applied_learnings, patterns_detected, errors_logged, count(d) as docs_count
                OPTIONAL MATCH (r:ProjectRules)
                WITH total_learnings, applied_learnings, patterns_detected, errors_logged, docs_count, count(r) as rules_count
                RETURN total_learnings, applied_learnings, patterns_detected, errors_logged, docs_count, rules_count
            """)
            
            stats = stats_result.single()
            if stats:
                print(f"Total de aprendizados: {stats['total_learnings']}")
                print(f"Aprendizados aplicados: {stats['applied_learnings']}")
                print(f"Padrões detectados: {stats['patterns_detected']}")
                print(f"Erros registrados: {stats['errors_logged']}")
                print(f"Documentações: {stats['docs_count']}")
                print(f"Regras de projeto: {stats['rules_count']}")
            
            # Verificar conhecimento recente
            print("\n🧠 CONHECIMENTO RECENTE")
            print("=" * 25)
            
            recent_result = session.run("""
                MATCH (n)
                WHERE n.created_at IS NOT NULL
                RETURN labels(n)[0] as label, n.name as name, n.created_at as created
                ORDER BY n.created_at DESC
                LIMIT 5
            """)
            
            recent_items = list(recent_result)
            if recent_items:
                for item in recent_items:
                    label = item["label"] or "Unknown"
                    name = item["name"] or "Sem nome"
                    created = item["created"]
                    print(f"• {label}: {name} ({created})")
            else:
                print("Nenhum conhecimento registrado")
            
            print("\n" + "=" * 50)
            
            # Se não há modo autônomo ativo, sugerir ativação
            if not autonomous_record or autonomous_record["a"].get("status") != "active":
                print("\n💡 RECOMENDAÇÃO: Ative o sistema autônomo para:")
                print("   • Monitoramento contínuo")
                print("   • Aprendizado automático")
                print("   • Detecção de padrões")
                print("   • Aplicação de aprendizados")
                
                activate = input("\nDeseja ativar o sistema autônomo agora? (s/n): ").lower().strip()
                if activate == 's':
                    activate_autonomous_system(session)
            else:
                print("\n✅ Sistema autônomo está ATIVO e funcionando!")
                
    except Exception as e:
        print(f"❌ Erro ao conectar com Neo4j: {e}")
    finally:
        driver.close()

def activate_autonomous_system(session):
    """Ativa o sistema autônomo no Neo4j"""
    try:
        # Criar registro de ativação
        session.run("""
            CREATE (a:AutonomousMode {
                activated_at: datetime(),
                status: 'active',
                monitoring_interval: 30,
                activated_by: 'manual_script'
            })
        """)
        
        # Criar regras básicas se não existirem
        session.run("""
            MERGE (r:ProjectRules {name: 'auto_generated'})
            ON CREATE SET r.created_at = datetime(),
                         r.description = 'Regras geradas automaticamente pelo sistema autônomo'
        """)
        
        print("✅ Sistema autônomo ATIVADO com sucesso!")
        print("🔄 O sistema começará a monitorar e aprender automaticamente")
        
    except Exception as e:
        print(f"❌ Erro ao ativar sistema autônomo: {e}")

if __name__ == "__main__":
    check_autonomous_status()