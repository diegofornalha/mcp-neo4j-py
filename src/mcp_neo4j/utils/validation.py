"""
Validação de inputs e dados para o sistema MCP Neo4j.
"""
from typing import Any, Dict
from pydantic import BaseModel, Field, field_validator


class MemoryProperties(BaseModel):
    """
    Validação de propriedades de memória.

    Attributes:
        name: Nome da memória (obrigatório, 1-255 caracteres)
        content: Conteúdo da memória (opcional)
        category: Categoria da memória (padrão: "general")
    """
    name: str = Field(min_length=1, max_length=255, description="Nome da memória")
    content: str = Field(default="", description="Conteúdo da memória")
    category: str = Field(default="general", description="Categoria da memória")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Valida que o nome não seja vazio após strip."""
        if not v.strip():
            raise ValueError("Name não pode ser vazio ou apenas espaços")
        return v.strip()

    @field_validator('category')
    @classmethod
    def category_valid(cls, v: str) -> str:
        """Valida e sanitiza categoria."""
        return v.strip().lower() if v else "general"


def validate_label(label: str) -> str:
    """
    Valida label do Neo4j.

    Args:
        label: Label a validar

    Returns:
        Label validado

    Raises:
        ValueError: Se label for inválido

    Examples:
        >>> validate_label("Learning")
        'Learning'
        >>> validate_label("")
        Traceback (most recent call last):
        ...
        ValueError: Label não pode ser vazio
    """
    if not label or not label.strip():
        raise ValueError("Label não pode ser vazio")

    label = label.strip()

    if not label[0].isalpha():
        raise ValueError("Label deve começar com letra")

    if not all(c.isalnum() or c == '_' for c in label):
        raise ValueError("Label deve conter apenas letras, números e underscores")

    return label


def validate_entity_name(name: str) -> str:
    """
    Valida nome de entidade.

    Args:
        name: Nome a validar

    Returns:
        Nome validado

    Raises:
        ValueError: Se nome for inválido
    """
    if not name or not name.strip():
        raise ValueError("Nome da entidade não pode ser vazio")

    name = name.strip()

    if len(name) > 255:
        raise ValueError("Nome da entidade não pode exceder 255 caracteres")

    return name


def validate_relation_type(relation_type: str) -> str:
    """
    Valida tipo de relação.

    Args:
        relation_type: Tipo de relação a validar

    Returns:
        Tipo de relação validado (uppercase, com underscores)

    Raises:
        ValueError: Se tipo de relação for inválido

    Examples:
        >>> validate_relation_type("works_at")
        'WORKS_AT'
        >>> validate_relation_type("KNOWS")
        'KNOWS'
    """
    if not relation_type or not relation_type.strip():
        raise ValueError("Tipo de relação não pode ser vazio")

    relation_type = relation_type.strip().upper()

    if not relation_type[0].isalpha():
        raise ValueError("Tipo de relação deve começar com letra")

    if not all(c.isalnum() or c == '_' for c in relation_type):
        raise ValueError("Tipo de relação deve conter apenas letras, números e underscores")

    return relation_type


def validate_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida propriedades genéricas.

    Args:
        properties: Dicionário de propriedades

    Returns:
        Propriedades validadas

    Raises:
        ValueError: Se propriedades forem inválidas
    """
    if not isinstance(properties, dict):
        raise ValueError("Propriedades devem ser um dicionário")

    if not properties:
        raise ValueError("Propriedades não podem estar vazias")

    if "name" not in properties:
        raise ValueError("Propriedades devem conter 'name'")

    # Validar propriedades usando MemoryProperties
    validated = MemoryProperties(**properties)

    return validated.model_dump()
