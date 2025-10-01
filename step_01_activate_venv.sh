#!/bin/bash

# Script para ativar o ambiente virtual do projeto MCP Neo4j
# Uso: source step_01_activate_venv.sh

echo "🚀 Ativando ambiente virtual MCP Neo4j..."

# Verificar se estamos no diretório correto
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do projeto (onde está o pyproject.toml)"
    return 1
fi

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Erro: Ambiente virtual não encontrado. Execute primeiro: python3.11 -m venv venv"
    return 1
fi

# Ativar o ambiente virtual
source venv/bin/activate

# Verificar se a ativação foi bem-sucedida
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✅ Ambiente virtual ativado com sucesso!"
    echo "📍 Python: $(python --version)"
    echo "📍 Diretório: $VIRTUAL_ENV"
    echo ""
    echo "📦 Pacotes instalados:"
    pip list | grep -E "(mcp|neo4j)"
    echo ""
    echo "💡 Para desativar: deactivate"
    echo "💡 Para testar conexão Neo4j: python src/mcp_neo4j/test_neo4j_connection.py"
else
    echo "❌ Falha ao ativar o ambiente virtual"
    return 1
fi
