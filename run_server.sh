#!/bin/bash
# Script para executar o servidor MCP Neo4j de qualquer lugar

cd /home/codable/terminal/mcp-neo4j-py
exec uv run python src/mcp_neo4j/server.py