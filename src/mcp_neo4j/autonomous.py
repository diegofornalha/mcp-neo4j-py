#!/usr/bin/env python3
"""
Sistema Autônomo de Auto-Aprimoramento
Monitora continuamente e aplica aprendizados automaticamente
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)


class AutonomousImprover:
    """Sistema autônomo que monitora e aprende continuamente"""
    
    def __init__(self, neo4j_conn, improver):
        self.conn = neo4j_conn
        self.improver = improver
        self.running = False
        self.last_check = datetime.now()
        self.monitoring_interval = 30  # segundos
        
    async def start(self):
        """Inicia o sistema autônomo"""
        self.running = True
        logger.info("🤖 Sistema Autônomo iniciado")
        
        # Iniciar tarefas assíncronas
        await asyncio.gather(
            self.monitor_continuously(),
            self.apply_learnings(),
            self.cleanup_old_data(),
            self.analyze_patterns()
        )
    
    async def monitor_continuously(self):
        """Monitora o sistema continuamente"""
        while self.running:
            try:
                # Verificar novas entradas no Neo4j
                new_entries = self.check_new_entries()
                
                if new_entries:
                    logger.info(f"📊 {len(new_entries)} novas entradas detectadas")
                    
                    for entry in new_entries:
                        # Analisar e aprender automaticamente
                        await self.analyze_entry(entry)
                
                # Verificar padrões
                patterns = self.detect_patterns()
                if patterns:
                    await self.save_patterns(patterns)
                
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                # Salvar erro para aprender
                self.improver.learn_from_execution(
                    "monitoring", 
                    str(e), 
                    success=False
                )
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def apply_learnings(self):
        """Aplica aprendizados automaticamente"""
        while self.running:
            try:
                # Buscar aprendizados recentes
                learnings = self.get_recent_learnings()
                
                for learning in learnings:
                    # Verificar se é aplicável
                    if self.is_applicable(learning):
                        await self.apply_learning(learning)
                        logger.info(f"✅ Aprendizado aplicado: {learning.get('name')}")
                
            except Exception as e:
                logger.error(f"Erro ao aplicar aprendizados: {e}")
            
            await asyncio.sleep(60)  # Verificar a cada minuto
    
    async def cleanup_old_data(self):
        """Limpa dados antigos e consolida conhecimento"""
        while self.running:
            try:
                # Aguardar 1 hora
                await asyncio.sleep(3600)
                
                # Consolidar aprendizados similares
                consolidated = self.consolidate_learnings()
                logger.info(f"🔄 {consolidated} aprendizados consolidados")
                
                # Remover dados obsoletos
                removed = self.remove_obsolete_data()
                logger.info(f"🗑️ {removed} dados obsoletos removidos")
                
            except Exception as e:
                logger.error(f"Erro na limpeza: {e}")
    
    async def analyze_patterns(self):
        """Analisa padrões e tendências"""
        while self.running:
            try:
                # Aguardar 5 minutos
                await asyncio.sleep(300)
                
                # Analisar padrões de erro
                error_patterns = self.analyze_error_patterns()
                if error_patterns:
                    await self.create_prevention_rules(error_patterns)
                
                # Analisar padrões de sucesso
                success_patterns = self.analyze_success_patterns()
                if success_patterns:
                    await self.create_best_practices(success_patterns)
                
            except Exception as e:
                logger.error(f"Erro na análise de padrões: {e}")
    
    def check_new_entries(self) -> List[Dict]:
        """Verifica novas entradas desde última checagem"""
        query = """
        MATCH (n)
        WHERE n.created_at >= $last_check
        RETURN n, labels(n) as labels
        ORDER BY n.created_at DESC
        LIMIT 50
        """
        
        results = self.conn.execute_query(
            query, 
            {"last_check": self.last_check.isoformat()}
        )
        
        self.last_check = datetime.now()
        return results
    
    async def analyze_entry(self, entry: Dict):
        """Analisa uma entrada e aprende com ela"""
        node = entry.get("n", {})
        labels = entry.get("labels", [])
        
        # Se for erro, aprender prevenção
        if "Error" in labels:
            prevention = self.generate_prevention(node)
            if prevention:
                self.save_prevention_rule(prevention)
        
        # Se for sucesso, identificar padrão
        elif "SuccessfulExecution" in labels:
            pattern = self.identify_success_pattern(node)
            if pattern:
                self.save_success_pattern(pattern)
        
        # Se for documentação, indexar
        elif "Documentation" in labels:
            await self.index_documentation(node)
    
    def detect_patterns(self) -> List[Dict]:
        """Detecta padrões nos dados"""
        query = """
        MATCH (n)
        WHERE n.created_at >= $time_window
        WITH labels(n)[0] as label, count(n) as count
        WHERE count > 3
        RETURN label, count
        ORDER BY count DESC
        """
        
        time_window = (datetime.now() - timedelta(hours=1)).isoformat()
        results = self.conn.execute_query(query, {"time_window": time_window})
        
        patterns = []
        for r in results:
            if r["count"] > 5:  # Padrão significativo
                patterns.append({
                    "type": r["label"],
                    "frequency": r["count"],
                    "detected_at": datetime.now().isoformat()
                })
        
        return patterns
    
    async def save_patterns(self, patterns: List[Dict]):
        """Salva padrões detectados"""
        for pattern in patterns:
            query = """
            MERGE (p:Pattern {type: $type})
            SET p += $props
            """
            self.conn.execute_query(
                query,
                {"type": pattern["type"], "props": pattern}
            )
    
    def get_recent_learnings(self) -> List[Dict]:
        """Busca aprendizados recentes não aplicados"""
        query = """
        MATCH (l:Learning)
        WHERE l.applied IS NULL OR l.applied = false
        AND l.created_at >= $time_window
        RETURN l
        ORDER BY l.created_at DESC
        LIMIT 10
        """
        
        time_window = (datetime.now() - timedelta(hours=24)).isoformat()
        results = self.conn.execute_query(query, {"time_window": time_window})
        
        return [r["l"] for r in results]
    
    def is_applicable(self, learning: Dict) -> bool:
        """Verifica se um aprendizado é aplicável"""
        # Verificar se tem informação suficiente
        if not learning.get("task") or not learning.get("result"):
            return False
        
        # Verificar se é recente
        created = learning.get("created_at")
        if created:
            age = datetime.now() - datetime.fromisoformat(created)
            if age.days > 7:  # Muito antigo
                return False
        
        return True
    
    async def apply_learning(self, learning: Dict):
        """Aplica um aprendizado específico"""
        # Marcar como aplicado
        query = """
        MATCH (l:Learning)
        WHERE elementId(l) = $id OR l.name = $name
        SET l.applied = true, l.applied_at = datetime()
        """
        
        self.conn.execute_query(
            query,
            {"id": learning.get("element_id"), "name": learning.get("name")}
        )
        
        # Criar regra baseada no aprendizado
        if learning.get("success"):
            await self.create_best_practice_from_learning(learning)
        else:
            await self.create_prevention_from_learning(learning)
    
    def consolidate_learnings(self) -> int:
        """Consolida aprendizados similares"""
        query = """
        MATCH (l1:Learning), (l2:Learning)
        WHERE l1.task = l2.task 
        AND elementId(l1) < elementId(l2)
        AND l1.success = l2.success
        WITH l1, collect(l2) as duplicates
        WHERE size(duplicates) > 0
        FOREACH (dup IN duplicates | DELETE dup)
        RETURN count(duplicates) as consolidated
        """
        
        results = self.conn.execute_query(query)
        return sum(r["consolidated"] for r in results)
    
    def remove_obsolete_data(self) -> int:
        """Remove dados obsoletos"""
        query = """
        MATCH (n)
        WHERE n.created_at < $cutoff
        AND NOT (n:ProjectRules OR n:Documentation OR n:Pattern)
        DELETE n
        RETURN count(n) as removed
        """
        
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        results = self.conn.execute_query(query, {"cutoff": cutoff})
        
        return results[0]["removed"] if results else 0
    
    def analyze_error_patterns(self) -> List[Dict]:
        """Analisa padrões de erro"""
        query = """
        MATCH (e:Error)
        WITH e.type as error_type, count(e) as frequency, 
             collect(e.message)[0..3] as samples
        WHERE frequency > 2
        RETURN error_type, frequency, samples
        """
        
        results = self.conn.execute_query(query)
        return results
    
    def analyze_success_patterns(self) -> List[Dict]:
        """Analisa padrões de sucesso"""
        query = """
        MATCH (s:SuccessfulExecution)
        WITH s.task as task_type, count(s) as frequency,
             avg(duration(s.created_at, s.completed_at)) as avg_duration
        WHERE frequency > 3
        RETURN task_type, frequency, avg_duration
        """
        
        results = self.conn.execute_query(query)
        return results
    
    async def create_prevention_rules(self, patterns: List[Dict]):
        """Cria regras de prevenção baseadas em padrões de erro"""
        for pattern in patterns:
            rule = {
                "name": f"prevent_{pattern['error_type']}",
                "description": f"Prevenir erro: {pattern['error_type']}",
                "frequency": pattern["frequency"],
                "created_at": datetime.now().isoformat(),
                "auto_generated": True
            }
            
            query = """
            MERGE (r:ProjectRules {name: 'auto_generated'})
            CREATE (rule:Rule $props)
            CREATE (r)-[:HAS_RULE]->(rule)
            """
            
            self.conn.execute_query(query, {"props": rule})
    
    async def create_best_practices(self, patterns: List[Dict]):
        """Cria melhores práticas baseadas em padrões de sucesso"""
        for pattern in patterns:
            practice = {
                "name": f"best_practice_{pattern['task_type']}",
                "description": f"Melhor prática para: {pattern['task_type']}",
                "frequency": pattern["frequency"],
                "created_at": datetime.now().isoformat(),
                "auto_generated": True
            }
            
            query = """
            CREATE (bp:BestPractice $props)
            """
            
            self.conn.execute_query(query, {"props": practice})
    
    def stop(self):
        """Para o sistema autônomo"""
        self.running = False
        logger.info("🛑 Sistema Autônomo parado")


# Função para ativar o modo autônomo
async def activate_autonomous_mode(neo4j_conn, improver):
    """Ativa o modo autônomo de auto-aprimoramento"""
    autonomous = AutonomousImprover(neo4j_conn, improver)
    
    logger.info("🚀 Ativando modo autônomo...")
    
    # Salvar estado no Neo4j
    query = """
    CREATE (a:AutonomousMode {
        activated_at: datetime(),
        status: 'active',
        monitoring_interval: $interval
    })
    """
    neo4j_conn.execute_query(query, {"interval": autonomous.monitoring_interval})
    
    # Iniciar sistema autônomo
    await autonomous.start()
    
    return autonomous