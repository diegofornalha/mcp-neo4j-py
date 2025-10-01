#!/usr/bin/env python3
"""
Sistema de Backup Temático para Neo4j
Permite backups separados por tema/categoria com validação de integridade
"""

import json
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


class ThematicBackup:
    """Sistema de backup temático com validação de integridade"""

    def __init__(self, connection):
        self.conn = connection
        # Usar diretório de backup no home do usuário, fora do .claude
        self.backup_dir = Path.home() / "memory-backups-thematic"
        self.backup_dir.mkdir(exist_ok=True)

    def analyze_themes(self) -> Dict[str, int]:
        """Analisa os temas/categorias existentes no Neo4j"""
        query = """
        MATCH (n)
        WITH n,
             COALESCE(n.category, n.type, n.topic, n.domain, 'general') as theme
        RETURN theme, count(n) as count
        ORDER BY count DESC
        """

        results = self.conn.execute_query(query)
        return {r['theme']: r['count'] for r in results}

    def get_smart_themes(self) -> Dict[str, List[str]]:
        """Define agrupamentos inteligentes de temas relacionados"""

        # Análise de labels e propriedades
        label_query = """
        MATCH (n)
        UNWIND labels(n) as label
        RETURN DISTINCT label, count(n) as count
        ORDER BY count DESC
        """

        labels = self.conn.execute_query(label_query)

        # Definir agrupamentos inteligentes
        theme_groups = {
            "learning_knowledge": ["Learning", "knowledge", "pattern", "insight", "lesson"],
            "communication": ["message", "conversation", "interaction", "response"],
            "technical": ["code", "bug", "error", "fix", "implementation", "technical"],
            "project_work": ["project", "task", "feature", "requirement", "solution"],
            "system_components": ["Component", "Agent", "System", "tool", "skill"],
            "improvements": ["Improvement", "optimization", "enhancement", "update"],
            "autonomous": ["autonomous", "self_improve", "decision", "rule"],
            "general": []  # Para itens não categorizados
        }

        return theme_groups

    def backup_by_theme(self, theme_name: str, node_filters: List[str]) -> str:
        """
        Cria backup de um tema específico

        Args:
            theme_name: Nome do tema para o arquivo
            node_filters: Lista de labels/tipos para incluir

        Returns:
            Path do arquivo criado
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Buscar nós do tema
        filter_conditions = []
        for filter_item in node_filters:
            filter_conditions.extend([
                f"'{filter_item}' IN labels(n)",
                f"n.category = '{filter_item}'",
                f"n.type = '{filter_item}'",
                f"n.topic = '{filter_item}'"
            ])

        where_clause = " OR ".join(filter_conditions) if filter_conditions else "TRUE"

        # Query para nós e seus relacionamentos
        nodes_query = f"""
        MATCH (n)
        WHERE {where_clause}
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN
            n as node,
            collect(DISTINCT r) as relationships,
            collect(DISTINCT m) as connected_nodes
        """

        results = self.conn.execute_query(nodes_query)

        # Estruturar dados do backup
        backup_data = {
            "metadata": {
                "theme": theme_name,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "filters": node_filters,
                "statistics": {
                    "total_nodes": 0,
                    "total_relationships": 0,
                    "node_types": {}
                }
            },
            "nodes": [],
            "relationships": [],
            "integrity": {}
        }

        # Processar resultados
        seen_nodes = set()
        seen_relationships = set()

        for record in results:
            node = record['node']
            node_id = node.element_id

            if node_id not in seen_nodes:
                backup_data['nodes'].append({
                    "id": node_id,
                    "labels": list(node.labels),
                    "properties": dict(node)
                })
                seen_nodes.add(node_id)

            # Adicionar relacionamentos
            for rel in record['relationships'] or []:
                rel_id = rel.element_id
                if rel_id not in seen_relationships:
                    backup_data['relationships'].append({
                        "id": rel_id,
                        "type": rel.type,
                        "start": rel.start_node.element_id,
                        "end": rel.end_node.element_id,
                        "properties": dict(rel)
                    })
                    seen_relationships.add(rel_id)

            # Adicionar nós conectados se não estiverem no filtro principal
            for connected in record['connected_nodes'] or []:
                conn_id = connected.element_id
                if conn_id not in seen_nodes:
                    backup_data['nodes'].append({
                        "id": conn_id,
                        "labels": list(connected.labels),
                        "properties": dict(connected),
                        "connected_only": True  # Marca como nó conectado
                    })
                    seen_nodes.add(conn_id)

        # Atualizar estatísticas
        backup_data['metadata']['statistics']['total_nodes'] = len(backup_data['nodes'])
        backup_data['metadata']['statistics']['total_relationships'] = len(backup_data['relationships'])

        # Contar tipos de nós
        for node in backup_data['nodes']:
            for label in node['labels']:
                backup_data['metadata']['statistics']['node_types'][label] = \
                    backup_data['metadata']['statistics']['node_types'].get(label, 0) + 1

        # Calcular hash de integridade
        content_str = json.dumps(backup_data['nodes'] + backup_data['relationships'],
                                sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()

        backup_data['integrity'] = {
            "hash": content_hash,
            "algorithm": "SHA256",
            "nodes_checksum": hashlib.md5(
                json.dumps(backup_data['nodes'], sort_keys=True).encode()
            ).hexdigest(),
            "relationships_checksum": hashlib.md5(
                json.dumps(backup_data['relationships'], sort_keys=True).encode()
            ).hexdigest()
        }

        # Salvar arquivo
        filename = f"THEME_{theme_name}_{timestamp}.json"
        filepath = self.backup_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        # Criar ZIP com validação
        zip_name = f"THEME_{theme_name}_{timestamp}.zip"
        zip_path = self.backup_dir / zip_name

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(filepath, filename)

            # Adicionar arquivo de validação
            validation = {
                "original_hash": content_hash,
                "file_size": filepath.stat().st_size,
                "node_count": len(backup_data['nodes']),
                "relationship_count": len(backup_data['relationships']),
                "theme": theme_name,
                "timestamp": timestamp
            }

            zf.writestr("validation.json", json.dumps(validation, indent=2))

        # Remover JSON temporário
        filepath.unlink()

        logger.info(f"Backup temático criado: {zip_name}")
        logger.info(f"  • Nós: {len(backup_data['nodes'])}")
        logger.info(f"  • Relacionamentos: {len(backup_data['relationships'])}")
        logger.info(f"  • Hash: {content_hash[:16]}...")

        return str(zip_path)

    def create_all_thematic_backups(self) -> Dict[str, str]:
        """Cria backups de todos os temas definidos"""

        theme_groups = self.get_smart_themes()
        backup_files = {}

        for theme_name, filters in theme_groups.items():
            if not filters and theme_name != "general":
                continue

            # Para "general", pegar tudo sem categoria específica
            if theme_name == "general":
                filters = ["uncategorized", "general", "misc"]

            try:
                filepath = self.backup_by_theme(theme_name, filters)
                backup_files[theme_name] = filepath
                logger.info(f"✅ Backup '{theme_name}' criado: {filepath}")
            except Exception as e:
                logger.error(f"❌ Erro no backup '{theme_name}': {e}")
                backup_files[theme_name] = f"ERRO: {str(e)}"

        # Criar índice mestre
        self._create_master_index(backup_files)

        return backup_files

    def _create_master_index(self, backup_files: Dict[str, str]):
        """Cria índice mestre dos backups temáticos"""

        index = {
            "created_at": datetime.now().isoformat(),
            "total_themes": len(backup_files),
            "backups": []
        }

        for theme, filepath in backup_files.items():
            if filepath.startswith("ERRO"):
                continue

            path = Path(filepath)
            if path.exists():
                index["backups"].append({
                    "theme": theme,
                    "file": path.name,
                    "size_kb": path.stat().st_size / 1024,
                    "created": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                })

        index_path = self.backup_dir / "MASTER_INDEX.json"
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)

        logger.info(f"📚 Índice mestre criado: {index_path}")

    def validate_backup(self, zip_path: str) -> bool:
        """Valida integridade de um backup"""

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Ler validação
                validation_data = json.loads(zf.read("validation.json"))

                # Extrair e verificar dados
                files = [f for f in zf.namelist() if f.endswith('.json') and f != 'validation.json']

                if not files:
                    logger.error("Nenhum arquivo de dados encontrado")
                    return False

                # Ler dados do backup
                backup_data = json.loads(zf.read(files[0]))

                # Recalcular hash
                content_str = json.dumps(
                    backup_data['nodes'] + backup_data['relationships'],
                    sort_keys=True
                )
                calculated_hash = hashlib.sha256(content_str.encode()).hexdigest()

                # Comparar
                if calculated_hash == validation_data['original_hash']:
                    logger.info(f"✅ Backup válido: {zip_path}")
                    return True
                else:
                    logger.error(f"❌ Backup corrompido: {zip_path}")
                    return False

        except Exception as e:
            logger.error(f"Erro ao validar backup: {e}")
            return False


def add_backup_tools_to_mcp(mcp_instance, neo4j_connection):
    """Adiciona ferramentas de backup temático ao MCP"""

    backup_system = ThematicBackup(neo4j_connection)

    @mcp_instance.tool()
    def backup_by_theme(
        theme: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Cria backup de um tema específico

        Args:
            theme: Nome do tema (learning_knowledge, technical, etc.)
            validate: Se deve validar o backup após criar

        Returns:
            Informações do backup criado
        """

        theme_groups = backup_system.get_smart_themes()

        if theme not in theme_groups:
            return {
                "error": f"Tema '{theme}' não reconhecido",
                "available_themes": list(theme_groups.keys())
            }

        filepath = backup_system.backup_by_theme(theme, theme_groups[theme])

        result = {
            "success": True,
            "theme": theme,
            "file": filepath,
            "size_kb": Path(filepath).stat().st_size / 1024
        }

        if validate:
            result["valid"] = backup_system.validate_backup(filepath)

        return result

    @mcp_instance.tool()
    def backup_all_themes() -> Dict[str, Any]:
        """
        Cria backups de todos os temas definidos

        Returns:
            Lista de backups criados com estatísticas
        """

        backup_files = backup_system.create_all_thematic_backups()

        return {
            "success": True,
            "total_themes": len(backup_files),
            "backups": backup_files,
            "master_index": str(backup_system.backup_dir / "MASTER_INDEX.json")
        }

    @mcp_instance.tool()
    def list_available_themes() -> Dict[str, Any]:
        """
        Lista temas disponíveis e estatísticas

        Returns:
            Temas e contagem de nós
        """

        themes = backup_system.analyze_themes()
        groups = backup_system.get_smart_themes()

        return {
            "raw_themes": themes,
            "smart_groups": {
                name: {
                    "filters": filters,
                    "description": _get_theme_description(name)
                }
                for name, filters in groups.items()
            },
            "total_nodes": sum(themes.values())
        }

    @mcp_instance.tool()
    def validate_thematic_backup(filepath: str) -> Dict[str, Any]:
        """
        Valida integridade de um backup temático

        Args:
            filepath: Caminho do arquivo ZIP

        Returns:
            Status da validação
        """

        is_valid = backup_system.validate_backup(filepath)

        return {
            "file": filepath,
            "valid": is_valid,
            "checked_at": datetime.now().isoformat()
        }

    return backup_system


def _get_theme_description(theme_name: str) -> str:
    """Retorna descrição do tema"""
    descriptions = {
        "learning_knowledge": "Aprendizados, conhecimento e insights",
        "communication": "Mensagens e interações",
        "technical": "Código, bugs e implementações",
        "project_work": "Projetos e tarefas",
        "system_components": "Componentes e agentes do sistema",
        "improvements": "Melhorias e otimizações",
        "autonomous": "Sistema autônomo e regras",
        "general": "Itens gerais não categorizados"
    }
    return descriptions.get(theme_name, "Sem descrição")