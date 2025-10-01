# Configuração Global do Servidor MCP Neo4j

## Como adicionar o servidor MCP de forma global

### Comando utilizado
```bash
claude mcp add --scope user neo4j-memory /Users/2a/.claude/mcp-neo4j-py/.venv/bin/python /Users/2a/.claude/mcp-neo4j-py/src/mcp_neo4j/server.py
```

### Parâmetros explicados
- `--scope user`: Define o escopo como "user" (global) em vez de "local" (projeto)
- `neo4j-memory`: Nome do servidor MCP
- `/Users/2a/.claude/mcp-neo4j-py/.venv/bin/python`: Caminho completo do Python no ambiente virtual
- `/Users/2a/.claude/mcp-neo4j-py/src/mcp_neo4j/server.py`: Caminho do script do servidor

### Verificar a configuração
```bash
# Em qualquer diretório
claude mcp list
```

### Remover configuração global (se necessário)
```bash
# Remove o servidor da configuração global
claude mcp remove neo4j-memory
```

### Arquivo de configuração
A configuração global é salva em:
```
/Users/2a/.claude.json
```

### Diferença entre escopos
- **local**: Servidor disponível apenas no projeto atual (salvo em `.mcp.json`)
- **user**: Servidor disponível globalmente em todos os projetos (salvo em `~/.claude.json`)
- **project**: Servidor disponível no projeto e seus subdiretórios

### Resultado
✅ Servidor MCP Neo4j agora está disponível globalmente em qualquer sessão do Claude Code