#!/usr/bin/env python3
"""
Script para migrar labels Learning para Memory
Mantém backup dos labels originais
"""

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações do Neo4j
NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
NEO4J_DATABASE = "neo4j"

def migrate_labels():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    with driver.session(database=NEO4J_DATABASE) as session:
        # Contar nós antes
        result = session.run("MATCH (l:Learning) RETURN count(l) as total")
        learning_count = result.single()['total']
        logger.info(f"Encontrados {learning_count} nós com label Learning")

        # Adicionar label Memory mantendo Learning
        result = session.run("""
            MATCH (l:Learning)
            SET l:Memory
            RETURN count(l) as migrated
        """)
        migrated = result.single()['migrated']
        logger.info(f"Migrados {migrated} nós - adicionado label Memory")

        # Verificar resultado
        result = session.run("MATCH (m:Memory) RETURN count(m) as total")
        memory_count = result.single()['total']
        logger.info(f"Total de nós com label Memory após migração: {memory_count}")

        # Mostrar alguns exemplos
        result = session.run("""
            MATCH (m:Memory)
            RETURN m.content as content, labels(m) as labels
            LIMIT 3
        """)

        logger.info("\nExemplos de nós migrados:")
        for record in result:
            content = record['content'][:50] if record['content'] else 'Sem conteúdo'
            labels = record['labels']
            logger.info(f"  Labels: {labels} - Conteúdo: {content}...")

    driver.close()
    logger.info("\n✅ Migração concluída!")

if __name__ == "__main__":
    migrate_labels()