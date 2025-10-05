"""
Funções de formatação e helpers para o sistema MCP Neo4j.
"""
from typing import Any, Dict, List


def format_namespace(namespace: str) -> str:
    """
    Formata namespace para uso em nomes de tools MCP.

    Args:
        namespace: Namespace a formatar

    Returns:
        Namespace formatado (vazio ou com "_" no final)

    Examples:
        >>> format_namespace("")
        ''
        >>> format_namespace("my_namespace")
        'my_namespace_'
    """
    return f"{namespace}_" if namespace else ""


def sanitize_label(label: str) -> str:
    """
    Sanitiza label do Neo4j removendo caracteres inválidos.

    Args:
        label: Label a sanitizar

    Returns:
        Label sanitizado (apenas caracteres alfanuméricos)

    Examples:
        >>> sanitize_label("My Label!")
        'MyLabel'
        >>> sanitize_label("user-profile")
        'userprofile'
    """
    return "".join(c for c in label if c.isalnum())


def format_entity_dict(entity: Any) -> Dict[str, Any]:
    """
    Converte Entity para dicionário formatado.

    Args:
        entity: Entity (Pydantic model)

    Returns:
        Dicionário com dados formatados
    """
    if hasattr(entity, 'model_dump'):
        return entity.model_dump()
    elif hasattr(entity, 'dict'):
        return entity.dict()
    else:
        return dict(entity)


def format_relation_dict(relation: Any) -> Dict[str, Any]:
    """
    Converte Relation para dicionário formatado.

    Args:
        relation: Relation (Pydantic model)

    Returns:
        Dicionário com dados formatados
    """
    if hasattr(relation, 'model_dump'):
        return relation.model_dump()
    elif hasattr(relation, 'dict'):
        return relation.dict()
    else:
        return dict(relation)


def format_knowledge_graph_response(entities: List[Any], relations: List[Any]) -> str:
    """
    Formata resposta do grafo de conhecimento para apresentação.

    Args:
        entities: Lista de entidades
        relations: Lista de relações

    Returns:
        String formatada com resumo do grafo
    """
    entity_summary = f"Entidades: {len(entities)}"
    relation_summary = f"Relações: {len(relations)}"

    if entities:
        entity_types = {}
        for entity in entities:
            entity_type = getattr(entity, 'type', 'unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        type_details = ", ".join([f"{t}: {c}" for t, c in entity_types.items()])
        entity_summary += f" ({type_details})"

    return f"{entity_summary}\n{relation_summary}"
